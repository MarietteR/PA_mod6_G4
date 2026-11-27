# Project Charter - Entendimiento del Negocio

## Nombre del Proyecto

[Nombre del proyecto aquí]

## Objetivo del Proyecto

[Descripción breve del objetivo del proyecto y por qué es importante]

## Alcance del Proyecto

### Incluye:

- [Descripción de los datos disponibles]
- [Descripción de los resultados esperados]
- [Criterios de éxito del proyecto]

### Excluye:

- [Descripción de lo que no está incluido en el proyecto]

## Metodología

El proyecto seguirá un enfoque iterativo basado en la metodología Team Data Science Process (TDSP) y trabajará con un conjunto de audios de hasta 50 categorías.
1. *Comprensión del problema*. Se definirán las categorías de sonidos que el sistema deberá reconocer y se establecerá cuáles se considerarán potencialmente generadoras de malestar en personas autistas para efectos del envío de alertas.
2. *Adquisición y comprensión de los datos*. Se realizará un análisis exploratorio de los audios para revisar la cantidad de grabaciones por categoría, su duración, su calidad y la consistencia de las etiquetas. A partir de los hallazgos, se definirán el preprocesamiento y la separación de los datos para entrenamiento, validación y prueba.
3. *Modelado*. Se entrenará un clasificador para identificar el sonido entre las categorías incluidas en el entrenamiento. Con un conjunto de prueba independiente, se evaluará el desempeño por categoría y se revisará si los errores de clasificación generan alertas indebidas u omiten alertas esperadas.
4. *Despliegue*. Se integrará el clasificador en un servicio web que procese el audio y devuelva el nombre del sonido detectado junto con su estado de alerta. Cuando corresponda, el servicio enviará la alerta con ese nombre. Este punto dependerá de si el tiempo nos da.

## Cronograma

| Etapa | Duración Estimada | Fechas |
|------|---------|-------|
| Entendimiento del negocio y carga de datos | 2 semanas | del 11 de noviemnbre al 25 de noviemnbre |
| Preprocesamiento, análisis exploratorio | 2 semanas | del 18 de noviembre al 3 de diciembre |
| Modelamiento y extracción de características | 2 semanas | del 26 de noviembre al 10 de diciembre |
| Despliegue | 1 semana | del 10 de diciembre al 17 de diciembre |
| Evaluación y entrega final | 1 semana | del 14 de diciembre al 21 de diciembre |

Hay que tener en cuenta que estas fechas son de ejemplo, estas deben ajustarse de acuerdo al proyecto.

## Equipo del Proyecto

- Mariette Rodríguez Líder
- David Rodríguez Data Engineer ML
- Brayan Sáenz Software Engineer ML
- Mariette Rodríguez Data sciencce

## Presupuesto

| Categoría de Gasto |	Descripción |	Costo Estimado (COP) |	Notas / Consideraciones |
|-----------|---------------|------------|-----|
| I. Personal	|---------|-----|-----|		
| Data Science |	Diseño del enfoque y revisión del desempeño por categoría y de los errores de alerta.	|$2.000.000	20 horas × $100.000. |-----|
| Ingenieros de ML |	Análisis y preparación de audios, entrenamiento del clasificador e integración con el servicio web.|	$2.400.000	80 horas × $30.000. |-----|
| II. Infraestructura y Software		|---------|-----|-----|		
| Plataforma Cloud |	Cómputo para entrenamiento y alojamiento temporal del servicio web.	|$250.000	|Bolsa estimada para las cinco semanas.|
| Almacenamiento Cloud |	Almacenamiento de audios y versiones del modelo.|	$50.000	| Bolsa estimada para las cinco semanas.|
| Licencias de Software |	Herramientas y librerías de código abierto.	|$0	| Sin costo de licencias.|
| III. Misceláneos 	|---------|-----|-----|				
| Investigación y Desarrollo |	Apoyo especializado para revisar qué categorías se marcarán como potencialmente generadoras de malestar.|	$300.000	| 3 horas × $100.000.|
| Gestión de Proyecto |	Coordinación, seguimiento y documentación de cierre.	|$200.000	|5 horas × $40.000.|
| Contingencias	| Fondo para imprevistos.	|$520.000	|10 % del subtotal de $5.200.000.|
|TOTAL ESTIMADO DEL PROYECTO|----|		$5.720.000	|5 semanas.|

## Stakeholders

- Personas autistas	Ayudar a definir qué sonidos incluir, en qué situaciones les afectan y cómo comunicar esa experiencia, con los apoyos que prefieran.
- Personas cuidadoras	Aportar ejemplos cotidianos, describir lo que observan y revisar si las categorías de sonidos tienen sentido en su contexto de cuidado.
- Profesionales de apoyo, por ejemplo, terapeutas ocupacionales con experiencia en autismo	Asesorar en la definición de categorías y en la interpretación de observaciones, junto con la persona autista y quien la cuida.
- Equipo técnico del proyecto	Definir cómo se etiquetarán los audios, entrenar el clasificador y medir qué sonidos confunde u omite.

## Aprobaciones

- Mariette Rodríguez Líder del proyecto
- 19 diciembre del 2026
