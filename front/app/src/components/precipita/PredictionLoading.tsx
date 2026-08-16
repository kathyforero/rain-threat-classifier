import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";

const STEPS = [
  "Consultando antecedentes meteorológicos",
  "Verificando disponibilidad de información",
  "Preparando variables climáticas",
  "Ejecutando clasificación",
  "Calculando probabilidades",
];

export function PredictionLoading() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setStep((current) => (current < STEPS.length - 1 ? current + 1 : current));
    }, 320);
    return () => window.clearInterval(interval);
  }, []);

  const progress = Math.round(((step + 1) / STEPS.length) * 100);

  return (
    <div
      className="rounded-xl border border-border bg-card p-5 shadow-card sm:p-6"
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center gap-3">
        <Loader2 aria-hidden="true" className="size-5 animate-spin text-primary" />
        <p className="text-sm font-semibold text-foreground">Procesando la consulta</p>
      </div>

      <Progress value={progress} className="mt-4" aria-label="Progreso del procesamiento" />

      <ol className="mt-4 space-y-2">
        {STEPS.map((label, index) => (
          <li
            key={label}
            className={
              index <= step
                ? "flex items-center gap-2 text-sm text-foreground"
                : "flex items-center gap-2 text-sm text-muted-foreground"
            }
          >
            <span
              aria-hidden="true"
              className={
                index < step
                  ? "size-2 shrink-0 rounded-full bg-primary"
                  : index === step
                    ? "size-2 shrink-0 animate-pulse rounded-full bg-sky-accent"
                    : "size-2 shrink-0 rounded-full bg-border"
              }
            />
            <span className="min-w-0">{label}</span>
          </li>
        ))}
      </ol>

      <div className="mt-6 space-y-3" aria-hidden="true">
        <Skeleton className="h-6 w-2/3" />
        <Skeleton className="h-24 w-full" />
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      </div>
    </div>
  );
}
