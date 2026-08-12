"""
04_generar_caracteristicas_v3.py

Experimento V3 de ingeniería temporal.

Parte de V2 y añade señal temporal explícita sin usar información futura:

1) Antecedentes estacionales del mismo mes calendario del objetivo en el año previo.
   Como el objetivo es t+1, ese antecedente corresponde a t-11.
2) Agregados recientes de 3 y 6 meses.
3) Tendencias simples entre el mes actual y el inmediatamente anterior.

Entradas:
    resultados_completo/dataset_modelo_mensual_v2.csv
    resultados_completo/columnas_modelo_v2.txt
    resultados_completo/indicadores_mensuales_todas_zonas.csv

Salidas:
    resultados_completo/dataset_modelo_mensual_v3.csv
    resultados_completo/columnas_modelo_v3.txt
    resultados_completo/resumen_caracteristicas_v3.json

El dataset V3 elimina únicamente las filas iniciales que no poseen historia suficiente
para construir lag11. NO modifica target_amenaza ni las particiones existentes.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "resultados_completo"

DATASET_V2 = DATA_DIR / "dataset_modelo_mensual_v2.csv"
FEATURES_V2 = DATA_DIR / "columnas_modelo_v2.txt"
MONTHLY_DATA = DATA_DIR / "indicadores_mensuales_todas_zonas.csv"

DATASET_OUT = DATA_DIR / "dataset_modelo_mensual_v3.csv"
FEATURES_OUT = DATA_DIR / "columnas_modelo_v3.txt"
SUMMARY_OUT = DATA_DIR / "resumen_caracteristicas_v3.json"


SEASONAL_BASE_FEATURES = [
    "prcptot_mm",
    "rx1day_mm",
    "rx5day_mm",
    "max_6h_mm",
    "wet_days",
    "sdii_mm_per_wet_day",
    "temperature_mean_c",
    "relative_humidity_mean_pct",
]

SEASONAL_FEATURES = [
    f"{feature}_lag11"
    for feature in SEASONAL_BASE_FEATURES
]

AGGREGATE_FEATURES = {
    "prcptot_media_3m": [f"prcptot_mm_lag{i}" for i in range(0, 3)],
    "prcptot_media_6m": [f"prcptot_mm_lag{i}" for i in range(0, 6)],
    "rx5_media_3m": [f"rx5day_mm_lag{i}" for i in range(0, 3)],
    "rx5_max_6m": [f"rx5day_mm_lag{i}" for i in range(0, 6)],
    "humedad_media_3m": [
        f"relative_humidity_mean_pct_lag{i}" for i in range(0, 3)
    ],
    "temperatura_media_3m": [
        f"temperature_mean_c_lag{i}" for i in range(0, 3)
    ],
}

TREND_FEATURES = {
    "prcptot_tendencia_1m": ("prcptot_mm_lag0", "prcptot_mm_lag1"),
    "rx5_tendencia_1m": ("rx5day_mm_lag0", "rx5day_mm_lag1"),
    "humedad_tendencia_1m": (
        "relative_humidity_mean_pct_lag0",
        "relative_humidity_mean_pct_lag1",
    ),
    "temperatura_tendencia_1m": (
        "temperature_mean_c_lag0",
        "temperature_mean_c_lag1",
    ),
}

NEW_FEATURES = (
    SEASONAL_FEATURES
    + list(AGGREGATE_FEATURES)
    + list(TREND_FEATURES)
)


def read_feature_list(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    for path in (DATASET_V2, FEATURES_V2, MONTHLY_DATA):
        if not path.exists():
            raise FileNotFoundError(f"No existe: {path}")

    df = pd.read_csv(DATASET_V2)
    monthly = pd.read_csv(MONTHLY_DATA)
    features_v2 = read_feature_list(FEATURES_V2)

    df["period_start"] = pd.to_datetime(df["period_start"], errors="raise")
    df["target_period_start"] = pd.to_datetime(
        df["target_period_start"], errors="raise"
    )
    monthly["period_start"] = pd.to_datetime(
        monthly["period_start"], errors="raise"
    )

    if len(features_v2) != 149:
        print(
            f"ADVERTENCIA: se esperaban 149 características V2 y se encontraron "
            f"{len(features_v2)}."
        )

    missing_monthly = sorted(
        set(SEASONAL_BASE_FEATURES) - set(monthly.columns)
    )
    if missing_monthly:
        raise ValueError(
            "Faltan indicadores mensuales necesarios para V3: "
            f"{missing_monthly}"
        )

    # ------------------------------------------------------------------
    # 1. LAG 11: mismo mes calendario del objetivo, un año antes.
    # Ej.: referencia dic-2025, objetivo ene-2026 -> lag11 = ene-2025.
    # ------------------------------------------------------------------
    monthly = monthly.sort_values(["zone_id", "period_start"]).copy()

    seasonal_cols = ["zone_id", "period_start"]
    for feature in SEASONAL_BASE_FEATURES:
        new_name = f"{feature}_lag11"
        monthly[new_name] = monthly.groupby("zone_id")[feature].shift(11)
        seasonal_cols.append(new_name)

    seasonal = monthly[seasonal_cols].copy()

    rows_before_merge = len(df)
    df = df.merge(
        seasonal,
        on=["zone_id", "period_start"],
        how="left",
        validate="one_to_one",
    )
    if len(df) != rows_before_merge:
        raise AssertionError("El merge de lag11 cambió la cantidad de filas.")

    # ------------------------------------------------------------------
    # 2. Agregados recientes.
    # ------------------------------------------------------------------
    for new_name, source_cols in AGGREGATE_FEATURES.items():
        missing = sorted(set(source_cols) - set(df.columns))
        if missing:
            raise ValueError(
                f"No se puede construir {new_name}; faltan: {missing}"
            )

        if new_name == "rx5_max_6m":
            df[new_name] = df[source_cols].max(axis=1)
        else:
            df[new_name] = df[source_cols].mean(axis=1)

    # ------------------------------------------------------------------
    # 3. Tendencias simples.
    # Positivo = valor del mes actual mayor al mes anterior.
    # ------------------------------------------------------------------
    for new_name, (current_col, previous_col) in TREND_FEATURES.items():
        for col in (current_col, previous_col):
            if col not in df.columns:
                raise ValueError(
                    f"No se puede construir {new_name}; falta {col}"
                )
        df[new_name] = df[current_col] - df[previous_col]

    features_v3 = features_v2 + NEW_FEATURES

    if len(features_v3) != len(set(features_v3)):
        duplicates = sorted(
            {feature for feature in features_v3 if features_v3.count(feature) > 1}
        )
        raise AssertionError(
            f"Hay características duplicadas en V3: {duplicates}"
        )

    # Lag11 no existe para los primeros meses de cada zona.
    # Se eliminan SOLO las filas que no tienen todas las features V3 disponibles.
    rows_before_drop = len(df)
    missing_mask = df[features_v3].isna().any(axis=1)
    removed_by_missing_history = int(missing_mask.sum())
    df = df.loc[~missing_mask].copy()
    rows_after_drop = len(df)

    if df[features_v3].isna().sum().sum() != 0:
        raise AssertionError("V3 aún contiene nulos en las características.")

    if df["target_amenaza"].isna().sum() != 0:
        raise AssertionError("V3 contiene targets nulos.")

    if set(df["target_amenaza"].unique()) != {"Baja", "Media", "Alta"}:
        raise AssertionError(
            "Las clases de target_amenaza cambiaron inesperadamente."
        )

    # ------------------------------------------------------------------
    # 4. Escritura.
    # ------------------------------------------------------------------
    serializable = df.copy()
    serializable["period_start"] = serializable["period_start"].dt.strftime(
        "%Y-%m-%d"
    )
    serializable["target_period_start"] = serializable[
        "target_period_start"
    ].dt.strftime("%Y-%m-%d")
    serializable.to_csv(DATASET_OUT, index=False)

    FEATURES_OUT.write_text(
        "\n".join(features_v3) + "\n",
        encoding="utf-8",
    )

    split_counts = {
        str(k): int(v)
        for k, v in df["split"].value_counts().to_dict().items()
    }

    summary = {
        "dataset_origen": str(DATASET_V2),
        "dataset_v3": str(DATASET_OUT),
        "filas_v2": int(rows_before_drop),
        "filas_eliminadas_por_historia_lag11": removed_by_missing_history,
        "filas_v3": int(rows_after_drop),
        "caracteristicas_v2": int(len(features_v2)),
        "caracteristicas_nuevas_v3": int(len(NEW_FEATURES)),
        "total_caracteristicas_v3": int(len(features_v3)),
        "lag11": SEASONAL_FEATURES,
        "agregados": list(AGGREGATE_FEATURES),
        "tendencias": list(TREND_FEATURES),
        "distribucion_split_v3": split_counts,
    }
    SUMMARY_OUT.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n" + "=" * 76)
    print("CARACTERÍSTICAS V3 GENERADAS")
    print("=" * 76)
    print(f"Filas V2:                              {rows_before_drop}")
    print(
        "Filas eliminadas por falta de lag11:   "
        f"{removed_by_missing_history}"
    )
    print(f"Filas V3:                              {rows_after_drop}")
    print(f"Características V2:                    {len(features_v2)}")
    print(f"Características nuevas V3:             {len(NEW_FEATURES)}")
    print(f"Total características V3:              {len(features_v3)}")

    print("\nNuevas características V3:")
    print("\n  Antecedentes estacionales (lag11):")
    for feature in SEASONAL_FEATURES:
        print(f"   - {feature}")

    print("\n  Agregados recientes:")
    for feature in AGGREGATE_FEATURES:
        print(f"   - {feature}")

    print("\n  Tendencias:")
    for feature in TREND_FEATURES:
        print(f"   - {feature}")

    print("\nDistribución por split:")
    print(df["split"].value_counts().to_string())

    print("\nArchivos generados:")
    print(f" - {DATASET_OUT}")
    print(f" - {FEATURES_OUT}")
    print(f" - {SUMMARY_OUT}")

    print(
        "\nIMPORTANTE: V3 debe evaluarse primero SOLO mediante la validación "
        "cruzada temporal interna de entrenamiento (hasta 2017). "
        "No uses aún 2018-2021 para decidir si conservar estas features."
    )


if __name__ == "__main__":
    main()
