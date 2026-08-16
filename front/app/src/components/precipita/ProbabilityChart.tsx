import { THREAT_CONFIG } from "@/lib/threat";
import type { ThreatLevel } from "@/types/prediction";

interface ProbabilityChartProps {
  probabilities: { low: number; medium: number; high: number };
  selectedLevel: ThreatLevel;
}

export function ProbabilityChart({ probabilities, selectedLevel }: ProbabilityChartProps) {
  const data = [
    { level: "Baja" as ThreatLevel, value: probabilities.low },
    { level: "Media" as ThreatLevel, value: probabilities.medium },
    { level: "Alta" as ThreatLevel, value: probabilities.high },
  ];

  return (
    <div className="mt-3">
      <ul className="space-y-3">
        {data.map((item) => {
          const config = THREAT_CONFIG[item.level];
          const isSelected = item.level === selectedLevel;
          return (
            <li key={item.level}>
              <div className="flex items-center justify-between gap-3">
                <span className="flex min-w-0 items-center gap-2 text-sm font-semibold text-foreground">
                  <span aria-hidden="true" className={`size-2.5 shrink-0 rounded-full ${config.dot}`} />
                  <span className="truncate">{config.label}</span>
                  {isSelected ? (
                    <span className="shrink-0 rounded-full border border-border bg-muted px-2 py-0.5 text-[10px] font-bold uppercase text-muted-foreground">
                      Estimada
                    </span>
                  ) : null}
                </span>
                <span className={`shrink-0 text-sm font-bold ${config.text}`}>{item.value} %</span>
              </div>
              <div
                className="mt-1.5 h-2.5 w-full overflow-hidden rounded-full bg-muted"
                role="meter"
                aria-label={`Probabilidad de ${config.label}`}
                aria-valuenow={item.value}
                aria-valuemin={0}
                aria-valuemax={100}
              >
                <div
                  className={`h-full rounded-full transition-[width] duration-700 ${config.dot}`}
                  style={{ width: `${item.value}%` }}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
