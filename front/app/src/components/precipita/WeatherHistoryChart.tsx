import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { HistoricalPoint } from "@/types/prediction";

interface WeatherHistoryChartProps {
  series: HistoricalPoint[];
  referenceMonth: string;
}

export function WeatherHistoryChart({ series, referenceMonth }: WeatherHistoryChartProps) {
  return (
    <div className="rounded-xl border border-border bg-card p-4 shadow-card sm:p-5">
      <h4 className="text-base font-bold text-foreground">
        Comportamiento reciente de la precipitación
      </h4>
      <p className="mt-1 text-xs text-muted-foreground">
        Precipitación acumulada mensual. La barra destacada corresponde al mes de referencia (
        {referenceMonth}).
      </p>

      <div className="mt-4 h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={series} margin={{ top: 8, right: 4, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis
              dataKey="month"
              tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
              axisLine={{ stroke: "var(--border)" }}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              width={40}
              tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
              axisLine={false}
              tickLine={false}
              label={{
                value: "mm",
                angle: -90,
                position: "insideLeft",
                style: { fontSize: 10, fill: "var(--muted-foreground)" },
              }}
            />
            <Tooltip
              contentStyle={{
                borderRadius: 10,
                border: "1px solid var(--border)",
                background: "var(--popover)",
                fontSize: 12,
              }}
              formatter={(value) => [`${value} mm`, "Precipitación"]}
            />
            <Bar dataKey="precipitation" radius={[5, 5, 0, 0]}>
              {series.map((point) => (
                <Cell
                  key={point.month}
                  fill={point.isReference ? "var(--primary)" : "var(--sky-accent)"}
                  opacity={point.isReference ? 1 : 0.65}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
