# Rain Threat Classifier

Proyecto académico para clasificar el nivel de **amenaza meteorológica mensual por precipitación** en zonas seleccionadas del Ecuador.

El problema se formula como:

```text
X(z, t) -> Y(z, t+1)
```

Con información meteorológica conocida de una zona `z` hasta el mes `t`, se clasifica la intensidad de precipitación del mes siguiente `t+1` como `Baja`, `Media` o `Alta`.

> El proyecto no estima riesgo integral de desastre ni reproduce alertas oficiales de INAMHI. La salida es una categoría estadística de amenaza meteorológica por precipitación intensa.

## Estructura

```text
rain-threat-classifier/
|-- modelo/                    # Pipeline, notebooks y exportación ML
|-- back/                      # Backend, reservado
|-- front/                     # Frontend, reservado
|-- datos/                     # Datos crudos, procesados y de modelado
|-- resultados/                # Reportes, métricas y artefactos reproducibles
|-- Tareas/                    # Entregas, correcciones y contexto académico
|-- zonas_era5_ecuador.csv
`-- README.md
```

Los datos y resultados se mantienen en la raíz para conservar una sola fuente de verdad.

## Datos y cobertura

La fuente base es **ERA5-Land**. El procesamiento actual utiliza físicamente seis variables meteorológicas horarias conservadas en los NetCDF:

- temperatura a 2 m (`t2m`);
- punto de rocío a 2 m (`d2m`);
- precipitación total (`tp`);
- presión superficial (`sp`);
- viento zonal a 10 m (`u10`);
- viento meridional a 10 m (`v10`).

La solicitud original al CDS también registró `volumetric_soil_water_layer_1`, pero esa variable no está presente en los NetCDF conservados y **no forma parte del procesamiento ni del modelado actual**.

Cobertura procesada: 1991–2025, 15 zonas, 420 meses por zona.

## Target

La variable física base es `rx5day_mm`, máximo acumulado de precipitación en cinco días consecutivos dentro del mes.

Los umbrales se calculan una sola vez con las **12 zonas de desarrollo** durante 1991–2017:

```text
Q33 global = 37.3479 mm
Q66 global = 70.9957 mm
```

La etiqueta es:

```text
Baja   : Rx5day < 37.3479 mm
Media  : 37.3479 <= Rx5day < 70.9957 mm
Alta   : Rx5day >= 70.9957 mm
```

Los mismos límites se aplican a todas las zonas y meses. Son umbrales estadísticos del proyecto, no umbrales oficiales de alerta.

## Indicadores y características

El Paso 02 construye un conjunto amplio de indicadores mensuales, entre ellos precipitación total mensual, `Rx1day`, `Rx5day`, máximos subdiarios, días húmedos, `R10mm`, `R20mm`, `SDII`, `CWD`, `CDD`, temperatura, humedad relativa, viento y presión.

Después del análisis del Paso 05 se conserva un **catálogo final de 38 características candidatas**. El modelo no usa automáticamente todos los indicadores generados.

Familias finales:

- 11 variables meteorológicas del mes `t`;
- 11 antecedentes `lag1`;
- 11 análogos estacionales `lag11`;
- latitud y longitud;
- `target_month_sin` y `target_month_cos`;
- `region` como variable categórica.

`zone_id`, fechas, `split`, `rol`, `amenaza_mes`, `target_rx5day_mm` y `target_amenaza` no son predictors del clasificador.

## Flujo oficial

```text
01 Descarga ERA5-Land
02 Construcción de indicadores
03 Auditoría de calidad
04 Target global + splits
05 Análisis e ingeniería de características
06 Comparación y tuning temporal de 5 modelos
07 Validación temporal de desarrollo
08 Evaluación final temporal + espacial
09 Entrenamiento/exportación del modelo operativo
10 Integración con frontend (pendiente)
```

Scripts/notebooks:

```text
modelo/01_descargar_era5_land_horario.py
modelo/02_construir_indicadores.py
modelo/03_validar_calidad_dataset.py
modelo/04_preparar_dataset_modelado.py
modelo/05_analisis_caracteristicas.ipynb
modelo/05_construir_caracteristicas_candidatas.py
modelo/06_entrenar_comparar_modelos.ipynb
modelo/07_validar_modelo.ipynb
modelo/08_evaluacion_final.ipynb
modelo/09_exportar_modelo_final.py
```

## Modelos comparados

1. Regresión Logística Multinomial
2. Random Forest
3. XGBoost
4. SVM con kernel RBF
5. MLP

Baselines:

- `Dummy_most_frequent`;
- `Persistencia`;
- `Climatologia_mes`;
- `Climatologia_zona_mes` para evaluación temporal en zonas conocidas.

`Climatologia_zona_mes` no se usa como baseline del holdout espacial porque requiere etiquetas históricas de la misma zona.

## Modelo ganador congelado

```text
SVM_RBF
C = 1
gamma = 0.05
selector numérico = all
```

Resultados de desarrollo:

```text
CV temporal 1991–2017      Macro F1 = 0.7188
Validación 2018–2021       Macro F1 = 0.6895
```

El equipo ya consultó la prueba temporal 2022–2025 con esta configuración congelada:

```text
Prueba temporal 2022–2025  Macro F1 = 0.6880
```

Por esta razón los hiperparámetros no deben modificarse retrospectivamente buscando mejorar ese mismo periodo. El holdout espacial de Santo Domingo, Nueva Loja y Macas se mantiene reservado hasta ejecutar formalmente el Paso 08.

## Modelo de evaluación vs modelo operativo

El modelo usado para medir 2022–2025 se entrena solo con datos de desarrollo hasta 2021.

Después de completar el Paso 08, el Paso 09 entrena un **modelo operativo** con todas las etiquetas disponibles de las 12 zonas de desarrollo hasta diciembre de 2025. Ese artefacto se usa para inferencia/frontend y no redefine las métricas oficiales de evaluación.

## `.joblib`

El `.joblib` guarda el `Pipeline` completo de scikit-learn. Se ignora en Git por ser un artefacto binario regenerable. La metadata y resúmenes pequeños de `resultados/modelo_final/` sí deben versionarse.
