# Módulo de modelo

Contiene el pipeline reproducible de machine learning del proyecto.

## Orden de ejecución

```text
01_descargar_era5_land_horario.py
02_construir_indicadores.py
03_validar_calidad_dataset.py
04_preparar_dataset_modelado.py
05_analisis_caracteristicas.ipynb
05_construir_caracteristicas_candidatas.py
06_entrenar_comparar_modelos.ipynb
07_validar_modelo.ipynb
08_evaluacion_final.ipynb
09_exportar_modelo_final.py
```

Los scripts detectan la raíz del repositorio o usan `parent.parent`, por lo que datos y resultados permanecen fuera de `modelo/`.

## Responsabilidades

- **01–03:** adquisición, construcción meteorológica y control de calidad.
- **04:** target global Rx5day, horizonte `t -> t+1` y particiones.
- **05:** análisis e ingeniería de las 38 características candidatas.
- **06:** comparación de cinco modelos con CV temporal y baselines.
- **07:** validación temporal 2018–2021 de la configuración congelada.
- **08:** evaluación final temporal y espacial.
- **09:** exportación operativa posterior a la evaluación; no vuelve a medir test/holdout.

## Configuración congelada

```text
SVM RBF
C = 1
gamma = 0.05
k = all
```

No modificar hiperparámetros basándose en 2022–2025, porque ese periodo ya fue consultado por el equipo.
