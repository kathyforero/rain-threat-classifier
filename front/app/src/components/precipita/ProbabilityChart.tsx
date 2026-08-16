import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, XAxis, YAxis } from "recharts";

import { THREAT_CONFIG } from "@/lib/threat";
import type { ThreatLevel } from "@/types/prediction";

interface ProbabilityChartProps {
  probabilities: { low: number; medium: number; high: number };
  selectedLevel: ThreatLevel;
}

export function ProbabilityChart({ probabilities, selectedLevel }: ProbabilityChartProps) {
  const data = [
    { level: "Baja" as ThreatLevel, name: "Amenaza Baja", value: probabilities.low },
    { level: "Media" as ThreatLevel, name: "Amenaza Media", value: probabilities.medium },
    { level: "Alta" as ThreatLevel, name: "Amenaza Alta", value: probabilities.high },
  ];

  return (
    <div className="mt-3">
      {/* Barras accesibles con texto: no dependen solo del color */}
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

      <div className="mt-5 h-40 w-full" aria-hidden="true">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 18, right: 8, left: 0, bottom: 0 }}>
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              axisLine={{ stroke: "var(--border)" }}
              tickLine={false}
            />
            <YAxis
              domain={[0, 100]}
              width={34}
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              axisLine={false}
              tickLine={false}
              unit="%"
            />
            <Bar dataKey="value" radius={[6, 6, 0, 0]} isAnimationActive>
              <LabelList
                dataKey="value"
                position="top"
                formatter={(value: number) => `${value} %`}
                style={{ fontSize: 11, fontWeight: 700, fill: "var(--foreground)" }}
              />
              {data.map((item) => (
                <Cell key={item.level} fill={THREAT_CONFIG[item.level].chartColor} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        Las tres probabilidades suman 100 % y la categoría estimada corresponde a la de mayor valor.
      </p>
    </div>
  );
}
