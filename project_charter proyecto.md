# Project Charter - Entendimiento del Negocio

## Nombre del Proyecto

Sistema de reconocimiento de sonidos domésticos para el apoyo en el cuidado de adultos mayores.

## Objetivo del Proyecto

En la actualidad está creciendo el número de personas mayores que viven solas o cuentan con acompañamiento parcial, lo que dificulta la supervisión continua de su entorno y la identificación oportuna de situaciones que puedan comprometer su bienestar, ya que sus cuidadores no pueden estar presentes durante todo el tiempo. Un sistema que escuche el entorno puede detectar eventos acústicos relevantes dentro de una vivienda y generar notificaciones oportunas para los cuidadores. Entre los posibles eventos de interés se encuentran la caída de objetos, la ruptura de elementos, episodios de tos y periodos inusuales de inactividad acústica. Todo esto sin que el cuidador tenga que revisar constantemente.

**Por qué es importante:** un sistema que genere notificaciones excesivas puede perder credibilidad y provocar que los cuidadores ignoren sus advertencias, mientras que una alerta omitida podría retrasar la atención ante una situación de riesgo. Por eso el proyecto no se limita a clasificar sonidos: busca decidir cuáles importan y cuándo avisar.

**Pregunta central:** ¿Puede un modelo entrenado con ESC-50 distinguir eventos relevantes para el cuidado del ruido ambiental con recall suficiente para alertar, y cómo cambia su desempeño cuando el audio no es un clip limpio y aislado?

**Objetivos específicos:**

1. **Auditar y comprender el dataset** (calidad, balance, artefactos) antes de modelar.
2. **Comparar representaciones y modelos** de clasificación: MFCC con SVM / Random Forest, CNN sobre espectrogramas Mel y embeddings preentrenados.
3. **Agrupar las clases por uso** (urgente, salud, actividad, ambiente) y evaluar la detección de eventos relevantes frente al ruido.
4. **Simular un día de audio continuo** (mezclando clips sobre fondo) para medir falsas alarmas por hora y retardo.
5. **Construir un prototipo con panel de visualización:** línea de tiempo, conteos por hora, comparación con la línea base y alertas simuladas.

## Alcance del Proyecto

**Aclaración de alcance importante:** un clasificador de sonidos no sabe *quién* produjo el sonido. El proyecto asume un **escenario controlado de una sola persona en el espacio monitoreado** (dispositivo en su vivienda o habitación) y no intenta atribuir un sonido a un individuo entre varios.

### Incluye:

- **Descripción de los datos disponibles:**
  - Dataset **ESC-50** (Piczak, 2015): 2.000 clips de audio WAV de 5 segundos, 44,1 kHz y mono, con 50 clases de 40 clips cada una y 5 folds prearmados para validación cruzada. Licencia CC BY-NC 3.0 (uso no comercial).
  - Las 50 clases se agrupan según su uso en el sistema (archivo `data/external/class_groups.csv`):

    | Grupo | Clases | Uso |
    |---|---|---|
    | Urgente (1) | `glass_breaking` | Notificación inmediata |
    | Salud (4) | `coughing`, `sneezing`, `breathing`, `snoring` | Conteo por hora y tendencia |
    | Actividad (16) | Pasos, puertas, agua, cocina, higiene, electrodomésticos, etc. | Señales de rutina; su ausencia prolongada puede alertar |
    | Ambiente (29) | Animales, clima, tráfico, etc. | Se descartan |

  - Hallazgos preliminares de la auditoría de calidad:
    - Todos los clips cumplen el formato esperado, pero 55 presentan saturación y 169 tienen menos de 1 s de audio activo.
    - Los eventos breves están rellenados con silencio digital hasta completar 5 s (mediana de relleno: ~0 % en ambiente y 65 % en urgente).
    - Con solo nivel, relleno y ancho de banda (sin el contenido del sonido), un Random Forest acierta 26 % frente a 2 % del azar. Esto indica riesgo de que un modelo aprenda artefactos y no el sonido.
    - 4 grabaciones originales aparecen en más de un fold, y el grupo urgente tiene una sola clase.
  - Audio propio (opcional) para probar la generalización fuera de ESC-50.

- **Descripción de los resultados esperados:**
  - Clasificación de las 50 clases de ESC-50 agrupadas en 4 grupos de uso.
  - Panel de visualización con eventos, tendencias y alertas simuladas.
  - Evaluación con folds oficiales y con un día sintético de audio continuo.
  - Pruebas con audio propio si es posible.

- **Criterios de éxito del proyecto:**
  - Modelo: F1 macro y por clase superiores al baseline MFCC + Random Forest reportado para ESC-50 (44,3 %)..
  - Alerta urgente: recall de `glass_breaking` y falsas alarmas por hora en el día sintético.
  - Robustez: reportar y analizar la caída de desempeño sin relleno, con ruido y con audio propio.

### Excluye:

- Identificar quién produce el sonido.
- Detección de caídas, voz o gritos (no están en ESC-50).
- Uso comercial (licencia CC BY-NC).
- Dispositivo médico o diagnóstico: el sistema es una herramienta de apoyo, no un sustituto del cuidador.

## Metodología

El proyecto sigue el ciclo de vida de TDSP (Team Data Science Process):

1. **Entendimiento del negocio y carga de datos:** definición del problema y carga y validación de ESC-50 (`src/data/load_esc50.py`).
2. **Auditoría y análisis exploratorio:** revisión de calidad, balance y artefactos del audio (`src/data/audit_dataset.py`), incluida una prueba de fuga con propiedades no semánticas.
3. **Preprocesamiento:** recortar cada clip al segmento activo y reemplazar el relleno de silencio por ruido de fondo real; normalizar el ancho de banda (filtro o remuestreo común), comparando resultados con y sin estas correcciones.
4. **Modelamiento y extracción de características:** MFCC con SVM / Random Forest, CNN sobre espectrogramas Mel y embeddings preentrenados con un clasificador simple. Validación con los folds oficiales, agrupando además por `src_file` para evitar el cruce de grabaciones.
5. **Simulación:** día sintético de audio continuo con eventos mezclados sobre fondo, ventanas deslizantes y umbrales por grupo, para medir falsas alarmas por hora y retardo.
6. **Despliegue:** prototipo con panel de visualización (línea de tiempo, conteos por hora, comparación con la línea base y alertas simuladas).
7. **Evaluación y entrega final.**

**Riesgos y consideraciones éticas:**

- *Fuga por artefactos de preprocesamiento:* normalización, validación por `src_file` y pruebas con audio propio.
- *Una sola clase urgente:* declararlo y evaluar datasets complementarios (por revisar sus licencias).
- *Diferencia entre clips de Freesound y una vivienda real:* día sintético con ruido de fondo y audio propio.
- *Privacidad:* se monitorea el entorno de una persona vulnerable, con datos de salud. Se propone procesamiento local, no guardar audio crudo y consentimiento informado, revisando la Ley 1581 de 2012.
- *Falsas alarmas o alertas perdidas:* umbrales por grupo y métricas de recall y falsas alarmas por hora.

## Cronograma
El cornograma se ve detallado en el documento adjunto en el repositorio



## Equipo del Proyecto

- Ángela Rodriguez: Líder del proyecto
- Brayan Jair Saenz: integrante del equipo.
- David Rodriguez: integrante del equipo.
- Repositorio: https://github.com/MarietteR/PA_mod6_G4.git

## Presupuesto

Proyecto académico sin presupuesto monetario asignado. Se usan recursos gratuitos: dataset abierto (ESC-50), software libre y los equipos de los integrantes.

## Stakeholders

- **Cuidadores familiares o profesionales:** usuarios directos de las notificaciones. Esperan alertas oportunas y pocas falsas alarmas, de modo que no tengan que revisar el sistema constantemente.
- **Persona cuidada (adulto mayor):** beneficiaria del sistema. Espera más autonomía con una supervisión discreta y respeto a su privacidad.

## Aprobaciones

- [Nombre y cargo del aprobador del proyecto]
- [Firma del aprobador]
- [Fecha de aprobación]
