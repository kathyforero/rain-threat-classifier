"""
Analiza y reduce las características candidatas del modelo meteorológico.

IMPORTANTE
----------
- La selección se calcula EXCLUSIVAMENTE con la partición de entrenamiento.
- No se consulta validación temporal, prueba temporal ni holdout espacial.
- La correlación se usa para eliminar redundancia, no para medir por sí sola
  capacidad predictiva.
- Cuando dos variables meteorológicas presentan |rho de Spearman| >= 0.95,
  se conserva preferentemente la que tenga mayor información mutua con la
  variable objetivo dentro del conjunto de entrenamiento.
- Las variables de contexto temporal/geográfico se conservan por decisión de
  diseño y no participan en la poda por correlación.

Ejecutar desde la raíz del proyecto:
    py 04_seleccionar_caracteristicas.py

o:
    python 04_seleccionar_caracteristicas.py

Entradas esperadas:
    resultados_completo/dataset_modelo_mensual.csv
    resultados_completo/columnas_recomendadas_modelo.txt

Salidas:
    resultados_completo/columnas_candidatas_modelo.txt
    resultados_completo/columnas_seleccionadas_modelo.txt
    resultados_seleccion_caracteristicas/reporte_correlaciones_altas.csv
    resultados_seleccion_caracteristicas/ranking_informacion_mutua.csv
    resultados_seleccion_caracteristicas/reporte_columnas_eliminadas.csv
    resultados_seleccion_caracteristicas/resumen_seleccion.json
    resultados_seleccion_caracteristicas/heatmap_correlaciones_fuertes.png
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif
from sklearn.preprocessing import LabelEncoder


# -----------------------------------------------------------------------------
# Configuración
# -----------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "resultados_completo"
SELECTION_DIR = BASE_DIR / "resultados_seleccion_caracteristicas"

DATASET_FILE = RESULTS_DIR / "dataset_modelo_mensual.csv"
OLD_FEATURES_FILE = RESULTS_DIR / "columnas_recomendadas_modelo.txt"
CANDIDATE_FEATURES_FILE = RESULTS_DIR / "columnas_candidatas_modelo.txt"
SELECTED_FEATURES_FILE = RESULTS_DIR / "columnas_seleccionadas_modelo.txt"

HIGH_CORR_FILE = SELECTION_DIR / "reporte_correlaciones_altas.csv"
MI_FILE = SELECTION_DIR / "ranking_informacion_mutua.csv"
REMOVED_FILE = SELECTION_DIR / "reporte_columnas_eliminadas.csv"
SUMMARY_FILE = SELECTION_DIR / "resumen_seleccion.json"
HEATMAP_FILE = SELECTION_DIR / "heatmap_correlaciones_fuertes.png"

TRAIN_SPLIT = "entrenamiento"
TARGET_COLUMN = "target_amenaza"
CORRELATION_METHOD = "spearman"
CORRELATION_THRESHOLD = 0.95
RANDOM_STATE = 42
MAX_HEATMAP_FEATURES = 40

# Se conservan por decisión de diseño: representan estacionalidad y ubicación.
PROTECTED_CONTEXT_FEATURES = {
    "month_sin",
    "month_cos",
    "latitud_solicitada",
    "longitud_solicitada",
}


# -----------------------------------------------------------------------------
# Utilidades
# -----------------------------------------------------------------------------

def load_feature_list(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def save_feature_list(path: Path, features: list[str]) -> None:
    path.write_text("\n".join(features) + "\n", encoding="utf-8")


def build_high_correlation_report(
    correlation_matrix: pd.DataFrame,
    threshold: float,
) -> pd.DataFrame:
    upper = correlation_matrix.where(
        np.triu(
            np.ones(correlation_matrix.shape, dtype=bool),
            k=1,
        )
    )

    rows: list[dict[str, object]] = []
    for column_b in upper.columns:
        strong = upper[column_b].dropna()
        strong = strong[strong >= threshold]
        for column_a, value in strong.items():
            rows.append({
                "caracteristica_a": column_a,
                "caracteristica_b": column_b,
                "correlacion_spearman_abs": float(value),
            })

    if not rows:
        return pd.DataFrame(
            columns=[
                "caracteristica_a",
                "caracteristica_b",
                "correlacion_spearman_abs",
            ]
        )

    return (
        pd.DataFrame(rows)
        .sort_values("correlacion_spearman_abs", ascending=False)
        .reset_index(drop=True)
    )


def greedy_correlation_pruning(
    weather_features: list[str],
    correlation_matrix: pd.DataFrame,
    mutual_information: dict[str, float],
    threshold: float,
) -> tuple[list[str], pd.DataFrame]:
    """
    Conserva primero las variables con mayor información mutua con el target.

    Una variable posterior se elimina si tiene correlación >= threshold con
    alguna variable ya conservada. Esto evita elegir arbitrariamente cuál de
    dos variables casi redundantes conservar.
    """

    ordered = sorted(
        weather_features,
        key=lambda feature: (
            -mutual_information.get(feature, 0.0),
            feature,
        ),
    )

    kept: list[str] = []
    removed_rows: list[dict[str, object]] = []

    for feature in ordered:
        conflicts = []
        for kept_feature in kept:
            rho = float(correlation_matrix.loc[feature, kept_feature])
            if rho >= threshold:
                conflicts.append((kept_feature, rho))

        if not conflicts:
            kept.append(feature)
            continue

        # Registrar la variable conservada con mayor correlación con la eliminada.
        representative, rho = max(conflicts, key=lambda item: item[1])
        removed_rows.append({
            "caracteristica_eliminada": feature,
            "motivo": f"correlacion_abs>={threshold}",
            "correlacionada_con": representative,
            "correlacion_spearman_abs": rho,
            "mi_eliminada": float(mutual_information.get(feature, 0.0)),
            "mi_conservada": float(mutual_information.get(representative, 0.0)),
        })

    removed = pd.DataFrame(removed_rows)
    if not removed.empty:
        removed = removed.sort_values(
            ["correlacion_spearman_abs", "caracteristica_eliminada"],
            ascending=[False, True],
        ).reset_index(drop=True)

    return kept, removed


def create_heatmap(
    correlation_matrix: pd.DataFrame,
    high_corr_pairs: pd.DataFrame,
    output_file: Path,
) -> None:
    if high_corr_pairs.empty:
        return

    # Tomar variables de los pares más fuertes hasta alcanzar un tamaño legible.
    selected: list[str] = []
    for _, row in high_corr_pairs.iterrows():
        for feature in (
            row["caracteristica_a"],
            row["caracteristica_b"],
        ):
            if feature not in selected:
                selected.append(feature)
            if len(selected) >= MAX_HEATMAP_FEATURES:
                break
        if len(selected) >= MAX_HEATMAP_FEATURES:
            break

    matrix = correlation_matrix.loc[selected, selected]

    fig_size = max(10, min(18, len(selected) * 0.38))
    fig, ax = plt.subplots(figsize=(fig_size, fig_size))
    image = ax.imshow(matrix.to_numpy(), vmin=0, vmax=1, aspect="auto")

    ax.set_xticks(np.arange(len(selected)))
    ax.set_yticks(np.arange(len(selected)))
    ax.set_xticklabels(selected, rotation=90, fontsize=6)
    ax.set_yticklabels(selected, fontsize=6)
    ax.set_title(
        "Correlación absoluta de Spearman\n"
        "Características involucradas en las correlaciones más fuertes"
    )

    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(output_file, dpi=180, bbox_inches="tight")
    plt.close(fig)


# -----------------------------------------------------------------------------
# Proceso principal
# -----------------------------------------------------------------------------

def main() -> None:
    if not DATASET_FILE.exists():
        raise FileNotFoundError(f"No se encontró: {DATASET_FILE}")
    if not OLD_FEATURES_FILE.exists():
        raise FileNotFoundError(f"No se encontró: {OLD_FEATURES_FILE}")

    SELECTION_DIR.mkdir(parents=True, exist_ok=True)

    frame = pd.read_csv(DATASET_FILE, encoding="utf-8-sig")
    candidate_features = load_feature_list(OLD_FEATURES_FILE)

    missing = sorted(set(candidate_features).difference(frame.columns))
    if missing:
        raise ValueError(
            "Hay características candidatas que no existen en el dataset:\n- "
            + "\n- ".join(missing)
        )

    if "split" not in frame.columns or TARGET_COLUMN not in frame.columns:
        raise ValueError("El dataset no contiene 'split' y/o 'target_amenaza'.")

    train = frame.loc[frame["split"] == TRAIN_SPLIT].copy()
    if train.empty:
        raise ValueError("No se encontraron filas de entrenamiento.")

    X_train = train[candidate_features].copy()
    y_text = train[TARGET_COLUMN].copy()

    if X_train.isna().any().any():
        null_columns = X_train.columns[X_train.isna().any()].tolist()
        raise ValueError(f"Hay nulos en características: {null_columns}")

    # Conservar una copia explícita del conjunto de 144 características candidatas.
    save_feature_list(CANDIDATE_FEATURES_FILE, candidate_features)

    # -------------------------------------------------------------------------
    # 1. Variables constantes
    # -------------------------------------------------------------------------
    unique_counts = X_train.nunique(dropna=False)
    constant_features = unique_counts[unique_counts <= 1].index.tolist()

    nonconstant_features = [
        feature
        for feature in candidate_features
        if feature not in constant_features
    ]

    # -------------------------------------------------------------------------
    # 2. Información mutua con el objetivo (solo TRAIN)
    # -------------------------------------------------------------------------
    encoder = LabelEncoder()
    y_train = encoder.fit_transform(y_text)

    mi_values = mutual_info_classif(
        X_train[nonconstant_features],
        y_train,
        random_state=RANDOM_STATE,
    )
    mutual_information = dict(zip(nonconstant_features, mi_values))

    mi_report = pd.DataFrame({
        "caracteristica": nonconstant_features,
        "informacion_mutua": [
            float(mutual_information[feature])
            for feature in nonconstant_features
        ],
    }).sort_values("informacion_mutua", ascending=False)
    mi_report.to_csv(MI_FILE, index=False, encoding="utf-8-sig")

    # -------------------------------------------------------------------------
    # 3. Correlación de Spearman (solo TRAIN)
    # -------------------------------------------------------------------------
    correlation_matrix = (
        X_train[nonconstant_features]
        .corr(method=CORRELATION_METHOD)
        .abs()
    )

    high_corr_report = build_high_correlation_report(
        correlation_matrix,
        CORRELATION_THRESHOLD,
    )
    high_corr_report.to_csv(
        HIGH_CORR_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    # -------------------------------------------------------------------------
    # 4. Poda conservadora por redundancia
    # -------------------------------------------------------------------------
    protected = [
        feature
        for feature in nonconstant_features
        if feature in PROTECTED_CONTEXT_FEATURES
    ]
    weather_features = [
        feature
        for feature in nonconstant_features
        if feature not in PROTECTED_CONTEXT_FEATURES
    ]

    kept_weather, removed_corr = greedy_correlation_pruning(
        weather_features,
        correlation_matrix,
        mutual_information,
        CORRELATION_THRESHOLD,
    )

    removed_rows: list[dict[str, object]] = []

    for feature in constant_features:
        removed_rows.append({
            "caracteristica_eliminada": feature,
            "motivo": "constante_en_entrenamiento",
            "correlacionada_con": "",
            "correlacion_spearman_abs": np.nan,
            "mi_eliminada": 0.0,
            "mi_conservada": np.nan,
        })

    if not removed_corr.empty:
        removed_rows.extend(removed_corr.to_dict("records"))

    removed_report = pd.DataFrame(removed_rows)
    if not removed_report.empty:
        removed_report.to_csv(
            REMOVED_FILE,
            index=False,
            encoding="utf-8-sig",
        )
    else:
        pd.DataFrame(columns=[
            "caracteristica_eliminada",
            "motivo",
            "correlacionada_con",
            "correlacion_spearman_abs",
            "mi_eliminada",
            "mi_conservada",
        ]).to_csv(REMOVED_FILE, index=False, encoding="utf-8-sig")

    # Preservar el orden original del archivo de candidatas.
    selected_set = set(kept_weather).union(protected)
    selected_features = [
        feature
        for feature in candidate_features
        if feature in selected_set
    ]

    save_feature_list(SELECTED_FEATURES_FILE, selected_features)

    create_heatmap(
        correlation_matrix,
        high_corr_report,
        HEATMAP_FILE,
    )

    summary = {
        "metodo_correlacion": CORRELATION_METHOD,
        "umbral_correlacion_abs": CORRELATION_THRESHOLD,
        "split_usado_para_seleccion": TRAIN_SPLIT,
        "filas_entrenamiento": int(len(train)),
        "caracteristicas_candidatas": int(len(candidate_features)),
        "caracteristicas_constantes_eliminadas": int(len(constant_features)),
        "pares_correlacion_alta": int(len(high_corr_report)),
        "caracteristicas_eliminadas_por_correlacion": int(len(removed_corr)),
        "caracteristicas_contexto_protegidas": protected,
        "caracteristicas_seleccionadas": int(len(selected_features)),
        "clases_objetivo": encoder.classes_.tolist(),
        "criterio_representante": (
            "entre variables meteorologicas con correlacion alta, "
            "se prioriza la de mayor informacion mutua con target_amenaza"
        ),
    }

    SUMMARY_FILE.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\nSELECCIÓN DE CARACTERÍSTICAS")
    print("----------------------------")
    print(f"Dataset: {DATASET_FILE.resolve()}")
    print(f"Filas usadas (solo entrenamiento): {len(train)}")
    print(f"Características candidatas: {len(candidate_features)}")
    print(f"Constantes eliminadas: {len(constant_features)}")
    print(
        f"Pares con |rho Spearman| >= {CORRELATION_THRESHOLD}: "
        f"{len(high_corr_report)}"
    )
    print(f"Eliminadas por redundancia: {len(removed_corr)}")
    print(f"Características seleccionadas: {len(selected_features)}")

    print("\nTop 10 por información mutua:")
    print(mi_report.head(10).to_string(index=False))

    if not high_corr_report.empty:
        print("\nTop 10 correlaciones absolutas:")
        print(high_corr_report.head(10).to_string(index=False))

    print("\nArchivos generados:")
    print(f"- {CANDIDATE_FEATURES_FILE.resolve()}")
    print(f"- {SELECTED_FEATURES_FILE.resolve()}")
    print(f"- {HIGH_CORR_FILE.resolve()}")
    print(f"- {MI_FILE.resolve()}")
    print(f"- {REMOVED_FILE.resolve()}")
    print(f"- {SUMMARY_FILE.resolve()}")
    if HEATMAP_FILE.exists():
        print(f"- {HEATMAP_FILE.resolve()}")

    print(
        "\nIMPORTANTE: no uses todavía validación temporal, prueba temporal "
        "ni holdout espacial para modificar esta selección."
    )


if __name__ == "__main__":
    main()
