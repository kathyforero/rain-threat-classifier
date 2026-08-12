"""
04_generar_caracteristicas_v2.py

Crea la versión V2 del dataset de modelado SIN modificar el dataset maestro.

V2 = 144 características candidatas originales
     + 3 variables one-hot de la amenaza conocida del mes actual
     + 2 variables cíclicas del mes objetivo (t+1)

Entradas:
    resultados_completo/dataset_modelo_mensual.csv
    resultados_completo/columnas_recomendadas_modelo.txt

Salidas:
    resultados_completo/dataset_modelo_mensual_v2.csv
    resultados_completo/columnas_modelo_v2.txt
    resultados_completo/resumen_caracteristicas_v2.json

Importante:
- amenaza_mes corresponde al mes de referencia t y es conocida al momento
  de estimar la amenaza de t+1.
- target_amenaza NO se usa como característica.
- target_month_sin/cos solo codifican el MES CALENDARIO del periodo objetivo;
  no contienen información meteorológica futura.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "resultados_completo"

DATASET_IN = DATA_DIR / "dataset_modelo_mensual.csv"
FEATURES_IN = DATA_DIR / "columnas_recomendadas_modelo.txt"

DATASET_OUT = DATA_DIR / "dataset_modelo_mensual_v2.csv"
FEATURES_OUT = DATA_DIR / "columnas_modelo_v2.txt"
SUMMARY_OUT = DATA_DIR / "resumen_caracteristicas_v2.json"

NEW_FEATURES = [
    "amenaza_actual_Baja",
    "amenaza_actual_Media",
    "amenaza_actual_Alta",
    "target_month_sin",
    "target_month_cos",
]

FORBIDDEN_FEATURES = {
    "target_amenaza",
    "target_rx5day_mm",
    "target_period_start",
    "rx5_q33",
    "rx5_q66",
}


def read_feature_list(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    if not DATASET_IN.exists():
        raise FileNotFoundError(f"No existe: {DATASET_IN}")
    if not FEATURES_IN.exists():
        raise FileNotFoundError(f"No existe: {FEATURES_IN}")

    df = pd.read_csv(DATASET_IN)
    original_features = read_feature_list(FEATURES_IN)

    required_columns = {
        "amenaza_mes",
        "target_period_start",
        "target_amenaza",
        "split",
        *original_features,
    }
    missing = sorted(required_columns - set(df.columns))
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {missing}")

    # ------------------------------------------------------------------
    # 1. Amenaza conocida del mes actual t
    # ------------------------------------------------------------------
    valid_classes = {"Baja", "Media", "Alta"}
    observed_classes = set(df["amenaza_mes"].dropna().unique())
    if observed_classes != valid_classes:
        raise ValueError(
            "amenaza_mes no contiene exactamente Baja/Media/Alta. "
            f"Encontrado: {sorted(observed_classes)}"
        )

    for cls in ["Baja", "Media", "Alta"]:
        df[f"amenaza_actual_{cls}"] = (df["amenaza_mes"] == cls).astype("int8")

    one_hot_sum = df[
        ["amenaza_actual_Baja", "amenaza_actual_Media", "amenaza_actual_Alta"]
    ].sum(axis=1)
    if not (one_hot_sum == 1).all():
        raise AssertionError("La codificación one-hot de amenaza_mes no es válida.")

    # ------------------------------------------------------------------
    # 2. Estacionalidad explícita del mes objetivo t+1
    # Mantiene la misma convención usada por month_sin/month_cos:
    # sin(2*pi*mes/12), cos(2*pi*mes/12).
    # ------------------------------------------------------------------
    target_date = pd.to_datetime(df["target_period_start"], errors="raise")
    target_month = target_date.dt.month.astype(int)

    df["target_month_sin"] = np.sin(2.0 * np.pi * target_month / 12.0)
    df["target_month_cos"] = np.cos(2.0 * np.pi * target_month / 12.0)

    # ------------------------------------------------------------------
    # 3. Lista V2
    # ------------------------------------------------------------------
    features_v2 = original_features + NEW_FEATURES

    if len(original_features) != 144:
        print(
            f"ADVERTENCIA: se esperaban 144 características originales y llegaron "
            f"{len(original_features)}. Se continuará usando la lista encontrada."
        )

    if len(features_v2) != len(set(features_v2)):
        duplicated = sorted(
            {x for x in features_v2 if features_v2.count(x) > 1}
        )
        raise AssertionError(f"Hay características duplicadas: {duplicated}")

    forbidden_found = sorted(FORBIDDEN_FEATURES.intersection(features_v2))
    if forbidden_found:
        raise AssertionError(
            f"Se detectaron variables prohibidas como entrada: {forbidden_found}"
        )

    missing_v2 = sorted(set(features_v2) - set(df.columns))
    if missing_v2:
        raise AssertionError(f"Faltan características V2: {missing_v2}")

    if df[features_v2].isna().sum().sum() != 0:
        null_counts = df[features_v2].isna().sum()
        raise AssertionError(
            "Hay nulos en V2:\n"
            + null_counts[null_counts > 0].to_string()
        )

    # Verificación de que no modificamos filas, target ni split.
    original_df = pd.read_csv(DATASET_IN)
    if len(df) != len(original_df):
        raise AssertionError("Cambió la cantidad de filas.")
    if not df["target_amenaza"].equals(original_df["target_amenaza"]):
        raise AssertionError("Se modificó target_amenaza.")
    if not df["split"].equals(original_df["split"]):
        raise AssertionError("Se modificaron las particiones.")

    # ------------------------------------------------------------------
    # 4. Escritura
    # ------------------------------------------------------------------
    df.to_csv(DATASET_OUT, index=False)
    FEATURES_OUT.write_text(
        "\n".join(features_v2) + "\n",
        encoding="utf-8",
    )

    summary = {
        "dataset_origen": str(DATASET_IN),
        "dataset_v2": str(DATASET_OUT),
        "filas": int(len(df)),
        "columnas_dataset_v2": int(df.shape[1]),
        "caracteristicas_originales": int(len(original_features)),
        "caracteristicas_nuevas": NEW_FEATURES,
        "total_caracteristicas_v2": int(len(features_v2)),
        "target": "target_amenaza",
        "descripcion": (
            "V2 conserva las características meteorológicas originales y añade "
            "la amenaza conocida del mes actual en one-hot y la estacionalidad "
            "del mes objetivo."
        ),
    }
    SUMMARY_OUT.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n" + "=" * 72)
    print("CARACTERÍSTICAS V2 GENERADAS")
    print("=" * 72)
    print(f"Dataset original:               {DATASET_IN}")
    print(f"Filas:                          {len(df)}")
    print(f"Características originales:     {len(original_features)}")
    print(f"Características nuevas:          {len(NEW_FEATURES)}")
    print(f"Total características V2:        {len(features_v2)}")
    print(f"Columnas totales dataset V2:     {df.shape[1]}")
    print("\nNuevas características:")
    for feature in NEW_FEATURES:
        print(f"  - {feature}")
    print("\nArchivos generados:")
    print(f"  - {DATASET_OUT}")
    print(f"  - {FEATURES_OUT}")
    print(f"  - {SUMMARY_OUT}")
    print(
        "\nIMPORTANTE: V2 no cambia target_amenaza ni las particiones. "
        "Todavía no uses prueba_temporal ni holdout_espacial para decidir cambios."
    )


if __name__ == "__main__":
    main()
