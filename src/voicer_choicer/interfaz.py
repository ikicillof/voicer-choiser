"""Interfaz de consola: todo lo que se imprime o se le pide al usuario.

Separar la interfaz de la lógica permite probar juego.py y puntaje.py sin
teclado ni pantalla, y cambiar la interfaz sin tocar la lógica.
"""

from __future__ import annotations

import os
import time

ANCHO = 50


def limpiar() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def titulo(texto: str) -> None:
    print("=" * ANCHO)
    print(texto.upper().center(ANCHO))
    print("=" * ANCHO)


def mensaje(texto: str = "") -> None:
    print(texto)


def error(texto: str) -> None:
    print(f"[!] {texto}")


def pausa(texto: str = "Presioná Enter para seguir...") -> None:
    input(texto)


def pedir_entero(pregunta: str, minimo: int, maximo: int) -> int:
    """Pide un número hasta que el usuario escriba uno válido."""
    while True:
        respuesta = input(f"{pregunta} [{minimo}-{maximo}]: ").strip()
        try:
            numero = int(respuesta)
        except ValueError:
            error("Escribí un número.")
            continue
        if minimo <= numero <= maximo:
            return numero
        error(f"Tiene que estar entre {minimo} y {maximo}.")


def pedir_texto(
    pregunta: str, largo_maximo: int, prohibidos: set[str] | None = None
) -> str:
    """Pide un texto no vacío, de largo acotado y que no esté en `prohibidos`."""
    prohibidos = prohibidos or set()
    while True:
        texto = input(f"{pregunta}: ").strip()
        if not texto:
            error("No puede quedar vacío.")
        elif len(texto) > largo_maximo:
            error(f"Máximo {largo_maximo} caracteres.")
        elif texto.lower() in {p.lower() for p in prohibidos}:
            error("Ese nombre ya está en uso.")
        else:
            return texto


def elegir_de_lista(pregunta: str, opciones: list[str]) -> int:
    """Muestra opciones numeradas y devuelve el índice elegido (desde 0)."""
    for numero, opcion in enumerate(opciones, start=1):
        print(f"  {numero}. {opcion}")
    return pedir_entero(pregunta, 1, len(opciones)) - 1


def cuenta_regresiva(segundos: int) -> None:
    for restante in range(segundos, 0, -1):
        print(f"  {restante}...", flush=True)
        time.sleep(1)
    print("  ¡AHORA!", flush=True)


def barra(puntos: float, ancho: int = 20) -> str:
    """Barra de progreso de texto: 72 -> '██████████████░░░░░░  72'."""
    llenos = round(puntos / 100 * ancho)
    return "█" * llenos + "░" * (ancho - llenos) + f" {puntos:3.0f}"


def mostrar_resultado(
    jugador: str, timbre: float, tono: float | None, total: int
) -> None:
    print(f"\n  {jugador}")
    print(f"    Timbre  {barra(timbre)}")
    if tono is None:
        print("    Tono    (el clip no tiene melodía)")
    else:
        print(f"    Tono    {barra(tono)}")
    print(f"    TOTAL   {barra(total)}")


def mostrar_tabla(filas: list[tuple[str, ...]], encabezados: tuple[str, ...]) -> None:
    """Tabla de texto con columnas alineadas."""
    anchos = [
        max(len(str(valor)) for valor in columna)
        for columna in zip(encabezados, *filas, strict=False)
    ]
    linea = "  ".join(f"{e:<{a}}" for e, a in zip(encabezados, anchos, strict=True))
    print(linea)
    print("-" * len(linea))
    for fila in filas:
        print("  ".join(f"{v!s:<{a}}" for v, a in zip(fila, anchos, strict=True)))
