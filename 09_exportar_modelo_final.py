from __future__ import annotations

import json
from functools import partial
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC


BASE_DIR = Path(__file__).resolve().parent
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
PARAMS_FILE = BASE_DIR / "resultados" / "modelos_cv" / "mejores_parametros.json"
WINNER_FILE = BASE_DIR / "resultados" / "modelos_cv" / "ganador_paso06.json"
OUTPUT_DIR = BASE_DIR / "resultados" / "modelo_final"

RANDOM_STATE = 42
CLASS_ORDER = ["Baja", "Media", "Alta"]
TARGET_TO_INT = {"Baja": 0, "Media": 1, "Alta": 2}
INT_TO_TARGET = {value: key for key, value in TARGET_TO_INT.items()}
FINAL_TRAIN_SPLITS = ["entrenamiento", "validacion_temporal"]
TEST_SPLIT = "prueba_temporal"


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


def make_pipeline(numeric_features, categorical_features, svm_params):
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
                    k=svm_params["preprocess__num__selector__k"],
                ),
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
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
                ),
            ),
        ]
    )


def calculate_metrics(y_true, y_pred):
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=[0, 1, 2],
        zero_division=0,
    )

    return {
        "modelo": "SVM_RBF",
        "evaluacion": "prueba_temporal_2022_2025",
        "macro_f1": f1_score(
            y_true,
            y_pred,
            average="macro",
            zero_division=0,
        ),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "accuracy": accuracy_score(y_true, y_pred),
        "precision_baja": precision[0],
        "recall_baja": recall[0],
        "f1_baja": f1[0],
        "support_baja": int(support[0]),
        "precision_media": precision[1],
        "recall_media": recall[1],
        "f1_media": f1[1],
        "support_media": int(support[1]),
        "precision_alta": precision[2],
        "recall_alta": recall[2],
        "f1_alta": f1[2],
        "support_alta": int(support[2]),
        "n": int(len(y_true)),
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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

    df = pd.read_csv(DATASET_FILE)
    catalog = pd.read_csv(CATALOG_FILE)

    features = catalog["caracteristica"].tolist()
    numeric_features = catalog.loc[
        catalog["tipo"] == "numerica",
        "caracteristica",
    ].tolist()
    categorical_features = catalog.loc[
        catalog["tipo"] == "categorica",
        "caracteristica",
    ].tolist()

    missing = sorted(set(features).difference(df.columns))
    if missing:
        raise ValueError(f"Faltan columnas en el dataset: {missing}")

    train = df[
        (df["rol"] == "desarrollo")
        & (df["split"].isin(FINAL_TRAIN_SPLITS))
    ].copy()
    test = df[
        (df["rol"] == "desarrollo")
        & (df["split"] == TEST_SPLIT)
    ].copy()

    if len(train) != 4320:
        raise ValueError(f"Se esperaban 4320 filas de train final, hay {len(train)}")
    if len(test) != 576:
        raise ValueError(f"Se esperaban 576 filas de prueba temporal, hay {len(test)}")

    X_train = train[features].copy()
    y_train = train["target_amenaza"].map(TARGET_TO_INT).astype(int)

    X_test = test[features].copy()
    y_test = test["target_amenaza"].map(TARGET_TO_INT).astype(int)

    pipeline = make_pipeline(
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        svm_params=svm_params,
    )
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    metrics = calculate_metrics(y_test, y_pred)

    model_file = OUTPUT_DIR / "modelo_svm_rbf_final.joblib"
    metadata_file = OUTPUT_DIR / "metadata_modelo_svm_rbf_final.json"
    metrics_file = OUTPUT_DIR / "metricas_prueba_temporal_modelo_final.csv"

    joblib.dump(pipeline, model_file)

    metadata = {
        "modelo": "SVM_RBF",
        "archivo_modelo": str(model_file.relative_to(BASE_DIR)),
        "dataset": str(DATASET_FILE.relative_to(BASE_DIR)),
        "catalogo_features": str(CATALOG_FILE.relative_to(BASE_DIR)),
        "features": features,
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "target": "target_amenaza",
        "label_mapping": {
            "target_to_int": TARGET_TO_INT,
            "int_to_target": {str(k): v for k, v in INT_TO_TARGET.items()},
        },
        "train_filter": {
            "rol": "desarrollo",
            "split": FINAL_TRAIN_SPLITS,
        },
        "test_filter": {
            "rol": "desarrollo",
            "split": TEST_SPLIT,
        },
        "n_train": int(len(train)),
        "n_test": int(len(test)),
        "svm_params": svm_params,
        "metricas_prueba_temporal": metrics,
        "nota": (
            "El .joblib contiene un Pipeline entrenado de scikit-learn. "
            "Recibe un DataFrame con las features oficiales y predice 0, 1 o 2; "
            "usar int_to_target para convertir a Baja, Media o Alta."
        ),
    }

    with metadata_file.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2, ensure_ascii=False)

    pd.DataFrame([metrics]).to_csv(
        metrics_file,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"Modelo guardado: {model_file}")
    print(f"Metadata guardada: {metadata_file}")
    print(f"Metricas guardadas: {metrics_file}")
    print(f"Train: {len(train):,} filas")
    print(f"Prueba temporal: {len(test):,} filas")
    print(f"macro_f1 prueba temporal: {metrics['macro_f1']:.4f}")
    print(f"balanced_accuracy prueba temporal: {metrics['balanced_accuracy']:.4f}")
    print(f"accuracy prueba temporal: {metrics['accuracy']:.4f}")


if __name__ == "__main__":
    main()
