"""Lógica de una partida: turnos, rondas y acumulación de puntos."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from voicer_choicer import audio, config, interfaz, packs, puntaje, ranking
from voicer_choicer.errores import ErrorAudio, GrabacionVaciaError

log = logging.getLogger(__name__)

INTENTOS_POR_TURNO = 2  # si la grabación sale vacía, se puede repetir una vez


class Partida:
    """Una partida de 1 a MAX_JUGADORES jugadores sobre un pack."""

    def __init__(self, jugadores: list[str], nombre_pack: str, rondas: int) -> None:
        self.jugadores = jugadores
        self.nombre_pack = nombre_pack
        self.clips = packs.elegir_clips(packs.listar_clips(nombre_pack), rondas)
        # Puntos de cada jugador en cada ronda. Diccionario: acceso O(1) por nombre.
        self.puntos: dict[str, list[int]] = {j: [] for j in jugadores}
        # Caché de análisis de los originales: cada clip se analiza una sola
        # vez aunque lo imiten tres jugadores.
        self._analisis_originales: dict[Path, puntaje.Analisis] = {}

    # ------------------------------------------------------------------
    def jugar(self) -> dict[str, int]:
        """Juega todas las rondas y devuelve el total de cada jugador."""
        for numero, clip in enumerate(self.clips, start=1):
            self._jugar_ronda(numero, clip)
        totales = self.totales()
        ranking.registrar_partida(totales, len(self.clips), self.nombre_pack)
        return totales

    def totales(self) -> dict[str, int]:
        return {jugador: sum(lista) for jugador, lista in self.puntos.items()}

    # ------------------------------------------------------------------
    def _jugar_ronda(self, numero: int, clip: Path) -> None:
        interfaz.limpiar()
        interfaz.titulo(f"Ronda {numero} de {len(self.clips)}")
        interfaz.mensaje(f"Clip: {packs.nombre_legible(clip)}\n")
        original = self._analisis_original(clip)
        segundos = audio.duracion(clip) + config.SEGUNDOS_EXTRA_GRABACION

        for jugador in self.jugadores:
            puntos = self._turno(jugador, clip, original, segundos)
            self.puntos[jugador].append(puntos)

        interfaz.mensaje("\nPuntaje acumulado:")
        for jugador, total in sorted(
            self.totales().items(), key=lambda par: par[1], reverse=True
        ):
            interfaz.mensaje(f"  {jugador:<{config.LARGO_MAXIMO_NOMBRE}} {total}")
        interfaz.pausa()

    def _analisis_original(self, clip: Path) -> puntaje.Analisis:
        if clip not in self._analisis_originales:
            self._analisis_originales[clip] = puntaje.analizar_archivo(clip)
        return self._analisis_originales[clip]

    def _turno(
        self, jugador: str, clip: Path, original: puntaje.Analisis, segundos: float
    ) -> int:
        """Un jugador escucha el clip, lo imita y recibe su puntaje."""
        interfaz.mensaje(f"\nTurno de {jugador}. Escuchá el original:")
        interfaz.pausa("Enter para escuchar...")
        audio.reproducir(clip)

        for intento in range(1, INTENTOS_POR_TURNO + 1):
            interfaz.pausa("Enter cuando estés listo para imitarlo...")
            interfaz.cuenta_regresiva(config.SEGUNDOS_CUENTA_REGRESIVA)
            grabacion = audio.grabar(segundos)
            interfaz.mensaje("  Analizando...")
            try:
                imitacion = puntaje.analizar(grabacion)
            except GrabacionVaciaError as error:
                interfaz.error(str(error))
                if intento < INTENTOS_POR_TURNO:
                    continue
                interfaz.mensaje("  Turno perdido: 0 puntos.")
                return 0
            break

        resultado = puntaje.comparar(original, imitacion)
        interfaz.mostrar_resultado(
            jugador, resultado.timbre, resultado.tono, resultado.total
        )
        log.info("%s imitó %s: %s", jugador, clip.name, resultado)
        if config.GUARDAR_GRABACIONES:
            self._guardar_grabacion(jugador, clip, grabacion)
        return resultado.total

    def _guardar_grabacion(self, jugador: str, clip: Path, grabacion) -> None:
        sello = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta = (
            config.CARPETA_GRABACIONES
            / f"{sello}_{packs.nombre_de_archivo_seguro(jugador)}_{clip.stem}.wav"
        )
        try:
            audio.guardar(ruta, grabacion)
        except ErrorAudio as error:  # no es grave: se avisa en el log y se sigue
            log.warning("No se guardó la grabación: %s", error)
