"""
Construye los indicadores meteorológicos derivados de las series horarias
puntuales de ERA5-Land.

RESPONSABILIDAD DE ESTE PASO
----------------------------
1. Leer los NetCDF oficiales de datos/crudos/era5_land/<zona>/.
2. Convertir las series horarias a indicadores diarios por zona.
3. Agregar los indicadores diarios a indicadores mensuales por zona.
4. Generar un reporte de calidad del procesamiento.

Este paso NO:
- crea el target de Machine Learning;
- crea rezagos/lags;
- asigna particiones train/validation/test;
- selecciona características;
- entrena modelos.

La descarga original incluye siete variables del CDS. Este procesamiento
mantiene la misma lógica histórica del proyecto y deriva indicadores a partir
de seis variables:
t2m, d2m, tp, sp, u10 y v10.

La humedad volumétrica del suelo descargada permanece conservada en los
NetCDF crudos, pero no se propaga a los datasets diario/mensual actuales.

SALIDAS
-------
datos/procesados/indicadores_diarios_todas_zonas.csv
datos/procesados/indicadores_mensuales_todas_zonas.csv
datos/calidad/reporte_calidad.csv
"""

from __future__ import annotations

import calendar
from datetime import timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr


BASE_DIR = Path(__file__).resolve().parent.parent
ZONES_FILE = BASE_DIR / "zonas_era5_ecuador.csv"

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

TARGET_START_DATE = pd.Timestamp("1991-01-01")
TARGET_END_DATE = pd.Timestamp("2025-12-31")

# Ecuador continental: desplazamiento fijo. Evita cambios históricos
# de horario civil al construir días climatológicos de 24 horas.
LOCAL_TIMEZONE = timezone(
    timedelta(hours=-5)
)

# La marca temporal de precipitación corresponde al final del intervalo.
PRECIP_INTERVAL_SHIFT_HOURS = -1

WET_DAY_THRESHOLD_MM = 1.0
HEAVY_DAY_THRESHOLD_MM = 10.0
VERY_HEAVY_DAY_THRESHOLD_MM = 20.0

ALIASES = {
    "t2m": "t2m",
    "2m_temperature": "t2m",
    "d2m": "d2m",
    "2m_dewpoint_temperature": "d2m",
    "tp": "tp",
    "total_precipitation": "tp",
    "sp": "sp",
    "surface_pressure": "sp",
    "u10": "u10",
    "10m_u_component_of_wind": "u10",
    "v10": "v10",
    "10m_v_component_of_wind": "v10",
}

EXPECTED_VARIABLES = [
    "t2m",
    "d2m",
    "tp",
    "sp",
    "u10",
    "v10",
]


def read_zones() -> pd.DataFrame:
    if not ZONES_FILE.exists():
        raise FileNotFoundError(
            f"No se encontró {ZONES_FILE}"
        )

    zones = pd.read_csv(
        ZONES_FILE,
        encoding="utf-8-sig",
    )

    required = {
        "zone_id",
        "ciudad",
        "provincia",
        "region",
        "latitud",
        "longitud",
        "rol",
    }

    missing = required.difference(
        zones.columns
    )

    if missing:
        raise ValueError(
            f"Faltan columnas en "
            f"{ZONES_FILE.name}: "
            f"{sorted(missing)}"
        )

    return zones


def find_time_name(ds: xr.Dataset) -> str:
    for candidate in (
        "time",
        "valid_time",
        "date",
    ):
        if (
            candidate in ds.coords
            or candidate in ds.dims
        ):
            return candidate

    raise KeyError(
        "No se encontró coordenada temporal. "
        f"Disponibles: {list(ds.coords)}"
    )


def frame_from_netcdf(
    path: Path,
) -> pd.DataFrame:
    with xr.open_dataset(path) as ds:
        time_name = find_time_name(ds)

        selected: dict[
            str,
            xr.DataArray,
        ] = {}

        for original_name in ds.data_vars:
            standard_name = ALIASES.get(
                original_name
            )

            if standard_name:
                selected[
                    standard_name
                ] = ds[original_name]

        if not selected:
            return pd.DataFrame()

        reduced = xr.Dataset(selected)
        frame = (
            reduced
            .to_dataframe()
            .reset_index()
        )

        if time_name != "time":
            frame = frame.rename(
                columns={
                    time_name: "time"
                }
            )

        keep = ["time"] + [
            column
            for column in selected
            if column in frame.columns
        ]

        frame = frame[keep]
        frame["time"] = pd.to_datetime(
            frame["time"],
            utc=True,
        )

        # Algunas conversiones pueden
        # repetir dimensiones escalares.
        frame = (
            frame
            .groupby(
                "time",
                as_index=False,
            )
            .first()
        )

        return frame


def load_zone_hourly(
    zone_id: str,
) -> pd.DataFrame:
    zone_dir = RAW_DIR / zone_id
    paths = sorted(
        zone_dir.rglob("*.nc")
    )

    if not paths:
        raise FileNotFoundError(
            f"No se encontraron NetCDF "
            f"para {zone_id} en "
            f"{zone_dir}"
        )

    frames: list[
        pd.DataFrame
    ] = []

    for path in paths:
        frame = frame_from_netcdf(path)

        if not frame.empty:
            frames.append(frame)

    if not frames:
        raise RuntimeError(
            f"Los NetCDF de {zone_id} "
            "no contienen variables "
            "reconocidas."
        )

    merged = frames[0]

    for frame in frames[1:]:
        duplicated = [
            column
            for column in frame.columns
            if (
                column != "time"
                and column
                in merged.columns
            )
        ]

        frame = frame.drop(
            columns=duplicated
        )

        merged = merged.merge(
            frame,
            on="time",
            how="outer",
        )

    merged = (
        merged
        .sort_values("time")
        .drop_duplicates(
            subset=["time"],
            keep="last",
        )
        .set_index("time")
    )

    full_index = pd.date_range(
        merged.index.min(),
        merged.index.max(),
        freq="h",
        tz="UTC",
    )

    merged = merged.reindex(
        full_index
    )
    merged.index.name = "time"

    return merged


def relative_humidity_from_temp_dewpoint(
    temperature_c: pd.Series,
    dewpoint_c: pd.Series,
) -> pd.Series:
    numerator = np.exp(
        (17.625 * dewpoint_c)
        / (243.04 + dewpoint_c)
    )
    denominator = np.exp(
        (17.625 * temperature_c)
        / (243.04 + temperature_c)
    )

    return (
        100.0
        * numerator
        / denominator
    ).clip(
        0.0,
        100.0,
    )


def longest_run(
    mask: pd.Series,
) -> int:
    if mask.empty:
        return 0

    longest = 0
    current = 0

    for value in (
        mask
        .fillna(False)
        .astype(bool)
        .to_numpy()
    ):
        if value:
            current += 1
            longest = max(
                longest,
                current,
            )
        else:
            current = 0

    return int(longest)


def hourly_to_daily(
    hourly: pd.DataFrame,
) -> pd.DataFrame:
    frame = hourly.copy()

    if "tp" not in frame.columns:
        raise KeyError(
            "No se encontró "
            "total_precipitation/tp. "
            "La precipitación es "
            "obligatoria."
        )

    if "t2m" in frame:
        frame[
            "temperature_c"
        ] = frame["t2m"] - 273.15

    if "d2m" in frame:
        frame[
            "dewpoint_c"
        ] = frame["d2m"] - 273.15

    if {
        "temperature_c",
        "dewpoint_c",
    }.issubset(frame.columns):
        frame[
            "relative_humidity_pct"
        ] = (
            relative_humidity_from_temp_dewpoint(
                frame["temperature_c"],
                frame["dewpoint_c"],
            )
        )

    if {
        "u10",
        "v10",
    }.issubset(frame.columns):
        frame[
            "wind_speed_ms"
        ] = np.sqrt(
            frame["u10"] ** 2
            + frame["v10"] ** 2
        )

    if "sp" in frame:
        frame[
            "surface_pressure_hpa"
        ] = frame["sp"] / 100.0

    frame["precip_mm"] = (
        frame["tp"] * 1000.0
    )

    tiny_negative = (
        frame["precip_mm"]
        .between(
            -1e-4,
            0.0,
            inclusive="both",
        )
    )

    frame.loc[
        tiny_negative,
        "precip_mm",
    ] = 0.0

    frame.loc[
        frame["precip_mm"] < 0.0,
        "precip_mm",
    ] = np.nan

    frame["precip_3h_mm"] = (
        frame["precip_mm"]
        .rolling(
            3,
            min_periods=3,
        )
        .sum()
    )

    frame["precip_6h_mm"] = (
        frame["precip_mm"]
        .rolling(
            6,
            min_periods=6,
        )
        .sum()
    )

    instant_local_date = (
        frame.index
        .tz_convert(
            LOCAL_TIMEZONE
        )
        .date
    )

    precip_local_date = (
        frame.index
        + pd.Timedelta(
            hours=PRECIP_INTERVAL_SHIFT_HOURS
        )
    ).tz_convert(
        LOCAL_TIMEZONE
    ).date

    precip_daily = (
        frame.assign(
            local_date=precip_local_date
        )
        .groupby("local_date")
        .agg(
            precip_total_mm=(
                "precip_mm",
                "sum",
            ),
            precip_max_1h_mm=(
                "precip_mm",
                "max",
            ),
            precip_max_3h_mm=(
                "precip_3h_mm",
                "max",
            ),
            precip_max_6h_mm=(
                "precip_6h_mm",
                "max",
            ),
            precip_hours_available=(
                "precip_mm",
                "count",
            ),
        )
    )

    instant_aggregations: dict[
        str,
        tuple[str, str],
    ] = (
        {
            "instant_hours_available": (
                "t2m",
                "count",
            )
        }
        if "t2m" in frame
        else {}
    )

    if "temperature_c" in frame:
        instant_aggregations.update({
            "temperature_mean_c": (
                "temperature_c",
                "mean",
            ),
            "temperature_max_c": (
                "temperature_c",
                "max",
            ),
            "temperature_min_c": (
                "temperature_c",
                "min",
            ),
        })

    if "dewpoint_c" in frame:
        instant_aggregations[
            "dewpoint_mean_c"
        ] = (
            "dewpoint_c",
            "mean",
        )

    if (
        "relative_humidity_pct"
        in frame
    ):
        instant_aggregations[
            "relative_humidity_mean_pct"
        ] = (
            "relative_humidity_pct",
            "mean",
        )

    if "wind_speed_ms" in frame:
        instant_aggregations.update({
            "wind_mean_ms": (
                "wind_speed_ms",
                "mean",
            ),
            "wind_max_ms": (
                "wind_speed_ms",
                "max",
            ),
        })

    if (
        "surface_pressure_hpa"
        in frame
    ):
        instant_aggregations[
            "surface_pressure_mean_hpa"
        ] = (
            "surface_pressure_hpa",
            "mean",
        )

    if instant_aggregations:
        instant_daily = (
            frame.assign(
                local_date=instant_local_date
            )
            .groupby("local_date")
            .agg(
                **instant_aggregations
            )
        )

        daily = precip_daily.join(
            instant_daily,
            how="outer",
        )
    else:
        daily = precip_daily

    daily.index = pd.to_datetime(
        daily.index
    )
    daily.index.name = "date"
    daily = daily.sort_index()

    daily = daily.loc[
        (
            daily.index
            >= TARGET_START_DATE
        )
        & (
            daily.index
            <= TARGET_END_DATE
        )
    ].copy()

    daily["precip_5day_mm"] = (
        daily["precip_total_mm"]
        .rolling(
            5,
            min_periods=5,
        )
        .sum()
    )

    return daily


def expected_days_for_period(
    period: pd.Period,
) -> int:
    return calendar.monthrange(
        period.year,
        period.month,
    )[1]


def daily_to_monthly(
    daily: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[
        dict[str, object]
    ] = []

    for period, group in daily.groupby(
        daily.index.to_period("M")
    ):
        wet_mask = (
            group["precip_total_mm"]
            >= WET_DAY_THRESHOLD_MM
        )

        dry_mask = (
            group["precip_total_mm"]
            < WET_DAY_THRESHOLD_MM
        ).where(
            group[
                "precip_total_mm"
            ].notna(),
            False,
        )

        total = (
            group["precip_total_mm"]
            .sum(min_count=1)
        )
        wet_days = int(
            wet_mask.sum()
        )
        expected_days = (
            expected_days_for_period(
                period
            )
        )
        days_available = int(
            group[
                "precip_total_mm"
            ].count()
        )

        row: dict[str, object] = {
            "period": str(period),
            "period_start": (
                period.to_timestamp()
            ),
            "year": int(period.year),
            "month": int(period.month),
            "expected_days_in_month": (
                expected_days
            ),
            "days_available": (
                days_available
            ),
            "is_complete_month": bool(
                days_available
                == expected_days
            ),
            "prcptot_mm": total,
            "rx1day_mm": (
                group[
                    "precip_total_mm"
                ].max()
            ),
            "rx5day_mm": (
                group[
                    "precip_5day_mm"
                ].max()
            ),
            "max_1h_mm": (
                group[
                    "precip_max_1h_mm"
                ].max()
            ),
            "max_3h_mm": (
                group[
                    "precip_max_3h_mm"
                ].max()
            ),
            "max_6h_mm": (
                group[
                    "precip_max_6h_mm"
                ].max()
            ),
            "wet_days": wet_days,
            "r10mm_days": int(
                (
                    group[
                        "precip_total_mm"
                    ]
                    >= HEAVY_DAY_THRESHOLD_MM
                ).sum()
            ),
            "r20mm_days": int(
                (
                    group[
                        "precip_total_mm"
                    ]
                    >= VERY_HEAVY_DAY_THRESHOLD_MM
                ).sum()
            ),
            "sdii_mm_per_wet_day": (
                total / wet_days
                if wet_days > 0
                else 0.0
            ),
            "cwd_days": longest_run(
                wet_mask.where(
                    group[
                        "precip_total_mm"
                    ].notna(),
                    False,
                )
            ),
            "cdd_days": longest_run(
                dry_mask
            ),
            "days_with_incomplete_precip_hours": int(
                (
                    group[
                        "precip_hours_available"
                    ]
                    != 24
                ).sum()
            ),
        }

        if (
            "instant_hours_available"
            in group
        ):
            row[
                "days_with_incomplete_instant_hours"
            ] = int(
                (
                    group[
                        "instant_hours_available"
                    ]
                    != 24
                ).sum()
            )
        else:
            row[
                "days_with_incomplete_instant_hours"
            ] = np.nan

        optional_specs = {
            "temperature_mean_c": (
                "temperature_mean_c",
                "mean",
            ),
            "temperature_max_c": (
                "temperature_max_c",
                "max",
            ),
            "temperature_min_c": (
                "temperature_min_c",
                "min",
            ),
            "dewpoint_mean_c": (
                "dewpoint_mean_c",
                "mean",
            ),
            "relative_humidity_mean_pct": (
                "relative_humidity_mean_pct",
                "mean",
            ),
            "wind_mean_ms": (
                "wind_mean_ms",
                "mean",
            ),
            "wind_max_ms": (
                "wind_max_ms",
                "max",
            ),
            "surface_pressure_mean_hpa": (
                "surface_pressure_mean_hpa",
                "mean",
            ),
        }

        for (
            output_name,
            (input_name, operation),
        ) in optional_specs.items():
            if input_name not in group:
                row[
                    output_name
                ] = np.nan
            elif operation == "mean":
                row[
                    output_name
                ] = group[
                    input_name
                ].mean()
            elif operation == "max":
                row[
                    output_name
                ] = group[
                    input_name
                ].max()
            elif operation == "min":
                row[
                    output_name
                ] = group[
                    input_name
                ].min()

        rows.append(row)

    monthly = (
        pd.DataFrame(rows)
        .sort_values(
            "period_start"
        )
    )

    # Se conservan estas columnas porque formaron parte
    # del dataset mensual generado originalmente.
    # Son transformaciones determinísticas del calendario,
    # no aprendidas a partir del target.
    monthly["month_sin"] = np.sin(
        2
        * np.pi
        * monthly["month"]
        / 12
    )
    monthly["month_cos"] = np.cos(
        2
        * np.pi
        * monthly["month"]
        / 12
    )

    return monthly


def count_available(
    hourly: pd.DataFrame,
    variable: str,
) -> int:
    if variable not in hourly:
        return 0

    return int(
        hourly[variable].count()
    )


def build_validation_summary(
    zone: pd.Series,
    hourly: pd.DataFrame,
    daily: pd.DataFrame,
    monthly: pd.DataFrame,
) -> dict[str, object]:
    expected_days = (
        TARGET_END_DATE
        - TARGET_START_DATE
    ).days + 1

    expected_months = (
        (
            TARGET_END_DATE.year
            - TARGET_START_DATE.year
        )
        * 12
        + TARGET_END_DATE.month
        - TARGET_START_DATE.month
        + 1
    )

    summary: dict[
        str,
        object,
    ] = {
        "zone_id": zone["zone_id"],
        "ciudad": zone["ciudad"],
        "rol": zone["rol"],
        "first_hour_utc_downloaded": (
            hourly.index.min()
        ),
        "last_hour_utc_downloaded": (
            hourly.index.max()
        ),
        "hourly_rows_downloaded": (
            len(hourly)
        ),
        "expected_local_days": (
            expected_days
        ),
        "daily_rows": len(daily),
        "missing_local_days": (
            expected_days
            - len(daily)
        ),
        "expected_months": (
            expected_months
        ),
        "monthly_rows": (
            len(monthly)
        ),
        "missing_months": (
            expected_months
            - len(monthly)
        ),
        "incomplete_months": int(
            (
                ~monthly[
                    "is_complete_month"
                ]
            ).sum()
        ),
        "days_with_precip_hours_not_24": int(
            (
                daily[
                    "precip_hours_available"
                ]
                != 24
            ).sum()
        ),
    }

    if (
        "instant_hours_available"
        in daily
    ):
        summary[
            "days_with_instant_hours_not_24"
        ] = int(
            (
                daily[
                    "instant_hours_available"
                ]
                != 24
            ).sum()
        )
    else:
        summary[
            "days_with_instant_hours_not_24"
        ] = np.nan

    for variable in EXPECTED_VARIABLES:
        available = count_available(
            hourly,
            variable,
        )

        summary[
            f"available_{variable}_hours"
        ] = available
        summary[
            f"missing_{variable}_hours"
        ] = (
            len(hourly)
            - available
        )

    return summary


def validate_global_result(
    validation: pd.DataFrame,
) -> None:
    problems: list[str] = []

    if (
        validation[
            "missing_local_days"
        ]
        != 0
    ).any():
        bad = validation.loc[
            validation[
                "missing_local_days"
            ]
            != 0,
            [
                "zone_id",
                "missing_local_days",
            ],
        ]

        problems.append(
            "Zonas con días locales "
            "faltantes:\n"
            + bad.to_string(
                index=False
            )
        )

    if (
        validation[
            "missing_months"
        ]
        != 0
    ).any():
        bad = validation.loc[
            validation[
                "missing_months"
            ]
            != 0,
            [
                "zone_id",
                "missing_months",
            ],
        ]

        problems.append(
            "Zonas con meses "
            "faltantes:\n"
            + bad.to_string(
                index=False
            )
        )

    if (
        validation[
            "incomplete_months"
        ]
        != 0
    ).any():
        bad = validation.loc[
            validation[
                "incomplete_months"
            ]
            != 0,
            [
                "zone_id",
                "incomplete_months",
            ],
        ]

        problems.append(
            "Zonas con meses "
            "incompletos:\n"
            + bad.to_string(
                index=False
            )
        )

    if (
        validation[
            "days_with_precip_hours_not_24"
        ]
        != 0
    ).any():
        bad = validation.loc[
            validation[
                "days_with_precip_hours_not_24"
            ]
            != 0,
            [
                "zone_id",
                "days_with_precip_hours_not_24",
            ],
        ]

        problems.append(
            "Zonas con días que no "
            "tienen 24 horas de "
            "precipitación:\n"
            + bad.to_string(
                index=False
            )
        )

    if problems:
        print(
            "\nADVERTENCIAS DE CALIDAD:"
        )

        for problem in problems:
            print(
                "\n" + problem
            )
    else:
        print(
            "\nValidación temporal correcta: "
            "cada zona tiene 12.784 días "
            "y 420 meses locales completos."
        )


def main() -> None:
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"No existe {RAW_DIR}. "
            "Ejecuta primero "
            "01_descargar_era5_land_horario.py."
        )

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    QUALITY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    zones = read_zones()

    all_daily: list[
        pd.DataFrame
    ] = []
    all_monthly: list[
        pd.DataFrame
    ] = []
    validation_rows: list[
        dict[str, object]
    ] = []

    for _, zone in zones.iterrows():
        zone_id = zone["zone_id"]
        zone_dir = RAW_DIR / zone_id

        if not zone_dir.exists():
            raise FileNotFoundError(
                f"Falta la carpeta cruda "
                f"de la zona {zone_id}: "
                f"{zone_dir}"
            )

        print(
            f"\nProcesando {zone_id}..."
        )

        hourly = load_zone_hourly(
            zone_id
        )
        daily = hourly_to_daily(
            hourly
        )
        monthly = daily_to_monthly(
            daily
        )

        metadata = {
            "zone_id": zone_id,
            "ciudad": zone["ciudad"],
            "provincia": (
                zone["provincia"]
            ),
            "region": zone["region"],
            "rol": zone["rol"],
            "latitud_solicitada": (
                zone["latitud"]
            ),
            "longitud_solicitada": (
                zone["longitud"]
            ),
        }

        for column, value in (
            metadata.items()
        ):
            daily[column] = value
            monthly[column] = value

        all_daily.append(
            daily.reset_index()
        )
        all_monthly.append(
            monthly
        )

        validation_rows.append(
            build_validation_summary(
                zone,
                hourly,
                daily,
                monthly,
            )
        )

    if not all_monthly:
        raise RuntimeError(
            "No se procesó ninguna zona."
        )

    daily_all = pd.concat(
        all_daily,
        ignore_index=True,
    )
    monthly_all = pd.concat(
        all_monthly,
        ignore_index=True,
    )
    validation = pd.DataFrame(
        validation_rows
    )

    daily_path = (
        PROCESSED_DIR
        / "indicadores_diarios_todas_zonas.csv"
    )
    monthly_path = (
        PROCESSED_DIR
        / "indicadores_mensuales_todas_zonas.csv"
    )
    validation_path = (
        QUALITY_DIR
        / "reporte_calidad.csv"
    )

    daily_all.to_csv(
        daily_path,
        index=False,
        encoding="utf-8-sig",
    )
    monthly_all.to_csv(
        monthly_path,
        index=False,
        encoding="utf-8-sig",
    )
    validation.to_csv(
        validation_path,
        index=False,
        encoding="utf-8-sig",
    )

    validate_global_result(
        validation
    )

    print("\nArchivos generados:")

    for path in (
        daily_path,
        monthly_path,
        validation_path,
    ):
        print(" -", path.resolve())

    print(
        "\nPaso 02 completado. "
        "No se generaron targets, "
        "lags, splits ni features "
        "de Machine Learning."
    )
    print(
        "Ahora ejecuta "
        "03_validar_calidad_dataset.py."
    )


if __name__ == "__main__":
    main()
