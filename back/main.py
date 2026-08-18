from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_FILE = BASE_DIR / "resultados" / "modelo_svm_rbf_operativo_2025.joblib"
MONTHLY_INDICATORS_FILE = (
    BASE_DIR / "datos" / "procesados" / "indicadores_mensuales_todas_zonas.csv"
)
CATALOG_FILE = (
    BASE_DIR
    / "resultados"
    / "analisis_caracteristicas"
    / "catalogo_caracteristicas_modelado.csv"
)

CLASS_LABELS = {0: "Baja", 1: "Media", 2: "Alta"}
LABEL_TO_PAYLOAD_KEY = {"Baja": "low", "Media": "medium", "Alta": "high"}
MONTH_SHORT = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
CURRENT_METEO_FEATURES = [
    "prcptot_mm",
    "rx5day_mm",
    "max_3h_mm",
    "sdii_mm_per_wet_day",
    "r20mm_days",
    "cwd_days",
    "cdd_days",
    "temperature_mean_c",
    "relative_humidity_mean_pct",
    "wind_mean_ms",
    "surface_pressure_mean_hpa",
]
LAGS = [1, 11]

FRONT_CITY_IDS = {
    "babahoyo": "babahoyo",
    "cuenca": "cuenca",
    "esmeraldas": "esmeraldas",
    "guayaquil": "guayaquil",
    "loja": "loja",
    "macas": "macas",
    "machala": "machala",
    "nueva_loja": "nueva-loja",
    "portoviejo": "portoviejo",
    "puyo": "puyo",
    "quito": "quito",
    "riobamba": "riobamba",
    "salinas": "salinas",
    "santo_domingo": "santo-domingo",
    "tena": "tena",
}


class PredictionRequest(BaseModel):
    cityId: str
    referenceMonth: str


app = FastAPI(title="Precipita EC API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def load_context():
    missing = [path for path in [MODEL_FILE, MONTHLY_INDICATORS_FILE, CATALOG_FILE] if not path.exists()]
    if missing:
        raise FileNotFoundError("Faltan archivos requeridos: " + ", ".join(str(path) for path in missing))

    model = joblib.load(MODEL_FILE)
    monthly = pd.read_csv(MONTHLY_INDICATORS_FILE, encoding="utf-8-sig")
    catalog = pd.read_csv(CATALOG_FILE, encoding="utf-8-sig")
    features = catalog["caracteristica"].tolist()

    df = build_inference_frame(monthly)
    df["front_city_id"] = df["zone_id"].map(FRONT_CITY_IDS)
    df = df[df["front_city_id"].notna()].copy()
    return model, df, catalog


def build_inference_frame(monthly: pd.DataFrame) -> pd.DataFrame:
    df = monthly.copy()
    df["period_start"] = pd.to_datetime(df["period_start"])
    df["target_period_start"] = df["period_start"] + pd.DateOffset(months=1)
    df["target_month"] = df["target_period_start"].dt.month
    df["target_month_sin"] = np.sin(2 * np.pi * df["target_month"] / 12)
    df["target_month_cos"] = np.cos(2 * np.pi * df["target_month"] / 12)

    df = df.sort_values(["zone_id", "period_start"]).copy()
    grouped = df.groupby("zone_id", sort=False)
    for feature in CURRENT_METEO_FEATURES:
        for lag in LAGS:
            df[f"{feature}__lag{lag}"] = grouped[feature].shift(lag)

    lag_features = [
        f"{feature}__lag{lag}"
        for feature in CURRENT_METEO_FEATURES
        for lag in LAGS
    ]
    df = df.dropna(subset=lag_features).reset_index(drop=True)
    df["period_obj"] = df["period"].map(lambda value: pd.Period(value, freq="M"))
    return df


def round_number(value, decimals=1):
    if pd.isna(value):
        return 0
    return round(float(value), decimals)


def month_short(value: str) -> str:
    period = pd.Period(value, freq="M")
    return f"{MONTH_SHORT[period.month - 1]} {str(period.year)[-2:]}"


def build_indicators(row) -> dict:
    return {
        "accumulatedPrecipitation": round_number(row["prcptot_mm"]),
        "maximumThreeHourPrecipitation": round_number(row["max_3h_mm"]),
        "maximumFiveDayPrecipitation": round_number(row["rx5day_mm"]),
        "rainfallIntensityPerWetDay": round_number(row["sdii_mm_per_wet_day"]),
        "intenseRainDays": int(round_number(row["r20mm_days"], 0)),
        "wetStreakDays": int(round_number(row["cwd_days"], 0)),
        "dryStreakDays": int(round_number(row["cdd_days"], 0)),
        "averageTemperature": round_number(row["temperature_mean_c"]),
        "relativeHumidity": round_number(row["relative_humidity_mean_pct"], 0),
        "windSpeed": round_number(float(row["wind_mean_ms"]) * 3.6),
        "surfacePressure": round_number(row["surface_pressure_mean_hpa"]),
    }


def build_history(city_rows: pd.DataFrame, reference_month: str) -> list[dict]:
    ref_period = pd.Period(reference_month, freq="M")
    start_period = ref_period - 11
    history_rows = city_rows[
        (city_rows["period_obj"] >= start_period)
        & (city_rows["period_obj"] <= ref_period)
    ].sort_values("period_obj")

    return [
        {
            "month": month_short(row["period"]),
            "precipitation": round_number(row["prcptot_mm"]),
            "isReference": row["period"] == reference_month,
        }
        for _, row in history_rows.iterrows()
    ]


def normalize_percentages(probabilities: dict[str, float]) -> dict[str, int]:
    rounded = {key: int(round(value * 100)) for key, value in probabilities.items()}
    delta = 100 - sum(rounded.values())
    if delta:
        winner = max(probabilities, key=probabilities.get)
        rounded[winner] += delta
    return rounded


def validate_model_input(X: pd.DataFrame, catalog: pd.DataFrame) -> None:
    features = catalog["caracteristica"].tolist()
    numeric_features = catalog.loc[catalog["tipo"] == "numerica", "caracteristica"].tolist()
    categorical_features = catalog.loc[catalog["tipo"] == "categorica", "caracteristica"].tolist()

    received = list(X.columns)
    missing = sorted(set(features).difference(received))
    extra = sorted(set(received).difference(features))

    if missing or extra:
        detail = []
        if missing:
            detail.append(f"Faltan features: {missing}")
        if extra:
            detail.append(f"Sobran features: {extra}")
        raise HTTPException(status_code=422, detail=" | ".join(detail))

    if received != features:
        raise HTTPException(
            status_code=422,
            detail="Las features no están en el orden esperado por el modelo.",
        )

    for column in numeric_features:
        try:
            pd.to_numeric(X[column])
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=f"La feature numérica {column} tiene un tipo de dato inválido.",
            ) from exc

    for column in categorical_features:
        if X[column].isna().any():
            raise HTTPException(
                status_code=422,
                detail=f"La feature categórica {column} no puede estar vacía.",
            )


@app.get("/health")
def health():
    load_context()
    return {"status": "ok"}


@app.post("/predict")
def predict(payload: PredictionRequest):
    model, df, catalog = load_context()
    features = catalog["caracteristica"].tolist()

    match = df[
        (df["front_city_id"] == payload.cityId)
        & (df["period"] == payload.referenceMonth)
    ]
    if match.empty:
        raise HTTPException(
            status_code=404,
            detail="No hay datos suficientes para esa ciudad y mes seleccionado.",
        )

    row = match.iloc[0]
    X = row[features].to_frame().T
    validate_model_input(X, catalog)
    prediction = int(model.predict(X)[0])
    class_order = list(model.named_steps["model"].classes_)
    proba_labels = [CLASS_LABELS[int(value)] for value in class_order]
    raw_probabilities = dict(zip(proba_labels, model.predict_proba(X)[0], strict=True))
    probabilities = normalize_percentages(
        {
            LABEL_TO_PAYLOAD_KEY[label]: raw_probabilities.get(label, 0.0)
            for label in ["Baja", "Media", "Alta"]
        }
    )
    city_rows = df[df["front_city_id"] == payload.cityId]

    return {
        "city": row["ciudad"],
        "province": row["provincia"],
        "referenceMonthRaw": row["period"],
        "targetMonthRaw": pd.to_datetime(row["target_period_start"]).strftime("%Y-%m"),
        "threatLevel": CLASS_LABELS[prediction],
        "confidence": max(probabilities.values()),
        "probabilities": probabilities,
        "dataAvailability": "sufficient",
        "indicators": build_indicators(row),
        "historicalSeries": build_history(city_rows, row["period"]),
    }
