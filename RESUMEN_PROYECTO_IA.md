# Resumen del proyecto de IA

Este proyecto construye un clasificador de amenaza mensual por lluvias intensas usando datos meteorologicos de ERA5-Land. La idea no es usar una caja negra lista, sino armar un flujo propio: descargar datos, procesarlos, crear indicadores, definir la etiqueta, entrenar modelos y comparar resultados.

## Que estamos prediciendo

El objetivo es clasificar la categoria de amenaza del mes siguiente:

- `Baja`
- `Media`
- `Alta`

La etiqueta se calcula con lluvia extrema relativa, principalmente usando `Rx5day`, que representa el maximo acumulado de lluvia en cinco dias consecutivos. Los umbrales se calculan por zona y mes para que cada ciudad se compare contra su propio comportamiento historico.

## Datos usados

La fuente base es ERA5-Land, con datos meteorologicos horarios. Esos datos no se usan directamente como millones de filas independientes; primero se resumen en indicadores diarios y mensuales.

Variables principales:

- precipitacion
- temperatura
- punto de rocio
- humedad relativa estimada
- viento
- presion superficial
- humedad del suelo

## Features o caracteristicas

Las caracteristicas son las columnas que el modelo usa para aprender patrones. En la version actual se trabaja con un catalogo de **38 caracteristicas candidatas**, construido despues del analisis exploratorio.

Ejemplos de caracteristicas:

- lluvia total mensual
- maximo diario de lluvia
- maximo de lluvia en 5 dias
- dias humedos
- dias con lluvia mayor a 10 mm o 20 mm
- rachas secas y humedas
- temperatura media
- humedad relativa
- viento medio

## Modelos comparados

En el Paso 06 se comparan 5 modelos principales de machine learning:

| Modelo | Que es |
| --- | --- |
| `Logistic_Regression` | Modelo lineal simple y explicable; sirve como referencia fuerte. |
| `Random_Forest` | Conjunto de arboles de decision; captura relaciones no lineales. |
| `XGBoost` | Modelo de boosting basado en arboles; suele rendir muy bien en datos tabulares. |
| `SVM_RBF` | Maquina de vectores de soporte con kernel RBF; captura fronteras no lineales. |
| `MLP` | Red neuronal simple para datos tabulares. |

Tambien se comparan baselines como `Persistencia`, `Climatologia_mes` y `Dummy_most_frequent`. Esos no son los modelos principales, sino puntos de referencia para verificar si los modelos realmente aportan valor.

## Modelo ganador

El ganador registrado en `resultados/modelos_cv/ganador_paso06.json` es:

```text
SVM_RBF
```

Sus parametros congelados son:

```text
C = 1
gamma = 0.05
selector de caracteristicas = all
```

Resultado en validacion cruzada:

```text
macro_f1_cv_media = 0.7188
balanced_accuracy_media = 0.7180
```

Luego se valida temporalmente en 2018-2021. En esa validacion, el SVM obtiene:

```text
macro_f1 = 0.6895
balanced_accuracy = 0.6892
accuracy = 0.6997
```

## Donde esta el modelo

El modelo final vigente esta guardado en:

```text
resultados/modelo_final/modelo_svm_rbf_final.joblib
```

Junto a ese archivo tambien se generaron:

```text
resultados/modelo_final/metadata_modelo_svm_rbf_final.json
resultados/modelo_final/metricas_prueba_temporal_modelo_final.csv
```

Ademas, el proyecto conserva:

- la seleccion del ganador: `resultados/modelos_cv/ganador_paso06.json`
- los mejores parametros: `resultados/modelos_cv/mejores_parametros.json`
- las metricas y comparaciones: `resultados/modelos_cv/` y `resultados/validacion_modelo/`
- las predicciones generadas durante validacion: `resultados/validacion_modelo/predicciones_validacion_2018_2021.csv`

Los archivos `.joblib` que existen estan en:

```text
deprecado/experimentos_antes_reformulacion/modelos/
```

Por estar en `deprecado`, corresponden a experimentos anteriores y no representan la version actual del flujo.

## Entonces, que es "el modelo"

En este proyecto, "el modelo" es una combinacion de dos cosas:

1. Un algoritmo: `SVM_RBF`, implementado con `SVC` de scikit-learn.
2. Un pipeline de preparacion: imputacion, escalado, codificacion de variables categoricas y seleccion de caracteristicas.

En los notebooks, ese pipeline se crea como un objeto de Python, se entrena con `.fit(...)` y luego produce predicciones con `.predict(...)`.

Conceptualmente:

```text
datos nuevos -> pipeline entrenado -> prediccion: 0, 1 o 2
```

La traduccion de la salida es:

```text
0 = Baja
1 = Media
2 = Alta
```

Esa equivalencia tambien esta guardada en el archivo de metadata.

## Que es un .joblib

Un `.joblib` es un archivo que guarda un objeto de Python ya entrenado. En este caso guarda el `Pipeline` completo de scikit-learn: preparacion de columnas, imputacion, escalado, one-hot encoding, seleccion de caracteristicas y el clasificador `SVM_RBF`.

Sirve para reutilizar el modelo sin volver a entrenarlo desde cero. Se carga con `joblib.load(...)` y luego se usa con `.predict(...)`.
