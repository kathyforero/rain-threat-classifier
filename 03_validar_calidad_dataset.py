"""
Audita la calidad de los datos crudos y de los datasets meteorológicos
derivados antes de iniciar cualquier etapa de Machine Learning.

EJECUTAR
--------
    py 03_validar_calidad_dataset.py

ENTRADAS
--------
datos/crudos/era5_land/<zona>/
datos/procesados/indicadores_diarios_todas_zonas.csv
datos/procesados/indicadores_mensuales_todas_zonas.csv
datos/calidad/reporte_calidad.csv
zonas_era5_ecuador.csv

SALIDA
------
datos/calidad/reporte_auditoria_dataset.csv

Este paso NO audita:
- target de clasificación;
- lags;
- train/validation/test;
- características seleccionadas;
- modelos.

Esas decisiones pertenecen a los pasos posteriores del pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent

ZONES_FILE = (
    BASE_DIR
    / "zonas_era5_ecuador.csv"
)
RAW_DIR = (
    BASE_DIR
    / "datos"
    / "crudos"
    / "era5_land"
)
PROCESSED_DIR = (
    BASE_DIR
    / "datos"
    / "procesados"
)
QUALITY_DIR = (
    BASE_DIR
    / "datos"
    / "calidad"
)

FILES = {
    "diario": (
        PROCESSED_DIR
        / "indicadores_diarios_todas_zonas.csv"
    ),
    "mensual": (
        PROCESSED_DIR
        / "indicadores_mensuales_todas_zonas.csv"
    ),
    "calidad": (
        QUALITY_DIR
        / "reporte_calidad.csv"
    ),
}

AUDIT_FILE = (
    QUALITY_DIR
    / "reporte_auditoria_dataset.csv"
)

EXPECTED_ZONES = 15
EXPECTED_DEVELOPMENT_ZONES = 12
EXPECTED_HOLDOUT_ZONES = 3
EXPECTED_DAYS_PER_ZONE = 12_784
EXPECTED_MONTHS_PER_ZONE = 420

EXPECTED_RAW_START = "1991-01-01"
EXPECTED_RAW_END = "2026-01-01"

EXPECTED_RAW_VARIABLES = {
    "2m_temperature",
    "2m_dewpoint_temperature",
    "total_precipitation",
    "surface_pressure",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "volumetric_soil_water_layer_1",
}

COMPLETE_MARKER_NAME = (
    "_DESCARGA_COMPLETA.json"
)

checks: list[
    dict[str, object]
] = []


def add_check(
    level: str,
    name: str,
    ok: bool,
    detail: str,
) -> None:
    checks.append({
        "nivel": level,
        "verificacion": name,
        "resultado": (
            "OK"
            if ok
            else level
        ),
        "detalle": detail,
    })


def require_columns(
    frame: pd.DataFrame,
    columns: list[str],
    dataset_name: str,
) -> bool:
    missing = sorted(
        set(columns)
        .difference(
            frame.columns
        )
    )

    add_check(
        "ERROR",
        (
            f"{dataset_name}: "
            "columnas obligatorias"
        ),
        not missing,
        (
            "Todas presentes."
            if not missing
            else f"Faltan: {missing}"
        ),
    )

    return not missing


def count_by_zone(
    frame: pd.DataFrame,
    expected: int,
    dataset_name: str,
) -> None:
    counts = (
        frame
        .groupby("zone_id")
        .size()
    )

    bad = counts[
        counts != expected
    ]

    add_check(
        "ERROR",
        (
            f"{dataset_name}: "
            "filas por zona"
        ),
        bad.empty,
        (
            f"Todas las zonas tienen "
            f"{expected} filas."
            if bad.empty
            else (
                "Conteos incorrectos: "
                f"{bad.to_dict()}"
            )
        ),
    )


def has_infinite(
    frame: pd.DataFrame,
) -> bool:
    numeric = frame.select_dtypes(
        include=[np.number]
    )

    return bool(
        np.isinf(
            numeric.to_numpy()
        ).any()
    )


def processed_without_soil(
    frame: pd.DataFrame,
    dataset_name: str,
) -> None:
    """
    La variable de humedad del suelo sí forma parte de la descarga cruda
    original, pero el pipeline histórico no la incorpora a los indicadores
    diario/mensual utilizados posteriormente.
    """
    soil_columns = [
        column
        for column in frame.columns
        if (
            "swvl1"
            in column.lower()
            or "soil_water"
            in column.lower()
        )
    ]

    add_check(
        "ERROR",
        (
            f"{dataset_name}: "
            "humedad del suelo no "
            "propagada al dataset derivado"
        ),
        not soil_columns,
        (
            "No existen columnas de "
            "humedad del suelo en el "
            "dataset derivado."
            if not soil_columns
            else (
                "Columnas encontradas: "
                f"{soil_columns}"
            )
        ),
    )


def load_reference_zones() -> pd.DataFrame:
    if not ZONES_FILE.exists():
        raise FileNotFoundError(
            f"No se encontró {ZONES_FILE}"
        )

    zones = pd.read_csv(
        ZONES_FILE,
        encoding="utf-8-sig",
    )

    required = [
        "zone_id",
        "ciudad",
        "provincia",
        "region",
        "latitud",
        "longitud",
        "rol",
    ]

    if not require_columns(
        zones,
        required,
        "Zonas",
    ):
        raise ValueError(
            "El catálogo de zonas "
            "no tiene la estructura "
            "esperada."
        )

    duplicate_ids = int(
        zones["zone_id"]
        .duplicated()
        .sum()
    )

    add_check(
        "ERROR",
        "Zonas: zone_id único",
        duplicate_ids == 0,
        f"Duplicados: {duplicate_ids}",
    )

    add_check(
        "ERROR",
        "Zonas: 15 zonas definidas",
        len(zones) == EXPECTED_ZONES,
        f"Filas encontradas: {len(zones)}",
    )

    roles = (
        zones
        .groupby("rol")["zone_id"]
        .nunique()
        .to_dict()
    )

    roles_ok = (
        roles.get(
            "desarrollo",
            0,
        )
        == EXPECTED_DEVELOPMENT_ZONES
        and roles.get(
            "validacion_espacial",
            0,
        )
        == EXPECTED_HOLDOUT_ZONES
    )

    add_check(
        "ERROR",
        (
            "Zonas: 12 desarrollo "
            "y 3 validación espacial"
        ),
        roles_ok,
        f"Distribución: {roles}",
    )

    return zones


def audit_raw_downloads(
    zones: pd.DataFrame,
) -> None:
    if not RAW_DIR.exists():
        add_check(
            "ERROR",
            "Crudos: directorio existe",
            False,
            f"No existe {RAW_DIR}",
        )
        return

    add_check(
        "ERROR",
        "Crudos: directorio existe",
        True,
        str(RAW_DIR),
    )

    missing_zone_dirs: list[str] = []
    missing_markers: list[str] = []
    invalid_markers: list[str] = []
    missing_files: list[str] = []
    variable_mismatches: list[str] = []
    date_mismatches: list[str] = []

    for _, zone in zones.iterrows():
        zone_id = zone["zone_id"]
        zone_dir = RAW_DIR / zone_id

        if not zone_dir.exists():
            missing_zone_dirs.append(
                zone_id
            )
            continue

        marker = (
            zone_dir
            / COMPLETE_MARKER_NAME
        )

        if not marker.exists():
            missing_markers.append(
                zone_id
            )
            continue

        try:
            payload = json.loads(
                marker.read_text(
                    encoding="utf-8"
                )
            )
        except Exception as exc:
            invalid_markers.append(
                f"{zone_id}: {exc}"
            )
            continue

        variables = set(
            payload.get(
                "variables",
                [],
            )
        )

        if variables != EXPECTED_RAW_VARIABLES:
            variable_mismatches.append(
                (
                    f"{zone_id}: "
                    f"{sorted(variables)}"
                )
            )

        if (
            payload.get(
                "fecha_inicial_solicitada"
            )
            != EXPECTED_RAW_START
            or payload.get(
                "fecha_final_solicitada"
            )
            != EXPECTED_RAW_END
        ):
            date_mismatches.append(
                zone_id
            )

        for relative_name in payload.get(
            "archivos_netcdf",
            [],
        ):
            if not (
                zone_dir
                / relative_name
            ).exists():
                missing_files.append(
                    (
                        f"{zone_id}/"
                        f"{relative_name}"
                    )
                )

    add_check(
        "ERROR",
        "Crudos: carpeta por cada zona",
        not missing_zone_dirs,
        (
            "Todas presentes."
            if not missing_zone_dirs
            else (
                "Faltan: "
                f"{missing_zone_dirs}"
            )
        ),
    )

    add_check(
        "ERROR",
        (
            "Crudos: marcador de descarga "
            "completa por zona"
        ),
        (
            not missing_markers
            and not invalid_markers
        ),
        (
            "Todos los marcadores "
            "son válidos."
            if (
                not missing_markers
                and not invalid_markers
            )
            else (
                f"Sin marcador: "
                f"{missing_markers}; "
                f"inválidos: "
                f"{invalid_markers}"
            )
        ),
    )

    add_check(
        "ERROR",
        (
            "Crudos: siete variables "
            "originales registradas"
        ),
        not variable_mismatches,
        (
            "Los marcadores registran "
            "las siete variables "
            "solicitadas originalmente."
            if not variable_mismatches
            else (
                "Diferencias: "
                + " | ".join(
                    variable_mismatches
                )
            )
        ),
    )

    add_check(
        "ERROR",
        (
            "Crudos: periodo solicitado "
            "1991-01-01 a 2026-01-01"
        ),
        not date_mismatches,
        (
            "Periodo correcto."
            if not date_mismatches
            else (
                "Zonas con periodo "
                f"distinto: "
                f"{date_mismatches}"
            )
        ),
    )

    add_check(
        "ERROR",
        (
            "Crudos: NetCDF listados "
            "en marcadores existen"
        ),
        not missing_files,
        (
            "Todos los archivos "
            "referenciados existen."
            if not missing_files
            else (
                "Faltan: "
                f"{missing_files}"
            )
        ),
    )


def audit_quality(
    frame: pd.DataFrame,
) -> None:
    needed = [
        "zone_id",
        "rol",
        "daily_rows",
        "monthly_rows",
        "missing_local_days",
        "missing_months",
        "incomplete_months",
        "days_with_precip_hours_not_24",
        "days_with_instant_hours_not_24",
        "missing_t2m_hours",
        "missing_d2m_hours",
        "missing_tp_hours",
        "missing_sp_hours",
        "missing_u10_hours",
        "missing_v10_hours",
    ]

    if not require_columns(
        frame,
        needed,
        "Calidad",
    ):
        return

    add_check(
        "ERROR",
        "Calidad: 15 zonas",
        (
            frame["zone_id"]
            .nunique()
            == EXPECTED_ZONES
        ),
        (
            "Zonas encontradas: "
            f"{frame['zone_id'].nunique()}"
        ),
    )

    roles = (
        frame
        .groupby("rol")["zone_id"]
        .nunique()
        .to_dict()
    )

    roles_ok = (
        roles.get(
            "desarrollo",
            0,
        )
        == EXPECTED_DEVELOPMENT_ZONES
        and roles.get(
            "validacion_espacial",
            0,
        )
        == EXPECTED_HOLDOUT_ZONES
    )

    add_check(
        "ERROR",
        (
            "Calidad: 12 zonas de "
            "desarrollo y 3 holdout"
        ),
        roles_ok,
        f"Distribución: {roles}",
    )

    zero_columns = [
        "missing_local_days",
        "missing_months",
        "incomplete_months",
        "days_with_precip_hours_not_24",
        "days_with_instant_hours_not_24",
        "missing_t2m_hours",
        "missing_d2m_hours",
        "missing_tp_hours",
        "missing_sp_hours",
        "missing_u10_hours",
        "missing_v10_hours",
    ]

    bad = {
        column: int(
            (
                frame[column] != 0
            ).sum()
        )
        for column in zero_columns
        if (
            frame[column] != 0
        ).any()
    }

    add_check(
        "ERROR",
        (
            "Calidad: cero faltantes "
            "temporales y meteorológicos"
        ),
        not bad,
        (
            "Todos los indicadores "
            "son cero."
            if not bad
            else (
                "Incidencias: "
                f"{bad}"
            )
        ),
    )

    daily_ok = bool(
        (
            frame["daily_rows"]
            == EXPECTED_DAYS_PER_ZONE
        ).all()
    )
    monthly_ok = bool(
        (
            frame["monthly_rows"]
            == EXPECTED_MONTHS_PER_ZONE
        ).all()
    )

    add_check(
        "ERROR",
        (
            "Calidad: 12.784 días "
            "y 420 meses por zona"
        ),
        (
            daily_ok
            and monthly_ok
        ),
        (
            "Conteos correctos."
            if (
                daily_ok
                and monthly_ok
            )
            else (
                "Hay conteos "
                "diferentes a "
                "los esperados."
            )
        ),
    )


def audit_daily(
    frame: pd.DataFrame,
) -> None:
    needed = [
        "zone_id",
        "date",
        "precip_total_mm",
        "precip_max_1h_mm",
        "precip_max_3h_mm",
        "precip_max_6h_mm",
        "precip_hours_available",
        "instant_hours_available",
        "temperature_mean_c",
        "temperature_max_c",
        "temperature_min_c",
        "dewpoint_mean_c",
        "relative_humidity_mean_pct",
        "wind_mean_ms",
        "wind_max_ms",
        "surface_pressure_mean_hpa",
    ]

    if not require_columns(
        frame,
        needed,
        "Diario",
    ):
        return

    frame["date"] = pd.to_datetime(
        frame["date"],
        errors="coerce",
    )

    count_by_zone(
        frame,
        EXPECTED_DAYS_PER_ZONE,
        "Diario",
    )

    duplicates = int(
        frame.duplicated(
            [
                "zone_id",
                "date",
            ]
        ).sum()
    )

    add_check(
        "ERROR",
        (
            "Diario: claves "
            "zona-fecha únicas"
        ),
        duplicates == 0,
        f"Duplicados: {duplicates}",
    )

    coverage = (
        frame
        .groupby("zone_id")["date"]
        .agg(["min", "max"])
    )

    coverage_ok = bool(
        (
            coverage["min"]
            == pd.Timestamp(
                "1991-01-01"
            )
        ).all()
        and (
            coverage["max"]
            == pd.Timestamp(
                "2025-12-31"
            )
        ).all()
    )

    add_check(
        "ERROR",
        (
            "Diario: cobertura exacta "
            "1991-01-01 a 2025-12-31"
        ),
        coverage_ok,
        (
            "Cobertura correcta."
            if coverage_ok
            else coverage.to_string()
        ),
    )

    required_values = [
        column
        for column in needed
        if column not in {
            "zone_id",
            "date",
        }
    ]

    nulls = (
        frame[
            required_values
        ]
        .isna()
        .sum()
    )
    bad_nulls = (
        nulls[
            nulls > 0
        ].to_dict()
    )

    add_check(
        "ERROR",
        (
            "Diario: variables "
            "obligatorias sin nulos"
        ),
        not bad_nulls,
        (
            "No hay nulos."
            if not bad_nulls
            else (
                "Nulos: "
                f"{bad_nulls}"
            )
        ),
    )

    precip_columns = [
        "precip_total_mm",
        "precip_max_1h_mm",
        "precip_max_3h_mm",
        "precip_max_6h_mm",
    ]

    negatives = int(
        (
            frame[
                precip_columns
            ]
            < 0
        ).any(
            axis=1
        ).sum()
    )

    add_check(
        "ERROR",
        (
            "Diario: precipitación "
            "no negativa"
        ),
        negatives == 0,
        (
            "Filas negativas: "
            f"{negatives}"
        ),
    )

    tolerance_mm = 1e-6

    hierarchy_bad = int(
        (
            (
                frame[
                    "precip_max_1h_mm"
                ]
                > frame[
                    "precip_max_3h_mm"
                ]
                + tolerance_mm
            )
            | (
                frame[
                    "precip_max_3h_mm"
                ]
                > frame[
                    "precip_max_6h_mm"
                ]
                + tolerance_mm
            )
        ).sum()
    )

    add_check(
        "ADVERTENCIA",
        (
            "Diario: máximo "
            "1h ≤ 3h ≤ 6h"
        ),
        hierarchy_bad == 0,
        (
            "Filas que no cumplen: "
            f"{hierarchy_bad}"
        ),
    )

    temp_bad = int(
        (
            (
                frame[
                    "temperature_min_c"
                ]
                > frame[
                    "temperature_mean_c"
                ]
            )
            | (
                frame[
                    "temperature_mean_c"
                ]
                > frame[
                    "temperature_max_c"
                ]
            )
        ).sum()
    )

    add_check(
        "ERROR",
        (
            "Diario: temperatura "
            "mínima ≤ media ≤ máxima"
        ),
        temp_bad == 0,
        (
            "Filas que no cumplen: "
            f"{temp_bad}"
        ),
    )

    rh_bad = int(
        (
            (
                frame[
                    "relative_humidity_mean_pct"
                ]
                < 0
            )
            | (
                frame[
                    "relative_humidity_mean_pct"
                ]
                > 100
            )
        ).sum()
    )

    add_check(
        "ERROR",
        (
            "Diario: humedad relativa "
            "entre 0 y 100"
        ),
        rh_bad == 0,
        (
            "Filas fuera de rango: "
            f"{rh_bad}"
        ),
    )

    range_bad = {
        "temperatura_fuera_-30_50": int(
            (
                (
                    frame[
                        "temperature_min_c"
                    ]
                    < -30
                )
                | (
                    frame[
                        "temperature_max_c"
                    ]
                    > 50
                )
            ).sum()
        ),
        "presion_fuera_500_1100": int(
            (
                (
                    frame[
                        "surface_pressure_mean_hpa"
                    ]
                    < 500
                )
                | (
                    frame[
                        "surface_pressure_mean_hpa"
                    ]
                    > 1100
                )
            ).sum()
        ),
        "viento_negativo": int(
            (
                (
                    frame[
                        "wind_mean_ms"
                    ]
                    < 0
                )
                | (
                    frame[
                        "wind_max_ms"
                    ]
                    < 0
                )
            ).sum()
        ),
    }

    add_check(
        "ADVERTENCIA",
        (
            "Diario: rangos "
            "físicos generales"
        ),
        all(
            value == 0
            for value
            in range_bad.values()
        ),
        str(range_bad),
    )

    infinite = has_infinite(
        frame
    )

    add_check(
        "ERROR",
        "Diario: sin infinitos",
        not infinite,
        (
            "No hay infinitos."
            if not infinite
            else (
                "Se detectaron "
                "infinitos."
            )
        ),
    )

    processed_without_soil(
        frame,
        "Diario",
    )


def audit_monthly(
    frame: pd.DataFrame,
) -> None:
    needed = [
        "zone_id",
        "period",
        "period_start",
        "expected_days_in_month",
        "days_available",
        "is_complete_month",
        "prcptot_mm",
        "rx1day_mm",
        "rx5day_mm",
        "max_1h_mm",
        "max_3h_mm",
        "max_6h_mm",
        "wet_days",
        "r10mm_days",
        "r20mm_days",
        "sdii_mm_per_wet_day",
        "cwd_days",
        "cdd_days",
        "temperature_mean_c",
        "temperature_max_c",
        "temperature_min_c",
        "dewpoint_mean_c",
        "relative_humidity_mean_pct",
        "wind_mean_ms",
        "wind_max_ms",
        "surface_pressure_mean_hpa",
    ]

    if not require_columns(
        frame,
        needed,
        "Mensual",
    ):
        return

    frame["period_start"] = (
        pd.to_datetime(
            frame["period_start"],
            errors="coerce",
        )
    )

    count_by_zone(
        frame,
        EXPECTED_MONTHS_PER_ZONE,
        "Mensual",
    )

    duplicates = int(
        frame.duplicated(
            [
                "zone_id",
                "period",
            ]
        ).sum()
    )

    add_check(
        "ERROR",
        (
            "Mensual: claves "
            "zona-periodo únicas"
        ),
        duplicates == 0,
        f"Duplicados: {duplicates}",
    )

    coverage = (
        frame
        .groupby("zone_id")[
            "period_start"
        ]
        .agg(["min", "max"])
    )

    coverage_ok = bool(
        (
            coverage["min"]
            == pd.Timestamp(
                "1991-01-01"
            )
        ).all()
        and (
            coverage["max"]
            == pd.Timestamp(
                "2025-12-01"
            )
        ).all()
    )

    add_check(
        "ERROR",
        (
            "Mensual: cobertura exacta "
            "1991-01 a 2025-12"
        ),
        coverage_ok,
        (
            "Cobertura correcta."
            if coverage_ok
            else coverage.to_string()
        ),
    )

    complete_days = (
        frame["days_available"]
        == frame[
            "expected_days_in_month"
        ]
    )

    complete_flag = (
        frame[
            "is_complete_month"
        ]
        .astype(str)
        .str.lower()
        .isin({
            "true",
            "1",
        })
    )

    add_check(
        "ERROR",
        (
            "Mensual: todos los "
            "meses completos"
        ),
        bool(
            complete_days.all()
            and complete_flag.all()
        ),
        (
            f"Días incompletos: "
            f"{(~complete_days).sum()}, "
            f"banderas falsas: "
            f"{(~complete_flag).sum()}"
        ),
    )

    required_values = [
        column
        for column in needed
        if column not in {
            "zone_id",
            "period",
            "period_start",
            "is_complete_month",
        }
    ]

    nulls = (
        frame[
            required_values
        ]
        .isna()
        .sum()
    )
    bad_nulls = (
        nulls[
            nulls > 0
        ].to_dict()
    )

    add_check(
        "ERROR",
        (
            "Mensual: variables "
            "obligatorias sin nulos"
        ),
        not bad_nulls,
        (
            "No hay nulos."
            if not bad_nulls
            else (
                "Nulos: "
                f"{bad_nulls}"
            )
        ),
    )

    logical_bad = {
        "prcptot_menor_rx1day": int(
            (
                frame["prcptot_mm"]
                + 1e-9
                < frame[
                    "rx1day_mm"
                ]
            ).sum()
        ),
        "r20_mayor_r10": int(
            (
                frame["r20mm_days"]
                > frame["r10mm_days"]
            ).sum()
        ),
        "r10_mayor_dias_humedos": int(
            (
                frame["r10mm_days"]
                > frame["wet_days"]
            ).sum()
        ),
        "cwd_mayor_dias_mes": int(
            (
                frame["cwd_days"]
                > frame[
                    "days_available"
                ]
            ).sum()
        ),
        "cdd_mayor_dias_mes": int(
            (
                frame["cdd_days"]
                > frame[
                    "days_available"
                ]
            ).sum()
        ),
        "temperatura_incoherente": int(
            (
                (
                    frame[
                        "temperature_min_c"
                    ]
                    > frame[
                        "temperature_mean_c"
                    ]
                )
                | (
                    frame[
                        "temperature_mean_c"
                    ]
                    > frame[
                        "temperature_max_c"
                    ]
                )
            ).sum()
        ),
    }

    add_check(
        "ERROR",
        (
            "Mensual: "
            "coherencia interna"
        ),
        all(
            value == 0
            for value
            in logical_bad.values()
        ),
        str(logical_bad),
    )

    infinite = has_infinite(
        frame
    )

    add_check(
        "ERROR",
        "Mensual: sin infinitos",
        not infinite,
        (
            "No hay infinitos."
            if not infinite
            else (
                "Se detectaron "
                "infinitos."
            )
        ),
    )

    processed_without_soil(
        frame,
        "Mensual",
    )


def audit_cross_dataset_consistency(
    zones: pd.DataFrame,
    quality: pd.DataFrame,
    daily: pd.DataFrame,
    monthly: pd.DataFrame,
) -> None:
    expected_ids = set(
        zones["zone_id"]
        .astype(str)
    )

    datasets = {
        "calidad": set(
            quality["zone_id"]
            .astype(str)
        ),
        "diario": set(
            daily["zone_id"]
            .astype(str)
        ),
        "mensual": set(
            monthly["zone_id"]
            .astype(str)
        ),
    }

    for name, ids in datasets.items():
        add_check(
            "ERROR",
            (
                f"Consistencia: zonas "
                f"de {name} coinciden "
                "con catálogo"
            ),
            ids == expected_ids,
            (
                "Coincidencia exacta."
                if ids == expected_ids
                else (
                    f"Faltan: "
                    f"{sorted(expected_ids - ids)}; "
                    f"sobran: "
                    f"{sorted(ids - expected_ids)}"
                )
            ),
        )


def main() -> None:
    checks.clear()

    missing_files = [
        str(path)
        for path in FILES.values()
        if not path.exists()
    ]

    if not ZONES_FILE.exists():
        missing_files.append(
            str(ZONES_FILE)
        )

    if missing_files:
        raise FileNotFoundError(
            "Faltan archivos:\n- "
            + "\n- ".join(
                missing_files
            )
        )

    QUALITY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    zones = load_reference_zones()

    quality = pd.read_csv(
        FILES["calidad"],
        encoding="utf-8-sig",
    )
    daily = pd.read_csv(
        FILES["diario"],
        encoding="utf-8-sig",
    )
    monthly = pd.read_csv(
        FILES["mensual"],
        encoding="utf-8-sig",
    )

    audit_raw_downloads(
        zones
    )
    audit_quality(
        quality
    )
    audit_daily(
        daily
    )
    audit_monthly(
        monthly
    )
    audit_cross_dataset_consistency(
        zones,
        quality,
        daily,
        monthly,
    )

    report = pd.DataFrame(
        checks
    )

    report.to_csv(
        AUDIT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    errors = report[
        (
            report["nivel"]
            == "ERROR"
        )
        & (
            report["resultado"]
            != "OK"
        )
    ]

    warnings = report[
        (
            report["nivel"]
            == "ADVERTENCIA"
        )
        & (
            report["resultado"]
            != "OK"
        )
    ]

    print(
        "\nRESUMEN DE AUDITORÍA"
    )
    print(
        "--------------------"
    )
    print(
        f"Verificaciones: "
        f"{len(report)}"
    )
    print(
        f"Errores: "
        f"{len(errors)}"
    )
    print(
        f"Advertencias: "
        f"{len(warnings)}"
    )
    print(
        f"Reporte: "
        f"{AUDIT_FILE.resolve()}"
    )

    if errors.empty:
        print(
            "\nCALIDAD ESTRUCTURAL "
            "APROBADA."
        )
        print(
            "Los datos crudos y los "
            "datasets meteorológicos "
            "procesados están listos "
            "para iniciar el Paso 04."
        )
    else:
        print(
            "\nCALIDAD NO APROBADA. "
            "Corrige estos puntos:"
        )
        print(
            errors[
                [
                    "verificacion",
                    "detalle",
                ]
            ].to_string(
                index=False
            )
        )


if __name__ == "__main__":
    main()
