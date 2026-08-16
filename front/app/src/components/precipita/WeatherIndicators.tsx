import {
  CloudRain,
  Droplets,
  Gauge,
  Layers,
  Thermometer,
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
      help: "Columna prcptot_mm enviada al modelo.",
    },
    {
      icon: Layers,
      label: "Precipitación máxima en cinco días",
      value: indicators.maximumFiveDayPrecipitation,
      unit: "mm",
      help: "Columna rx5day_mm enviada al modelo.",
    },
    {
      icon: Droplets,
      label: "Precipitación máxima en 3 horas",
      value: indicators.maximumThreeHourPrecipitation,
      unit: "mm",
      help: "Columna max_3h_mm enviada al modelo.",
    },
    {
      icon: Zap,
      label: "Intensidad en días lluviosos",
      value: indicators.rainfallIntensityPerWetDay,
      unit: "mm/día",
      help: "Columna sdii_mm_per_wet_day enviada al modelo.",
    },
    {
      icon: CloudRain,
      label: "Días con precipitación intensa",
      value: indicators.intenseRainDays,
      unit: "días",
      help: "Columna r20mm_days enviada al modelo.",
    },
    {
      icon: Waves,
      label: "Racha húmeda máxima",
      value: indicators.wetStreakDays,
      unit: "días",
      help: "Columna cwd_days enviada al modelo.",
    },
    {
      icon: Waves,
      label: "Racha seca máxima",
      value: indicators.dryStreakDays,
      unit: "días",
      help: "Columna cdd_days enviada al modelo.",
    },
    {
      icon: Thermometer,
      label: "Temperatura promedio",
      value: indicators.averageTemperature,
      unit: "°C",
      help: "Columna temperature_mean_c enviada al modelo.",
    },
    {
      icon: Waves,
      label: "Humedad relativa",
      value: indicators.relativeHumidity,
      unit: "%",
      help: "Columna relative_humidity_mean_pct enviada al modelo.",
    },
    {
      icon: Wind,
      label: "Velocidad promedio del viento",
      value: indicators.windSpeed,
      unit: "km/h",
      help: "Columna wind_mean_ms enviada al modelo; se muestra convertida a km/h.",
    },
    {
      icon: Gauge,
      label: "Presión atmosférica",
      value: indicators.surfacePressure,
      unit: "hPa",
      help: "Columna surface_pressure_mean_hpa enviada al modelo.",
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
