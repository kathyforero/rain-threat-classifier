# Integracion local con precipita-ecuador-forecast

## Decision

No vamos a usar API.

La forma mas rapida para que funcione en tu computador es:

```text
Python ejecuta el modelo .joblib
        |
        v
genera predictions-local.json
        |
        v
el frontend React lee ese JSON local
```

Esto no sirve como sistema publico desplegado, pero si sirve perfecto para una demo local y para conectar el modelo real con el front sin montar backend.

## Estado actual

Este documento queda como referencia de integracion local no oficial. En la reestructura actual del repositorio, el flujo academico se mantiene hasta el Paso 08 y no hay un script operativo de exportacion local dentro de `modelo/`.

Si se retoma esta integracion, el script deberia ubicarse en:

```text
modelo/10_exportar_predicciones_front_local.py
```

## Archivos esperados para esa integracion

En `rain-threat-classifier`:

```text
modelo/10_exportar_predicciones_front_local.py
```

Ese script carga:

```text
resultados/modelo_final/modelo_svm_rbf_final.joblib
datos/modelado/dataset_caracteristicas_candidatas.csv
```

y genera:

```text
C:\Users\drami\Documents\GitHub\precipita-ecuador-forecast\public\predictions-local.json
```

Tambien deja una copia en:

```text
resultados/modelo_final/predictions-local.json
```

En `precipita-ecuador-forecast`:

```text
src/services/predictionService.ts
```

Ahora el `predictionService` usa `localStaticPredictionService`, que lee:

```text
/predictions-local.json
```

desde la carpeta `public`.

## Como se ejecutaria

Desde `rain-threat-classifier`:

```powershell
.\.venv\Scripts\python.exe modelo/10_exportar_predicciones_front_local.py
```

Ese comando solo aplica si el script existe. Despues corres el frontend como normalmente lo ejecutes en tu computador.

El front no le pregunta nada a una API. Solo lee el JSON local generado previamente.

## Limitacion importante

El modelo no puede inventar datos meteorologicos de 2026 si no existen features procesadas para 2026.

El JSON generado actualmente cubre los meses de referencia disponibles en el dataset:

```text
2020-01 a 2025-11
```

El selector del front muestra hasta `2025-12`, pero `2025-12` queda como datos insuficientes porque el dataset vigente llega hasta noviembre de 2025 como mes de referencia.

Para consultar 2026 localmente habria que:

1. descargar/procesar datos 2026;
2. reconstruir features;
3. volver a ejecutar `modelo/10_exportar_predicciones_front_local.py`;
4. refrescar el frontend.

## Que tan complicado fue

Bajo.

No se rehizo el front. Solo se cambio el punto donde antes usaba datos simulados para que ahora lea predicciones reales generadas por Python.

## Resumen en una frase

El modelo corre en tu computador con Python, genera un JSON, y el frontend lo consume localmente sin API.
