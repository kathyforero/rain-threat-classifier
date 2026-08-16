import { RotateCcw, TriangleAlert } from "lucide-react";

import { Button } from "@/components/ui/button";

interface ErrorStateProps {
  onRetry: () => void;
}

export function ErrorState({ onRetry }: ErrorStateProps) {
  return (
    <section
      role="alert"
      className="rounded-xl border border-threat-high/35 bg-threat-high-soft p-5 shadow-card sm:p-6"
    >
      <div className="flex items-start gap-3">
        <TriangleAlert aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-threat-high" />
        <div className="min-w-0">
          <h3 className="text-base font-bold text-foreground">Consulta no completada</h3>
          <p className="mt-2 text-sm leading-relaxed text-foreground/90">
            No fue posible completar la consulta. Intenta nuevamente.
          </p>
          <Button variant="outline" className="mt-4" onClick={onRetry}>
            <RotateCcw aria-hidden="true" />
            <span>Reintentar</span>
          </Button>
        </div>
      </div>
    </section>
  );
}
