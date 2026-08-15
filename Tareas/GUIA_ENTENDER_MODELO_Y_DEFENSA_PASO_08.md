# Guia para entender y defender el modelo

Alcance: proyecto oficial hasta el Paso 08.

## 1. La idea mas importante

El modelo NO predice primero un valor exacto de `rx5day_mm` para luego clasificarlo.

El modelo aprende directamente esto:

```text
variables conocidas hasta el mes actual -> clase del mes siguiente
```

Ejemplo:

```text
Datos conocidos hasta enero 2019 -> amenaza de febrero 2019
```

La salida es:

- `Baja`
- `Media`
- `Alta`

Eso se llama clasificacion supervisada multiclase.

## 2. Que significa aprendizaje supervisado

Es supervisado porque durante el entrenamiento cada ejemplo ya tiene respuesta real.

Una fila de entrenamiento se ve asi:

```text
X = variables conocidas hasta enero 2019
y = clase real de febrero 2019
```

El modelo compara su prediccion contra la clase real y ajusta sus parametros internos para equivocarse menos.

No es no supervisado, porque no estamos agrupando datos sin respuesta. Aqui si tenemos una etiqueta real: `target_amenaza`.

## 3. Como sabe predecir el mes siguiente

No "adivina" usando solo tres meses sueltos. Aprende patrones desde miles de ejemplos historicos.

Durante entrenamiento ve muchas situaciones como:

```text
enero 1995 en Guayaquil -> febrero 1995 fue Alta
enero 1996 en Guayaquil -> febrero 1996 fue Media
enero 1997 en Quito -> febrero 1997 fue Baja
...
```

Con esos ejemplos aprende relaciones entre:

- lluvia reciente;
- lluvia de un periodo parecido del ano anterior;
- humedad;
- temperatura;
- viento;
- presion;
- region;
- ubicacion;
- mes del ano;
- clase real del mes siguiente.

Cuando predice un nuevo mes, recibe solo una fila resumida, pero esa fila se interpreta usando lo aprendido de toda la historia.

Respuesta corta:

> El entrenamiento usa toda la historia disponible. La prediccion puntual usa un resumen del mes actual y antecedentes seleccionados.

## 4. Que meses entran en una prediccion

Para predecir `t+1`, el modelo usa:

- mes actual `t`;
- mes anterior `t-1`, llamado `lag1`;
- mismo mes calendario del ano anterior al objetivo, llamado `lag11`;
- mes objetivo representado con seno/coseno;
- ubicacion y region.

Ejemplo:

```text
Quiero predecir febrero 2020.
Mes actual t: enero 2020.
lag1: diciembre 2019.
lag11: febrero 2019.
```

No se envia toda la serie historica completa porque los modelos usados trabajan con filas tabulares. La historia se resume en variables relevantes.

## 5. Por que no enviamos solo rx5day

Porque hay dos `rx5day` diferentes:

### rx5day futuro

Es el `rx5day_mm` del mes que queremos predecir.

Ejemplo:

```text
rx5day de febrero 2020
```

Ese valor NO se conoce cuando estamos en enero 2020. Por eso no puede entrar al modelo como predictor.

### rx5day conocido

Son valores de meses anteriores o actuales.

Ejemplo:

```text
rx5day de enero 2020
rx5day de diciembre 2019
rx5day de febrero 2019
```

Estos si se pueden usar porque ya ocurrieron.

Entonces:

- `rx5day_mm` futuro sirve para construir la clase real historica.
- `rx5day_mm` conocido sirve como una pista mas para predecir.

Si solo usaramos `rx5day` conocido, el modelo seria muy limitado. Las demas variables agregan contexto atmosferico y geografico.

## 6. Como se crea la clase real

La clase real se llama:

```text
target_amenaza
```

Se crea mirando el `rx5day_mm` real del mes siguiente.

`rx5day_mm` significa: maxima precipitacion acumulada en 5 dias dentro de un mes.

Usamos percentiles 33 y 66. No son cuartiles; los cuartiles dividen en 4 partes, aqui dividimos en 3 clases.

Umbrales:

- `Q33 = 37.3479 mm`
- `Q66 = 70.9957 mm`

Reglas:

- `Baja`: `rx5day_mm < Q33`
- `Media`: `Q33 <= rx5day_mm < Q66`
- `Alta`: `rx5day_mm >= Q66`

Los umbrales se guardan en:

```text
datos/modelado/umbrales_amenaza.csv
```

Hasta el Paso 08, esos umbrales se usan para crear la etiqueta del dataset. No son parte de un archivo de modelo.

## 7. Hay sesgo por zonas secas o humedas

Si, puede afectar, y hay que saber defenderlo.

Como usamos umbrales globales, una zona humeda puede tener mas meses `Alta` y una zona seca mas meses `Baja`.

Eso no es necesariamente error. Significa que `Alta` representa mucha lluvia en terminos absolutos para todo Ecuador.

Alternativa:

- Umbrales por zona: medirian "alto para esa zona".
- Umbrales globales: permiten comparar la misma cantidad de lluvia entre zonas.

Nuestro proyecto eligio umbrales globales para mantener una definicion fisica unica.

## 8. De donde salen las variables originales

Primero se descargan variables horarias de ERA5-Land:

- temperatura;
- punto de rocio;
- precipitacion;
- presion superficial;
- viento componente U;
- viento componente V;
- humedad del suelo.

Luego se transforman en indicadores diarios y mensuales.

Del dataset mensual salen variables como:

- `prcptot_mm`
- `rx1day_mm`
- `rx5day_mm`
- `max_1h_mm`
- `max_3h_mm`
- `max_6h_mm`
- `wet_days`
- `r10mm_days`
- `r20mm_days`
- `sdii_mm_per_wet_day`
- `cwd_days`
- `cdd_days`
- `temperature_mean_c`
- `temperature_max_c`
- `temperature_min_c`
- `dewpoint_mean_c`
- `relative_humidity_mean_pct`
- `wind_mean_ms`
- `wind_max_ms`
- `surface_pressure_mean_hpa`
- latitud, longitud, region y mes.

## 9. Como llegamos a 38 features

No usamos todas las variables posibles porque algunas son repetidas, muy parecidas o peligrosas para el modelo.

Primero se analizaron variables con:

- informacion mutua;
- correlacion de Spearman;
- revision de redundancia;
- analisis de lags.

Luego se eligio un conjunto compacto:

- 11 variables meteorologicas actuales;
- esas mismas 11 con `lag1`;
- esas mismas 11 con `lag11`;
- 2 variables geograficas;
- 2 variables de mes objetivo;
- 1 variable categorica de region.

Total:

```text
11 + 11 + 11 + 2 + 2 + 1 = 38
```

## 10. Las 11 variables meteorologicas actuales

- `prcptot_mm`: lluvia total del mes.
- `rx5day_mm`: maxima lluvia acumulada en 5 dias.
- `max_3h_mm`: maxima lluvia acumulada en 3 horas.
- `sdii_mm_per_wet_day`: intensidad media en dias lluviosos.
- `r20mm_days`: dias con lluvia igual o mayor a 20 mm.
- `cwd_days`: mayor racha de dias humedos.
- `cdd_days`: mayor racha de dias secos.
- `temperature_mean_c`: temperatura media.
- `relative_humidity_mean_pct`: humedad relativa media.
- `wind_mean_ms`: velocidad media del viento.
- `surface_pressure_mean_hpa`: presion superficial media.

## 11. Variables que NO entran

No entran:

- `target_amenaza`: es la respuesta.
- `target_rx5day_mm`: es el valor futuro.
- `target_period_start`: identifica el mes futuro.
- `split`: solo dice si es train, validacion o prueba.
- `rol`: solo dice si la zona es desarrollo o espacial.
- `zone_id`, `ciudad`, `provincia`: pueden hacer que el modelo memorice zonas.
- controles de calidad como dias disponibles o meses completos.

Esto evita fuga de informacion y memorizacion.

## 12. Que son target_month_sin y target_month_cos

Sirven para representar el mes del ano como ciclo.

Si usamos solo numeros:

```text
enero = 1
diciembre = 12
```

El modelo podria creer que enero esta muy lejos de diciembre porque `12 - 1 = 11`.

Pero en clima, diciembre y enero estan juntos en el ciclo anual.

Por eso usamos seno y coseno: convierten los meses en una rueda.

## 13. Conceptos antes de hablar de modelos

### Accuracy

Porcentaje total de aciertos.

Si acierta 70 de 100, accuracy = 70%.

### Precision

De todo lo que el modelo predijo como una clase, cuanto fue correcto.

Ejemplo:

```text
Predijo Alta 100 veces.
75 eran realmente Alta.
Precision Alta = 75%.
```

### Recall

De todos los casos reales de una clase, cuantos encontro.

Ejemplo:

```text
Habia 100 meses Alta.
Detecto 70.
Recall Alta = 70%.
```

### F1

Combina precision y recall:

```text
F1 = 2 * (precision * recall) / (precision + recall)
```

Indica equilibrio. Si precision o recall son bajos, F1 baja.

### Macro F1

Calcula F1 para cada clase y luego promedia:

```text
F1 Baja + F1 Media + F1 Alta
----------------------------
              3
```

La usamos porque da el mismo peso a las tres clases.

### Micro F1

Calcula el rendimiento global mezclando todas las clases. En clasificacion multiclase simple se parece mucho a accuracy.

Por eso preferimos Macro F1: muestra mejor si una clase esta fallando.

### Balanced accuracy

Promedia el recall de cada clase. Ayuda cuando las clases no estan perfectamente balanceadas.

### Baseline

Es una regla simple de comparacion.

Si un modelo complejo no supera un baseline, entonces no aporta mucho.

Baselines usados:

- Dummy: siempre predice la clase mas frecuente.
- Persistencia: predice que el mes siguiente sera igual al mes actual.
- Climatologia mensual: usa la clase mas frecuente historica por mes.

## 14. Como se entrena cada modelo

Todos reciben las mismas features y el mismo target.

Antes de entrenar:

- se imputan faltantes con mediana;
- se escala cuando el modelo lo necesita;
- `region` se convierte con one-hot;
- `SelectKBest` prueba cuantas variables numericas usar dentro de cada fold.

Validacion cruzada temporal:

- Fold 1: entrena hasta 2004, valida 2005-2007.
- Fold 2: entrena hasta 2007, valida 2008-2010.
- Fold 3: entrena hasta 2010, valida 2011-2013.
- Fold 4: entrena hasta 2013, valida 2014-2017.

## 15. Que significa C antes de verlo en modelos

`C` es un hiperparametro de algunos modelos.

Un hiperparametro es una configuracion que elegimos/probamos antes del entrenamiento final.

En SVM y Regresion Logistica:

- `C` bajo: modelo mas controlado, menos riesgo de sobreajuste.
- `C` alto: modelo mas flexible, puede ajustar mas los datos.

El valor de `C` se elige probando opciones en validacion cruzada temporal.

## 16. Modelos comparados

### Regresion Logistica

Modelo lineal. Aprende pesos para las variables y calcula probabilidades de `Baja`, `Media` y `Alta`.

Ejemplo conceptual:

```text
mas lluvia + mas humedad + cierto mes -> sube probabilidad de Alta
```

Resultado:

- Macro F1: `0.6967`
- Mejor `C = 0.1`

### Random Forest

Conjunto de muchos arboles de decision.

Cada arbol aprende reglas como:

```text
si rx5day actual > X y humedad > Y, entonces...
```

Luego los arboles votan.

Resultado:

- Macro F1: `0.7012`
- `max_depth = 18`
- `min_samples_leaf = 1`

### XGBoost

Modelo de arboles secuenciales.

Cada arbol nuevo intenta corregir errores de los anteriores.

Resultado:

- Macro F1: `0.7064`
- `learning_rate = 0.08`
- `max_depth = 3`

### SVM RBF

Busca fronteras para separar clases. Con kernel RBF puede hacer fronteras curvas.

Parametros:

- `C = 1`: equilibrio entre margen y errores.
- `gamma = 0.05`: que tan local es la influencia de cada punto.
- `kernel = rbf`: permite separacion no lineal.

Resultado:

- Macro F1: `0.7188`

Fue el ganador.

### MLP

Red neuronal simple.

Usamos:

- una capa oculta de 64 neuronas;
- `alpha = 0.0001` como regularizacion;
- `k = 10` variables numericas seleccionadas.

El MLP no "inventa" solo la arquitectura. Nosotros definimos opciones, y el entrenamiento ajusta los pesos internos.

Resultado:

- Macro F1: `0.6782`

## 17. Por que gano SVM RBF

Ranking por Macro F1:

```text
SVM RBF              0.7188
XGBoost              0.7064
Random Forest        0.7012
Regresion Logistica  0.6967
MLP                  0.6782
```

Defensa:

> Gano SVM RBF porque capturo mejor relaciones no lineales entre precipitacion, humedad, presion, viento, ubicacion y estacionalidad. Ademas, fue evaluado con el mismo protocolo temporal que los demas modelos y supero los baselines.

## 18. Resumen para decir en voz alta

El proyecto usa aprendizaje supervisado para clasificar la amenaza de precipitacion del mes siguiente. La etiqueta Baja/Media/Alta se crea con percentiles 33 y 66 de `rx5day_mm` historico. El modelo no usa el `rx5day` futuro como entrada; usa variables conocidas del mes actual, lag1, lag11, ubicacion, region y estacionalidad. Se redujo a 38 features para evitar redundancia, fuga de informacion y memorizacion. Se compararon cinco modelos con validacion temporal y gano SVM RBF por mejor Macro F1.
