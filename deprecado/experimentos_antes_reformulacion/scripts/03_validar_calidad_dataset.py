"""
Audita los archivos generados en resultados_completo/.

Ejecutar:
    py 03_validar_calidad_dataset.py

Genera:
    resultados_completo/reporte_auditoria_dataset.csv
    resultados_completo/columnas_recomendadas_modelo.txt
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "resultados_completo"

FILES = {
    "diario": RESULTS_DIR / "indicadores_diarios_todas_zonas.csv",
    "mensual": RESULTS_DIR / "indicadores_mensuales_todas_zonas.csv",
    "calidad": RESULTS_DIR / "reporte_calidad.csv",
    "modelo": RESULTS_DIR / "dataset_modelo_mensual.csv",
}

AUDIT_FILE = RESULTS_DIR / "reporte_auditoria_dataset.csv"
FEATURES_FILE = RESULTS_DIR / "columnas_recomendadas_modelo.txt"

EXPECTED_ZONES = 15
EXPECTED_DAYS_PER_ZONE = 12_784
EXPECTED_MONTHS_PER_ZONE = 420
EXPECTED_MODEL_ROWS_PER_ZONE = 413

EXPECTED_SPLITS = {
    "entrenamiento": 3804,
    "validacion_temporal": 576,
    "prueba_temporal": 576,
    "holdout_historia": 951,
    "holdout_espacial": 288,
}

VALID_LABELS = {"Baja", "Media", "Alta"}

checks: list[dict[str, object]] = []


def add_check(
    level: str,
    name: str,
    ok: bool,
    detail: str,
) -> None:
    checks.append({
        "nivel": level,
        "verificacion": name,
        "resultado": "OK" if ok else level,
        "detalle": detail,
    })


def require_columns(
    frame: pd.DataFrame,
    columns: list[str],
    dataset_name: str,
) -> bool:
    missing = sorted(set(columns).difference(frame.columns))
    add_check(
        "ERROR",
        f"{dataset_name}: columnas obligatorias",
        not missing,
        "Todas presentes." if not missing else f"Faltan: {missing}",
    )
    return not missing


def count_by_zone(
    frame: pd.DataFrame,
    expected: int,
    dataset_name: str,
) -> None:
    counts = frame.groupby("zone_id").size()
    bad = counts[counts != expected]
    add_check(
        "ERROR",
        f"{dataset_name}: filas por zona",
        bad.empty,
        (
            f"Todas las zonas tienen {expected} filas."
            if bad.empty
            else f"Conteos incorrectos: {bad.to_dict()}"
        ),
    )


def has_infinite(frame: pd.DataFrame) -> bool:
    numeric = frame.select_dtypes(include=[np.number])
    return bool(np.isinf(numeric.to_numpy()).any())


def no_soil_columns(frame: pd.DataFrame, dataset_name: str) -> None:
    forbidden = [
        column
        for column in frame.columns
        if "swvl1" in column.lower()
        or "soil_water" in column.lower()
    ]
    add_check(
        "ERROR",
        f"{dataset_name}: humedad del suelo eliminada",
        not forbidden,
        (
            "No existen columnas de humedad del suelo."
            if not forbidden
            else f"Aún aparecen: {forbidden}"
        ),
    )


def audit_quality(frame: pd.DataFrame) -> None:
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
    if not require_columns(frame, needed, "Calidad"):
        return

    add_check(
        "ERROR",
        "Calidad: 15 zonas",
        frame["zone_id"].nunique() == EXPECTED_ZONES,
        f"Zonas encontradas: {frame['zone_id'].nunique()}",
    )

    roles = frame.groupby("rol")["zone_id"].nunique().to_dict()
    roles_ok = (
        roles.get("desarrollo", 0) == 12
        and roles.get("validacion_espacial", 0) == 3
    )
    add_check(
        "ERROR",
        "Calidad: 12 zonas de desarrollo y 3 holdout",
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
        column: int((frame[column] != 0).sum())
        for column in zero_columns
        if (frame[column] != 0).any()
    }
    add_check(
        "ERROR",
        "Calidad: cero faltantes temporales y meteorológicos",
        not bad,
        "Todos los indicadores son cero."
        if not bad
        else f"Incidencias: {bad}",
    )

    daily_ok = bool((frame["daily_rows"] == 12_784).all())
    monthly_ok = bool((frame["monthly_rows"] == 420).all())
    add_check(
        "ERROR",
        "Calidad: 12.784 días y 420 meses por zona",
        daily_ok and monthly_ok,
        (
            "Conteos correctos."
            if daily_ok and monthly_ok
            else "Hay conteos diferentes a los esperados."
        ),
    )

    no_soil_columns(frame, "Calidad")


def audit_daily(frame: pd.DataFrame) -> None:
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
    if not require_columns(frame, needed, "Diario"):
        return

    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    count_by_zone(frame, EXPECTED_DAYS_PER_ZONE, "Diario")

    duplicates = int(frame.duplicated(["zone_id", "date"]).sum())
    add_check(
        "ERROR",
        "Diario: claves zona-fecha únicas",
        duplicates == 0,
        f"Duplicados: {duplicates}",
    )

    coverage = frame.groupby("zone_id")["date"].agg(["min", "max"])
    coverage_ok = bool(
        (coverage["min"] == pd.Timestamp("1991-01-01")).all()
        and (coverage["max"] == pd.Timestamp("2025-12-31")).all()
    )
    add_check(
        "ERROR",
        "Diario: cobertura exacta 1991-01-01 a 2025-12-31",
        coverage_ok,
        "Cobertura correcta."
        if coverage_ok
        else coverage.to_string(),
    )

    nullable_exceptions = {"zone_id", "date"}
    required_values = [
        column for column in needed
        if column not in nullable_exceptions
    ]
    nulls = frame[required_values].isna().sum()
    bad_nulls = nulls[nulls > 0].to_dict()
    add_check(
        "ERROR",
        "Diario: variables obligatorias sin nulos",
        not bad_nulls,
        "No hay nulos."
        if not bad_nulls
        else f"Nulos: {bad_nulls}",
    )

    precip = [
        "precip_total_mm",
        "precip_max_1h_mm",
        "precip_max_3h_mm",
        "precip_max_6h_mm",
    ]
    negatives = int((frame[precip] < 0).any(axis=1).sum())
    add_check(
        "ERROR",
        "Diario: precipitación no negativa",
        negatives == 0,
        f"Filas negativas: {negatives}",
    )

    TOLERANCIA_PRECIP_MM = 1e-6

    hierarchy_bad = int(
        (
            (
                frame["precip_max_1h_mm"]
                > frame["precip_max_3h_mm"] + TOLERANCIA_PRECIP_MM
            )
            | (
                frame["precip_max_3h_mm"]
                > frame["precip_max_6h_mm"] + TOLERANCIA_PRECIP_MM
            )
        ).sum()
    )
    add_check(
        "ADVERTENCIA",
        "Diario: máximo 1h ≤ 3h ≤ 6h",
        hierarchy_bad == 0,
        f"Filas que no cumplen: {hierarchy_bad}",
    )

    temp_bad = int(
        (
            (frame["temperature_min_c"] > frame["temperature_mean_c"])
            | (frame["temperature_mean_c"] > frame["temperature_max_c"])
        ).sum()
    )
    add_check(
        "ERROR",
        "Diario: temperatura mínima ≤ media ≤ máxima",
        temp_bad == 0,
        f"Filas que no cumplen: {temp_bad}",
    )

    rh_bad = int(
        (
            (frame["relative_humidity_mean_pct"] < 0)
            | (frame["relative_humidity_mean_pct"] > 100)
        ).sum()
    )
    add_check(
        "ERROR",
        "Diario: humedad relativa entre 0 y 100",
        rh_bad == 0,
        f"Filas fuera de rango: {rh_bad}",
    )

    range_bad = {
        "temperatura_fuera_-30_50": int(
            (
                (frame["temperature_min_c"] < -30)
                | (frame["temperature_max_c"] > 50)
            ).sum()
        ),
        "presion_fuera_500_1100": int(
            (
                (frame["surface_pressure_mean_hpa"] < 500)
                | (frame["surface_pressure_mean_hpa"] > 1100)
            ).sum()
        ),
        "viento_negativo": int(
            (
                (frame["wind_mean_ms"] < 0)
                | (frame["wind_max_ms"] < 0)
            ).sum()
        ),
    }
    add_check(
        "ADVERTENCIA",
        "Diario: rangos físicos generales",
        all(value == 0 for value in range_bad.values()),
        str(range_bad),
    )

    add_check(
        "ERROR",
        "Diario: sin infinitos",
        not has_infinite(frame),
        "No hay infinitos."
        if not has_infinite(frame)
        else "Se detectaron infinitos.",
    )

    no_soil_columns(frame, "Diario")


def audit_monthly(frame: pd.DataFrame) -> None:
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
    if not require_columns(frame, needed, "Mensual"):
        return

    count_by_zone(frame, EXPECTED_MONTHS_PER_ZONE, "Mensual")

    duplicates = int(frame.duplicated(["zone_id", "period"]).sum())
    add_check(
        "ERROR",
        "Mensual: claves zona-periodo únicas",
        duplicates == 0,
        f"Duplicados: {duplicates}",
    )

    complete_days = (
        frame["days_available"]
        == frame["expected_days_in_month"]
    )
    complete_flag = (
        frame["is_complete_month"]
        .astype(str)
        .str.lower()
        .isin({"true", "1"})
    )
    add_check(
        "ERROR",
        "Mensual: todos los meses completos",
        bool(complete_days.all() and complete_flag.all()),
        (
            f"Días incompletos: {(~complete_days).sum()}, "
            f"banderas falsas: {(~complete_flag).sum()}"
        ),
    )

    required_values = [
        column for column in needed
        if column not in {
            "zone_id",
            "period",
            "period_start",
            "is_complete_month",
        }
    ]
    nulls = frame[required_values].isna().sum()
    bad_nulls = nulls[nulls > 0].to_dict()
    add_check(
        "ERROR",
        "Mensual: variables obligatorias sin nulos",
        not bad_nulls,
        "No hay nulos."
        if not bad_nulls
        else f"Nulos: {bad_nulls}",
    )

    logical_bad = {
        "prcptot_menor_rx1day": int(
            (frame["prcptot_mm"] + 1e-9 < frame["rx1day_mm"]).sum()
        ),
        "r20_mayor_r10": int(
            (frame["r20mm_days"] > frame["r10mm_days"]).sum()
        ),
        "r10_mayor_dias_humedos": int(
            (frame["r10mm_days"] > frame["wet_days"]).sum()
        ),
        "cwd_mayor_dias_mes": int(
            (frame["cwd_days"] > frame["days_available"]).sum()
        ),
        "cdd_mayor_dias_mes": int(
            (frame["cdd_days"] > frame["days_available"]).sum()
        ),
        "temperatura_incoherente": int(
            (
                (frame["temperature_min_c"] > frame["temperature_mean_c"])
                | (
                    frame["temperature_mean_c"]
                    > frame["temperature_max_c"]
                )
            ).sum()
        ),
    }
    add_check(
        "ERROR",
        "Mensual: coherencia interna",
        all(value == 0 for value in logical_bad.values()),
        str(logical_bad),
    )

    no_soil_columns(frame, "Mensual")


def recommended_features(frame: pd.DataFrame) -> list[str]:
    lag_pattern = re.compile(r"_lag[0-6]$")
    lag_columns = [
        column
        for column in frame.columns
        if lag_pattern.search(column)
    ]
    context = [
        column
        for column in (
            "month_sin",
            "month_cos",
            "latitud_solicitada",
            "longitud_solicitada",
        )
        if column in frame.columns
    ]
    return sorted(lag_columns) + context


def audit_model(frame: pd.DataFrame) -> None:
    needed = [
        "zone_id",
        "period_start",
        "target_period_start",
        "target_amenaza",
        "target_rx5day_mm",
        "split",
        "rol",
        "baseline_count",
        "rx5_q33",
        "rx5_q66",
    ]
    if not require_columns(frame, needed, "Modelo"):
        return

    count_by_zone(
        frame,
        EXPECTED_MODEL_ROWS_PER_ZONE,
        "Modelo",
    )

    duplicates = int(
        frame.duplicated(["zone_id", "period_start"]).sum()
    )
    add_check(
        "ERROR",
        "Modelo: claves zona-periodo únicas",
        duplicates == 0,
        f"Duplicados: {duplicates}",
    )

    labels = set(frame["target_amenaza"].dropna().unique())
    add_check(
        "ERROR",
        "Modelo: etiquetas Baja, Media y Alta",
        labels == VALID_LABELS,
        f"Etiquetas encontradas: {sorted(labels)}",
    )

    target_nulls = int(frame["target_amenaza"].isna().sum())
    add_check(
        "ERROR",
        "Modelo: etiqueta sin nulos",
        target_nulls == 0,
        f"Nulos: {target_nulls}",
    )

    threshold_bad = int(
        (
            frame["rx5_q33"].isna()
            | frame["rx5_q66"].isna()
            | (frame["rx5_q33"] > frame["rx5_q66"])
            | (frame["baseline_count"] < 10)
        ).sum()
    )
    add_check(
        "ERROR",
        "Modelo: terciles históricos válidos",
        threshold_bad == 0,
        f"Filas inválidas: {threshold_bad}",
    )

    split_counts = frame["split"].value_counts().to_dict()
    add_check(
        "ERROR",
        "Modelo: particiones temporales y espaciales",
        split_counts == EXPECTED_SPLITS,
        f"Conteos: {split_counts}",
    )

    development_in_holdout = int(
        (
            (frame["rol"] == "desarrollo")
            & frame["split"].isin(
                {"holdout_historia", "holdout_espacial"}
            )
        ).sum()
    )
    holdout_in_development = int(
        (
            (frame["rol"] == "validacion_espacial")
            & frame["split"].isin(
                {
                    "entrenamiento",
                    "validacion_temporal",
                    "prueba_temporal",
                }
            )
        ).sum()
    )
    add_check(
        "ERROR",
        "Modelo: holdout espacial separado",
        (
            development_in_holdout == 0
            and holdout_in_development == 0
        ),
        (
            f"Desarrollo en holdout: {development_in_holdout}; "
            f"holdout en desarrollo: {holdout_in_development}"
        ),
    )

    all_null = frame.columns[frame.isna().all()].tolist()
    add_check(
        "ERROR",
        "Modelo: sin columnas totalmente nulas",
        not all_null,
        "No hay columnas totalmente nulas."
        if not all_null
        else f"Columnas: {all_null}",
    )

    no_soil_columns(frame, "Modelo")

    features = recommended_features(frame)
    leakage = [
        column for column in features
        if column.startswith("target_")
    ]
    add_check(
        "ERROR",
        "Modelo: variables recomendadas sin fuga del objetivo",
        not leakage,
        (
            f"Variables recomendadas: {len(features)}; "
            f"fugas: {leakage}"
        ),
    )

    FEATURES_FILE.write_text(
        "\n".join(features) + "\n",
        encoding="utf-8",
    )

    distributions = (
        frame.groupby("split")["target_amenaza"]
        .value_counts(normalize=True)
        .rename("proporcion")
        .reset_index()
    )
    minority = distributions[
        distributions["proporcion"] < 0.10
    ]
    add_check(
        "ADVERTENCIA",
        "Modelo: ninguna clase menor al 10% por partición",
        minority.empty,
        "Distribución aceptable."
        if minority.empty
        else minority.to_string(index=False),
    )

    add_check(
        "ERROR",
        "Modelo: sin infinitos",
        not has_infinite(frame),
        "No hay infinitos."
        if not has_infinite(frame)
        else "Se detectaron infinitos.",
    )


def main() -> None:
    missing_files = [
        str(path)
        for path in FILES.values()
        if not path.exists()
    ]
    if missing_files:
        raise FileNotFoundError(
            "Faltan archivos:\n- " + "\n- ".join(missing_files)
        )

    quality = pd.read_csv(FILES["calidad"], encoding="utf-8-sig")
    daily = pd.read_csv(FILES["diario"], encoding="utf-8-sig")
    monthly = pd.read_csv(FILES["mensual"], encoding="utf-8-sig")
    model = pd.read_csv(FILES["modelo"], encoding="utf-8-sig")

    audit_quality(quality)
    audit_daily(daily)
    audit_monthly(monthly)
    audit_model(model)

    report = pd.DataFrame(checks)
    report.to_csv(
        AUDIT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    errors = report[
        (report["nivel"] == "ERROR")
        & (report["resultado"] != "OK")
    ]
    warnings = report[
        (report["nivel"] == "ADVERTENCIA")
        & (report["resultado"] != "OK")
    ]

    print("\nRESUMEN DE AUDITORÍA")
    print("--------------------")
    print(f"Verificaciones: {len(report)}")
    print(f"Errores: {len(errors)}")
    print(f"Advertencias: {len(warnings)}")
    print(f"Reporte: {AUDIT_FILE.resolve()}")
    print(f"Variables: {FEATURES_FILE.resolve()}")

    if errors.empty:
        print(
            "\nCALIDAD ESTRUCTURAL APROBADA. "
            "Puedes continuar con análisis exploratorio y modelado."
        )
    else:
        print(
            "\nCALIDAD NO APROBADA. Corrige estos puntos:"
        )
        print(
            errors[["verificacion", "detalle"]]
            .to_string(index=False)
        )


if __name__ == "__main__":
    main()
