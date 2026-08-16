import {
  CloudRain,
  Droplets,
  Gauge,
  Layers,
  Thermometer,
  Umbrella,
  Waves,
  Wind,
  Zap,
} from "lucide-react";

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { WeatherIndicatorsData } from "@/types/prediction";

interface WeatherIndicatorsProps {
  indicators: WeatherIndicatorsData;
}

export function WeatherIndicators({ indicators }: WeatherIndicatorsProps) {
  const items = [
    {
      icon: CloudRain,
      label: "Precipitación acumulada mensual",
      value: indicators.accumulatedPrecipitation,
      unit: "mm",
      help: "Suma de la precipitación registrada durante el mes de referencia.",
    },
    {
      icon: Droplets,
      label: "Precipitación máxima en un día",
      value: indicators.maximumDailyPrecipitation,
      unit: "mm",
      help: "Mayor cantidad de lluvia registrada en un solo día del mes.",
    },
    {
      icon: Layers,
      label: "Precipitación máxima en cinco días",
      value: indicators.maximumFiveDayPrecipitation,
      unit: "mm",
      help: "Mayor acumulado en cinco días consecutivos; refleja la persistencia de la lluvia.",
    },
    {
      icon: Umbrella,
      label: "Días con lluvia",
      value: indicators.rainyDays,
      unit: "días",
      help: "Días del mes con precipitación registrada.",
    },
    {
      icon: Zap,
      label: "Días con precipitación intensa",
      value: indicators.intenseRainDays,
      unit: "días",
      help: "Días en los que la lluvia superó el umbral de intensidad considerado por el modelo.",
    },
    {
      icon: Thermometer,
      label: "Temperatura promedio",
      value: indicators.averageTemperature,
      unit: "°C",
      help: "Promedio mensual de temperatura del aire.",
    },
    {
      icon: Waves,
      label: "Humedad relativa",
      value: indicators.relativeHumidity,
      unit: "%",
      help: "Promedio mensual de humedad relativa.",
    },
    {
      icon: Wind,
      label: "Velocidad promedio del viento",
      value: indicators.windSpeed,
      unit: "km/h",
      help: "Promedio mensual de velocidad del viento en superficie.",
    },
    {
      icon: Gauge,
      label: "Presión atmosférica",
      value: indicators.surfacePressure,
      unit: "hPa",
      help: "Presión en superficie; varía según la altitud de la ciudad.",
    },
  ];

  return (
    <TooltipProvider delayDuration={150}>
      <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {items.map(({ icon: Icon, label, value, unit, help }) => (
          <li key={label} className="rounded-xl border border-border bg-card p-4 shadow-card">
            <div className="flex items-start justify-between gap-2">
              <Icon aria-hidden="true" className="size-4 shrink-0 text-sky-accent" />
              <Tooltip>
                <TooltipTrigger
                  className="rounded-full border border-border px-1.5 text-[10px] font-bold text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  aria-label={`Información sobre ${label}`}
                >
                  ?
                </TooltipTrigger>
                <TooltipContent className="max-w-56 text-xs">{help}</TooltipContent>
              </Tooltip>
            </div>
            <p className="mt-2 text-sm font-medium leading-snug text-muted-foreground">{label}</p>
            <p className="mt-1 text-xl font-bold text-foreground">
              {value}
              <span className="ml-1 text-sm font-semibold text-muted-foreground">{unit}</span>
            </p>
          </li>
        ))}
      </ul>
    </TooltipProvider>
  );
}
