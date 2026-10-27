"""Entrada y salida de audio: micrófono, parlantes y archivos .wav.

Usa sounddevice (grabar/reproducir, sobre PortAudio) y soundfile (leer y
escribir .wav, sobre libsndfile). No hace ningún análisis: eso es tarea de
puntaje.py. Así, si mañana se cambia la librería de micrófono, solo se toca
este archivo.
"""

from __future__ import annotations

import logging
from pathlib import Path

from voicer_choicer import config
from voicer_choicer.errores import ErrorAudio

log = logging.getLogger(__name__)

try:
    import sounddevice as sd
    import soundfile as sf
except OSError as error:  # pragma: no cover - depende de la máquina
    # sounddevice tira OSError si no encuentra la biblioteca PortAudio.
    sd = None
    sf = None
    _ERROR_IMPORTACION = error
else:
    _ERROR_IMPORTACION = None


def _requerir_dispositivos() -> None:
    if sd is None:
        raise ErrorAudio(f"No se pudo inicializar el audio: {_ERROR_IMPORTACION}")


def verificar_microfono() -> str:
    """Devuelve el nombre del micrófono por defecto o lanza ErrorAudio."""
    _requerir_dispositivos()
    try:
        dispositivo = sd.query_devices(kind="input")
    except (sd.PortAudioError, ValueError) as error:
        raise ErrorAudio("No se encontró ningún micrófono conectado.") from error
    return str(dispositivo["name"])


def duracion(ruta: Path) -> float:
    """Duración en segundos de un archivo de audio, sin cargarlo entero."""
    _requerir_dispositivos()
    try:
        return float(sf.info(str(ruta)).duration)
    except RuntimeError as error:
        raise ErrorAudio(
            f"El archivo {ruta.name} está dañado o no es audio."
        ) from error


def reproducir(ruta: Path) -> None:
    """Reproduce un .wav y espera a que termine."""
    _requerir_dispositivos()
    try:
        datos, sr = sf.read(str(ruta), dtype="float32")
        sd.play(datos, sr)
        sd.wait()
    except RuntimeError as error:  # soundfile: archivo ilegible
        raise ErrorAudio(f"No se pudo leer {ruta.name}.") from error
    except sd.PortAudioError as error:
        raise ErrorAudio("No se pudo usar la salida de audio.") from error


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
        raise ErrorAudio("No se pudo grabar desde el micrófono.") from error
    log.debug("Grabados %.1f s a %d Hz", segundos, sr)
    return grabacion[:, 0]  # de forma (muestras, 1) a (muestras,)


def guardar(ruta: Path, senal, sr: int = config.FRECUENCIA_MUESTREO) -> None:
    """Guarda una señal como .wav, creando la carpeta si hace falta."""
    _requerir_dispositivos()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    try:
        sf.write(str(ruta), senal, sr)
    except (RuntimeError, OSError) as error:
        raise ErrorAudio(f"No se pudo guardar {ruta.name}: {error}") from error
