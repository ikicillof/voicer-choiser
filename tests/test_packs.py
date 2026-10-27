"""Pruebas del manejo de packs y clips."""

import random
import tempfile
import unittest
from pathlib import Path

from voicer_choicer import packs
from voicer_choicer.errores import PackInvalidoError


class TestPacks(unittest.TestCase):
    def setUp(self):
        self.carpeta_tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.carpeta_tmp.name)
        (self.raiz / "animales").mkdir()
        for nombre in ("gato.wav", "perro.wav", "vaca.wav", "notas.txt"):
            (self.raiz / "animales" / nombre).touch()
        (self.raiz / "vacio").mkdir()

    def tearDown(self):
        self.carpeta_tmp.cleanup()

    def test_solo_lista_packs_con_wav(self):
        self.assertEqual(packs.listar_packs(self.raiz), ["animales"])

    def test_listar_clips_ignora_otros_archivos(self):
        nombres = [c.name for c in packs.listar_clips("animales", self.raiz)]
        self.assertEqual(nombres, ["gato.wav", "perro.wav", "vaca.wav"])

    def test_pack_vacio_o_inexistente(self):
        with self.assertRaises(PackInvalidoError):
            packs.listar_clips("vacio", self.raiz)
        with self.assertRaises(PackInvalidoError):
            packs.listar_clips("no_existe", self.raiz)

    def test_elegir_sin_repetir(self):
        clips = packs.listar_clips("animales", self.raiz)
        elegidos = packs.elegir_clips(clips, 10, random.Random(1))
        self.assertEqual(len(elegidos), 3)
        self.assertEqual(len(set(elegidos)), 3)

    def test_nombre_libre_no_pisa(self):
        ruta = packs.siguiente_nombre_libre("animales", "gato", self.raiz)
        self.assertEqual(ruta.name, "gato_2.wav")

    def test_nombre_de_archivo_seguro(self):
        self.assertEqual(
            packs.nombre_de_archivo_seguro("Risa: Malvada?"), "risa__malvada_"
        )

    def test_nombre_legible(self):
        self.assertEqual(packs.nombre_legible(Path("gato_enojado.wav")), "Gato enojado")


if __name__ == "__main__":
    unittest.main()
