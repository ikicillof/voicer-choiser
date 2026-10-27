"""Cálculo del puntaje de una imitación usando librosa.

Es el único módulo del proyecto que importa librosa. El resto del programa
recibe resultados en tipos nativos de Python (float, list), así que no
necesita saber nada de arreglos de NumPy.

Idea general:
    1. Cada audio se "analiza" una sola vez: se recorta el silencio, se
       normaliza el volumen y se extraen dos descripciones por cuadro:
       - MFCC  -> describe el timbre (cómo "suena" la voz)
       - pyin  -> describe el tono (qué nota se está cantando)
    2. Se alinean en el tiempo el original y la imitación con DTW sobre los
       MFCC. Así no se castiga a quien imita más rápido o más lento.
    3. Con ese mismo camino de alineación se comparan las curvas de tono,
       descontando la diferencia de altura entre las dos voces.
"""

from __future__ import annotations

import logging
import math
import statistics
from dataclasses import dataclass
from pathlib import Path

import librosa

from voicer_choicer import config
from voicer_choicer.errores import ErrorAudio, GrabacionVaciaError

log = logging.getLogger(__name__)


@dataclass
class Analisis:
    """Descripción de un audio lista para comparar.

    mfcc: matriz de librosa de forma (13, cuadros). Es lo único que queda
          como arreglo, porque se le pasa directo a librosa.sequence.dtw.
    tono: lista de semitonos (escala MIDI) por cuadro; None en los cuadros
          sin tono (silencio, consonantes, ruido).
    duracion: segundos de audio útil, después de recortar silencios.
    """

    mfcc: object
    tono: list[float | None]
    duracion: float


@dataclass
class Resultado:
    """Puntaje de una imitación, de 0 a 100 en cada componente."""

    timbre: float
    tono: float | None  # None si ninguno de los dos audios tiene tono
    total: int


# --------------------------------------------------------------------------
# Análisis de un audio
# --------------------------------------------------------------------------


def cargar(ruta: Path) -> object:
    """Lee un .wav y lo remuestrea a la frecuencia del juego (mono)."""
    try:
        senal, _ = librosa.load(ruta, sr=config.FRECUENCIA_MUESTREO, mono=True)
    except Exception as error:  # soundfile lanza varios tipos distintos
        raise ErrorAudio(f"No se pudo leer el audio {ruta.name}: {error}") from error
    return senal


def analizar(senal, sr: int = config.FRECUENCIA_MUESTREO) -> Analisis:
    """Recorta, normaliza y extrae timbre y tono de una señal."""
    # 0. librosa.effects.trim mide el silencio en forma RELATIVA al pico de la
    #    propia señal, así que una grabación que es solo ruido de fondo no se
    #    detecta como vacía. Por eso primero se mira el volumen absoluto.
    pico = float(abs(senal).max()) if len(senal) else 0.0
    if pico < config.PICO_MINIMO:
        raise GrabacionVaciaError(
            "No se escuchó nada. Acercate al micrófono y probá de nuevo."
        )

    # 1. Recortar silencios al principio y al final. Sin esto, el medio
    #    segundo que tarda el jugador en arrancar empeora el puntaje.
    recortada, _ = librosa.effects.trim(senal, top_db=config.UMBRAL_SILENCIO_DB)
    duracion = len(recortada) / sr
    if duracion < config.DURACION_MINIMA_SEG:
        raise GrabacionVaciaError(
            "No se escuchó nada. Acercate al micrófono y probá de nuevo."
        )

    # 2. Normalizar para que gritar o susurrar no cambie el resultado.
    recortada = librosa.util.normalize(recortada)

    # 3. Timbre: MFCC. Se descarta el coeficiente 0 (es casi la energía
    #    total, o sea el volumen) y se resta la media de cada coeficiente
    #    (normalización cepstral), que compensa diferencias de micrófono.
    mfcc = librosa.feature.mfcc(
        y=recortada,
        sr=sr,
        n_mfcc=config.CANTIDAD_MFCC,
        n_fft=config.TAMANIO_VENTANA,
        hop_length=config.SALTO,
    )[1:]
    mfcc = mfcc - mfcc.mean(axis=1, keepdims=True)

    # 4. Tono: pyin devuelve la frecuencia fundamental por cuadro (NaN si
    #    el cuadro no tiene tono). Usa el mismo SALTO que los MFCC, así el
    #    cuadro i de una curva corresponde al cuadro i de la otra.
    f0, _, _ = librosa.pyin(
        recortada,
        fmin=librosa.note_to_hz(config.NOTA_MINIMA),
        fmax=librosa.note_to_hz(config.NOTA_MAXIMA),
        sr=sr,
        frame_length=config.TAMANIO_VENTANA,
        hop_length=config.SALTO,
    )
    tono = _a_semitonos(f0.tolist())

    return Analisis(mfcc=mfcc, tono=tono, duracion=duracion)


def analizar_archivo(ruta: Path) -> Analisis:
    """Atajo: cargar + analizar."""
    return analizar(cargar(ruta))


def _a_semitonos(frecuencias: list[float]) -> list[float | None]:
    """Pasa Hz a semitonos en escala MIDI (69 = La 440 Hz); NaN pasa a None.

    En semitonos, "una nota más arriba" siempre suma 1, sin importar si la
    voz es grave o aguda. En Hz no: subir una octava desde 110 Hz suma 110,
    pero desde 440 Hz suma 440.
    """
    return [
        None if math.isnan(hz) else 12 * math.log2(hz / 440.0) + 69
        for hz in frecuencias
    ]


# --------------------------------------------------------------------------
# Comparación
# --------------------------------------------------------------------------


def comparar(original: Analisis, imitacion: Analisis) -> Resultado:
    """Compara dos análisis y devuelve el puntaje."""
    camino, costo_medio = _alinear(original, imitacion)
    puntos_timbre = _puntaje_timbre(costo_medio)
    puntos_tono = _puntaje_tono(original.tono, imitacion.tono, camino)

    if puntos_tono is None:
        # Clips sin tono (por ejemplo, un ruido de puerta): solo cuenta el timbre.
        total = puntos_timbre
    else:
        total = config.PESO_TIMBRE * puntos_timbre + config.PESO_TONO * puntos_tono

    log.debug(
        "costo_medio=%.2f timbre=%.1f tono=%s pasos=%d",
        costo_medio,
        puntos_timbre,
        puntos_tono,
        len(camino),
    )
    return Resultado(timbre=puntos_timbre, tono=puntos_tono, total=round(total))


def _alinear(
    original: Analisis, imitacion: Analisis
) -> tuple[list[tuple[int, int]], float]:
    """Alinea los MFCC con DTW y devuelve (camino, costo medio por paso).

    librosa.sequence.dtw devuelve:
      D  -> matriz de costo acumulado; D[-1, -1] es el costo total.
      wp -> camino de alineación como pares (i, j), del final al principio.
    Se divide el costo total por el largo del camino para que un clip largo
    no tenga más costo que uno corto solo por tener más cuadros.
    """
    costo_acumulado, camino = librosa.sequence.dtw(
        X=original.mfcc, Y=imitacion.mfcc, metric="euclidean"
    )
    pares = [(int(i), int(j)) for i, j in camino.tolist()]
    costo_medio = float(costo_acumulado[-1, -1]) / len(pares)
    return pares, costo_medio


def _puntaje_timbre(costo_medio: float) -> float:
    """Convierte el costo DTW (0 = idéntico) en puntos de 0 a 100.

    Se usa una curva exponencial decreciente: baja rápido al principio y
    después se aplana, así una imitación mala y una pésima no quedan con
    puntajes negativos ni muy distintos entre sí.
    """
    return 100.0 * math.exp(-costo_medio / config.ESCALA_COSTO_TIMBRE)


def _puntaje_tono(
    tono_original: list[float | None],
    tono_imitacion: list[float | None],
    camino: list[tuple[int, int]],
) -> float | None:
    """Error medio de tono (en semitonos) sobre el camino de alineación.

    1. Se toman los pasos del camino donde los dos audios tienen tono y se
       calcula la mediana de las diferencias. Ese es el "corrimiento" de la
       imitación: una voz grave que imita una aguda canta la misma melodía,
       pero varios semitonos más abajo. Restarlo hace que importe la forma
       de la melodía y no la altura absoluta.
    2. En cada paso donde el original tiene tono:
       - si la imitación también tiene, el error es la diferencia ya
         corregida (con tope en ERROR_TONO_MAXIMO);
       - si la imitación no tiene tono ahí (silencio, ruido, susurro),
         cuenta como error máximo. Así un ruido no "acierta" por azar.
    """
    tope = config.ERROR_TONO_MAXIMO
    pares = [
        (tono_original[i], tono_imitacion[j])
        for i, j in camino
        if i < len(tono_original)
        and j < len(tono_imitacion)
        and tono_original[i] is not None
    ]
    if len(pares) < config.PARES_SONOROS_MINIMOS:
        return None  # el original casi no tiene tono: no se evalúa

    diferencias = [a - b for a, b in pares if b is not None]
    if len(diferencias) < config.PARES_SONOROS_MINIMOS:
        return 0.0  # el original tenía melodía y la imitación no
    corrimiento = statistics.median(diferencias)

    errores = [
        tope if b is None else min(abs(a - b - corrimiento), tope) for a, b in pares
    ]
    return 100.0 * (1.0 - statistics.fmean(errores) / tope)


def precalentar() -> None:
    """Fuerza la compilación de numba antes de la primera ronda.

    Varias funciones internas de librosa (DTW, Viterbi de pyin) están
    compiladas con numba la primera vez que se llaman. Esa primera llamada
    puede tardar varios segundos; mejor que pase en el menú y no en medio
    del turno de un jugador.
    """
    tono = librosa.tone(220, sr=config.FRECUENCIA_MUESTREO, duration=1.0)
    analisis = analizar(tono)
    comparar(analisis, analisis)
