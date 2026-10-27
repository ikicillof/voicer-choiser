"""Pruebas del cálculo de puntaje con señales sintéticas generadas por librosa."""

import statistics
import unittest

import librosa

from voicer_choicer import config, puntaje
from voicer_choicer.errores import GrabacionVaciaError

SR = config.FRECUENCIA_MUESTREO


def chirp(desde, hasta, segundos=1.5):
    return librosa.chirp(fmin=desde, fmax=hasta, sr=SR, duration=segundos)


class TestAnalisis(unittest.TestCase):
    def test_silencio_es_grabacion_vacia(self):
        silencio = librosa.tone(440, sr=SR, duration=1.0) * 0.0
        with self.assertRaises(GrabacionVaciaError):
            puntaje.analizar(silencio)

    def test_tono_en_semitonos(self):
        analisis = puntaje.analizar(librosa.tone(220, sr=SR, duration=1.0))
        sonoros = [t for t in analisis.tono if t is not None]
        self.assertGreater(len(sonoros), 10)
        # 220 Hz es el La 3, que en escala MIDI es la nota 57.
        self.assertAlmostEqual(statistics.median(sonoros), 57, delta=0.2)

    def test_semitonos_sin_tono(self):
        self.assertEqual(puntaje._a_semitonos([float("nan")] * 3), [None, None, None])

    def test_mfcc_sin_coeficiente_cero(self):
        analisis = puntaje.analizar(librosa.tone(220, sr=SR, duration=1.0))
        self.assertEqual(analisis.mfcc.shape[0], config.CANTIDAD_MFCC - 1)


class TestComparacion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = puntaje.analizar(chirp(500, 1000))

    def test_misma_senal_da_100(self):
        resultado = puntaje.comparar(self.original, self.original)
        self.assertEqual(resultado.total, 100)

    def test_parecido_gana_a_distinto(self):
        parecido = puntaje.comparar(
            self.original, puntaje.analizar(chirp(480, 950, 1.8))
        )
        distinto = puntaje.comparar(self.original, puntaje.analizar(chirp(1000, 500)))
        self.assertGreater(parecido.total, distinto.total)

    def test_velocidad_distinta_no_castiga_tanto(self):
        # DTW debería absorber que la imitación sea más lenta.
        lento = puntaje.comparar(self.original, puntaje.analizar(chirp(500, 1000, 2.5)))
        self.assertGreater(lento.total, 60)

    def test_puntajes_en_rango(self):
        resultado = puntaje.comparar(self.original, puntaje.analizar(chirp(1000, 500)))
        self.assertTrue(0 <= resultado.timbre <= 100)
        self.assertTrue(0 <= resultado.tono <= 100)
        self.assertTrue(0 <= resultado.total <= 100)


class TestTono(unittest.TestCase):
    def test_otra_altura_misma_melodia(self):
        # La misma melodía cantada 5 semitonos más grave no pierde puntos.
        original = [60.0, 62.0, 64.0, 65.0] * 10
        grave = [t - 5 for t in original]
        camino = [(i, i) for i in range(len(original))]
        self.assertAlmostEqual(puntaje._puntaje_tono(original, grave, camino), 100.0)

    def test_silencio_al_final_no_corre_la_melodia(self):
        # Antes se restaba la mediana de cada curva y unos cuadros de más
        # alcanzaban para correr toda la melodía (ver informe, 4.14).
        original = [-2.5] * 20 + [2.5] * 20
        imitacion = [-2.5] * 20 + [2.5] * 23
        camino = [(min(i, 39), i) for i in range(43)]
        self.assertGreater(puntaje._puntaje_tono(original, imitacion, camino), 99)

    def test_original_sin_tono_no_evalua_tono(self):
        sin_tono = [None] * 50
        camino = [(i, i) for i in range(50)]
        self.assertIsNone(puntaje._puntaje_tono(sin_tono, sin_tono, camino))

    def test_imitacion_muda_da_cero_de_tono(self):
        con_tono = [0.0] * 50
        camino = [(i, i) for i in range(50)]
        self.assertEqual(puntaje._puntaje_tono(con_tono, [None] * 50, camino), 0.0)


if __name__ == "__main__":
    unittest.main()
