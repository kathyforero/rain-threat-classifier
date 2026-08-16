import { useMemo, useState } from "react";

type ModelKey = "SVM_RBF" | "XGBoost" | "Random_Forest" | "Logistic_Regression" | "MLP";

interface ModelInfo {
  key: ModelKey;
  name: string;
  summary: string;
  training: string;
  metrics: {
    macroF1: number;
    balancedAccuracy: number;
    accuracy: number;
    recallHigh: number;
  };
  params: string;
  confusión: number[][];
}

const MODELS: ModelInfo[] = [
  {
    key: "SVM_RBF",
    name: "SVM con kernel RBF",
    summary:
      "Busca una frontera flexible entre Baja, Media y Alta. El kernel RBF permite separar patrones no lineales.",
    training:
      "Se entrenó con validación temporal y búsqueda de C=1, gamma=0.05 y selector de variables en all.",
    metrics: { macroF1: 0.7188, balancedAccuracy: 0.718, accuracy: 0.7202, recallHigh: 0.7131 },
    params: "C=1, gamma=0.05, features=all",
    confusión: [
      [516, 122, 17],
      [79, 381, 128],
      [13, 164, 452],
    ],
  },
  {
    key: "XGBoost",
    name: "XGBoost",
    summary:
      "Combina árboles pequeños en secuencia; cada arbol intenta corregir errores del anterior.",
    training: "Se probó con learning_rate=0.08, max_depth=3 y todas las variables seleccionadas.",
    metrics: { macroF1: 0.7064, balancedAccuracy: 0.705, accuracy: 0.7093, recallHigh: 0.6981 },
    params: "learning_rate=0.08, max_depth=3, features=all",
    confusión: [
      [515, 118, 22],
      [85, 370, 133],
      [12, 173, 444],
    ],
  },
  {
    key: "Random_Forest",
    name: "Random Forest",
    summary:
      "Entrena muchos árboles de decisión y vota la clase final. Es robusto ante relaciones no lineales.",
    training: "Su mejor configuración usó max_depth=18, min_samples_leaf=1 y todas las variables.",
    metrics: { macroF1: 0.7012, balancedAccuracy: 0.7001, accuracy: 0.7052, recallHigh: 0.7017 },
    params: "max_depth=18, min_samples_leaf=1, features=all",
    confusión: [
      [520, 116, 19],
      [87, 355, 146],
      [15, 167, 447],
    ],
  },
  {
    key: "Logistic_Regression",
    name: "Regresión Logística Multinomial",
    summary:
      "Modelo lineal que aprende pesos por variable para estimar la clase. Sirve como referencia interpretable.",
    training: "Su mejor resultado se obtuvo con C=0.1 y todas las variables disponibles.",
    metrics: { macroF1: 0.6967, balancedAccuracy: 0.6971, accuracy: 0.7018, recallHigh: 0.7182 },
    params: "C=0.1, features=all",
    confusión: [
      [520, 115, 20],
      [106, 338, 144],
      [15, 159, 455],
    ],
  },
  {
    key: "MLP",
    name: "MLP",
    summary:
      "Red neuronal multicapa que aprende combinaciones no lineales. Aquí se uso una capa oculta compacta.",
    training: "Su mejor búsqueda uso alpha=0.0001, hidden_layer_sizes=[64] y selector de 10 variables.",
    metrics: { macroF1: 0.6782, balancedAccuracy: 0.6793, accuracy: 0.685, recallHigh: 0.685 },
    params: "alpha=0.0001, capa oculta=[64], features=10",
    confusión: [
      [526, 105, 24],
      [100, 321, 167],
      [23, 170, 436],
    ],
  },
];

const VARIABLE_GROUPS = [
  "Precipitación mensual",
  "Intensidad de lluvia",
  "Rachas húmedas y secas",
  "Temperatura media",
  "Humedad relativa",
  "Viento",
  "Presión atmosférica",
  "Mes objetivo",
  "Ubicación geográfica",
  "Antecedentes lag1 y lag11",
];

const LABELS = ["Baja", "Media", "Alta"];

function percent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

export function ModelsSection() {
  const [selectedKey, setSelectedKey] = useState<ModelKey>("SVM_RBF");
  const selectedModel = MODELS.find((model) => model.key === selectedKey) ?? MODELS[0];
  const maxCell = useMemo(
    () => Math.max(...selectedModel.confusión.flat()),
    [selectedModel.confusión],
  );

  return (
    <section id="modelo" aria-labelledby="modelos-titulo" className="border-t border-border">
      <div className="mx-auto w-[94vw] max-w-[1480px] px-2 py-14 sm:px-4 md:py-20">
        <div className="grid gap-8 xl:grid-cols-[0.85fr_1.15fr]">
          <div className="min-w-0">
            <h2 id="modelos-titulo" className="text-2xl font-bold text-foreground sm:text-3xl">
              Modelos utilizados
            </h2>
            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted-foreground sm:text-base">
              El proyecto compara cinco clasificadores supervisados. Selecciona un modelo para ver
              su explicación, métricas principales y matriz de confusión.
            </p>

            <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
              {MODELS.map((model) => {
                const active = model.key === selectedModel.key;
                return (
                  <button
                    key={model.key}
                    type="button"
                    className={`rounded-xl border p-4 text-left shadow-card transition-colors ${
                      active
                        ? "border-primary bg-primary text-primary-foreground"
                        : "border-border bg-card text-foreground hover:border-primary/45 hover:bg-accent/70"
                    }`}
                    onClick={() => setSelectedKey(model.key)}
                    aria-pressed={active}
                  >
                    <span className="flex items-center justify-between gap-3">
                      <span className="text-sm font-bold">{model.name}</span>
                      <span
                        className={`shrink-0 rounded-md border px-2.5 py-0.5 text-xs font-semibold ${
                          active
                            ? "border-transparent bg-secondary text-secondary-foreground"
                            : "border-border text-foreground"
                        }`}
                      >
                        {model.key === "SVM_RBF" ? "Ganador" : "Comparado"}
                      </span>
                    </span>
                    <span
                      className={`mt-1.5 block text-xs leading-relaxed ${
                        active ? "text-primary-foreground/80" : "text-muted-foreground"
                      }`}
                    >
                      Macro F1 {percent(model.metrics.macroF1)}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="min-w-0 rounded-xl border border-border bg-card p-5 shadow-lift sm:p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="text-xl font-bold text-foreground">{selectedModel.name}</h3>
                <p className="mt-1.5 max-w-3xl text-sm leading-relaxed text-muted-foreground">
                  {selectedModel.summary}
                </p>
              </div>
            </div>

            <p className="mt-4 rounded-lg border border-primary/15 bg-accent/55 p-3 text-sm leading-relaxed text-foreground">
              {selectedModel.training}
            </p>

            <dl className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <Metric label="Macro F1" value={percent(selectedModel.metrics.macroF1)} />
              <Metric
                label="Balanced accuracy"
                value={percent(selectedModel.metrics.balancedAccuracy)}
              />
              <Metric label="Accuracy" value={percent(selectedModel.metrics.accuracy)} />
              <Metric label="Recall Alta" value={percent(selectedModel.metrics.recallHigh)} />
            </dl>

            <div className="mt-6 grid gap-5 lg:grid-cols-[minmax(220px,0.55fr)_minmax(360px,1.45fr)]">
              <div className="rounded-lg border border-border bg-muted/35 p-4">
                <h4 className="text-sm font-bold text-foreground">Configuración usada</h4>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {selectedModel.params}
                </p>
              </div>

              <div className="min-w-0">
                <h4 className="text-sm font-bold text-foreground">Matriz de confusión OOF</h4>
                <p className="mt-1 text-xs text-muted-foreground">
                  Filas: clase real. Columnas: clase predicha.
                </p>
                <div className="mt-3 overflow-x-auto">
                  <table className="w-full min-w-[360px] border-separate border-spacing-1 text-center text-xs">
                    <thead>
                      <tr>
                        <th className="p-2 text-left font-semibold text-muted-foreground">
                          Real / Pred
                        </th>
                        {LABELS.map((label) => (
                          <th key={label} className="rounded-md bg-muted p-2 font-bold text-foreground">
                            {label}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {selectedModel.confusión.map((row, rowIndex) => (
                        <tr key={LABELS[rowIndex]}>
                          <th className="rounded-md bg-muted p-2 text-left font-bold text-foreground">
                            {LABELS[rowIndex]}
                          </th>
                          {row.map((value, columnIndex) => {
                            const intensity = 0.12 + (value / maxCell) * 0.78;
                            const correct = rowIndex === columnIndex;
                            return (
                              <td
                                key={`${LABELS[rowIndex]}-${LABELS[columnIndex]}`}
                                className="rounded-md p-2 font-bold"
                                style={{
                                  backgroundColor: correct
                                    ? `oklch(0.51 0.15 238 / ${intensity})`
                                    : `oklch(0.63 0.14 72 / ${Math.max(0.1, intensity * 0.48)})`,
                                  color: correct ? "var(--primary-foreground)" : "var(--foreground)",
                                }}
                              >
                                {value}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(320px,0.9fr)]">
          <div className="rounded-xl border border-border bg-card p-5 shadow-card">
            <h3 className="text-base font-bold text-foreground">Variables usadas por los modelos</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              Todos los modelos reciben la misma base de variables meteorológicas, temporales y
              geográficas; cambia el algoritmo que aprende la relación con la amenaza.
            </p>
            <ul className="mt-4 flex flex-wrap gap-2">
              {VARIABLE_GROUPS.map((variable) => (
                <li
                  key={variable}
                  className="rounded-full border border-border bg-muted/45 px-3 py-1.5 text-xs font-semibold text-secondary-foreground"
                >
                  {variable}
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-xl border border-primary/15 bg-sky-soft/70 p-5 shadow-card">
            <h3 className="text-base font-bold text-foreground">Validación temporal</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              Entrenamos con periodos históricos anteriores y validamos contra meses posteriores
              para simular un uso real: predecir el futuro sin mezclar información de adelante. En
              esa prueba, el SVM mantuvo el mejor equilibrio general con Macro F1 de 71.9%,
              balanced accuracy de 71.8% y accuracy de 72.0%.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-muted/35 p-3">
      <dt className="text-[11px] font-bold uppercase text-muted-foreground">{label}</dt>
      <dd className="mt-1 text-lg font-bold text-foreground">{value}</dd>
    </div>
  );
}
