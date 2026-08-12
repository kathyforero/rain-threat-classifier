"""
04_generar_caracteristicas_v4.py

Experimento V4: contexto espacial explícito.

Parte del dataset V3 y añade:
- One-hot de las 12 zonas de desarrollo.
- One-hot de las regiones presentes en entrenamiento.

IMPORTANTE:
- Las categorías se obtienen SOLO del split "entrenamiento".
- Las zonas reservadas para holdout espacial NO crean columnas propias.
  Cuando se evalúen, todas las columnas zona_* quedarán en 0.
- Se conservan latitud y longitud, por lo que una zona no vista sigue teniendo
  representación espacial continua.
- No se modifica target_amenaza ni las particiones.

Entradas:
    resultados_completo/dataset_modelo_mensual_v3.csv
    resultados_completo/columnas_modelo_v3.txt

Salidas:
    resultados_completo/dataset_modelo_mensual_v4.csv
    resultados_completo/columnas_modelo_v4.txt
    resultados_completo/resumen_caracteristicas_v4.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "resultados_completo"

DATASET_IN = DATA_DIR / "dataset_modelo_mensual_v3.csv"
FEATURES_IN = DATA_DIR / "columnas_modelo_v3.txt"

DATASET_OUT = DATA_DIR / "dataset_modelo_mensual_v4.csv"
FEATURES_OUT = DATA_DIR / "columnas_modelo_v4.txt"
SUMMARY_OUT = DATA_DIR / "resumen_caracteristicas_v4.json"


def read_feature_list(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def safe_name(value: str) -> str:
    text = str(value).strip().lower()
    text = (
        text.replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
            .replace("ñ", "n")
    )
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text


def main() -> None:
    for path in (DATASET_IN, FEATURES_IN):
        if not path.exists():
            raise FileNotFoundError(f"No existe: {path}")

    df = pd.read_csv(DATASET_IN)
    features_v3 = read_feature_list(FEATURES_IN)

    required = {"zone_id", "region", "split", "target_amenaza", *features_v3}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {missing}")

    train_df = df[df["split"] == "entrenamiento"].copy()
    if train_df.empty:
        raise ValueError("No existen filas con split='entrenamiento'.")

    # --------------------------------------------------------------
    # 1. Categorías permitidas: SOLO las observadas en entrenamiento.
    # --------------------------------------------------------------
    train_zones = sorted(train_df["zone_id"].dropna().unique().tolist())
    train_regions = sorted(train_df["region"].dropna().unique().tolist())

    if len(train_zones) != 12:
        print(
            f"ADVERTENCIA: se esperaban 12 zonas de desarrollo y se encontraron "
            f"{len(train_zones)}."
        )

    zone_features = []
    for zone in train_zones:
        col = f"zona_{safe_name(zone)}"
        df[col] = (df["zone_id"] == zone).astype("int8")
        zone_features.append(col)

    region_features = []
    for region in train_regions:
        col = f"region_{safe_name(region)}"
        df[col] = (df["region"] == region).astype("int8")
        region_features.append(col)

    new_features = zone_features + region_features
    features_v4 = features_v3 + new_features

    # --------------------------------------------------------------
    # 2. Auditorías.
    # --------------------------------------------------------------
    if len(features_v4) != len(set(features_v4)):
        duplicates = sorted(
            {x for x in features_v4 if features_v4.count(x) > 1}
        )
        raise AssertionError(f"Características duplicadas: {duplicates}")

    missing_v4 = sorted(set(features_v4) - set(df.columns))
    if missing_v4:
        raise AssertionError(f"Faltan features V4: {missing_v4}")

    if df[features_v4].isna().sum().sum() != 0:
        nulls = df[features_v4].isna().sum()
        raise AssertionError(
            "Hay nulos en V4:\n"
            + nulls[nulls > 0].to_string()
        )

    # En entrenamiento cada fila debe pertenecer a exactamente una zona conocida.
    train_encoded = df.loc[
        df["split"] == "entrenamiento", zone_features
    ].sum(axis=1)
    if not (train_encoded == 1).all():
        raise AssertionError(
            "Alguna fila de entrenamiento no quedó asociada a exactamente "
            "una zona de desarrollo."
        )

    # Las zonas de holdout espacial no deben disponer de una columna propia.
    holdout_mask = df["split"].isin(["holdout_historia", "holdout_espacial"])
    holdout_zone_sums = df.loc[holdout_mask, zone_features].sum(axis=1)
    if len(holdout_zone_sums) and not (holdout_zone_sums == 0).all():
        raise AssertionError(
            "Una zona reservada fue codificada como una zona de desarrollo."
        )

    # Región sí puede generalizar porque las categorías regionales son compartidas.
    train_region_encoded = df.loc[
        df["split"] == "entrenamiento", region_features
    ].sum(axis=1)
    if not (train_region_encoded == 1).all():
        raise AssertionError(
            "Alguna fila de entrenamiento no quedó asociada a una región."
        )

    # --------------------------------------------------------------
    # 3. Guardado.
    # --------------------------------------------------------------
    df.to_csv(DATASET_OUT, index=False)
    FEATURES_OUT.write_text(
        "\n".join(features_v4) + "\n",
        encoding="utf-8",
    )

    summary = {
        "dataset_origen": str(DATASET_IN),
        "dataset_v4": str(DATASET_OUT),
        "filas": int(len(df)),
        "caracteristicas_v3": int(len(features_v3)),
        "zonas_desarrollo": [str(z) for z in train_zones],
        "regiones_entrenamiento": [str(r) for r in train_regions],
        "features_zona": zone_features,
        "features_region": region_features,
        "caracteristicas_nuevas_v4": int(len(new_features)),
        "total_caracteristicas_v4": int(len(features_v4)),
        "nota_holdout": (
            "Las zonas reservadas no tienen columna one-hot propia; sus zona_* "
            "quedan en 0 y mantienen latitud, longitud y región."
        ),
    }
    SUMMARY_OUT.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n" + "=" * 76)
    print("CARACTERÍSTICAS V4 GENERADAS")
    print("=" * 76)
    print(f"Filas:                              {len(df)}")
    print(f"Características V3:                {len(features_v3)}")
    print(f"Zonas de desarrollo codificadas:   {len(zone_features)}")
    print(f"Regiones codificadas:              {len(region_features)}")
    print(f"Características nuevas V4:         {len(new_features)}")
    print(f"Total características V4:          {len(features_v4)}")

    print("\nZonas de desarrollo:")
    for zone in train_zones:
        print(f" - {zone}")

    print("\nRegiones:")
    for region in train_regions:
        print(f" - {region}")

    print("\nFeatures nuevas de zona:")
    for feature in zone_features:
        print(f" - {feature}")

    print("\nFeatures nuevas de región:")
    for feature in region_features:
        print(f" - {feature}")

    print("\nArchivos generados:")
    print(f" - {DATASET_OUT}")
    print(f" - {FEATURES_OUT}")
    print(f" - {SUMMARY_OUT}")

    print(
        "\nIMPORTANTE: evalúa V4 primero SOLO mediante CV temporal interna "
        "(entrenamiento hasta 2017). No consultes todavía test ni holdout."
    )


if __name__ == "__main__":
    main()
