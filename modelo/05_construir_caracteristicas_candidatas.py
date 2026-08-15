"""
PASO 05B · CONSTRUIR CARACTERÍSTICAS CANDIDATAS

Objetivo
--------
Construir un conjunto compacto y reproducible de características candidatas
para el modelado, a partir de las conclusiones del análisis del Paso 05A.

Principios
----------
1. No se usa ninguna variable futura como predictor.
2. No se usan zone_id/ciudad/provincia como features del clasificador.
3. Se eliminan por diseño grupos de variables fuertemente redundantes.
4. Los lags candidatos se limitan a:
      - lag1  : antecedente inmediato.
      - lag11 : mismo mes calendario del año anterior al mes objetivo.
   No se crean lag0..lag12 indiscriminadamente.
5. La selección SUPERVISADA definitiva NO se realiza aquí.
   El Paso 06 deberá ejecutar SelectKBest dentro de cada fold de CV temporal.
6. El test temporal y el holdout espacial no participan en ninguna decisión.

Entrada
-------
datos/modelado/dataset_objetivo_mensual.csv

Salida
------
datos/modelado/dataset_caracteristicas_candidatas.csv
resultados/analisis_caracteristicas/catalogo_caracteristicas_modelado.csv

La creación de lags usa exclusivamente valores pasados dentro de cada zona.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "datos"
    / "modelado"
    / "dataset_objetivo_mensual.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "datos"
    / "modelado"
    / "dataset_caracteristicas_candidatas.csv"
)

REPORT_DIR = (
    BASE_DIR
    / "resultados"
    / "analisis_caracteristicas"
)

CATALOG_FILE = (
    REPORT_DIR
    / "catalogo_caracteristicas_modelado.csv"
)

# -----------------------------------------------------------------------------
# Características actuales retenidas por DISEÑO.
#
# La reducción aquí es principalmente semántica + redundancia no supervisada.
# No se escogen variables por un umbral de MI calculado sobre todo train.
# La selección supervisada se deja para el Pipeline/CV del Paso 06.
# -----------------------------------------------------------------------------

CURRENT_METEO_FEATURES = [
    # Magnitud mensual de precipitación.
    "prcptot_mm",

    # Intensidad acumulada multidiaria.
    "rx5day_mm",

    # Intensidad subdiaria representativa.
    # Se conserva max_3h frente a max_1h/max_6h por alta redundancia.
    "max_3h_mm",

    # Intensidad media durante días húmedos.
    "sdii_mm_per_wet_day",

    # Frecuencia de episodios claramente intensos.
    "r20mm_days",

    # Persistencia húmeda y seca.
    "cwd_days",
    "cdd_days",

    # Estado termodinámico.
    # Se conserva temperatura media; min/max/dewpoint son muy redundantes.
    "temperature_mean_c",
    "relative_humidity_mean_pct",

    # Circulación y estado atmosférico.
    # Se conserva viento medio frente a viento máximo por redundancia.
    "wind_mean_ms",
    "surface_pressure_mean_hpa",
]

GEOGRAPHIC_NUMERIC_FEATURES = [
    "latitud_solicitada",
    "longitud_solicitada",
]

CATEGORICAL_FEATURES = [
    "region",
]

# Los lags se crean para las variables meteorológicas retenidas.
# lag1 = memoria reciente.
# lag11 = mismo mes calendario del año anterior al mes objetivo.
LAG_SOURCE_FEATURES = CURRENT_METEO_FEATURES.copy()
LAGS = [1, 11]

METADATA_COLUMNS = [
    "zone_id",
    "ciudad",
    "provincia",
    "region",
    "rol",
    "period",
    "period_start",
    "target_period_start",
    "split",
    "amenaza_mes",
    "target_amenaza",
    "target_rx5day_mm",
]


def require_columns(
    frame: pd.DataFrame,
    columns: list[str],
) -> None:
    missing = sorted(
        set(columns).difference(frame.columns)
    )

    if missing:
        raise ValueError(
            f"Faltan columnas obligatorias: {missing}"
        )


def add_target_month_features(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    result = frame.copy()

    result["target_month"] = (
        result["target_period_start"].dt.month
    )

    result["target_month_sin"] = np.sin(
        2
        * np.pi
        * result["target_month"]
        / 12
    )

    result["target_month_cos"] = np.cos(
        2
        * np.pi
        * result["target_month"]
        / 12
    )

    return result


def add_backward_lags(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    result = (
        frame.sort_values(
            ["zone_id", "period_start"]
        )
        .copy()
    )

    grouped = result.groupby(
        "zone_id",
        sort=False,
    )

    for feature in LAG_SOURCE_FEATURES:
        for lag in LAGS:
            result[
                f"{feature}__lag{lag}"
            ] = grouped[feature].shift(lag)

    return result


def build_catalog(
    numeric_features: list[str],
    lag_features: list[str],
) -> pd.DataFrame:
    rows: list[dict[str, str]] = []

    for feature in CURRENT_METEO_FEATURES:
        rows.append({
            "caracteristica": feature,
            "familia": "meteorologica_actual",
            "tipo": "numerica",
            "disponibilidad": "conocida_en_t",
            "justificacion": (
                "Representación meteorológica retenida tras "
                "revisión semántica y de redundancia."
            ),
        })

    for feature in GEOGRAPHIC_NUMERIC_FEATURES:
        rows.append({
            "caracteristica": feature,
            "familia": "geografica",
            "tipo": "numerica",
            "disponibilidad": "estatica",
            "justificacion": (
                "Contexto espacial continuo potencialmente "
                "generalizable a zonas no vistas."
            ),
        })

    rows.extend([
        {
            "caracteristica": "target_month_sin",
            "familia": "estacionalidad",
            "tipo": "numerica",
            "disponibilidad": "conocida_en_t",
            "justificacion": (
                "Codificación cíclica del mes objetivo."
            ),
        },
        {
            "caracteristica": "target_month_cos",
            "familia": "estacionalidad",
            "tipo": "numerica",
            "disponibilidad": "conocida_en_t",
            "justificacion": (
                "Codificación cíclica del mes objetivo."
            ),
        },
    ])

    for feature in CATEGORICAL_FEATURES:
        rows.append({
            "caracteristica": feature,
            "familia": "geografica",
            "tipo": "categorica",
            "disponibilidad": "estatica",
            "justificacion": (
                "Contexto regional generalizable; se codificará "
                "dentro del Pipeline del Paso 06."
            ),
        })

    for feature in lag_features:
        source, lag_text = feature.split("__lag")
        lag = int(lag_text)

        rows.append({
            "caracteristica": feature,
            "familia": (
                "antecedente_reciente"
                if lag == 1
                else "analogo_estacional"
            ),
            "tipo": "numerica",
            "disponibilidad": "historica",
            "justificacion": (
                "lag1: antecedente inmediato."
                if lag == 1
                else (
                    "lag11: mismo mes calendario del año "
                    "anterior al mes objetivo."
                )
            ),
        })

    return pd.DataFrame(rows)


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"No se encontró {INPUT_FILE}. "
            "Ejecuta primero el Paso 04."
        )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig",
    )

    require_columns(
        df,
        METADATA_COLUMNS
        + CURRENT_METEO_FEATURES
        + GEOGRAPHIC_NUMERIC_FEATURES,
    )

    df["period_start"] = pd.to_datetime(
        df["period_start"]
    )

    df["target_period_start"] = pd.to_datetime(
        df["target_period_start"]
    )

    df = add_target_month_features(df)
    df = add_backward_lags(df)

    lag_features = [
        f"{feature}__lag{lag}"
        for feature in LAG_SOURCE_FEATURES
        for lag in LAGS
    ]

    numeric_features = (
        CURRENT_METEO_FEATURES
        + GEOGRAPHIC_NUMERIC_FEATURES
        + [
            "target_month_sin",
            "target_month_cos",
        ]
        + lag_features
    )

    model_columns = (
        METADATA_COLUMNS
        + [
            "target_month",
        ]
        + numeric_features
    )

    output = df[model_columns].copy()

    # lag11 hace que los primeros 11 registros de cada zona no tengan
    # historia suficiente. La pérdida ocurre explícitamente aquí, no antes.
    before = len(output)

    output = output.dropna(
        subset=lag_features
    ).reset_index(drop=True)

    removed = before - len(output)

    # Ninguna feature puede contener valores futuros.
    forbidden_predictors = {
        "target_amenaza",
        "target_rx5day_mm",
        "target_period_start",
    }

    accidental = (
        forbidden_predictors
        .intersection(numeric_features)
    )

    if accidental:
        raise RuntimeError(
            f"Leakage detectado en predictors: {sorted(accidental)}"
        )

    # Validaciones esperadas por la estructura temporal.
    expected_total = 6120

    if len(output) != expected_total:
        raise ValueError(
            f"Se esperaban {expected_total} filas después de lag11 "
            f"y se obtuvieron {len(output)}."
        )

    split_counts = (
        output["split"]
        .value_counts()
        .to_dict()
    )

    expected_train = 3744

    if split_counts.get("entrenamiento") != expected_train:
        raise ValueError(
            "El número de filas de entrenamiento después de crear "
            f"lag11 debería ser {expected_train}, pero es "
            f"{split_counts.get('entrenamiento')}."
        )

    output.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    catalog = build_catalog(
        numeric_features,
        lag_features,
    )

    catalog.to_csv(
        CATALOG_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        "PASO 05B · CARACTERÍSTICAS CANDIDATAS"
    )
    print(
        "-------------------------------------"
    )
    print(
        f"Filas de entrada: {before:,}"
    )
    print(
        f"Filas eliminadas por falta de lag11: {removed:,}"
    )
    print(
        f"Filas finales: {len(output):,}"
    )
    print(
        f"Características numéricas candidatas: "
        f"{len(numeric_features)}"
    )
    print(
        f"Características categóricas candidatas: "
        f"{len(CATEGORICAL_FEATURES)}"
    )
    print(
        f"Total de candidatas antes de one-hot: "
        f"{len(numeric_features) + len(CATEGORICAL_FEATURES)}"
    )

    print(
        "\nConteos por split:"
    )
    print(
        output["split"]
        .value_counts()
        .to_string()
    )

    print(
        "\nArchivo generado:"
    )
    print(
        OUTPUT_FILE.resolve()
    )

    print(
        "\nCatálogo:"
    )
    print(
        CATALOG_FILE.resolve()
    )

    print(
        "\nIMPORTANTE:"
    )
    print(
        "No se realizó selección supervisada definitiva."
    )
    print(
        "El Paso 06 deberá ejecutar la selección dentro "
        "de cada fold de validación temporal."
    )


if __name__ == "__main__":
    main()
