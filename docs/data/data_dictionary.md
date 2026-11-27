# Diccionario de datos

Dataset: **ESC-50** (commit `33c8ce9`, versión de datos **v1**). 2.000 clips de audio ambiental de 5 s, 50 clases balanceadas (40 clips por clase), 5 categorías principales, 5 folds predefinidos, 1.524 grabaciones de origen distintas de Freesound. Cifras verificadas con `scripts/data_acquisition/main.py` el 2026-11-26.

## Base de datos 1: metadatos de clips (`meta/esc50.csv`)

Tabla con una fila por clip (2.000 filas × 7 columnas originales). La función `load_metadata()` la carga con los tipos indicados y agrega 3 columnas derivadas (marcadas como *derivada*).

| Variable | Descripción | Tipo de dato | Rango/Valores posibles | Fuente de datos |
| --- | --- | --- | --- | --- |
| `filename` | Nombre del archivo WAV, con formato `{FOLD}-{CLIP_ID}-{TAKE}-{TARGET}.wav`. Clave primaria. | texto (`string`) | 2.000 valores únicos, p. ej. `1-100032-A-0.wav` | `data/raw/ESC-50-master/meta/esc50.csv` |
| `fold` | Fold de validación cruzada predefinido. Agrupa los fragmentos de una misma grabación de origen para evitar fugas. **No se debe partir el dataset al azar.** | entero (`int8`) | {1, 2, 3, 4, 5}; 400 clips por fold | `meta/esc50.csv` |
| `target` | **Variable objetivo.** Índice numérico de la clase. | entero (`int8`), categórico nominal | [0, 49]; 40 clips por clase | `meta/esc50.csv` |
| `category` | Nombre de la clase (equivalente 1:1 a `target`). | categórico (`category`) | 50 valores; ver Base de datos 3 | `meta/esc50.csv` |
| `esc10` | Indica si el clip pertenece al subconjunto ESC-10 (10 clases, licencia CC BY). | booleano | `True` (400 clips, 10 clases) / `False` (1.600) | `meta/esc50.csv` |
| `src_file` | ID de la grabación original en Freesound de la que se extrajo el clip. Varios clips pueden venir de la misma grabación. | texto (`string`) | 1.524 IDs distintos; de 1 a 8 clips por grabación | `meta/esc50.csv` |
| `take` | Letra que distingue los fragmentos extraídos de una misma grabación. | texto (`string`) | A–H. Frecuencias: A 1.527, B 317, C 88, D 38, E 15, F 7, G 5, H 3 | `meta/esc50.csv` |
| `clip_id` | *Derivada.* ID de Freesound tomado del nombre de archivo; coincide con `src_file` en el 100 % de las filas. | texto (`string`) | igual que `src_file` | `load_metadata()` a partir de `filename` |
| `major_category` | *Derivada.* Categoría principal según el README (`target // 10`). | categórico (`category`) | Animals; Natural soundscapes & water sounds; Human, non-speech sounds; Interior/domestic sounds; Exterior/urban noises (400 clips cada una) | `load_metadata()` + README de ESC-50 |
| `path` | *Derivada.* Ruta absoluta del WAV en la máquina local. | texto (`string`) | `<repo>/data/raw/ESC-50-master/audio/<filename>` | `load_metadata()` |

- **Variable**: nombre de la variable.
- **Descripción**: breve descripción de la variable.
- **Tipo de dato**: tipo de dato que contiene la variable.
- **Rango/Valores posibles**: rango o valores que puede tomar la variable.
- **Fuente de datos**: fuente de los datos de la variable.

## Base de datos 2: señales de audio (`audio/*.wav`)

2.000 archivos WAV (844 MB) que se cargan uno a uno con `load_clip(path)`. Cada archivo corresponde a una fila de la Base de datos 1 a través de `filename`.

| Variable | Descripción | Tipo de dato | Rango/Valores posibles | Fuente de datos |
| --- | --- | --- | --- | --- |
| `waveform` | Señal de audio muestreada (forma de onda). 359 de los 2.000 clips terminan con ≥ 0,5 s de silencio digital (ceros) de relleno hasta completar 5 s. | arreglo `numpy` `float32`, forma `(220500,)` | amplitud en [-1,0, 1,0]; offset DC < 0,2 en todos los clips (verificado) | `data/raw/ESC-50-master/audio/<filename>` |
| `sample_rate` | Frecuencia de muestreo. | entero | 44.100 Hz en los 2.000 clips (verificado) | cabecera WAV (`soundfile`) |
| `channels` | Número de canales. | entero | 1 (mono) en los 2.000 clips (verificado) | cabecera WAV |
| `frames` / duración | Número de muestras por clip. | entero | 220.500 muestras = 5,0 s en los 2.000 clips (verificado) | cabecera WAV |

## Base de datos 3: catálogo de clases

Valores de `target` y `category`, agrupados por `major_category`. ⭐ = clase del subconjunto ESC-10. Todas las clases tienen 40 clips; entre paréntesis, el número de grabaciones de origen (`src_file`) distintas por clase.

| `major_category` | Clases (`target`: `category`) |
| --- | --- |
| **Animals** (0–9) | 0: dog ⭐ (38) · 1: rooster ⭐ (33) · 2: pig (21) · 3: cow (27) · 4: frog (21) · 5: cat (27) · 6: hen (28) · 7: insects (26) · 8: sheep (20) · 9: crow (28) |
| **Natural soundscapes & water sounds** (10–19) | 10: rain ⭐ (40) · 11: sea_waves ⭐ (26) · 12: crackling_fire ⭐ (32) · 13: crickets (38) · 14: chirping_birds (31) · 15: water_drops (32) · 16: wind (25) · 17: pouring_water (31) · 18: toilet_flush (40) · 19: thunderstorm (23) |
| **Human, non-speech sounds** (20–29) | 20: crying_baby ⭐ (18) · 21: sneezing ⭐ (40) · 22: clapping (33) · 23: breathing (33) · 24: coughing (39) · 25: footsteps (32) · 26: laughing (36) · 27: brushing_teeth (29) · 28: snoring (33) · 29: drinking_sipping (33) |
| **Interior/domestic sounds** (30–39) | 30: door_wood_knock (36) · 31: mouse_click (38) · 32: keyboard_typing (37) · 33: door_wood_creaks (26) · 34: can_opening (39) · 35: washing_machine (26) · 36: vacuum_cleaner (30) · 37: clock_alarm (36) · 38: clock_tick ⭐ (40) · 39: glass_breaking (37) |
| **Exterior/urban noises** (40–49) | 40: helicopter ⭐ (15) · 41: chainsaw ⭐ (22) · 42: siren (28) · 43: car_horn (37) · 44: engine (34) · 45: train (28) · 46: church_bells (36) · 47: airplane (32) · 48: fireworks (16) · 49: hand_saw (22) |

## Notas de calidad y uso

- **Particiones:** usar siempre los folds predefinidos (`fold_split`: entrenamiento 1–3, validación 4, prueba 5; o validación cruzada de 5 folds). Una partición aleatoria pondría fragmentos de la misma grabación en entrenamiento y en prueba.
- **Fuga entre clases (hallazgo):** 4 grabaciones de origen aparecen en dos clases y en folds distintos (`131943`, `209698`: clock_tick/clock_alarm; `134049`, `234879`: hen/rooster). Se documenta y no se corrige (ver `data_definition.md`).
- **Sesgo conocido (README del autor):** algunas grabaciones originales tuvieron un preprocesamiento dependiente de la clase (principalmente limitación de banda), lo que puede filtrar información al modelo. Se reportará como limitación.
- **Licencia:** CC BY-NC (uso académico permitido). Si se suben clips de muestra a Git, deben ser de ESC-10 (CC BY) y conservar su atribución.
