"""Ranking de puntajes guardado en un archivo JSON dentro del proyecto.

Formato de datos/ranking.json: una lista de entradas, cada una un diccionario
    {"jugador": "Ana", "puntaje": 213, "rondas": 3, "pack": "demo",
     "fecha": "2026-11-05 18:30"}

Se eligió JSON porque viene con Python (módulo json), es texto legible y
se puede abrir a mano para revisar o corregir.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path

from voicer_choicer import config

log = logging.getLogger(__name__)


def cargar(archivo: Path = config.ARCHIVO_RANKING) -> list[dict]:
    """Lee todas las entradas. Si el archivo no existe, devuelve lista vacía.

    Si el archivo está dañado (JSON inválido), se renombra a .corrupto para
    no perder los datos y se arranca un ranking nuevo.
    """
    if not archivo.exists():
        return []
    try:
        with archivo.open(encoding="utf-8") as f:
            datos = json.load(f)
    except json.JSONDecodeError:
        respaldo = archivo.with_suffix(".corrupto")
        os.replace(archivo, respaldo)
        log.warning("ranking.json dañado; se movió a %s", respaldo.name)
        return []
    if not isinstance(datos, list):
        log.warning("ranking.json no tiene una lista; se ignora")
        return []
    return [e for e in datos if _entrada_valida(e)]


def _entrada_valida(entrada: object) -> bool:
    return (
        isinstance(entrada, dict)
        and isinstance(entrada.get("jugador"), str)
        and isinstance(entrada.get("puntaje"), int)
    )


def guardar(entradas: list[dict], archivo: Path = config.ARCHIVO_RANKING) -> None:
    """Escribe todas las entradas de forma segura.

    Primero escribe un archivo temporal y después lo reemplaza de un golpe
    con os.replace. Si el programa se corta a mitad de escritura, el
    ranking anterior queda intacto.
    """
    archivo.parent.mkdir(parents=True, exist_ok=True)
    temporal = archivo.with_suffix(".tmp")
    with temporal.open("w", encoding="utf-8") as f:
        json.dump(entradas, f, ensure_ascii=False, indent=2)
    os.replace(temporal, archivo)


def registrar_partida(
    totales: dict[str, int],
    rondas: int,
    pack: str,
    archivo: Path = config.ARCHIVO_RANKING,
) -> None:
    """Agrega una entrada por jugador al final del ranking."""
    entradas = cargar(archivo)
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    for jugador, puntaje in totales.items():
        entradas.append(
            {
                "jugador": jugador,
                "puntaje": puntaje,
                "rondas": rondas,
                "pack": pack,
                "fecha": fecha,
            }
        )
    guardar(entradas, archivo)


def mejores(cantidad: int = 10, archivo: Path = config.ARCHIVO_RANKING) -> list[dict]:
    """Las `cantidad` mejores partidas, de mayor a menor puntaje.

    Para comparar partidas de distinta cantidad de rondas se ordena por el
    promedio por ronda. sorted usa Timsort: O(n log n).
    """
    entradas = cargar(archivo)
    return sorted(entradas, key=promedio_por_ronda, reverse=True)[:cantidad]


def promedio_por_ronda(entrada: dict) -> float:
    return entrada["puntaje"] / max(1, entrada.get("rondas", 1))
