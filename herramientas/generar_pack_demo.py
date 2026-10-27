"""Genera el pack 'demo' con sonidos sintéticos para probar el juego sin grabar nada.

Uso (desde la raíz del proyecto, con el entorno activado):
    python herramientas/generar_pack_demo.py

Son silbidos y notas: se imitan silbando o tarareando. Para clips de voz,
usar la opción "Grabar un clip nuevo" del menú.
"""

from pathlib import Path

import librosa
import soundfile as sf

SR = 22050
DESTINO = Path(__file__).resolve().parents[1] / "packs" / "demo"


def chirp(desde, hasta, segundos):
    return librosa.chirp(fmin=desde, fmax=hasta, sr=SR, duration=segundos).tolist()


def nota(hz, segundos):
    return librosa.tone(hz, sr=SR, duration=segundos).tolist()


def con_fundido(muestras, segundos=0.05, volumen=0.5):
    """Baja el volumen y suaviza principio y final para que no haga 'clic'."""
    muestras = [volumen * m for m in muestras]
    n = int(segundos * SR)
    for k in range(n):
        factor = k / n
        muestras[k] *= factor
        muestras[-1 - k] *= factor
    return muestras


CLIPS = {
    "silbido_que_sube": lambda: chirp(500, 1000, 1.5),
    "silbido_que_baja": lambda: chirp(1000, 450, 1.5),
    "sirena": lambda: (chirp(600, 900, 0.6) + chirp(900, 600, 0.6)) * 2,
    "dos_notas": lambda: nota(330, 0.8) + nota(440, 0.8),
    "nota_larga": lambda: nota(262, 2.0),
}


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    for nombre, generar in CLIPS.items():
        ruta = DESTINO / f"{nombre}.wav"
        sf.write(ruta, con_fundido(generar()), SR)
        print(f"Creado packs/demo/{ruta.name}")


if __name__ == "__main__":
    main()
