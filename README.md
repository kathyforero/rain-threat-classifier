# Rain Threat Classifier

Proyecto academico para clasificar la amenaza meteorologica mensual por precipitacion en zonas seleccionadas del Ecuador.

La idea no es usar una caja negra lista, sino construir un flujo propio: descargar datos, procesarlos, crear indicadores, definir la etiqueta, entrenar modelos y comparar resultados.

## Estructura

```text
rain-threat-classifier/
|-- modelo/                    # Pipeline, notebooks y entrenamiento ML
|-- back/                      # Backend de aplicacion, por ahora reservado
|-- front/                     # Frontend/interfaz, por ahora reservado
|-- datos/                     # Datos crudos, procesados y de modelado
|-- resultados/                # Reportes, metricas y salidas del modelo
|-- Tareas/                    # Entregas, correcciones y guias de defensa
|-- zonas_era5_ecuador.csv
`-- README.md
```

Los datos y resultados se mantienen en la raiz para no duplicar archivos pesados y conservar una sola fuente de verdad.

## Objetivo

El problema se formula como:

```text
X(z, t) -> Y(z, t+1)
```

Es decir, con variables conocidas de una zona `z` hasta el mes `t`, se clasifica la amenaza del mes siguiente `t+1` en:

- `Baja`
- `Media`
- `Alta`

La etiqueta se calcula con `Rx5day`, que representa el maximo acumulado de lluvia en cinco dias consecutivos. Los umbrales actuales son globales: se calculan con las 12 zonas de desarrollo entre 1991 y 2017 y se aplican a todas las zonas.

## Datos Usados

La fuente base es ERA5-Land, con datos meteorologicos horarios. Esos datos no se usan directamente como millones de filas independientes; primero se resumen en indicadores diarios y mensuales.

Variables principales:

- precipitacion
- temperatura
- punto de rocio
- humedad relativa estimada
- viento
- presion superficial
- humedad del suelo

## Features

Las features son las columnas que el modelo usa para aprender patrones. En la version actual se trabaja con un catalogo de 38 caracteristicas candidatas, construido despues del analisis exploratorio.

Ejemplos:

- lluvia total mensual
- maximo diario de lluvia
- maximo de lluvia en 5 dias
- dias humedos
- dias con lluvia mayor a 10 mm o 20 mm
- rachas secas y humedas
- temperatura media
- humedad relativa
- viento medio

## Flujo Oficial ML

Ejecutar desde la raiz del proyecto:

```bat
py modelo/01_descargar_era5_land_horario.py
py modelo/02_construir_indicadores.py
py modelo/03_validar_calidad_dataset.py
py modelo/04_preparar_dataset_modelado.py
py modelo/05_construir_caracteristicas_candidatas.py
```

Luego abrir los notebooks:

```text
modelo/05_analisis_caracteristicas.ipynb
modelo/06_entrenar_comparar_modelos.ipynb
modelo/07_validar_modelo.ipynb
modelo/08_evaluacion_final.ipynb
```

## Modelos Comparados

En el Paso 06 se comparan cinco modelos principales de machine learning:

| Modelo | Que es |
| --- | --- |
| `Logistic_Regression` | Modelo lineal simple y explicable; sirve como referencia fuerte. |
| `Random_Forest` | Conjunto de arboles de decision; captura relaciones no lineales. |
| `XGBoost` | Modelo de boosting basado en arboles; suele rendir muy bien en datos tabulares. |
| `SVM_RBF` | Maquina de vectores de soporte con kernel RBF; captura fronteras no lineales. |
| `MLP` | Red neuronal simple para datos tabulares. |

Tambien se comparan baselines como `Persistencia`, `Climatologia_mes` y `Dummy_most_frequent`. Esos no son los modelos principales, sino puntos de referencia para verificar si los modelos realmente aportan valor.

## Modelo Ganador

El ganador registrado en `resultados/modelos_cv/ganador_paso06.json` es:

```text
SVM_RBF
```

Parametros congelados:

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

Validacion temporal 2018-2021:

```text
macro_f1 = 0.6895
balanced_accuracy = 0.6892
accuracy = 0.6997
```

## Que Es El Modelo

En este proyecto, "el modelo" es una combinacion de dos cosas:

1. Un algoritmo: `SVM_RBF`, implementado con `SVC` de scikit-learn.
2. Un pipeline de preparacion: imputacion, escalado, codificacion de variables categoricas y seleccion de caracteristicas.

En los notebooks, ese pipeline se crea como un objeto de Python, se entrena con `.fit(...)` y luego produce predicciones con `.predict(...)`.

Conceptualmente:

```text
datos nuevos -> pipeline entrenado -> prediccion: 0, 1 o 2
```

Traduccion de salida:

```text
0 = Baja
1 = Media
2 = Alta
```

## Artefactos Importantes

El proyecto conserva:

- seleccion del ganador: `resultados/modelos_cv/ganador_paso06.json`
- mejores parametros: `resultados/modelos_cv/mejores_parametros.json`
- metricas y comparaciones: `resultados/modelos_cv/`
- validacion temporal: `resultados/validacion_modelo/`
- predicciones de validacion: `resultados/validacion_modelo/predicciones_validacion_2018_2021.csv`

## Sobre `.joblib`

Un `.joblib` es un archivo que guarda un objeto de Python ya entrenado. En este caso guarda el `Pipeline` completo de scikit-learn: preparacion de columnas, imputacion, escalado, one-hot encoding, seleccion de caracteristicas y el clasificador `SVM_RBF`.

Sirve para reutilizar el modelo sin volver a entrenarlo desde cero. Se carga con `joblib.load(...)` y luego se usa con `.predict(...)`.
