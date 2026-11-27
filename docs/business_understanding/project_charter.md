# Project Charter - Entendimiento del Negocio

## Nombre del Proyecto

Sistema de reconocimiento de sonidos para el apoyo en el cuidado de personas con necesidades especiales.

## Objetivo del Proyecto

Muchas personas con necesidades especiales (por ejemplo, adultos mayores, personas con discapacidad o con condiciones de salud que requieren acompañamiento) viven solas o cuentan con acompañamiento parcial, lo que dificulta la supervisión continua de su entorno y la identificación oportuna de situaciones que puedan comprometer su bienestar, ya que sus cuidadores no pueden estar presentes durante todo el tiempo. Un sistema que escuche el entorno puede detectar eventos acústicos relevantes dentro de una vivienda y generar notificaciones oportunas para los cuidadores. Entre los posibles eventos de interés se encuentran la caída de objetos, la ruptura de elementos, episodios de tos y periodos inusuales de inactividad acústica. Todo esto sin que el cuidador tenga que revisar constantemente.

**Por qué es importante:** un sistema que genere notificaciones excesivas puede perder credibilidad y provocar que los cuidadores ignoren sus advertencias, mientras que una alerta omitida podría retrasar la atención ante una situación de riesgo. Por eso el proyecto no se limita a clasificar sonidos: busca decidir cuáles importan y cuándo avisar.

## Alcance del Proyecto

### Incluye

**Población objetivo:** personas con necesidades especiales que requieren acompañamiento y viven solas o con apoyo parcial, como adultos mayores, personas con discapacidad o con condiciones de salud que necesitan supervisión. El diseño es general: los sonidos del hogar y las reglas de alerta aplican a todos estos perfiles, aunque cada uno podría requerir ajustar las clases prioritarias y los umbrales.

**Aclaración de alcance importante:** un clasificador de sonidos no sabe quién produjo el sonido. El proyecto asume un escenario controlado de una sola persona en el espacio monitoreado (dispositivo en su vivienda o habitación) y no intenta atribuir un sonido a un individuo entre varios.

**Descripción de los datos disponibles:**

- Dataset **ESC-50** (Piczak, 2015): 2.000 clips de audio WAV de 5 segundos, 44,1 kHz y mono, con 50 clases de 40 clips cada una y 5 folds prearmados para validación cruzada. Licencia CC BY-NC 3.0 (uso no comercial).
- Las 50 clases se agrupan según su uso en el sistema (archivo `data/external/class_groups.csv`). Es una agrupación inicial que se revisará cuando se profundice en perfiles específicos:

  | Grupo          | Clases                                                         | Uso                                                     |
  | -------------- | -------------------------------------------------------------- | ------------------------------------------------------- |
  | Urgente (1)    | `glass_breaking`                                               | Notificación inmediata                                  |
  | Salud (4)      | `coughing`, `sneezing`, `breathing`, `snoring`                 | Conteo por hora y tendencia                             |
  | Actividad (16) | Pasos, puertas, agua, cocina, higiene, electrodomésticos, etc. | Señales de rutina; su ausencia prolongada puede alertar |
  | Ambiente (29)  | Animales, clima, tráfico, etc.                                 | Se descartan                                            |

- Hallazgos preliminares de la auditoría de calidad (`reports/`):
  - Todos los clips cumplen el formato esperado, pero 55 presentan saturación y 169 tienen menos de 1 s de audio activo.
  - Los eventos breves están rellenados con silencio digital hasta completar 5 s (mediana de relleno: ~0 % en ambiente y 65 % en urgente).
  - Con solo nivel, relleno y ancho de banda (sin el contenido del sonido), un Random Forest acierta 26 % frente a 2 % del azar. Esto indica riesgo de que un modelo aprenda artefactos y no el sonido.
  - 4 grabaciones originales aparecen en más de un fold, y el grupo urgente tiene una sola clase.
- Audio propio (opcional) para probar la generalización fuera de ESC-50.

- **Descripción de los resultados esperados:**
  - Clasificación de las 50 clases de ESC-50 agrupadas en 4 grupos de uso.
  - Panel de visualización con eventos, tendencias y alertas simuladas (entregable principal).
  - Evaluación con folds oficiales y con un día sintético de audio continuo.
  - Pruebas con audio propio si es posible.
  - Opcional: servicio web que procese el audio y devuelva el nombre del sonido detectado y su estado de alerta.

- **Criterios de éxito del proyecto:**
  - Modelo: F1 macro y por clase superiores al baseline MFCC + Random Forest reportado para ESC-50 (44,3 %). Meta numérica: [COMPLETAR].
  - Alerta urgente: recall de `glass_breaking` y falsas alarmas por hora en el día sintético. Metas: [COMPLETAR].
  - Errores de alerta: revisar si los errores de clasificación generan alertas indebidas u omiten alertas esperadas.
  - Robustez: reportar y analizar la caída de desempeño sin relleno, con ruido y con audio propio.
  - Prototipo: el panel muestra eventos, tendencias y alertas de un día simulado.

### Excluye

- Identificar quién produce el sonido.
- Detección de caídas de personas, voz o gritos (no están en ESC-50).
- Alarma de humo (la clase `clock_alarm` es un despertador).
- Uso comercial (licencia CC BY-NC).
- Dispositivo médico o diagnóstico: el sistema es una herramienta de apoyo, no un sustituto del cuidador.

## Metodología

El proyecto seguirá un enfoque iterativo basado en la metodología Team Data Science Process (TDSP) y trabajará con un conjunto de audios de hasta 50 categorías.

1. _Comprensión del problema_. Se definirán las categorías de sonidos que el sistema deberá reconocer y se establecerá cuáles se considerarán potencialmente generadoras de malestar en personas autistas para efectos del envío de alertas.
2. _Adquisición y comprensión de los datos_. Se realizará un análisis exploratorio de los audios para revisar la cantidad de grabaciones por categoría, su duración, su calidad y la consistencia de las etiquetas. A partir de los hallazgos, se definirán el preprocesamiento y la separación de los datos para entrenamiento, validación y prueba.
3. _Modelado_. Se entrenará un clasificador para identificar el sonido entre las categorías incluidas en el entrenamiento. Con un conjunto de prueba independiente, se evaluará el desempeño por categoría y se revisará si los errores de clasificación generan alertas indebidas u omiten alertas esperadas.
4. _Despliegue_. Se integrará el clasificador en un servicio web que procese el audio y devuelva el nombre del sonido detectado junto con su estado de alerta. Cuando corresponda, el servicio enviará la alerta con ese nombre. Este punto dependerá de si el tiempo nos da.

## Cronograma

| Etapa                                        | Duración Estimada | Fechas                                   |
| -------------------------------------------- | ----------------- | ---------------------------------------- |
| Entendimiento del negocio y carga de datos   | 2 semanas         | del 11 de noviemnbre al 25 de noviemnbre |
| Preprocesamiento, análisis exploratorio      | 2 semanas         | del 18 de noviembre al 3 de diciembre    |
| Modelamiento y extracción de características | 2 semanas         | del 26 de noviembre al 10 de diciembre   |
| Despliegue                                   | 1 semana          | del 10 de diciembre al 17 de diciembre   |
| Evaluación y entrega final                   | 1 semana          | del 14 de diciembre al 21 de diciembre   |

Hay que tener en cuenta que estas fechas son de ejemplo, estas deben ajustarse de acuerdo al proyecto.

## Equipo del Proyecto

- Mariette Rodríguez Líder
- David Rodríguez Data Engineer ML
- Brayan Sáenz Software Engineer ML
- Mariette Rodríguez Data scientist

## Presupuesto

| Categoría de Gasto             | Descripción                                                                                              | Costo Estimado (COP)           | Notas / Consideraciones                |
| ------------------------------ | -------------------------------------------------------------------------------------------------------- | ------------------------------ | -------------------------------------- |
| I. Personal                    | ---------                                                                                                | -----                          | -----                                  |
| Data Science                   | Diseño del enfoque y revisión del desempeño por categoría y de los errores de alerta.                    | $2.000.000 20 horas × $100.000. | -----                                  |
| Ingenieros de ML               | Análisis y preparación de audios, entrenamiento del clasificador e integración con el servicio web.      | $2.400.000 80 horas × $30.000.  | -----                                  |
| II. Infraestructura y Software | ---------                                                                                                | -----                          | -----                                  |
| Plataforma Cloud               | Cómputo para entrenamiento y alojamiento temporal del servicio web.                                      | $250.000                       | Bolsa estimada para las cinco semanas. |
| Almacenamiento Cloud           | Almacenamiento de audios y versiones del modelo.                                                         | $50.000                        | Bolsa estimada para las cinco semanas. |
| Licencias de Software          | Herramientas y librerías de código abierto.                                                              | $0                             | Sin costo de licencias.                |
| III. Misceláneos               | ---------                                                                                                | -----                          | -----                                  |
| Investigación y Desarrollo     | Apoyo especializado para revisar qué categorías se marcarán como potencialmente generadoras de malestar. | $300.000                       | 3 horas × $100.000.                    |
| Gestión de Proyecto            | Coordinación, seguimiento y documentación de cierre.                                                     | $200.000                       | 5 horas × $40.000.                     |
| Contingencias                  | Fondo para imprevistos.                                                                                  | $520.000                       | 10 % del subtotal de $5.200.000.       |
| TOTAL ESTIMADO DEL PROYECTO    | ----                                                                                                     | $5.720.000                     | 5 semanas.                             |

## Stakeholders

- Personas autistas Ayudar a definir qué sonidos incluir, en qué situaciones les afectan y cómo comunicar esa experiencia, con los apoyos que prefieran.
- Personas cuidadoras Aportar ejemplos cotidianos, describir lo que observan y revisar si las categorías de sonidos tienen sentido en su contexto de cuidado.
- Profesionales de apoyo, por ejemplo, terapeutas ocupacionales con experiencia en autismo Asesorar en la definición de categorías y en la interpretación de observaciones, junto con la persona autista y quien la cuida.
- Equipo técnico del proyecto Definir cómo se etiquetarán los audios, entrenar el clasificador y medir qué sonidos confunde u omite.

## Aprobaciones

Mariette Rodríguez Líder del proyecto
