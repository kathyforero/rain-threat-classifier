"""
PASO 09 · ENTRENAR Y EXPORTAR MODELO OPERATIVO FINAL

Este paso se ejecuta DESPUÉS de completar la evaluación final del Paso 08.
No vuelve a medir test ni holdout.

Entrena el pipeline operativo con todas las etiquetas disponibles de las
12 zonas de desarrollo hasta diciembre de 2025:

    entrenamiento + validacion_temporal + prueba_temporal

Las tres zonas de holdout espacial permanecen fuera del entrenamiento.

El SVM y sus hiperparámetros están congelados desde el Paso 06:
    kernel = RBF
    C = 1
    gamma = 0.05
    k = all

Para el prototipo se habilita probability=True. Esto añade estimaciones de
probabilidad de libsvm sin reabrir la selección del clasificador. Las clases
se siguen prediciendo con la frontera SVM congelada.
"""

from __future__ import annotations

import json
from functools import partial
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC


BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_FILE = (
    BASE_DIR
    / "datos"
    / "modelado"
    / "dataset_caracteristicas_candidatas.csv"
)
CATALOG_FILE = (
    BASE_DIR
    / "resultados"
    / "analisis_caracteristicas"
    / "catalogo_caracteristicas_modelado.csv"
)
THRESHOLDS_FILE = (
    BASE_DIR
    / "datos"
    / "modelado"
    / "umbrales_amenaza.csv"
)
PARAMS_FILE = (
    BASE_DIR
    / "resultados"
    / "modelos_cv"
    / "mejores_parametros.json"
)
WINNER_FILE = (
    BASE_DIR
    / "resultados"
    / "modelos_cv"
    / "ganador_paso06.json"
)
FINAL_EVALUATION_FILE = (
    BASE_DIR
    / "resultados"
    / "evaluacion_final"
    / "resumen_evaluacion_final.csv"
)
OUTPUT_DIR = BASE_DIR / "resultados" / "modelo_final"

RANDOM_STATE = 42
CLASS_ORDER = ["Baja", "Media", "Alta"]
TARGET_TO_INT = {"Baja": 0, "Media": 1, "Alta": 2}
INT_TO_TARGET = {value: key for key, value in TARGET_TO_INT.items()}

FINAL_TRAIN_SPLITS = [
    "entrenamiento",
    "validacion_temporal",
    "prueba_temporal",
]

EXPECTED_SVM_PARAMS = {
    "model__C": 1,
    "model__gamma": 0.05,
    "preprocess__num__selector__k": "all",
}

FORBIDDEN_FEATURES = {
    "target_amenaza",
    "target_rx5day_mm",
    "target_period_start",
    "amenaza_mes",
    "split",
    "rol",
    "zone_id",
    "ciudad",
    "provincia",
    "period",
    "period_start",
}


def make_onehot_encoder():
    try:
        return OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=False,
        )
    except TypeError:
        return OneHotEncoder(
            handle_unknown="ignore",
            sparse=False,
        )


def make_pipeline(
    numeric_features,
    categorical_features,
    svm_params,
):
    numeric_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "selector",
                SelectKBest(
                    score_func=partial(
                        mutual_info_classif,
                        random_state=RANDOM_STATE,
                    ),
                    k=svm_params[
                        "preprocess__num__selector__k"
                    ],
                ),
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        [
            (
                "imputer",
                SimpleImputer(strategy="most_frequent"),
            ),
            ("onehot", make_onehot_encoder()),
        ]
    )

    preprocessor = ColumnTransformer(
        [
            ("num", numeric_pipeline, numeric_features),
            ("cat", categorical_pipeline, categorical_features),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )

    return Pipeline(
        [
            ("preprocess", preprocessor),
            (
                "model",
                SVC(
                    kernel="rbf",
                    C=svm_params["model__C"],
                    gamma=svm_params["model__gamma"],
                    probability=True,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def main():
    # Barrera de orden: primero debe haberse documentado la evaluación final.
    if not FINAL_EVALUATION_FILE.exists():
        raise FileNotFoundError(
            "No se encontró la evaluación final del Paso 08: "
            f"{FINAL_EVALUATION_FILE}. Ejecuta y revisa el Paso 08 antes "
            "de exportar el modelo operativo."
        )

    required_files = [
        DATASET_FILE,
        CATALOG_FILE,
        THRESHOLDS_FILE,
        PARAMS_FILE,
        WINNER_FILE,
    ]

    missing_files = [
        str(path)
        for path in required_files
        if not path.exists()
    ]

    if missing_files:
        raise FileNotFoundError(
            "Faltan archivos requeridos:\n- "
            + "\n- ".join(missing_files)
        )

    with WINNER_FILE.open(encoding="utf-8") as file:
        winner_payload = json.load(file)

    if winner_payload["modelo_ganador"] != "SVM_RBF":
        raise ValueError(
            "El ganador registrado no es SVM_RBF: "
            f"{winner_payload['modelo_ganador']}"
        )

    with PARAMS_FILE.open(encoding="utf-8") as file:
        all_params = json.load(file)

    svm_params = all_params["SVM_RBF"]

    if svm_params != EXPECTED_SVM_PARAMS:
        raise ValueError(
            "Los parámetros SVM ya no coinciden con la configuración "
            "congelada del proyecto.\n"
            f"Esperado: {EXPECTED_SVM_PARAMS}\n"
            f"Encontrado: {svm_params}"
        )

    df = pd.read_csv(DATASET_FILE, encoding="utf-8-sig")
    catalog = pd.read_csv(CATALOG_FILE, encoding="utf-8-sig")
    thresholds = pd.read_csv(
        THRESHOLDS_FILE,
        encoding="utf-8-sig",
    )

    features = catalog["caracteristica"].tolist()
    numeric_features = catalog.loc[
        catalog["tipo"] == "numerica",
        "caracteristica",
    ].tolist()
    categorical_features = catalog.loc[
        catalog["tipo"] == "categorica",
        "caracteristica",
    ].tolist()

    leakage = sorted(
        set(features).intersection(FORBIDDEN_FEATURES)
    )

    if leakage:
        raise RuntimeError(
            f"LEAKAGE: el catálogo contiene columnas prohibidas: {leakage}"
        )

    missing = sorted(set(features).difference(df.columns))

    if missing:
        raise ValueError(
            f"Faltan columnas del catálogo en el dataset: {missing}"
        )

    train = df[
        (df["rol"] == "desarrollo")
        & (df["split"].isin(FINAL_TRAIN_SPLITS))
    ].copy()

    if len(train) != 4896:
        raise ValueError(
            "Se esperaban 4.896 filas de desarrollo hasta 2025 "
            f"y se encontraron {len(train)}."
        )

    if train["zone_id"].nunique() != 12:
        raise ValueError(
            "El entrenamiento operativo debe contener exactamente "
            "las 12 zonas de desarrollo."
        )

    X_train = train[features].copy()
    y_train = (
        train["target_amenaza"]
        .map(TARGET_TO_INT)
        .astype(int)
    )

    pipeline = make_pipeline(
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        svm_params=svm_params,
    )

    pipeline.fit(X_train, y_train)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    model_file = (
        OUTPUT_DIR
        / "modelo_svm_rbf_operativo_2025.joblib"
    )
    metadata_file = (
        OUTPUT_DIR
        / "metadata_modelo_svm_rbf_operativo_2025.json"
    )
    training_summary_file = (
        OUTPUT_DIR
        / "resumen_entrenamiento_modelo_operativo.csv"
    )

    joblib.dump(pipeline, model_file)

    threshold_row = thresholds.iloc[0]

    metadata = {
        "modelo": "SVM_RBF",
        "tipo_artefacto": "modelo_operativo_post_evaluacion",
        "archivo_modelo": str(model_file.relative_to(BASE_DIR)),
        "dataset": str(DATASET_FILE.relative_to(BASE_DIR)),
        "catalogo_features": str(CATALOG_FILE.relative_to(BASE_DIR)),
        "features": features,
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "n_features_catalogo": int(len(features)),
        "target": "target_amenaza",
        "horizonte": "mes_t_a_mes_t_mas_1",
        "label_mapping": {
            "target_to_int": TARGET_TO_INT,
            "int_to_target": {
                str(k): v
                for k, v in INT_TO_TARGET.items()
            },
        },
        "umbrales_target": {
            "variable": "rx5day_mm",
            "q33_global_mm": float(
                threshold_row["q33_global_mm"]
            ),
            "q66_global_mm": float(
                threshold_row["q66_global_mm"]
            ),
            "scope": threshold_row["scope"],
            "nota": (
                "Umbrales estadísticos del proyecto; no son "
                "umbrales oficiales de alerta de INAMHI."
            ),
        },
        "train_filter": {
            "rol": "desarrollo",
            "splits": FINAL_TRAIN_SPLITS,
            "zonas": 12,
            "hasta_target": str(
                pd.to_datetime(
                    train["target_period_start"]
                ).max().date()
            ),
        },
        "n_train": int(len(train)),
        "svm_params_clasificacion": svm_params,
        "probabilidades": {
            "disponibles": True,
            "metodo": "SVC probability=True (estimacion probabilistica de libsvm)",
            "nota": (
                "Las probabilidades son estimaciones para la interfaz. "
                "No reabren la selección del clasificador ni sustituyen "
                "las métricas de evaluación del Paso 08."
            ),
        },
        "evaluacion": {
            "archivo_oficial": str(
                FINAL_EVALUATION_FILE.relative_to(BASE_DIR)
            ),
            "nota": (
                "Este Paso 09 no reevalúa test ni holdout. "
                "Las métricas oficiales permanecen en resultados/evaluacion_final/."
            ),
        },
    }

    with metadata_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=2,
            ensure_ascii=False,
        )

    summary = pd.DataFrame([
        {
            "modelo": "SVM_RBF",
            "n_train": len(train),
            "zonas_entrenamiento": train["zone_id"].nunique(),
            "primer_target": pd.to_datetime(
                train["target_period_start"]
            ).min().date(),
            "ultimo_target": pd.to_datetime(
                train["target_period_start"]
            ).max().date(),
            "C": svm_params["model__C"],
            "gamma": svm_params["model__gamma"],
            "selector_k": svm_params[
                "preprocess__num__selector__k"
            ],
            "probability": True,
        }
    ])

    summary.to_csv(
        training_summary_file,
        index=False,
        encoding="utf-8-sig",
    )

    print("PASO 09 · MODELO OPERATIVO EXPORTADO")
    print("------------------------------------")
    print(f"Train: {len(train):,} filas")
    print("Zonas: 12 de desarrollo")
    print("Último target etiquetado usado: 2025-12")
    print(f"Modelo: {model_file}")
    print(f"Metadata: {metadata_file}")
    print(f"Resumen: {training_summary_file}")
    print(
        "No se recalcularon métricas de test ni holdout en este paso."
    )


if __name__ == "__main__":
    main()
