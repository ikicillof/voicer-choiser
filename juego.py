"""Lógica de una partida: turnos, rondas y acumulación de puntos.

El estado de una partida es un diccionario con las claves:
    "jugadores": lista de nombres, en orden de turno
    "nombre_pack": pack elegido
    "clips": rutas de los clips que se van a jugar (uno por ronda)
    "rondas_totales": cantidad de rondas (len de "clips")
    "ronda_actual": número de la ronda en curso (0 antes de empezar)
    "puntajes": puntos de cada jugador en cada ronda, por nombre
    "analisis_originales": caché de análisis de los clips originales
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import audio
import config
import interfaz
import packs
import puntaje
import ranking

log = logging.getLogger(__name__)

INTENTOS_POR_TURNO = 2  # si la grabación sale vacía, se puede repetir una vez


def nueva_partida(jugadores: list[str], nombre_pack: str, rondas: int) -> dict:
    """Crea el estado de una partida de 1 a MAX_JUGADORES jugadores sobre un pack."""
    clips = packs.elegir_clips(packs.listar_clips(nombre_pack), rondas)
    return {
        "jugadores": jugadores,
        "nombre_pack": nombre_pack,
        "clips": clips,
        "rondas_totales": len(clips),
        "ronda_actual": 0,
        # Puntos de cada jugador en cada ronda. Diccionario: acceso O(1) por nombre.
        "puntajes": {j: [] for j in jugadores},
        # Caché de análisis de los originales: cada clip se analiza una sola
        # vez aunque lo imiten tres jugadores.
        "analisis_originales": {},
    }


# ----------------------------------------------------------------------
def jugar_partida(partida: dict) -> dict[str, int]:
    """Juega todas las rondas y devuelve el total de cada jugador."""
    for numero, clip in enumerate(partida["clips"], start=1):
        partida["ronda_actual"] = numero
        jugar_ronda(partida, clip)
    return terminar_partida(partida)


def terminar_partida(partida: dict) -> dict[str, int]:
    """Registra la partida en el ranking y devuelve el total de cada jugador."""
    totales = calcular_totales(partida)
    ranking.registrar_partida(
        totales, partida["rondas_totales"], partida["nombre_pack"]
    )
    return totales


def calcular_totales(partida: dict) -> dict[str, int]:
    return {jugador: sum(lista) for jugador, lista in partida["puntajes"].items()}


# ----------------------------------------------------------------------
def jugar_ronda(partida: dict, clip: Path) -> None:
    interfaz.limpiar()
    interfaz.titulo(f"Ronda {partida['ronda_actual']} de {partida['rondas_totales']}")
    interfaz.mensaje(f"Clip: {packs.nombre_legible(clip)}\n")
    original = analisis_original(partida, clip)
    segundos = audio.duracion(clip) + config.SEGUNDOS_EXTRA_GRABACION

    for jugador in partida["jugadores"]:
        puntos = jugar_turno(jugador, clip, original, segundos)
        partida["puntajes"][jugador].append(puntos)

    interfaz.mensaje("\nPuntaje acumulado:")
    for jugador, total in sorted(
        calcular_totales(partida).items(), key=lambda par: par[1], reverse=True
    ):
        interfaz.mensaje(f"  {jugador:<{config.LARGO_MAXIMO_NOMBRE}} {total}")
    interfaz.pausa()


def analisis_original(partida: dict, clip: Path) -> dict:
    cache = partida["analisis_originales"]
    if clip not in cache:
        cache[clip] = puntaje.analizar_archivo(clip)
    return cache[clip]


def jugar_turno(jugador: str, clip: Path, original: dict, segundos: float) -> int:
    """Un jugador escucha el clip, lo imita y recibe su puntaje."""
    interfaz.mensaje(f"\nTurno de {jugador}. Escuchá el original:")
    interfaz.pausa("Enter para escuchar...")
    audio.reproducir(clip)

    imitacion = None
    for _ in range(INTENTOS_POR_TURNO):
        interfaz.pausa("Enter cuando estés listo para imitarlo...")
        interfaz.cuenta_regresiva(config.SEGUNDOS_CUENTA_REGRESIVA)
        grabacion = audio.grabar(segundos)
        interfaz.mensaje("  Analizando...")
        imitacion = puntaje.analizar(grabacion)
        if imitacion is not None:
            break
        interfaz.error(puntaje.MENSAJE_GRABACION_VACIA)

    if imitacion is None:
        interfaz.mensaje("  Turno perdido: 0 puntos.")
        return 0

    resultado = puntaje.comparar(original, imitacion)
    interfaz.mostrar_resultado(
        jugador, resultado["timbre"], resultado["tono"], resultado["total"]
    )
    tono = "-" if resultado["tono"] is None else f"{resultado['tono']:.0f}"
    log.info(
        "%s imitó %s: timbre=%d tono=%s total=%d",
        jugador,
        clip.name,
        resultado["timbre"],
        tono,
        resultado["total"],
    )
    if config.GUARDAR_GRABACIONES:
        guardar_grabacion(jugador, clip, grabacion)
    return resultado["total"]


def guardar_grabacion(jugador: str, clip: Path, grabacion) -> None:
    sello = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta = (
        config.CARPETA_GRABACIONES
        / f"{sello}_{packs.nombre_de_archivo_seguro(jugador)}_{clip.stem}.wav"
    )
    try:
        audio.guardar(ruta, grabacion)
    except RuntimeError as error:  # no es grave: se avisa en el log y se sigue
        log.warning("No se guardó la grabación: %s", error)
