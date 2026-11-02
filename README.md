# Voicer Choicer en consola

Juego de imitación de voz para la consola, inspirado en *Voicer Choicer*. El programa reproduce un clip de audio, cada jugador lo imita por el micrófono y recibe un puntaje de 0 a 100 según qué tan parecido suena (timbre) y qué tan bien siguió la melodía (tono).

El análisis de audio está hecho con **[librosa](https://librosa.org)**, la tecnología investigada en el trabajo práctico. El informe completo está en `docs/`.

- De 1 a 3 jugadores por turnos, en la misma computadora.
- Packs de clips: cada carpeta dentro de `packs/` es un pack con archivos `.wav`.
- Se pueden grabar clips propios desde el menú.
- Ranking guardado en `datos/ranking.json`, sin base de datos.

## Requisitos

- **Windows 10 u 11** (también funciona en Linux y macOS).
- **Python 3.12 o superior.** librosa 1.0 no se instala en versiones anteriores.
- Un **micrófono** y parlantes o auriculares. Con auriculares se evita que el micrófono capte el clip original.
- Conexión a internet solo para instalar las dependencias.

## Instalación (Windows)

Todos los comandos se escriben en **PowerShell** o en el **Símbolo del sistema**, parados en la carpeta del proyecto (la que contiene este README).

1. **Instalar Python 3.12 o 3.13** desde <https://www.python.org/downloads/>. En el instalador, tildar **"Add python.exe to PATH"**. Para verificar:

   ```
   py --version
   ```

2. **Crear el entorno virtual:**

   ```
   py -3.12 -m venv .venv
   ```

3. **Activarlo:**

   ```
   .venv\Scripts\activate
   ```

   Si PowerShell responde que la ejecución de scripts está deshabilitada, correr una sola vez el comando siguiente y volver a activar el entorno:

   ```
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   ```

   Con el entorno activado, la línea del prompt empieza con `(.venv)`.

4. **Instalar las dependencias:**

   ```
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

   El proyecto no se instala: se ejecuta directamente desde esta carpeta.

## Ejecución

```
python main.py
```

La primera vez el juego tarda unos segundos en "preparar el motor de audio". Es la compilación de numba que hace librosa por dentro; después queda guardada.

No hace falta configurar nada más. Las carpetas `datos/` (ranking y log) y `grabaciones/` se crean solas.

## Uso rápido

```
==================================================
                  MENÚ PRINCIPAL
==================================================
  1. Jugar
  2. Ver ranking
  3. Grabar un clip nuevo
  4. Salir
```

1. **Jugar:** se elige un pack, la cantidad de jugadores (1 a 3) y sus nombres. Cada ronda tiene un clip distinto. Para cada jugador:
   - Enter para escuchar el original.
   - Enter cuando esté listo.
   - Cuenta regresiva y a imitar.

   Al final de cada turno aparece el puntaje:

   ```
     Ana
       Timbre  ███████████████░░░░░  74
       Tono    ██████████████████░░  88
       TOTAL   ████████████████░░░░  80
   ```

   El total es 60% timbre y 40% tono. Si el clip no tiene melodía (un ruido, por ejemplo), cuenta solo el timbre.

2. **Ver ranking:** las 10 mejores partidas, ordenadas por promedio por ronda.
3. **Grabar un clip nuevo:** graba 4 segundos y los guarda en el pack que indiques. Si el pack no existe, lo crea.

El pack `demo` trae silbidos y notas sintéticas para probar el juego sin grabar nada; se imitan silbando o tarareando. Para regenerarlo:

```
python -m herramientas.generar_pack_demo
```

**Agregar un pack propio:** crear una carpeta dentro de `packs/` y poner archivos `.wav` mono y de 16 bits, de unos 1 a 4 segundos. El nombre del archivo es el nombre que se muestra: `gato_enojado.wav` aparece como "Gato enojado".

## Pruebas

```
python -m unittest discover tests
```

Las pruebas no usan micrófono: generan señales sintéticas con librosa y reemplazan el audio por *mocks*. Hay que correrlas desde la carpeta del proyecto.

## Estructura

```
voicer-choicer/
├── README.md
├── requirements.txt        # dependencias directas con versión fija
├── main.py                 # punto de entrada y menú
├── juego.py                # funciones de la partida: rondas y turnos
├── interfaz.py             # todo lo que se imprime o se pide por teclado
├── puntaje.py              # análisis y comparación con librosa
├── audio.py                # micrófono, parlantes y .wav
├── packs.py                # carpetas de clips
├── ranking.py              # ranking en JSON
├── config.py               # constantes ajustables
├── tests/                  # pruebas con unittest
├── packs/demo/             # clips de ejemplo
├── herramientas/           # script que genera el pack demo
└── docs/                   # informe y diagramas
```

## Problemas frecuentes

| Problema | Solución |
|---|---|
| `py` no se reconoce como comando | Reinstalar Python tildando "Add python.exe to PATH", o usar la ruta completa a `python.exe`. |
| `ERROR: ... requires a different Python` al instalar librosa | Tenés Python 3.11 o anterior. Instalar 3.12 o 3.13 y crear el `.venv` de nuevo con `py -3.12`. |
| "No se encontró ningún micrófono conectado" | Conectar el micrófono antes de abrir el juego y revisar que Windows lo tenga como dispositivo de entrada predeterminado: Configuración → Sistema → Sonido. |
| Siempre dice "No se escuchó nada" | Windows puede estar bloqueando el micrófono para las apps de escritorio: Configuración → Privacidad y seguridad → Micrófono. También se puede subir el volumen de entrada o bajar `PICO_MINIMO` en `config.py`. |
| La primera ronda tarda mucho | Es la compilación de numba. Pasa una sola vez; las siguientes ejecuciones arrancan más rápido. |
| `ModuleNotFoundError` al importar `audio`, `config`, `juego`, etc. | Los comandos se corren desde la carpeta del proyecto, con el entorno activado (`.venv\Scripts\activate`). |
| "tiene que ser mono y de 16 bits" | Un clip de `packs/` no es mono o no es de 16 bits. Convertirlo (por ejemplo con Audacity) o volver a grabarlo desde el menú. |
| Los puntajes parecen muy altos o muy bajos | Ajustar `ESCALA_COSTO_TIMBRE` y `ERROR_TONO_MAXIMO` en `config.py`. En la sección 4.13 del informe está cómo se calibraron. |

## Dependencias

| Paquete | Versión | Uso |
|---|---|---|
| librosa | 1.0.0 | MFCC, pyin, DTW, recorte de silencios y carga de audio. Instala además NumPy, SciPy, numba, soundfile, soxr, joblib y otras. |
| sounddevice | 0.5.5 | Grabar y reproducir. En Windows ya incluye PortAudio. |

El resto (`wave`, `json`, `pathlib`, `random`, `statistics`, `logging`, `unittest`) viene con Python. Los `.wav` se leen y escriben con el módulo `wave`.
