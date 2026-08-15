# Resumen de tareas y estado actual del proyecto

Este documento resume lo declarado en las tareas del proyecto, las correcciones recibidas por el docente/ayudante y lo que actualmente existe en el repositorio.

> Nota: los PDFs de `correcion` mantienen el texto base de la entrega, pero agregan observaciones visuales en rojo/anotaciones. Esas observaciones si fueron consideradas en este resumen.

## Objetivo actual del proyecto

El proyecto busca clasificar el nivel de amenaza meteorologica por precipitacion para el mes siguiente en zonas seleccionadas del Ecuador.

La salida esperada es una clase:

- `Baja`
- `Media`
- `Alta`

El sistema no pretende predecir el clima exacto de un dia, ni calcular riesgo integral de desastre, inundaciones o impactos humanos. Lo que hace es usar datos historicos meteorologicos para estimar la amenaza de precipitacion del siguiente mes.

## Evolucion declarada en las tareas

### Tarea 1

La primera tarea trataba sobre aplicaciones de IA en logistica de ultima milla. Era una etapa exploratoria y no corresponde directamente al proyecto actual de lluvia.

En esta etapa todavia no estaba definido el proyecto meteorologico.

Correccion recibida:

- Calificacion: `7/10`.
- Faltaron datasets concretos, restricciones operativas, objetivos y criterios de evaluacion.
- Se mencionaban modelos de IA de forma generica, sin decir que algoritmos se usarian.
- Faltaba justificar por que esos problemas requerian IA.
- Se pidieron referencias reales.
- Se observo que no debia usarse ChatGPT ni herramientas IA para esa tarea.

### Tarea 2

Aqui aparece el primer enfoque del proyecto actual: predecir o clasificar riesgo de lluvias intensas en Ecuador usando datos historicos del INAMHI.

Se declaro:

- Uso de datos meteorologicos historicos.
- Variables como precipitacion, temperatura, estacion, provincia, anio y mes.
- Clasificacion en niveles `bajo`, `medio` y `alto`.
- Comparacion inicial de modelos como regresion logistica, arboles, Random Forest y XGBoost.
- Posible aplicacion sencilla en Streamlit o Flask.

Lo importante: todavia se hablaba de "riesgo", aunque el alcance real era mas meteorologico que social o de desastre.

Correccion recibida:

- Calificacion: `8/10`.
- La propuesta fue aceptada, pero se pidio concretar mejor el objetivo.
- Se marco un problema clave: si la etiqueta `riesgo bajo/medio/alto` se construye con la misma precipitacion mensual que entra al modelo, el modelo solo aprende una regla circular.
- Se pidio definir si se clasificaba el mes actual o un mes futuro.
- Si el objetivo era preventivo, debian usarse variables historicas previas, ubicacion, mes y rezagos.
- Se pidio reemplazar ejemplos referenciales con datos reales descargados.
- Se pidio modelar formalmente entradas, salidas, variable objetivo, restricciones, actores, flujo y criterios de evaluacion.
- Se pidio usar referencias reales; ChatGPT no podia ser la referencia.

### Tarea 3

La tarea 3 corrige y delimita mejor el problema. El proyecto pasa de "riesgo de lluvias intensas" a "amenaza meteorologica por lluvias intensas".

Cambios importantes:

- Se deja claro que no se calcula riesgo integral de desastre.
- Se busca clasificar el mes siguiente, no el mismo mes.
- Se evita usar informacion futura del mes objetivo para no causar fuga de datos.
- Se cambia el foco hacia fuentes abiertas como Copernicus / ERA5-Land.
- La unidad del problema pasa a ser zona-mes.

La idea queda asi: con informacion disponible hasta el mes `t`, clasificar la amenaza del mes `t+1`.

Correccion recibida:

- Calificacion: `6/10`.
- Se mezclaba modelamiento del problema con decisiones de solucion e implementacion.
- Elementos como API de Copernicus, interpolacion, percentiles y modelos predictivos debian quedar fuera del analisis del problema.
- Se pidio separar claramente: modelamiento del problema, descripcion preliminar de la solucion e implementacion.
- Los casos de uso estaban mas cerca de actividades que de verdaderos casos de uso.
- Se pidio justificar mejor por que usar IA y no solo analisis estadistico.
- Se pidio comparar al menos 5 modelos y escoger el mejor para la interfaz.
- Se pidio explicar mejor donde estaba la "parte inteligente".
- Se pidio documentar mejor referencias, prompts, respuestas y reflexion critica.
- Se advirtio no usar APIs, prompts o funciones existentes que resolvieran directamente el problema.

### Tarea 4

La tarea 4 consolida el diseno del proyecto.

Se declara:

- Uso de datos ERA5-Land en formato NetCDF.
- Procesamiento hacia una tabla mensual por zona.
- Construccion de indicadores de precipitacion y variables meteorologicas.
- Variable objetivo con clases `Baja`, `Media`, `Alta`.
- Particion temporal para evaluar generalizacion.
- Comparacion de 5 modelos:
  - Regresion Logistica Multinomial
  - Random Forest
  - XGBoost
  - SVM con kernel RBF
  - MLP
- Seleccion del modelo definitivo segun Macro F1, balanced accuracy, recall de clase Alta, estabilidad y sobreajuste.

Aunque en el diseno se propone Random Forest como modelo principal inicial, tambien se declara que el modelo final debe elegirse por desempeno. Eso coincide con lo que hicimos actualmente.

Correccion recibida:

- Calificacion: `8.5/10`.
- Se pidio corregir detalles de redaccion y notacion.
- Se pidio describir mejor Copernicus/ERA5-Land: resolucion, variables disponibles y cobertura temporal.
- Para la entrega final, se pidio precisar como construir la etiqueta `Baja/Media/Alta`.
- Se pidio explicar como evitar sesgo al calcular umbrales historicos.
- Se pidio indicar como manejar zonas con pocos datos.
- Se pidio mejorar diagramas de solucion: menos texto, mejor tamano y mayor claridad.
- Se pidio agregar en el texto las sesiones/capturas o contenido de uso de IA, ademas de enlaces.

## Lo que tenemos implementado actualmente

El repositorio actual ya sigue principalmente lo declarado desde la Tarea 3 y Tarea 4.

Tenemos un pipeline por pasos:

- `01_descargar_era5_land_horario.py`: descarga datos meteorologicos.
- `02_construir_indicadores.py`: construye indicadores desde los datos crudos.
- `03_validar_calidad_dataset.py`: revisa calidad del dataset.
- `04_preparar_dataset_modelado.py`: prepara la tabla para modelado.
- `05_construir_caracteristicas_candidatas.py`: genera variables candidatas.
- `06_entrenar_comparar_modelos.ipynb`: entrena y compara modelos.
- `07_validar_modelo.ipynb`: valida el modelo seleccionado.
- `08_evaluacion_final.ipynb`: evaluacion final.
- `09_exportar_modelo_final.py`: entrena y exporta el modelo final `.joblib`.
- `10_exportar_predicciones_front_local.py`: genera predicciones locales en JSON para el frontend.

## Modelos comparados

Actualmente se compararon efectivamente 5 modelos:

- Logistic Regression
- Random Forest
- XGBoost
- SVM RBF
- MLP

Tambien se usaron baselines de comparacion, como persistencia, climatologia mensual y dummy classifier.

El modelo ganador actual es `SVM_RBF`, no Random Forest. Esto no contradice la Tarea 4, porque ahi se propuso Random Forest como candidato principal, pero se dejo como criterio final escoger el mejor modelo segun metricas.

## Resultado actual del modelo

El modelo final exportado esta en:

`resultados/modelo_final/modelo_svm_rbf_final.joblib`

Metricas actuales principales:

- Validacion temporal 2018-2021:
  - Macro F1: `0.6895`
  - Balanced accuracy: `0.6892`
  - Accuracy: `0.6997`

- Prueba temporal 2022-2025:
  - Macro F1: `0.6880`
  - Balanced accuracy: `0.6869`
  - Accuracy: `0.6997`

Esto indica que el modelo mantiene un desempeno similar entre validacion y prueba temporal, lo cual es positivo porque no parece depender solo de memorizar el entrenamiento.

## Que hemos corregido o ajustado

Hasta ahora hemos corregido varias cosas importantes:

- Se cambio el enfoque de "riesgo" a "amenaza meteorologica", que es mas correcto para los datos usados.
- Se abandono la idea de depender solo de INAMHI y se uso ERA5-Land / Copernicus como fuente principal.
- Se definio el problema como prediccion del mes siguiente usando datos disponibles hasta el mes de consulta.
- Se evito el planteamiento circular: la prediccion usa informacion disponible antes del mes objetivo.
- Se separo mejor el analisis del problema de la implementacion tecnica.
- Se compararon realmente los 5 modelos declarados.
- Se eligio el modelo ganador por metricas, no por preferencia inicial.
- Se exporto el modelo final a `.joblib`.
- Se genero una salida local para conectar con el frontend sin API.
- Se ajusto el `.gitignore` para no subir datos crudos ni carpetas pesadas.

## Correcciones aun sensibles para la entrega final

Aunque el proyecto ya esta bastante alineado, hay puntos que conviene dejar muy claros en el informe final:

- Explicar con precision como se construye la etiqueta `Baja/Media/Alta`.
- Justificar que los umbrales historicos se calculan sin usar informacion futura.
- Describir bien ERA5-Land/Copernicus: cobertura temporal, variables y resolucion.
- Explicar por que se usa IA: no solo para aplicar umbrales, sino para aprender patrones multivariables y temporales.
- Aclarar que el modelo final fue escogido por comparacion de metricas.
- Mejorar diagramas si se entregan: menos texto y mas claridad visual.
- Documentar el uso de IA en el proceso, con prompts/respuestas/reflexion si la rubrica lo pide.

## Estado frente a lo declarado

En general, lo que estamos haciendo coincide con lo declarado en las tareas mas maduras, especialmente Tarea 3 y Tarea 4.

La principal diferencia es que en la documentacion se hablaba mucho de Random Forest como modelo principal propuesto, pero en la implementacion gano SVM RBF. Esto es aceptable porque el propio planteamiento decia que el modelo definitivo se seleccionaria por comparacion y metricas.

Otra diferencia menor es que algunas variables o lags mencionados en el diseno pueden no coincidir exactamente con las variables finales usadas. En la practica actual se trabaja con un conjunto de caracteristicas candidatas y seleccion de variables dentro del pipeline.

## Integracion actual con frontend

No estamos usando una API.

La integracion actual es local y semi-estatica:

1. El modelo `.joblib` se ejecuta en tu computador con Python.
2. El script genera un archivo `predictions-local.json`.
3. El frontend lee ese JSON como archivo estatico.

Esto permite mostrar resultados en una pagina web sin montar backend, sin servidor de modelo y sin depender de una API.

## Conclusion

El proyecto actual consiste en un clasificador de amenaza meteorologica por precipitacion para el mes siguiente en Ecuador. Usa datos historicos, construye indicadores, compara 5 modelos de aprendizaje automatico y exporta el mejor modelo encontrado.

Hasta ahora, el trabajo implementado esta alineado con el objetivo declarado en las ultimas tareas. Lo mas importante a cuidar en la documentacion final es explicar claramente que no se predice una lluvia diaria exacta ni un desastre, sino una categoria de amenaza meteorologica mensual.
