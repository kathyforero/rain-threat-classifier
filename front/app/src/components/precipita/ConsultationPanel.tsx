import { RotateCcw, Search } from "lucide-react";

import { CitySelector } from "@/components/precipita/CitySelector";
import { MonthSelector } from "@/components/precipita/MonthSelector";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import type { QueryStatus } from "@/components/precipita/useConsultation";
import { getCityById } from "@/data/cities";

interface ConsultationPanelProps {
  selectedCityId: string | null;
  referenceMonth: string | null;
  status: QueryStatus;
  onCityChange: (cityId: string) => void;
  onCityClear: () => void;
  onMonthChange: (month: string) => void;
  onSubmit: () => void;
}

export function ConsultationPanel({
  selectedCityId,
  referenceMonth,
  status,
  onCityChange,
  onCityClear,
  onMonthChange,
  onSubmit,
}: ConsultationPanelProps) {
  const city = getCityById(selectedCityId);
  const isComplete = Boolean(city && referenceMonth);
  const isLoading = status === "loading";

  const hint = !city
    ? "Selecciona una ciudad para comenzar."
    : !referenceMonth
      ? "Selecciona un mes de referencia."
      : "Datos listos para estimar.";

  return (
    <div className="rounded-xl border border-border bg-card/95 p-4 shadow-lift backdrop-blur">
      <h2 className="text-lg font-bold text-foreground">Selector de consulta</h2>
      <p className="mt-1 text-sm text-muted-foreground">{hint}</p>

      <form
        className="mt-4 space-y-4"
        onSubmit={(event) => {
          event.preventDefault();
          if (isComplete && !isLoading) onSubmit();
        }}
      >
        <div className="space-y-2">
          <Label htmlFor="city-selector" className="text-sm font-semibold">
            Ciudad
          </Label>
          <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_98px] sm:items-center">
            <CitySelector value={selectedCityId} onChange={onCityChange} showLabel={false} />
            <Button
              type="button"
              variant="outline"
              className="h-11 w-full px-3 text-sm leading-none"
              disabled={!city || isLoading}
              onClick={onCityClear}
            >
              <RotateCcw aria-hidden="true" />
              <span>Limpiar</span>
            </Button>
          </div>
        </div>

        <MonthSelector value={referenceMonth} onChange={onMonthChange} />

        <MapLegend />

        <Button type="submit" size="lg" className="w-full" disabled={!isComplete || isLoading}>
          <Search aria-hidden="true" />
          <span>{isLoading ? "Estimando..." : "Estimar amenaza"}</span>
        </Button>
        {!isComplete ? (
          <p className="text-xs text-muted-foreground" role="note">
            El botón se habilita cuando hayas seleccionado una ciudad y un mes valido.
          </p>
        ) : null}
      </form>
    </div>
  );
}

function MapLegend() {
  return (
    <ul className="rounded-lg border border-primary/15 bg-accent/60 p-3 text-xs font-medium text-foreground">
      <li className="flex items-center gap-2">
        <span aria-hidden="true" className="size-2.5 rounded-full bg-sky-accent" />
        Punto azul: ciudad disponible
      </li>
      <li className="mt-2 flex items-center gap-2">
        <span aria-hidden="true" className="size-3.5 rounded-full bg-primary ring-4 ring-accent" />
        Punto azul destacado: ciudad seleccionada
      </li>
      <li className="mt-2 flex items-center gap-2">
        <span aria-hidden="true" className="h-0 w-5 border-t-2 border-slate-400" />
        Límites grises: provincias de referencia
      </li>
    </ul>
  );
}
