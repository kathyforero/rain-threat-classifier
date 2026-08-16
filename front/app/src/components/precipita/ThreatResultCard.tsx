import { CheckCircle2, ShieldAlert, TriangleAlert } from "lucide-react";

import { ProbabilityChart } from "@/components/precipita/ProbabilityChart";
import { Badge } from "@/components/ui/badge";
import { THREAT_CONFIG } from "@/lib/threat";
import type { PredictionResult, ThreatLevel } from "@/types/prediction";

const ICONS: Record<ThreatLevel, typeof CheckCircle2> = {
  Baja: CheckCircle2,
  Media: TriangleAlert,
  Alta: ShieldAlert,
};

interface ThreatResultCardProps {
  result: PredictionResult;
}

export function ThreatResultCard({ result }: ThreatResultCardProps) {
  if (!result.threatLevel || !result.probabilities) return null;
  const config = THREAT_CONFIG[result.threatLevel];
  const Icon = ICONS[result.threatLevel];

  return (
    <article
      className="rounded-xl border border-border bg-card p-5 shadow-lift sm:p-6"
      aria-label="Resultado de la clasificación"
    >
      <header className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-4 sm:flex sm:flex-wrap sm:justify-between">
        <div className="min-w-0">
          <h3 className="truncate text-xl font-bold text-foreground sm:text-2xl">{result.city}</h3>
          <p className="text-sm text-muted-foreground">Provincia de {result.province}</p>
        </div>
        <Badge variant="secondary" className="shrink-0">
          Resultado estimado
        </Badge>
      </header>

      <dl className="mt-5 grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-border bg-muted/50 p-3">
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Período consultado
          </dt>
          <dd className="text-sm font-bold text-foreground">{result.referenceMonth}</dd>
        </div>
        <div className="rounded-xl border border-border bg-muted/50 p-3">
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Estimación para
          </dt>
          <dd className="text-sm font-bold text-foreground">{result.targetMonth}</dd>
        </div>
      </dl>

      <div
        className={`mt-4 rounded-xl border p-4 ${config.bg} ${config.border}`}
        role="group"
        aria-label={`Nivel estimado: ${config.label}`}
      >
        <div className="flex items-start gap-3">
          <Icon aria-hidden="true" className={`mt-0.5 size-6 shrink-0 ${config.text}`} />
          <div className="min-w-0">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              Nivel estimado
            </p>
            <p className={`text-lg font-bold sm:text-xl ${config.text}`}>{config.label}</p>
            <p className="mt-2 text-sm leading-relaxed text-foreground/90">{config.description}</p>
          </div>
        </div>
        {typeof result.confidence === "number" ? (
          <p className="mt-3 border-t border-border/60 pt-3 text-sm text-muted-foreground">
            Nivel de confianza de la categoría estimada:{" "}
            <span className="font-bold text-foreground">{result.confidence} %</span>
          </p>
        ) : null}
      </div>

      <div className="mt-6">
        <h4 className="text-base font-bold text-foreground">Probabilidades por categoría</h4>
        <ProbabilityChart probabilities={result.probabilities} selectedLevel={result.threatLevel} />
      </div>
    </article>
  );
}
