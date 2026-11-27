# Definición de los datos

## Origen de los datos

- **Fuente:** dataset público **ESC-50: Dataset for Environmental Sound Classification** (Piczak, 2015), repositorio oficial <https://github.com/karolpiczak/ESC-50>. Los clips fueron extraídos manualmente de grabaciones de campo públicas de [Freesound.org](https://freesound.org).
- **Forma de obtención:** descarga directa por HTTPS del archivo ZIP de GitHub **fijado a un commit**, no de la rama `master`, para que la versión de los datos no cambie aunque el repositorio de origen cambie.

| Atributo | Valor |
| --- | --- |
| Commit de origen | `33c8ce9eb2cf0b1c2f8bcf322eb349b6be34dbb6` (`master` al 2023-10-13) |
| URL de descarga | `https://codeload.github.com/karolpiczak/ESC-50/zip/33c8ce9eb2cf0b1c2f8bcf322eb349b6be34dbb6` |
| Tamaño del ZIP | 645.8 MB |
| SHA-256 del ZIP | `661183a6f53ef04f12c9bd618fed0ddc1713280d6c94a5a5431e844ba6f6a21f` |
| Tamaño extraído | 884 MB, 2.011 archivos (2.000 WAV + metadatos, licencia y README) |
| Licencia | CC BY-NC 3.0 (uso no comercial); el subconjunto ESC-10 es CC BY. Atribuciones por clip en `LICENSE`. |
| Cita | Piczak, K. J. (2015). *ESC: Dataset for Environmental Sound Classification*. ACM Multimedia, 1015–1018. DOI `10.1145/2733373.2806390` |

El commit, la URL y el hash están centralizados en `src/care_sound_monitor/config.py` (`SOURCE_COMMIT`, `SOURCE_URL`, `SOURCE_SHA256`).

## Especificación de los scripts para la carga de datos

| Archivo | Responsabilidad |
| --- | --- |
| `scripts/data_acquisition/main.py` | Punto de entrada (CLI). Descarga, extrae, carga, valida y escribe el reporte `reports/data_acquisition.json`. Devuelve código de salida `1` si falla alguna validación de severidad *error*. |
| `src/care_sound_monitor/config.py` | Constantes: rutas, origen fijado y el "contrato" del dataset (2.000 clips, 50 clases × 40, 5 folds × 400, 44,1 kHz, mono, 5 s). |
| `src/care_sound_monitor/database/acquisition.py` | `download_archive` (descarga en streaming a un archivo `.part` y lo renombra solo si el SHA-256 coincide), `extract_archive` (extracción protegida contra *zip-slip* y normalización de la carpeta a `ESC-50-master`), `acquire` (orquesta ambos pasos; es idempotente). |
| `src/care_sound_monitor/database/loading.py` | `load_metadata` (CSV → `DataFrame` tipado con ruta absoluta de cada WAV), `load_clip` (WAV → `float32` en [-1, 1]), `iter_clips`, `fold_split` (partición por folds predefinidos), `class_names`, `summarize` y `validate_dataset` (15 verificaciones de integridad). |
| `tests/test_data_acquisition.py` | 13 pruebas unitarias sobre un mini-dataset sintético (no requieren descarga; aptas para CI). |

**Ejecución** (desde la raíz del repositorio):

```bash
uv venv --python 3.11 .venv && source .venv/bin/activate   # o python -m venv .venv
pip install -e ".[dev,dvc]"
python scripts/data_acquisition/main.py          # descarga (~1 min) + extracción + validación
python scripts/data_acquisition/main.py --archive /ruta/ESC-50.zip   # reutilizar un ZIP ya descargado
pytest -q                                         # pruebas unitarias
```

**Uso desde código** (fases siguientes):

```python
from care_sound_monitor.database import load_metadata, fold_split, load_clip

df = load_metadata()                      # 2000 filas, una por clip
splits = fold_split(df)                   # train = folds 1-3, val = 4, test = 5
y, sr = load_clip(splits["train"].loc[0, "path"])   # y: (220500,) float32, sr = 44100
```

### Validaciones implementadas (`validate_dataset`) y resultado sobre los datos reales

Ejecución del 2026-11-26: **PASS, 14/15 verificaciones superadas y 1 advertencia documentada**.

| # | Verificación | Severidad | Resultado |
| --- | --- | --- | --- |
| 1 | 2.000 filas en `esc50.csv` | error | ✅ |
| 2 | Sin valores faltantes | error | ✅ |
| 3 | `filename` único | error | ✅ |
| 4 | 50 clases | error | ✅ |
| 5 | 40 clips por clase (balance perfecto) | error | ✅ |
| 6 | Relación `target` ↔ `category` 1:1 | error | ✅ |
| 7 | 5 folds de 400 clips | error | ✅ |
| 8 | El nombre de archivo coincide con `fold`, `take` y `target` | error | ✅ 0 discrepancias |
| 9 | Cada `src_file` está en un único fold **dentro de su clase** (sin fuga) | error | ✅ |
| 10 | Cada `src_file` está en un único fold **entre clases** | advertencia | ⚠️ 4 grabaciones (ver abajo) |
| 11 | ESC-10 = 10 clases completas (400 clips) | error | ✅ |
| 12 | Todos los WAV listados existen | error | ✅ |
| 13 | No hay WAV sin listar | error | ✅ |
| 14 | Formato 44.100 Hz, mono, 220.500 muestras (5 s) | error | ✅ 0 no conformes |
| 15 | Contenido decodificable, no silencioso y offset DC < 0,2 (igual que las pruebas del propio ESC-50) | error | ✅ |

**Hallazgo (advertencia 10):** 4 grabaciones de origen de Freesound se reutilizan en **dos clases distintas y en folds distintos**: `131943` y `209698` (*clock_tick* / *clock_alarm*), y `134049` y `234879` (*hen* / *rooster*). Son 9 clips en total. Esto contradice parcialmente la garantía del README ("fragmentos de una misma grabación en un único fold"). La consideramos una fuga menor entre clases: se documenta, no se modifica el dataset (para conservar la comparabilidad con la literatura) y se revisará en el análisis de errores de esas dos parejas de clases.

## Referencias a rutas o bases de datos origen y destino

El proyecto no usa un motor de base de datos: el "almacén" de destino es un **sistema de archivos versionado con DVC**, y la tabla de metadatos se carga en memoria como `pandas.DataFrame`.

```text
GitHub (commit fijado) ──HTTPS──▶ data/external/ESC-50-33c8ce9.zip ──unzip──▶ data/raw/ESC-50-master/ ──dvc add──▶ caché/remoto DVC
                                   (caché local, ignorado por Git)              (versión de datos v1)
```

### Rutas de origen de datos

- **Ubicación:** `https://codeload.github.com/karolpiczak/ESC-50/zip/<SOURCE_COMMIT>`; copia local cacheada en `data/external/ESC-50-33c8ce9.zip`.
- **Estructura del archivo de origen** (tras extraer y normalizar la carpeta raíz):

```text
data/raw/ESC-50-master/
├── audio/               2.000 archivos {FOLD}-{CLIP_ID}-{TAKE}-{TARGET}.wav (PCM, 44,1 kHz, mono, 5 s; 844 MB)
├── meta/
│   ├── esc50.csv        metadatos, una fila por clip (ver diccionario de datos)
│   └── esc50-human.xlsx resultados del experimento de clasificación humana (no se usa)
├── LICENSE              licencia y atribución por clip
├── README.md            descripción oficial del dataset
├── esc50.gif, pytest.ini, requirements.txt, tests/   material del repositorio original (no se usa)
```

- **Transformación y limpieza en esta fase:** **ninguna sobre los datos**. La versión v1 es el dataset crudo e inmutable. La carga solo (a) tipa las columnas del CSV, (b) agrega `clip_id`, `major_category` y `path`, y (c) valida. El remuestreo a 16 kHz, los log-mel, los embeddings YAMNet, el aumento de datos y el conjunto ruidoso corresponden a las versiones v2–v4 (fase de preprocesamiento).

### Base de datos de destino

- **Destino:** `data/raw/ESC-50-master/`, versionado con **DVC** (`data/raw/ESC-50-master.dvc`, hash de directorio `58f5f86caf19fe90fab4d1a7fcd430bc.dir`, 884.047.129 bytes, 2.011 archivos). Git versiona únicamente el archivo `.dvc`; los datos se suben al remoto DVC del equipo con `dvc push`.
- **Estructura:** la descrita arriba; la tabla lógica es `meta/esc50.csv` enriquecida en memoria (ver `docs/data/data_dictionary.md`). El reporte de procedencia y validación queda en `reports/data_acquisition.json`.
- **Procedimiento de carga y versionado:**

```bash
python scripts/data_acquisition/main.py          # 1. adquirir + validar (exit 0)
dvc add data/raw/ESC-50-master                   # 2. registrar v1 (ya hecho; genera el .dvc)
git add data/raw/ESC-50-master.dvc data/raw/.gitignore
git commit -m "data: add raw ESC-50 (v1)"
dvc remote add -d storage <ruta-o-url-del-remoto-compartido>   # 3. una sola vez, pendiente de definir por el equipo
dvc push && git tag -a data-v1 -m "Raw ESC-50" && git push origin --tags
# Reproducir en otra máquina:  git checkout data-v1 && dvc pull
```

- **Idempotencia:** si el ZIP verificado o la carpeta extraída ya existen, se reutilizan (segunda ejecución ≈ 3 s). `--force` descarga y extrae de nuevo.
