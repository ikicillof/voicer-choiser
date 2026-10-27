"""Punto de entrada: configura el logging y muestra el menú principal."""

from __future__ import annotations

import logging

from voicer_choicer import audio, config, interfaz, packs, puntaje, ranking
from voicer_choicer.errores import ErrorJuego, GrabacionVaciaError
from voicer_choicer.juego import Partida

log = logging.getLogger("voicer_choicer")

OPCIONES_MENU = ["Jugar", "Ver ranking", "Grabar un clip nuevo", "Salir"]


def configurar_logging() -> None:
    config.CARPETA_DATOS.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=config.ARCHIVO_LOG,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )


def main() -> None:
    configurar_logging()
    log.info("Inicio del programa")
    interfaz.limpiar()
    interfaz.titulo("Voicer Choicer")

    try:
        microfono = audio.verificar_microfono()
    except ErrorJuego as error:
        interfaz.error(str(error))
        interfaz.mensaje("Conectá un micrófono y volvé a abrir el juego.")
        return
    interfaz.mensaje(f"Micrófono: {microfono}")
    interfaz.mensaje("Preparando el motor de audio (la primera vez tarda un poco)...")
    puntaje.precalentar()

    while True:
        interfaz.mensaje()
        interfaz.titulo("Menú principal")
        try:
            opcion = interfaz.elegir_de_lista("Elegí una opción", OPCIONES_MENU)
            if opcion == 0:
                menu_jugar()
            elif opcion == 1:
                menu_ranking()
            elif opcion == 2:
                menu_grabar_clip()
            else:
                interfaz.mensaje("¡Hasta la próxima!")
                break
        except ErrorJuego as error:
            # Errores esperables (micrófono, archivos): se avisa y se vuelve al menú.
            log.warning("Error del juego: %s", error)
            interfaz.error(str(error))
        except KeyboardInterrupt:
            interfaz.mensaje("\nSe canceló la acción; volvemos al menú.")
        except (
            EOFError
        ):  # se cerró la entrada estándar (por ejemplo, Ctrl+Z en Windows)
            break
    log.info("Fin del programa")


def menu_jugar() -> None:
    disponibles = packs.listar_packs()
    if not disponibles:
        interfaz.error("No hay packs. Creá uno con 'Grabar un clip nuevo'.")
        return
    interfaz.titulo("Nueva partida")
    nombre_pack = disponibles[interfaz.elegir_de_lista("Elegí un pack", disponibles)]

    cantidad = interfaz.pedir_entero("¿Cuántos jugadores?", 1, config.MAX_JUGADORES)
    jugadores: list[str] = []
    for numero in range(1, cantidad + 1):
        nombre = interfaz.pedir_texto(
            f"Nombre del jugador {numero}", config.LARGO_MAXIMO_NOMBRE, set(jugadores)
        )
        jugadores.append(nombre)

    partida = Partida(jugadores, nombre_pack, config.RONDAS_POR_PARTIDA)
    totales = partida.jugar()

    interfaz.limpiar()
    interfaz.titulo("Resultado final")
    filas = sorted(totales.items(), key=lambda par: par[1], reverse=True)
    for puesto, (jugador, total) in enumerate(filas, start=1):
        interfaz.mensaje(
            f"  {puesto}. {jugador:<{config.LARGO_MAXIMO_NOMBRE}} {total} puntos"
        )
    interfaz.mensaje(f"\n¡Ganó {filas[0][0]}!")
    interfaz.pausa()


def menu_ranking() -> None:
    interfaz.titulo("Ranking (promedio por ronda)")
    mejores = ranking.mejores(10)
    if not mejores:
        interfaz.mensaje("Todavía no se jugó ninguna partida.")
    else:
        filas = [
            (
                str(i),
                e["jugador"],
                f"{ranking.promedio_por_ronda(e):.1f}",
                e.get("pack", "-"),
                e.get("fecha", "-"),
            )
            for i, e in enumerate(mejores, start=1)
        ]
        interfaz.mostrar_tabla(filas, ("#", "Jugador", "Promedio", "Pack", "Fecha"))
    interfaz.pausa()


def menu_grabar_clip() -> None:
    """Graba un clip propio y lo guarda en un pack (nuevo o existente)."""
    interfaz.titulo("Grabar un clip nuevo")
    nombre_pack = interfaz.pedir_texto("Nombre del pack (existente o nuevo)", 20)
    nombre_clip = interfaz.pedir_texto(
        "Nombre del clip (por ejemplo: gato_enojado)", 30
    )
    destino = packs.siguiente_nombre_libre(
        packs.nombre_de_archivo_seguro(nombre_pack),
        packs.nombre_de_archivo_seguro(nombre_clip),
    )

    interfaz.mensaje(f"Vas a grabar {config.SEGUNDOS_CLIP_NUEVO:.0f} segundos.")
    interfaz.pausa("Enter para empezar...")
    interfaz.cuenta_regresiva(config.SEGUNDOS_CUENTA_REGRESIVA)
    senal = audio.grabar(config.SEGUNDOS_CLIP_NUEVO)
    try:
        puntaje.analizar(senal)  # valida que no haya quedado en silencio
    except GrabacionVaciaError as error:
        interfaz.error(f"{error} El clip no se guardó.")
        return
    audio.guardar(destino, senal)
    interfaz.mensaje(f"Clip guardado en packs/{destino.parent.name}/{destino.name}")
    interfaz.pausa()


if __name__ == "__main__":
    main()
