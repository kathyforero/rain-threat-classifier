import type { City } from "@/types/prediction";

interface CityMarkerProps {
  city: City;
  x: number;
  y: number;
  selected: boolean;
  scale: number;
  onSelect: (cityId: string) => void;
  onHoverChange: (cityId: string | null) => void;
}

export function CityMarker({
  city,
  x,
  y,
  selected,
  scale,
  onSelect,
  onHoverChange,
}: CityMarkerProps) {
  const inv = 1 / scale;

  return (
    <g
      transform={`translate(${x} ${y}) scale(${inv})`}
      role="button"
      tabIndex={0}
      aria-pressed={selected}
      aria-label={`Seleccionar ${city.name}, provincia de ${city.province}`}
      className="cursor-pointer outline-none [&:focus-visible_.marker-ring]:opacity-100"
      onClick={(event) => {
        event.stopPropagation();
        onSelect(city.id);
      }}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect(city.id);
        }
      }}
      onMouseEnter={() => onHoverChange(city.id)}
      onMouseLeave={() => onHoverChange(null)}
      onFocus={() => onHoverChange(city.id)}
      onBlur={() => onHoverChange(null)}
    >
      {/* Área de toque amplia para dispositivos móviles */}
      <circle r={20} fill="transparent" />
      <circle
        className="marker-ring opacity-0 transition-opacity"
        r={17}
        fill="none"
        stroke="var(--ring)"
        strokeWidth={2.5}
      />
      {selected ? <circle r={14} fill="var(--sky-accent)" opacity={0.28} /> : null}
      <circle
        r={selected ? 9 : 6.5}
        fill={selected ? "var(--primary)" : "var(--sky-accent)"}
        stroke="var(--card)"
        strokeWidth={2.5}
        className="transition-all"
      />
      {selected ? (
        <>
          <rect x={-54} y={-42} width={108} height={23} rx={11.5} fill="var(--primary)" />
          <text
            x={0}
            y={-26}
            textAnchor="middle"
            fontSize={12}
            fontWeight={700}
            fill="var(--primary-foreground)"
          >
            {city.name}
          </text>
        </>
      ) : null}
    </g>
  );
}
