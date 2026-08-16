import { FileQuestion } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { PredictionResult } from "@/types/prediction";

interface InsufficientDataStateProps {
  result: PredictionResult;
  onModifyQuery: () => void;
}

export function InsufficientDataState({ result, onModifyQuery }: InsufficientDataStateProps) {
  return (
    <section
      aria-labelledby="sin-datos-titulo"
      className="rounded-2xl border border-border bg-card p-5 shadow-card sm:p-6"
    >
      <div className="flex items-start gap-3">
        <FileQuestion aria-hidden="true" className="mt-0.5 size-6 shrink-0 text-muted-foreground" />
        <div className="min-w-0">
          <h3 id="sin-datos-titulo" className="text-lg font-bold text-foreground">
            Antecedentes insuficientes
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-foreground/90">
            No existen antecedentes meteorológicos suficientes para generar una clasificación
            confiable para la ciudad y el periodo seleccionados.
          </p>
        </div>
      </div>

      <dl className="mt-5 grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-border bg-muted/50 p-3">
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Ciudad seleccionada
          </dt>
          <dd className="text-sm font-bold text-foreground">
            {result.city} — {result.province}
          </dd>
        </div>
        <div className="rounded-xl border border-border bg-muted/50 p-3">
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Período consultado
          </dt>
          <dd className="text-sm font-bold text-foreground">{result.referenceMonth}</dd>
        </div>
      </dl>

      <Button className="mt-5 w-full sm:w-auto" onClick={onModifyQuery}>
        Modificar consulta
      </Button>
    </section>
  );
}
