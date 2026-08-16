interface CityTooltipProps {
  x: number;
  y: number;
  cityName: string;
  province: string;
  scale: number;
  mapWidth: number;
}

/** Tooltip dibujado dentro del SVG: funciona con mouse, teclado y pantallas táctiles. */
export function CityTooltip({ x, y, cityName, province, scale, mapWidth }: CityTooltipProps) {
  const inv = 1 / scale;
  const width = 276;
  const height = 104;
  const placeLeft = x + (22 + width) * inv > mapWidth;
  const offsetX = placeLeft ? -(22 + width) * inv : 22 * inv;

  return (
    <g transform={`translate(${x + offsetX} ${y - (height * inv) / 2})`} pointerEvents="none">
      <g transform={`scale(${inv})`}>
        <rect
          x={0}
          y={0}
          width={width}
          height={height}
          rx={12}
          fill="var(--popover)"
          stroke="var(--border)"
          strokeWidth={1.5}
        />
        <text x={18} y={32} fontSize={20} fontWeight={800} fill="var(--foreground)">
          {cityName}
        </text>
        <text x={18} y={58} fontSize={15} fill="var(--muted-foreground)">
          Provincia de {province}
        </text>
        <text x={18} y={84} fontSize={14} fontWeight={700} fill="var(--sky-accent)">
          Zona disponible para consulta
        </text>
      </g>
    </g>
  );
}
