"""
PASO 04 · PREPARAR DATASET SUPERVISADO Y DIAGNOSTICAR EL TARGET

Problema supervisado
--------------------
Para cada zona z y mes t:

    X(z, t) -> Y(z, t+1)

donde Y(z, t+1) representa el nivel de intensidad de precipitación del mes
siguiente, definido a partir de Rx5day con DOS UMBRALES GLOBALES ABSOLUTOS
(en mm) calculados una sola vez.

Definición final del target
---------------------------
1. Se toma Rx5day mensual como variable física base.
2. Se usan ÚNICAMENTE las 12 zonas de desarrollo y el periodo 1991-2017.
3. Se agrupan todos esos valores de Rx5day en una sola distribución.
4. Se calculan:
       Q33_global
       Q66_global
5. Los mismos dos umbrales se aplican a TODAS las zonas y TODOS los meses:

       Baja  : Rx5day < Q33_global
       Media : Q33_global <= Rx5day < Q66_global
       Alta  : Rx5day >= Q66_global

Por tanto, una misma magnitud de Rx5day recibe la misma clase sin importar
la zona o el mes. La climatología, estacionalidad y contexto geográfico se
reservan para las CARACTERÍSTICAS de pasos posteriores, no para redefinir
el significado físico del target.

Importante
----------
- Los umbrales NO son umbrales oficiales de alerta de INAMHI.
- Son umbrales estadísticos globales para discretizar Rx5day en tres niveles.
- El test temporal 2022-2025 y el holdout espacial se etiquetan porque hacen
  parte del dataset final, pero NO se incluyen en los diagnósticos usados para
  tomar decisiones durante el desarrollo.
- Este paso NO crea lags, NO selecciona características y NO entrena modelos.

Entradas
--------
datos/procesados/indicadores_mensuales_todas_zonas.csv

Salidas
-------
datos/modelado/dataset_objetivo_mensual.csv
datos/modelado/umbrales_amenaza.csv

resultados/diagnostico_target/
    resumen_target.csv
    distribucion_por_split.csv
    distribucion_por_zona.csv
    distribucion_por_mes.csv
    transiciones_conteos.csv
    transiciones_normalizadas.csv
    comparacion_periodos.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = (
    BASE_DIR
    / "datos"
    / "procesados"
    / "indicadores_mensuales_todas_zonas.csv"
)

MODEL_DIR = BASE_DIR / "datos" / "modelado"

DIAGNOSTIC_DIR = (
    BASE_DIR
    / "resultados"
    / "diagnostico_target"
)

OUTPUT_DATASET = (
    MODEL_DIR
    / "dataset_objetivo_mensual.csv"
)

OUTPUT_THRESHOLDS = (
    MODEL_DIR
    / "umbrales_amenaza.csv"
)

TARGET_VARIABLE = "rx5day_mm"

DEVELOPMENT_ROLE = "desarrollo"
SPATIAL_HOLDOUT_ROLE = "validacion_espacial"

# Periodo que puede intervenir en el cálculo de umbrales.
THRESHOLD_START = pd.Timestamp("1991-01-01")
THRESHOLD_END = pd.Timestamp("2017-12-01")

# Particiones definidas respecto al MES OBJETIVO.
TRAIN_END = pd.Timestamp("2017-12-01")

VALIDATION_START = pd.Timestamp("2018-01-01")
VALIDATION_END = pd.Timestamp("2021-12-01")

TEST_START = pd.Timestamp("2022-01-01")
TEST_END = pd.Timestamp("2025-12-01")

Q_LOW = 0.33
Q_HIGH = 0.66

CLASS_ORDER = ["Baja", "Media", "Alta"]

EXPECTED_ZONES = 15
EXPECTED_DEVELOPMENT_ZONES = 12
EXPECTED_HOLDOUT_ZONES = 3
EXPECTED_MONTHS_PER_ZONE = 420
EXPECTED_INPUT_ROWS = 6300

EXPECTED_SUPERVISED_ROWS_PER_ZONE = 419
EXPECTED_SUPERVISED_ROWS = 6285

EXPECTED_SPLIT_COUNTS = {
    "entrenamiento": 3876,
    "validacion_temporal": 576,
    "prueba_temporal": 576,
    "holdout_historia": 969,
    "holdout_espacial": 288,
}

# 12 zonas × 27 años × 12 meses
EXPECTED_THRESHOLD_N = 3888


# =============================================================================
# UTILIDADES
# =============================================================================

def require_columns(
    frame: pd.DataFrame,
    required: list[str],
) -> None:
    missing = sorted(
        set(required).difference(frame.columns)
    )

    if missing:
        raise ValueError(
            "Faltan columnas obligatorias en el dataset mensual: "
            f"{missing}"
        )


def classify_threat_global(
    rx5day: pd.Series,
    q33: float,
    q66: float,
) -> pd.Series:
    return pd.Series(
        np.select(
            [
                rx5day < q33,
                (rx5day >= q33) & (rx5day < q66),
                rx5day >= q66,
            ],
            CLASS_ORDER,
            default=None,
        ),
        index=rx5day.index,
        dtype="object",
    )


def assign_split(row: pd.Series) -> str:
    target_date = row["target_period_start"]
    role = row["rol"]

    if role == DEVELOPMENT_ROLE:
        if target_date <= TRAIN_END:
            return "entrenamiento"

        if VALIDATION_START <= target_date <= VALIDATION_END:
            return "validacion_temporal"

        if TEST_START <= target_date <= TEST_END:
            return "prueba_temporal"

    if role == SPATIAL_HOLDOUT_ROLE:
        if target_date <= TRAIN_END:
            return "holdout_historia"

        if VALIDATION_START <= target_date <= TEST_END:
            return "holdout_espacial"

    raise ValueError(
        "No se pudo asignar split para "
        f"zone_id={row['zone_id']}, "
        f"rol={role}, "
        f"target_period_start={target_date}"
    )


def normalize_distribution(
    frame: pd.DataFrame,
    group_columns: list[str],
) -> pd.DataFrame:
    """
    Genera distribuciones únicamente con combinaciones realmente observadas.

    observed=True corrige el bug anterior en el que pandas expandía
    combinaciones inexistentes al trabajar con categorías.
    """
    counts = (
        frame.groupby(
            group_columns + ["target_amenaza"],
            observed=True,
        )
        .size()
        .rename("cantidad")
        .reset_index()
    )

    totals = (
        counts.groupby(
            group_columns,
            observed=True,
        )["cantidad"]
        .transform("sum")
    )

    counts["porcentaje"] = (
        100.0
        * counts["cantidad"]
        / totals
    )

    return counts


# =============================================================================
# 1. CARGA Y VALIDACIÓN DEL DATASET CANÓNICO
# =============================================================================

def load_monthly_dataset() -> pd.DataFrame:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"No se encontró {INPUT_FILE}. "
            "Ejecuta primero los pasos 02 y 03."
        )

    frame = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig",
    )

    require_columns(
        frame,
        [
            "zone_id",
            "ciudad",
            "provincia",
            "region",
            "rol",
            "period",
            "period_start",
            "year",
            "month",
            TARGET_VARIABLE,
        ],
    )

    frame["period_start"] = pd.to_datetime(
        frame["period_start"]
    )

    frame = (
        frame.sort_values(
            ["zone_id", "period_start"]
        )
        .reset_index(drop=True)
    )

    if len(frame) != EXPECTED_INPUT_ROWS:
        raise ValueError(
            f"Se esperaban {EXPECTED_INPUT_ROWS} filas mensuales "
            f"y se encontraron {len(frame)}."
        )

    if frame["zone_id"].nunique() != EXPECTED_ZONES:
        raise ValueError(
            "El dataset no contiene exactamente "
            f"{EXPECTED_ZONES} zonas."
        )

    rows_per_zone = frame.groupby(
        "zone_id"
    ).size()

    bad = rows_per_zone[
        rows_per_zone != EXPECTED_MONTHS_PER_ZONE
    ]

    if not bad.empty:
        raise ValueError(
            "No todas las zonas tienen "
            f"{EXPECTED_MONTHS_PER_ZONE} meses: "
            f"{bad.to_dict()}"
        )

    duplicate_keys = int(
        frame.duplicated(
            ["zone_id", "period_start"]
        ).sum()
    )

    if duplicate_keys:
        raise ValueError(
            "Se encontraron claves zona-mes duplicadas: "
            f"{duplicate_keys}"
        )

    development_count = frame.loc[
        frame["rol"] == DEVELOPMENT_ROLE,
        "zone_id",
    ].nunique()

    holdout_count = frame.loc[
        frame["rol"] == SPATIAL_HOLDOUT_ROLE,
        "zone_id",
    ].nunique()

    if (
        development_count != EXPECTED_DEVELOPMENT_ZONES
        or holdout_count != EXPECTED_HOLDOUT_ZONES
    ):
        raise ValueError(
            "Distribución de roles inesperada. "
            f"desarrollo={development_count}, "
            f"validacion_espacial={holdout_count}"
        )

    if frame[TARGET_VARIABLE].isna().any():
        raise ValueError(
            f"{TARGET_VARIABLE} contiene valores nulos."
        )

    return frame


# =============================================================================
# 2. UMBRALES GLOBALES ABSOLUTOS
# =============================================================================

def fit_global_threat_thresholds(
    frame: pd.DataFrame,
) -> tuple[float, float, int]:
    baseline = frame.loc[
        (frame["rol"] == DEVELOPMENT_ROLE)
        & (
            frame["period_start"]
            >= THRESHOLD_START
        )
        & (
            frame["period_start"]
            <= THRESHOLD_END
        )
    ].copy()

    n = len(baseline)

    if n != EXPECTED_THRESHOLD_N:
        raise ValueError(
            "El conjunto usado para calcular los umbrales globales "
            f"debería tener {EXPECTED_THRESHOLD_N} observaciones "
            f"y tiene {n}."
        )

    if (
        baseline["zone_id"].nunique()
        != EXPECTED_DEVELOPMENT_ZONES
    ):
        raise ValueError(
            "Los umbrales globales deben calcularse únicamente "
            "con las 12 zonas de desarrollo."
        )

    q33 = float(
        baseline[TARGET_VARIABLE].quantile(Q_LOW)
    )

    q66 = float(
        baseline[TARGET_VARIABLE].quantile(Q_HIGH)
    )

    if not np.isfinite(q33) or not np.isfinite(q66):
        raise ValueError(
            "Los umbrales globales no son finitos."
        )

    if q33 >= q66:
        raise ValueError(
            "Se esperaba Q33_global < Q66_global."
        )

    return q33, q66, n


def build_threshold_table(
    q33: float,
    q66: float,
    n: int,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "definicion": (
                    "terciles_globales_rx5day"
                ),
                "variable": TARGET_VARIABLE,
                "unidad": "mm",
                "scope": (
                    "12_zonas_desarrollo_1991_2017"
                ),
                "fecha_inicio": str(
                    THRESHOLD_START.date()
                ),
                "fecha_fin": str(
                    THRESHOLD_END.date()
                ),
                "zonas_utilizadas": (
                    EXPECTED_DEVELOPMENT_ZONES
                ),
                "observaciones": n,
                "q33_global_mm": q33,
                "q66_global_mm": q66,
                "interpretacion_baja": (
                    "rx5day < q33_global_mm"
                ),
                "interpretacion_media": (
                    "q33_global_mm <= rx5day < q66_global_mm"
                ),
                "interpretacion_alta": (
                    "rx5day >= q66_global_mm"
                ),
                "nota": (
                    "Umbrales estadísticos del proyecto; "
                    "no corresponden a umbrales oficiales "
                    "de alerta meteorológica."
                ),
            }
        ]
    )


# =============================================================================
# 3. ETIQUETA OBSERVADA Y TARGET t+1
# =============================================================================

def build_supervised_dataset(
    frame: pd.DataFrame,
    q33: float,
    q66: float,
) -> pd.DataFrame:
    labeled = frame.copy()

    labeled["amenaza_mes"] = (
        classify_threat_global(
            labeled[TARGET_VARIABLE],
            q33,
            q66,
        )
    )

    if labeled["amenaza_mes"].isna().any():
        raise ValueError(
            "No se pudo asignar amenaza_mes "
            "a todas las filas."
        )

    labeled = (
        labeled.sort_values(
            ["zone_id", "period_start"]
        )
        .reset_index(drop=True)
    )

    grouped = labeled.groupby(
        "zone_id",
        sort=False,
    )

    labeled["target_period_start"] = (
        grouped["period_start"].shift(-1)
    )

    labeled["target_rx5day_mm"] = (
        grouped[TARGET_VARIABLE].shift(-1)
    )

    labeled["target_amenaza"] = (
        grouped["amenaza_mes"].shift(-1)
    )

    supervised = labeled.loc[
        labeled["target_period_start"].notna()
    ].copy()

    expected_target_period = (
        supervised["period_start"]
        + pd.offsets.MonthBegin(1)
    )

    bad_horizon = int(
        (
            expected_target_period
            != supervised[
                "target_period_start"
            ]
        ).sum()
    )

    if bad_horizon:
        raise ValueError(
            "Se encontraron filas cuyo target "
            "no corresponde exactamente al mes siguiente: "
            f"{bad_horizon}"
        )

    supervised["split"] = supervised.apply(
        assign_split,
        axis=1,
    )

    return supervised


# =============================================================================
# 4. VALIDACIONES ESTRUCTURALES
# =============================================================================

def validate_supervised_dataset(
    frame: pd.DataFrame,
) -> None:
    if len(frame) != EXPECTED_SUPERVISED_ROWS:
        raise ValueError(
            f"Se esperaban {EXPECTED_SUPERVISED_ROWS} filas supervisadas "
            f"y se obtuvieron {len(frame)}."
        )

    rows_per_zone = frame.groupby(
        "zone_id"
    ).size()

    bad = rows_per_zone[
        rows_per_zone
        != EXPECTED_SUPERVISED_ROWS_PER_ZONE
    ]

    if not bad.empty:
        raise ValueError(
            "No todas las zonas tienen "
            f"{EXPECTED_SUPERVISED_ROWS_PER_ZONE} ejemplos supervisados: "
            f"{bad.to_dict()}"
        )

    split_counts = (
        frame["split"]
        .value_counts()
        .to_dict()
    )

    if split_counts != EXPECTED_SPLIT_COUNTS:
        raise ValueError(
            "Los conteos de las particiones "
            "no coinciden con lo esperado.\n"
            f"Esperado: {EXPECTED_SPLIT_COUNTS}\n"
            f"Obtenido: {split_counts}"
        )

    forbidden_nulls = frame[
        [
            "target_period_start",
            "target_rx5day_mm",
            "target_amenaza",
            "split",
        ]
    ].isna().sum()

    if (
        forbidden_nulls > 0
    ).any():
        raise ValueError(
            "Hay nulos en columnas esenciales: "
            f"{forbidden_nulls[forbidden_nulls > 0].to_dict()}"
        )

    classifier_train = frame[
        frame["split"] == "entrenamiento"
    ]

    unexpected_roles = (
        set(
            classifier_train["rol"].unique()
        )
        - {DEVELOPMENT_ROLE}
    )

    if unexpected_roles:
        raise ValueError(
            "El entrenamiento contiene roles no permitidos: "
            f"{sorted(unexpected_roles)}"
        )


# =============================================================================
# 5. DIAGNÓSTICOS DEL TARGET
# =============================================================================

def save_diagnostics(
    frame: pd.DataFrame,
    q33: float,
    q66: float,
) -> None:
    """
    IMPORTANTE:
    Los diagnósticos para decisiones de desarrollo solo observan:
      - entrenamiento
      - validación temporal

    No se inspeccionan distribuciones del test 2022-2025 ni del holdout
    espacial para evitar adaptar decisiones a conjuntos reservados.
    """
    DIAGNOSTIC_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    development_view = frame[
        frame["split"].isin(
            [
                "entrenamiento",
                "validacion_temporal",
            ]
        )
    ].copy()

    # -------------------------------------------------------------------------
    # Resumen
    # -------------------------------------------------------------------------
    summary_rows = [
        {
            "metrica": "filas_dataset_supervisado_total",
            "valor": len(frame),
        },
        {
            "metrica": "filas_diagnostico_desarrollo",
            "valor": len(development_view),
        },
        {
            "metrica": "zonas_totales",
            "valor": frame["zone_id"].nunique(),
        },
        {
            "metrica": "zonas_diagnostico",
            "valor": development_view["zone_id"].nunique(),
        },
        {
            "metrica": "variable_base_target",
            "valor": TARGET_VARIABLE,
        },
        {
            "metrica": "q33_global_mm",
            "valor": q33,
        },
        {
            "metrica": "q66_global_mm",
            "valor": q66,
        },
        {
            "metrica": "scope_umbrales",
            "valor": (
                "12 zonas desarrollo, 1991-2017"
            ),
        },
        {
            "metrica": "nota",
            "valor": (
                "Test temporal y holdout espacial "
                "no incluidos en diagnósticos."
            ),
        },
    ]

    for split_name in [
        "entrenamiento",
        "validacion_temporal",
    ]:
        subset = development_view[
            development_view["split"]
            == split_name
        ]

        for class_name in CLASS_ORDER:
            summary_rows.append(
                {
                    "metrica": (
                        f"{split_name}_"
                        f"target_{class_name.lower()}"
                    ),
                    "valor": int(
                        (
                            subset["target_amenaza"]
                            == class_name
                        ).sum()
                    ),
                }
            )

    pd.DataFrame(
        summary_rows
    ).to_csv(
        DIAGNOSTIC_DIR / "resumen_target.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # -------------------------------------------------------------------------
    # Distribución por split
    # -------------------------------------------------------------------------
    by_split = normalize_distribution(
        development_view,
        ["split"],
    )

    by_split.to_csv(
        DIAGNOSTIC_DIR
        / "distribucion_por_split.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # -------------------------------------------------------------------------
    # Distribución por zona
    # BUG CORREGIDO:
    # observed=True + target como string evita combinaciones inexistentes.
    # Esperado: 12 zonas × hasta 3 clases = máximo 36 filas.
    # -------------------------------------------------------------------------
    by_zone = normalize_distribution(
        development_view,
        [
            "zone_id",
            "ciudad",
            "rol",
        ],
    )

    by_zone.to_csv(
        DIAGNOSTIC_DIR
        / "distribucion_por_zona.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # -------------------------------------------------------------------------
    # Distribución por mes objetivo
    # -------------------------------------------------------------------------
    month_view = development_view.assign(
        target_month=(
            development_view[
                "target_period_start"
            ].dt.month
        )
    )

    by_month = normalize_distribution(
        month_view,
        ["target_month"],
    )

    by_month.to_csv(
        DIAGNOSTIC_DIR
        / "distribucion_por_mes.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # -------------------------------------------------------------------------
    # Transiciones amenaza(t) -> amenaza(t+1)
    # Solo desarrollo observado durante train + validation.
    # -------------------------------------------------------------------------
    transition_counts = pd.crosstab(
        development_view[
            "amenaza_mes"
        ],
        development_view[
            "target_amenaza"
        ],
        dropna=False,
    ).reindex(
        index=CLASS_ORDER,
        columns=CLASS_ORDER,
        fill_value=0,
    )

    transition_counts.index.name = (
        "amenaza_mes_t"
    )

    transition_counts.columns.name = (
        "amenaza_mes_t_mas_1"
    )

    transition_counts.to_csv(
        DIAGNOSTIC_DIR
        / "transiciones_conteos.csv",
        encoding="utf-8-sig",
    )

    transition_normalized = (
        transition_counts.div(
            transition_counts.sum(
                axis=1
            ),
            axis=0,
        )
    )

    transition_normalized.to_csv(
        DIAGNOSTIC_DIR
        / "transiciones_normalizadas.csv",
        encoding="utf-8-sig",
    )

    # -------------------------------------------------------------------------
    # Comparación train vs validation solamente.
    # -------------------------------------------------------------------------
    comparison = normalize_distribution(
        development_view,
        ["split"],
    )

    comparison.to_csv(
        DIAGNOSTIC_DIR
        / "comparacion_periodos.csv",
        index=False,
        encoding="utf-8-sig",
    )


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    DIAGNOSTIC_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "PASO 04 · PREPARACIÓN DEL PROBLEMA SUPERVISADO"
    )
    print(
        "------------------------------------------------"
    )

    monthly = load_monthly_dataset()

    print(
        f"Dataset mensual cargado: "
        f"{len(monthly):,} filas, "
        f"{monthly['zone_id'].nunique()} zonas."
    )

    q33, q66, threshold_n = (
        fit_global_threat_thresholds(
            monthly
        )
    )

    print(
        "\nUmbrales globales de Rx5day "
        "calculados únicamente con "
        "las 12 zonas de desarrollo (1991-2017):"
    )
    print(
        f"Q33 global = {q33:.4f} mm"
    )
    print(
        f"Q66 global = {q66:.4f} mm"
    )
    print(
        f"Observaciones usadas = {threshold_n:,}"
    )

    thresholds = build_threshold_table(
        q33,
        q66,
        threshold_n,
    )

    supervised = build_supervised_dataset(
        monthly,
        q33,
        q66,
    )

    validate_supervised_dataset(
        supervised
    )

    thresholds.to_csv(
        OUTPUT_THRESHOLDS,
        index=False,
        encoding="utf-8-sig",
    )

    supervised.to_csv(
        OUTPUT_DATASET,
        index=False,
        encoding="utf-8-sig",
    )

    save_diagnostics(
        supervised,
        q33,
        q66,
    )

    split_counts = (
        supervised["split"]
        .value_counts()
        .reindex(
            list(
                EXPECTED_SPLIT_COUNTS
            )
        )
    )

    print(
        "\nConteos estructurales por split:"
    )
    print(
        split_counts.to_string()
    )

    print(
        "\nArchivos principales:"
    )
    print(
        f" - {OUTPUT_DATASET.resolve()}"
    )
    print(
        f" - {OUTPUT_THRESHOLDS.resolve()}"
    )
    print(
        f" - Diagnósticos: "
        f"{DIAGNOSTIC_DIR.resolve()}"
    )

    print(
        "\nPASO 04 COMPLETADO."
    )
    print(
        "El target utiliza umbrales globales absolutos de Rx5day."
    )
    print(
        "El bug de combinaciones inexistentes en la distribución "
        "por zona fue corregido."
    )
    print(
        "El test 2022-2025 y el holdout espacial no se incluyen "
        "en los diagnósticos de desarrollo."
    )
    print(
        "Todavía no se han creado lags, seleccionado características "
        "ni entrenado modelos."
    )


if __name__ == "__main__":
    main()
