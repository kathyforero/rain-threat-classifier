import { useMemo, useState } from "react";
import { ArrowLeft } from "lucide-react";

import { CityMarker } from "@/components/precipita/CityMarker";
import { CityTooltip } from "@/components/precipita/CityTooltip";
import { Button } from "@/components/ui/button";
import { CITIES, getCityById } from "@/data/cities";
import {
  CONTINENTAL_PROVINCES,
  MAP_HEIGHT,
  MAP_WIDTH,
  projectPoint,
} from "@/data/ecuadorMap";

interface EcuadorMapProps {
  selectedCityId: string | null;
  onSelectCity: (cityId: string) => void;
  onResetView: () => void;
  variant?: "card" | "hero";
}

const ZOOM = 1.9;
const VIEWBOX_PAD_X = 150;
const VIEWBOX_PAD_Y = 70;
const VIEWBOX_WIDTH = MAP_WIDTH + VIEWBOX_PAD_X * 2;
const VIEWBOX_HEIGHT = MAP_HEIGHT + VIEWBOX_PAD_Y * 2;

// Ajuste visual de marcadores: algunas ciudades reales caen cerca de fronteras/costa.
// En el mapa interactivo las movemos hacia el interior de su provincia para evitar lecturas ambiguas.
const MARKER_VISUAL_OFFSET: Record<string, { x: number; y: number }> = {
  babahoyo: { x: 0, y: -16 },
  cuenca: { x: 0, y: 12 },
  esmeraldas: { x: 18, y: 18 },
  guayaquil: { x: 0, y: -16 },
  loja: { x: -26, y: -2 },
  machala: { x: 26, y: 18 },
  puyo: { x: 46, y: 8 },
  salinas: { x: 42, y: -12 },
  tena: { x: 0, y: -16 },
};

function getMarkerPoint(city: (typeof CITIES)[number]) {
  const point = projectPoint(city.longitude, city.latitude);
  const offset = MARKER_VISUAL_OFFSET[city.id] ?? { x: 0, y: 0 };
  return {
    x: point.x + offset.x,
    y: point.y + offset.y,
  };
}

export function EcuadorMap({
  selectedCityId,
  onSelectCity,
  onResetView,
  variant = "card",
}: EcuadorMapProps) {
  const [hoveredCityId, setHoveredCityId] = useState<string | null>(null);

  const selectedCity = getCityById(selectedCityId);
  const hoveredCity = getCityById(hoveredCityId);

  const markers = useMemo(() => CITIES.map((city) => ({ city, ...getMarkerPoint(city) })), []);

  // Centrado visual sobre la ciudad seleccionada (transform animado por CSS).
  const view = useMemo(() => {
    if (!selectedCity) return { scale: 1, tx: 0, ty: 0 };
    const { x, y } = getMarkerPoint(selectedCity);
    return {
      scale: ZOOM,
      tx: VIEWBOX_WIDTH / 2 - VIEWBOX_PAD_X - x * ZOOM,
      ty: VIEWBOX_HEIGHT / 2 - VIEWBOX_PAD_Y - y * ZOOM,
    };
  }, [selectedCity]);

  const activeCity = hoveredCity ?? null;
  const activeMarker = activeCity
    ? markers.find((m) => m.city.id === activeCity.id)
    : undefined;

  return (
    <div className={variant === "hero" ? "absolute inset-0" : "relative"}>
      <div
        className={
          variant === "hero"
            ? "absolute inset-0 overflow-hidden bg-sky-soft"
            : "relative overflow-hidden rounded-xl border border-border bg-card shadow-card"
        }
      >
        {selectedCity ? (
          <Button
            type="button"
            size="sm"
            variant="secondary"
            className={
              variant === "hero"
                ? "absolute left-4 top-[76px] z-20 border border-primary/20 bg-card/95 text-primary shadow-lift hover:bg-accent"
                : "absolute left-4 top-4 z-20 border border-primary/20 bg-card/95 text-primary shadow-lift hover:bg-accent"
            }
            onClick={onResetView}
          >
            <ArrowLeft aria-hidden="true" />
            <span>Retroceder</span>
          </Button>
        ) : null}
        <svg
          viewBox={`${-VIEWBOX_PAD_X} ${-VIEWBOX_PAD_Y} ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
          preserveAspectRatio="xMidYMid meet"
          className={
            variant === "hero"
              ? selectedCity
                ? "absolute left-[-24vw] top-[-90px] h-[132%] w-[112vw] max-w-none touch-manipulation select-none lg:left-[-20vw] lg:w-[106vw]"
                : "absolute left-[-9vw] top-[-40px] h-[118%] w-[78vw] max-w-none touch-manipulation select-none lg:left-[-7vw] lg:w-[72vw]"
              : "h-[56vh] min-h-[360px] max-h-[560px] w-full touch-manipulation select-none"
          }
          role="group"
          aria-label="Mapa interactivo del Ecuador con las provincias de referencia y ciudades disponibles para consulta"
          onClick={() => setHoveredCityId(null)}
        >
          <title>Mapa del Ecuador con ciudades disponibles para consulta</title>
          <rect
            x={-VIEWBOX_PAD_X}
            y={-VIEWBOX_PAD_Y}
            width={VIEWBOX_WIDTH}
            height={VIEWBOX_HEIGHT}
            fill="var(--sky-soft)"
          />

          <g
            style={{
              transform: `translate(${view.tx}px, ${view.ty}px) scale(${view.scale})`,
              transition: "transform 600ms cubic-bezier(0.4, 0, 0.2, 1)",
            }}
          >
            {CONTINENTAL_PROVINCES.map((province) => {
              const isSelectedProvince = selectedCity?.province === province.name;
              return (
                <path
                  key={province.name}
                  d={province.d}
                  aria-hidden="true"
                  pointerEvents="none"
                  fill={isSelectedProvince ? "var(--accent)" : "var(--card)"}
                  stroke={isSelectedProvince ? "var(--primary)" : "oklch(0.62 0.025 252)"}
                  strokeWidth={isSelectedProvince ? 2 : 1}
                  vectorEffect="non-scaling-stroke"
                  className="transition-colors"
                />
              );
            })}

            {markers.map(({ city, x, y }) => (
              <CityMarker
                key={city.id}
                city={city}
                x={x}
                y={y}
                scale={view.scale}
                selected={selectedCityId === city.id}
                onSelect={(id) => {
                  setHoveredCityId(null);
                  onSelectCity(id);
                }}
                onHoverChange={setHoveredCityId}
              />
            ))}

            {activeMarker && activeCity ? (
              <CityTooltip
                x={activeMarker.x}
                y={activeMarker.y}
                cityName={activeCity.name}
                province={activeCity.province}
                scale={view.scale}
                mapWidth={MAP_WIDTH}
              />
            ) : null}
          </g>
        </svg>
      </div>
    </div>
  );
}
