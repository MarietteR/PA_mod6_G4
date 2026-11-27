# Team Data Science Project Template

Esta plantilla es una implementación de la plantilla de proyecto de Team Data Science Process que actualmente se utiliza en el "Programa de Formación en Machine Learning y Data Science" en la Universidad Nacional de Colombia.

Esta plantilla proporciona las siguientes carpetas y archivos:

* `src`: acá debe ir el código o implementación del proyecto en Python.
* `docs`: en esta carpeta se encuentran las plantillas de los documentos definidos en la metodología.
* `scripts`: esta carpeta debe contener los scripts/notebooks que se ejecutarán.
* `pyproject.toml`: archivo de definición del proyecto en Python.

---

## Proyecto G4: clasificación de sonidos ambientales ESC-50 con MLOps

Ciclo de vida MLOps reproducible (Git + DVC + MLflow, metodología TDSP) sobre el dataset [ESC-50](https://github.com/karolpiczak/ESC-50). Paquete Python: `src/esc50_mlops`.

### Inicio rápido: adquisición y carga de datos (versión de datos v1)

```bash
uv venv --python 3.11 .venv && source .venv/bin/activate   # o: python3.11 -m venv .venv
pip install -e ".[dev,dvc]"
python scripts/data_acquisition/main.py    # descarga ESC-50 (commit fijado, SHA-256 verificado), extrae y valida
pytest -q                                   # pruebas unitarias (offline)
dvc pull                                    # alternativa a la descarga, una vez configurado el remoto DVC
```

Documentación de esta fase: [`docs/business_understanding/project_charter.md`](docs/business_understanding/project_charter.md), [`docs/data/data_definition.md`](docs/data/data_definition.md), [`docs/data/data_dictionary.md`](docs/data/data_dictionary.md).
