# Integración local con precipita-ecuador-forecast

## Decisión

Para la demo académica se propone una integración local sin API:

```text
Python carga el modelo operativo .joblib
        |
        v
genera predictions-local.json
        |
        v
el frontend React lee ese JSON estático
```

No es una arquitectura pública de producción, pero evita desplegar un backend solo para la demostración.

## Estado actual

El pipeline académico llega hasta el Paso 09. El futuro script de inferencia/frontend debe ubicarse en:

```text
modelo/10_exportar_predicciones_front_local.py
```

Ese Paso 10 todavía debe implementarse después de completar la evaluación final y exportar el modelo operativo.

## Enero de 2026 sí puede predecirse con los datos actuales

El problema es:

```text
X(t) -> Y(t+1)
```

Por tanto, para predecir **enero de 2026** no necesitamos observar enero de 2026. Necesitamos construir las features conocidas hasta **diciembre de 2025**:

```text
mes de entrada      = diciembre 2025
mes objetivo        = enero 2026
lag1                = noviembre 2025
lag11               = enero 2025
+ meteorología de diciembre 2025
+ geografía/región
+ codificación del mes objetivo
```

`indicadores_mensuales_todas_zonas.csv` sí contiene diciembre de 2025.

El archivo `dataset_caracteristicas_candidatas.csv` termina en noviembre de 2025 como **mes de entrada supervisado** porque una fila de diciembre de 2025 no tiene todavía una etiqueta observada para enero de 2026. Esa ausencia de target impide usarla para entrenamiento, pero **no impide usar diciembre de 2025 para inferencia**.

Solo para predecir febrero de 2026 y meses posteriores sería necesario incorporar nuevos datos meteorológicos observados de 2026.

## Probabilidades

El Paso 09 operativo habilita `SVC(probability=True)` para que el futuro Paso 10 pueda producir, además de la clase, estimaciones como:

```json
{
  "prediccion": "Alta",
  "probabilidades": {
    "Baja": 0.08,
    "Media": 0.21,
    "Alta": 0.71
  }
}
```

Estas probabilidades son estimaciones del SVM para la interfaz y no sustituyen las métricas clasificatorias oficiales del Paso 08.

## Archivos esperados

Después del Paso 09:

```text
resultados/modelo_final/modelo_svm_rbf_operativo_2025.joblib
resultados/modelo_final/metadata_modelo_svm_rbf_operativo_2025.json
```

El futuro Paso 10 generará:

```text
resultados/modelo_final/predictions-local.json
```

y opcionalmente copiará el mismo archivo a la carpeta `public/` del frontend.
