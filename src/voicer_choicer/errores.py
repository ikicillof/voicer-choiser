"""Excepciones propias del juego.

Tener una jerarquía propia permite que main.py capture "cualquier error del
juego" con un solo except, sin tapar errores de programación (TypeError, etc.).
"""


class ErrorJuego(Exception):
    """Base de todos los errores esperables del juego."""


class ErrorAudio(ErrorJuego):
    """No se pudo grabar, reproducir o leer un audio."""


class GrabacionVaciaError(ErrorJuego):
    """La grabación quedó en silencio o es demasiado corta para analizarla."""


class PackInvalidoError(ErrorJuego):
    """El pack elegido no existe o no tiene clips .wav."""
