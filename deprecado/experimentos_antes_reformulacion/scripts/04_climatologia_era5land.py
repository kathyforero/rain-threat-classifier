"""
04_climatologia_era5land.py

Funciones para crear características climatológicas usando EXCLUSIVAMENTE
los indicadores mensuales de ERA5-Land.

La climatología se ajusta con un corte temporal explícito. Esto permite usar
la misma lógica dentro de cada fold temporal sin incorporar información futura.

Características añadidas:
- z-score climatológico por zona + mes para 7 variables, lags 0, 1 y 2.
- contexto climatológico de Rx5day del mes objetivo:
  media, desviación estándar, q33 y q66.

No modifica el target ni requiere fuentes externas.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


CLIMATE_VARIABLES = [
    "relative_humidity_mean_pct",
    "sdii_mm_per_wet_day",
    "rx1day_mm",
    "rx5day_mm",
    "prcptot_mm",
    "temperature_mean_c",
    "dewpoint_mean_c",
]

CLIMATE_LAGS = [0, 1, 2]

CLIMATE_FEATURE_NAMES = [
    f"clim_z_{variable}_lag{lag}"
    for variable in CLIMATE_VARIABLES
    for lag in CLIMATE_LAGS
] + [
    "target_rx5_clim_mean",
    "target_rx5_clim_std",
    "target_rx5_clim_q33",
    "target_rx5_clim_q66",
]


@dataclass
class ClimateReference:
    variable_stats: dict[str, pd.DataFrame]
    target_rx5_stats: pd.DataFrame
    cutoff: pd.Timestamp


def prepare_monthly(monthly: pd.DataFrame) -> pd.DataFrame:
    result = monthly.copy()
    result["period_start"] = pd.to_datetime(result["period_start"], errors="raise")
    result["month"] = result["period_start"].dt.month.astype(int)
    return result


def fit_climatology(
    monthly: pd.DataFrame,
    cutoff: pd.Timestamp,
    zones: list[str] | np.ndarray,
) -> ClimateReference:
    """
    Ajusta referencias climatológicas SOLO con observaciones <= cutoff
    y las zonas proporcionadas.
    """
    monthly = prepare_monthly(monthly)
    cutoff = pd.Timestamp(cutoff)

    history = monthly[
        (monthly["period_start"] <= cutoff)
        & (monthly["zone_id"].isin(list(zones)))
    ].copy()

    if history.empty:
        raise ValueError("No existen observaciones para ajustar la climatología.")

    missing = sorted(set(CLIMATE_VARIABLES) - set(history.columns))
    if missing:
        raise ValueError(f"Faltan variables ERA5-Land: {missing}")

    variable_stats: dict[str, pd.DataFrame] = {}

    for variable in CLIMATE_VARIABLES:
        stats = (
            history.groupby(["zone_id", "month"])[variable]
            .agg(["mean", "std", "count"])
            .sort_index()
        )
        variable_stats[variable] = stats

    target_rx5_stats = (
        history.groupby(["zone_id", "month"])["rx5day_mm"]
        .agg(
            mean="mean",
            std="std",
            count="count",
            q33=lambda s: s.quantile(1.0 / 3.0),
            q66=lambda s: s.quantile(2.0 / 3.0),
        )
        .sort_index()
    )

    return ClimateReference(
        variable_stats=variable_stats,
        target_rx5_stats=target_rx5_stats,
        cutoff=cutoff,
    )


def _lookup(
    stats: pd.DataFrame,
    zones: pd.Series,
    months: np.ndarray,
    column: str,
) -> np.ndarray:
    lookup = stats[column].to_dict()
    keys = list(zip(zones.astype(str).tolist(), months.astype(int).tolist()))

    missing = [key for key in keys if key not in lookup]
    if missing:
        unique_missing = sorted(set(missing))[:10]
        raise ValueError(
            "No existe climatología para algunos pares zona/mes. "
            f"Ejemplos: {unique_missing}"
        )

    return np.asarray([lookup[key] for key in keys], dtype=float)


def add_climate_features(
    frame: pd.DataFrame,
    base_X: pd.DataFrame,
    reference: ClimateReference,
) -> pd.DataFrame:
    """
    Añade las características climatológicas a base_X.

    frame debe contener:
    - zone_id
    - period_start
    - target_period_start
    - las columnas meteorológicas *_lag0, *_lag1, *_lag2
    """
    frame = frame.copy()
    frame["period_start"] = pd.to_datetime(frame["period_start"], errors="raise")
    frame["target_period_start"] = pd.to_datetime(
        frame["target_period_start"], errors="raise"
    )

    result = base_X.copy()

    for variable in CLIMATE_VARIABLES:
        stats = reference.variable_stats[variable]

        for lag in CLIMATE_LAGS:
            source_col = f"{variable}_lag{lag}"
            if source_col not in frame.columns:
                raise ValueError(f"Falta {source_col} en el dataset.")

            lag_dates = pd.DatetimeIndex(frame["period_start"]) - pd.DateOffset(
                months=lag
            )
            lag_months = lag_dates.month

            means = _lookup(stats, frame["zone_id"], lag_months, "mean")
            stds = _lookup(stats, frame["zone_id"], lag_months, "std")

            # Evitar divisiones por cero sin convertir una variable constante
            # en una fuente artificial de valores extremos.
            safe_stds = np.where(
                np.isfinite(stds) & (np.abs(stds) > 1e-9),
                stds,
                1.0,
            )

            values = frame[source_col].to_numpy(dtype=float)
            result[f"clim_z_{variable}_lag{lag}"] = (
                values - means
            ) / safe_stds

    # Contexto climatológico DEL MES OBJETIVO. Son referencias históricas,
    # no valores meteorológicos futuros del target.
    target_months = pd.DatetimeIndex(frame["target_period_start"]).month
    rx_stats = reference.target_rx5_stats

    result["target_rx5_clim_mean"] = _lookup(
        rx_stats, frame["zone_id"], target_months, "mean"
    )
    result["target_rx5_clim_std"] = _lookup(
        rx_stats, frame["zone_id"], target_months, "std"
    )
    result["target_rx5_clim_q33"] = _lookup(
        rx_stats, frame["zone_id"], target_months, "q33"
    )
    result["target_rx5_clim_q66"] = _lookup(
        rx_stats, frame["zone_id"], target_months, "q66"
    )

    if result[CLIMATE_FEATURE_NAMES].isna().sum().sum() != 0:
        raise AssertionError(
            "Se generaron nulos en las características climatológicas."
        )

    return result
