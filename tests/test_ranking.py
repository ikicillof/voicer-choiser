"""Pruebas de la persistencia del ranking en JSON."""

import json
import tempfile
import unittest
from pathlib import Path

from voicer_choicer import ranking


class TestRanking(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.archivo = Path(self.carpeta.name) / "ranking.json"

    def tearDown(self):
        self.carpeta.cleanup()

    def test_archivo_inexistente_da_lista_vacia(self):
        self.assertEqual(ranking.cargar(self.archivo), [])

    def test_registrar_y_ordenar(self):
        ranking.registrar_partida({"Ana": 240, "Beto": 150}, 3, "demo", self.archivo)
        ranking.registrar_partida({"Caro": 90}, 1, "demo", self.archivo)
        mejores = ranking.mejores(10, self.archivo)
        # Caro: 90 en 1 ronda (90 por ronda) supera a Ana: 240 en 3 (80 por ronda).
        self.assertEqual([e["jugador"] for e in mejores], ["Caro", "Ana", "Beto"])

    def test_archivo_corrupto_se_respalda(self):
        self.archivo.write_text("{esto no es json", encoding="utf-8")
        self.assertEqual(ranking.cargar(self.archivo), [])
        self.assertTrue(self.archivo.with_suffix(".corrupto").exists())

    def test_entradas_invalidas_se_ignoran(self):
        datos = [{"jugador": "Ana", "puntaje": 10}, {"jugador": 3}, "basura"]
        self.archivo.write_text(json.dumps(datos), encoding="utf-8")
        self.assertEqual(len(ranking.cargar(self.archivo)), 1)


if __name__ == "__main__":
    unittest.main()
