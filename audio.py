"""Entrada y salida de audio: micrófono, parlantes y archivos .wav.

Usa sounddevice (grabar/reproducir, sobre PortAudio) y el módulo wave de la
biblioteca estándar (leer y escribir .wav de 16 bits, mono). No hace ningún
análisis: eso es tarea de puntaje.py. Así, si mañana se cambia la librería de
micrófono, solo se toca este archivo.
"""

from __future__ import annotations

import logging
import wave
from pathlib import Path

import numpy as np

import config

log = logging.getLogger(__name__)

try:
    import sounddevice as sd
except OSError as error:  # pragma: no cover - depende de la máquina
    # sounddevice tira OSError si no encuentra la biblioteca PortAudio.
    sd = None
    _ERROR_IMPORTACION = error
else:
    _ERROR_IMPORTACION = None

BYTES_POR_MUESTRA = 2  # .wav de 16 bits
ESCALA_INT16 = 32768.0  # int16 (-32768..32767) <-> float32 (-1..1)


def _requerir_dispositivos() -> None:
    if sd is None:
        raise RuntimeError(f"No se pudo inicializar el audio: {_ERROR_IMPORTACION}")


def _abrir_wav(ruta: Path) -> wave.Wave_read:
    """Abre un .wav para leer y valida que sea mono y de 16 bits."""
    try:
        archivo = wave.open(str(ruta), "rb")
    except (wave.Error, EOFError) as error:
        raise RuntimeError(
            f"El archivo {ruta.name} está dañado o no es audio."
        ) from error
    canales = archivo.getnchannels()
    bits = archivo.getsampwidth() * 8
    if canales != 1 or bits != BYTES_POR_MUESTRA * 8:
        archivo.close()
        raise ValueError(
            f"El archivo {ruta.name} tiene que ser mono y de 16 bits "
            f"(tiene {canales} canal(es) y {bits} bits)."
        )
    return archivo


def verificar_microfono() -> str:
    """Devuelve el nombre del micrófono por defecto o lanza RuntimeError."""
    _requerir_dispositivos()
    try:
        dispositivo = sd.query_devices(kind="input")
    except (sd.PortAudioError, ValueError) as error:
        raise RuntimeError("No se encontró ningún micrófono conectado.") from error
    return str(dispositivo["name"])


def duracion(ruta: Path) -> float:
    """Duración en segundos de un archivo de audio, sin cargarlo entero."""
    with _abrir_wav(ruta) as archivo:
        return archivo.getnframes() / archivo.getframerate()


def reproducir(ruta: Path) -> None:
    """Reproduce un .wav y espera a que termine."""
    _requerir_dispositivos()
    with _abrir_wav(ruta) as archivo:
        sr = archivo.getframerate()
        crudo = archivo.readframes(archivo.getnframes())
    # De int16 a float32 entre -1 y 1, como entrega sounddevice al grabar.
    datos = np.frombuffer(crudo, dtype="<i2").astype(np.float32) / ESCALA_INT16
    try:
        sd.play(datos, sr)
        sd.wait()
    except sd.PortAudioError as error:
        raise RuntimeError("No se pudo usar la salida de audio.") from error


def grabar(segundos: float, sr: int = config.FRECUENCIA_MUESTREO):
    """Graba del micrófono por defecto y devuelve la señal mono.

    sd.rec arranca la grabación en otro hilo (el callback de PortAudio) y
    vuelve enseguida; sd.wait() bloquea hasta que se llenó el búfer.
    """
    _requerir_dispositivos()
    try:
        grabacion = sd.rec(
            int(segundos * sr), samplerate=sr, channels=1, dtype="float32"
        )
        sd.wait()
    except sd.PortAudioError as error:
        raise RuntimeError("No se pudo grabar desde el micrófono.") from error
    log.debug("Grabados %.1f s a %d Hz", segundos, sr)
    return grabacion[:, 0]  # de forma (muestras, 1) a (muestras,)


def guardar(ruta: Path, senal, sr: int = config.FRECUENCIA_MUESTREO) -> None:
    """Guarda una señal float entre -1 y 1 como .wav mono de 16 bits.

    Los valores fuera de rango se recortan para que no den la vuelta al
    convertirlos a enteros. Crea la carpeta si hace falta.
    """
    ruta.parent.mkdir(parents=True, exist_ok=True)
    recortada = np.clip(np.asarray(senal, dtype=np.float64), -1.0, 1.0)
    enteros = np.rint(recortada * (ESCALA_INT16 - 1)).astype(np.int16)
    try:
        with wave.open(str(ruta), "wb") as archivo:
            archivo.setnchannels(1)
            archivo.setsampwidth(BYTES_POR_MUESTRA)
            archivo.setframerate(sr)
            archivo.writeframes(enteros.tobytes())
    except (wave.Error, OSError) as error:
        raise RuntimeError(f"No se pudo guardar {ruta.name}: {error}") from error
