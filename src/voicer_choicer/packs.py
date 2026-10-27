"""Packs de clips: cada pack es una carpeta dentro de packs/ con archivos .wav."""

from __future__ import annotations

import random
from pathlib import Path

from voicer_choicer import config
from voicer_choicer.errores import PackInvalidoError

EXTENSION = ".wav"


def listar_packs(carpeta: Path = config.CARPETA_PACKS) -> list[str]:
    """Nombres de los packs que tienen al menos un clip, en orden alfabético."""
    if not carpeta.is_dir():
        return []
    return sorted(
        sub.name
        for sub in carpeta.iterdir()
        if sub.is_dir() and any(sub.glob(f"*{EXTENSION}"))
    )


def listar_clips(nombre_pack: str, carpeta: Path = config.CARPETA_PACKS) -> list[Path]:
    """Rutas de los clips de un pack, en orden alfabético."""
    ruta = carpeta / nombre_pack
    if not ruta.is_dir():
        raise PackInvalidoError(f"No existe el pack '{nombre_pack}'.")
    clips = sorted(ruta.glob(f"*{EXTENSION}"))
    if not clips:
        raise PackInvalidoError(
            f"El pack '{nombre_pack}' no tiene archivos {EXTENSION}."
        )
    return clips


def elegir_clips(
    clips: list[Path], cantidad: int, azar: random.Random | None = None
) -> list[Path]:
    """Elige `cantidad` clips distintos al azar (o todos, si hay menos).

    random.sample elige sin repetición, así no toca dos veces el mismo clip
    en una partida.
    """
    azar = azar or random.Random()
    return azar.sample(clips, min(cantidad, len(clips)))


def nombre_legible(ruta: Path) -> str:
    """'gato_enojado.wav' -> 'Gato enojado'."""
    return ruta.stem.replace("_", " ").replace("-", " ").capitalize()


def nombre_de_archivo_seguro(texto: str) -> str:
    """Deja solo letras, números, '_' y '-' (Windows no acepta : ? * etc.)."""
    return "".join(c if c.isalnum() or c in "_-" else "_" for c in texto.lower())


def siguiente_nombre_libre(
    nombre_pack: str, base: str, carpeta: Path = config.CARPETA_PACKS
) -> Path:
    """Ruta para un clip nuevo sin pisar uno existente: base.wav, base_2.wav, ..."""
    destino = carpeta / nombre_pack
    candidato = destino / f"{base}{EXTENSION}"
    numero = 2
    while candidato.exists():
        candidato = destino / f"{base}_{numero}{EXTENSION}"
        numero += 1
    return candidato
