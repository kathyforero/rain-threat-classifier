# Pipeline ERA5-Land para amenaza mensual por lluvias intensas

## Decisión metodológica

- Fuente original: datos horarios puntuales de ERA5-Land.
- Procesamiento intermedio: indicadores diarios.
- Unidad final del modelo: una fila por zona y mes.
- Objetivo: clasificar la categoría del mes siguiente.
- Periodo sugerido: 1991-2025.
- Zonas de desarrollo: 12.
- Zonas reservadas para validación espacial: 3.

Los datos horarios no se convierten en millones de muestras independientes.
Se resumen en indicadores diarios y mensuales para conservar información de
intensidad y duración sin inflar artificialmente el número de observaciones.

## Indicadores generados

Precipitación:
- PRCPTOT: precipitación total mensual.
- Rx1day: máximo acumulado diario del mes.
- Rx5day: máximo acumulado en cinco días consecutivos.
- Máximos en 1, 3 y 6 horas.
- Días húmedos, días >= 10 mm y días >= 20 mm.
- SDII: intensidad promedio por día húmedo.
- CWD y CDD: rachas húmedas y secas.

Otras variables:
- Temperatura media, máxima y mínima.
- Punto de rocío y humedad relativa estimada.
- Viento medio y máximo.
- Presión superficial.
- Humedad de la primera capa del suelo.

## Instalación

```bat
py -m pip install --upgrade "cdsapi>=0.7.7" truststore
py -m pip install xarray netCDF4 pandas numpy
```

Configura las credenciales de Copernicus en:

```text
C:/Users/TU_USUARIO/.cdsapirc
```

## Ejecución

### 1. Probar la descarga

En `01_descargar_era5_land_horario.py` deja:

```python
TEST_MODE = True
```

Luego ejecuta:

```bat
py 01_descargar_era5_land_horario.py
```

La prueba descarga Guayaquil para enero de 2024 y guarda los archivos en `datos_horarios_crudos/prueba`.

### 2. Procesar la prueba

En `02_construir_dataset_mensual.py` deja:

```python
DATA_MODE = "prueba"
```

Luego ejecuta:

```bat
py 02_construir_dataset_mensual.py
```

### 3. Descargar el histórico completo

Cambia en el descargador:

```python
TEST_MODE = False
```

y ejecuta el descargador. Los archivos completos se guardan en `datos_horarios_crudos/completo`, por lo que la prueba no hará que el programa omita accidentalmente el histórico.

Después cambia en el procesador:

```python
DATA_MODE = "completo"
```

y ejecútalo nuevamente.

## Archivos de salida

En `resultados_prueba` o `resultados_completo`, según el modo, se generan:

- `indicadores_diarios_todas_zonas.csv`
- `indicadores_mensuales_todas_zonas.csv`
- `reporte_calidad.csv`
- `dataset_modelo_mensual.csv`

## Etiqueta preliminar

La etiqueta se basa en Rx5day del mes objetivo. Los percentiles 33 y 66 se
calculan por zona y mes del año usando solamente el periodo histórico de
entrenamiento. Así, una lluvia normal para Esmeraldas no se interpreta igual
que una lluvia excepcional para Salinas.

La etiqueta es una clasificación relativa para el proyecto académico. No es
una alerta oficial ni una escala de riesgo de desastre.

## Partición temporal

- Entrenamiento: hasta 2017.
- Validación temporal: 2018-2021.
- Prueba temporal: 2022-2025.
- Santo Domingo, Nueva Loja y Macas se mantienen como validación espacial.

## Advertencia sobre los archivos anteriores

Los archivos `data_stream-oper_stepType-*.nc` descargados anteriormente
cubren una malla completa sobre Ecuador continental y no un único punto.
Cada combinación de hora, latitud y longitud genera una observación. Después
esa cantidad se multiplica por cada variable seleccionada. Por eso contienen
millones de valores aunque ocupen pocos megabytes gracias a la compresión
NetCDF.
