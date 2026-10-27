"""Prueba de una partida completa sin micrófono ni teclado.

Se reemplazan (mock) las funciones de audio e interfaz: la "imitación" que
graba cada jugador es directamente el clip original leído del disco.

Ojo: no se puede reemplazar builtins.print, porque numba resuelve print
como una función propia al compilar y falla si encuentra un objeto Mock.
"""

import unittest
from unittest import mock

from voicer_choicer import config, juego, puntaje

CARPETA_DEMO = config.CARPETA_PACKS / "demo"


@unittest.skipUnless(
    CARPETA_DEMO.is_dir(), "falta el pack demo (herramientas/generar_pack_demo.py)"
)
class TestPartida(unittest.TestCase):
    def test_partida_de_dos_jugadores(self):
        clip_actual = {}

        def reproducir(ruta):
            clip_actual["ruta"] = ruta

        def grabar(_segundos):
            return puntaje.cargar(clip_actual["ruta"])  # imitación perfecta

        with (
            mock.patch.object(juego.audio, "reproducir", side_effect=reproducir),
            mock.patch.object(juego.audio, "grabar", side_effect=grabar),
            mock.patch.object(juego.audio, "duracion", return_value=1.5),
            mock.patch.object(juego.interfaz, "pausa"),
            mock.patch.object(juego.interfaz, "limpiar"),
            mock.patch.object(juego.interfaz, "cuenta_regresiva"),
            mock.patch.object(juego.interfaz, "mensaje"),
            mock.patch.object(juego.interfaz, "titulo"),
            mock.patch.object(juego.interfaz, "mostrar_resultado"),
            mock.patch.object(juego.config, "GUARDAR_GRABACIONES", False),
            mock.patch.object(juego.ranking, "registrar_partida") as registrar,
        ):
            partida = juego.Partida(["Ana", "Beto"], "demo", rondas=2)
            totales = partida.jugar()

        self.assertEqual(totales, {"Ana": 200, "Beto": 200})
        registrar.assert_called_once()
        self.assertEqual(len(partida._analisis_originales), 2)  # la caché funcionó


if __name__ == "__main__":
    unittest.main()
