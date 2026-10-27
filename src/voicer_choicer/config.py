"""Configuración central del juego.

Todos los valores ajustables están acá para no tener "números mágicos"
repartidos por el código. Si hay que calibrar el puntaje, se toca este archivo.
"""

from pathlib import Path

# --- Rutas -------------------------------------------------------------------
# config.py está en src/voicer_choicer/, así que la raíz del proyecto
# queda dos carpetas más arriba.
RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
CARPETA_PACKS = RAIZ_PROYECTO / "packs"
CARPETA_DATOS = RAIZ_PROYECTO / "datos"
CARPETA_GRABACIONES = RAIZ_PROYECTO / "grabaciones"
ARCHIVO_RANKING = CARPETA_DATOS / "ranking.json"
ARCHIVO_LOG = CARPETA_DATOS / "voicer.log"

# --- Partida -----------------------------------------------------------------
MAX_JUGADORES = 3
RONDAS_POR_PARTIDA = 3
LARGO_MAXIMO_NOMBRE = 15
SEGUNDOS_CUENTA_REGRESIVA = 3
SEGUNDOS_EXTRA_GRABACION = 1.0  # margen por si el jugador arranca tarde
SEGUNDOS_CLIP_NUEVO = 4.0  # duración al grabar un clip propio
GUARDAR_GRABACIONES = True  # guarda cada imitación en grabaciones/

# --- Audio -------------------------------------------------------------------
FRECUENCIA_MUESTREO = 22050  # Hz; la misma que usa librosa por defecto
UMBRAL_SILENCIO_DB = 30  # para librosa.effects.trim
DURACION_MINIMA_SEG = 0.3  # por debajo de esto la grabación se considera vacía
PICO_MINIMO = 0.02  # amplitud máxima (de 0 a 1) por debajo de la cual es silencio

# --- Análisis con librosa ----------------------------------------------------
TAMANIO_VENTANA = 2048  # muestras por cuadro (n_fft / frame_length)
SALTO = 512  # hop_length: mismo valor para MFCC y pyin
CANTIDAD_MFCC = 14  # se calculan 14 y se descarta el coeficiente 0
NOTA_MINIMA = "C2"  # rango de búsqueda de pyin (unos 65 Hz)
NOTA_MAXIMA = "C7"  # (unos 2093 Hz, alcanza para silbidos)

# --- Puntaje -----------------------------------------------------------------
PESO_TIMBRE = 0.6
PESO_TONO = 0.4
ESCALA_COSTO_TIMBRE = 70.0  # calibrado con audios de prueba (ver informe, 4.13)
ERROR_TONO_MAXIMO = 4.0  # semitonos de error medio que dan 0 puntos de tono
PARES_SONOROS_MINIMOS = 5  # cuadros con tono en ambos audios para evaluar el tono
