import type { ThreatLevel } from "@/types/prediction";

export const MONTH_NAMES = [
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre",
] as const;

/** "2025-11" -> "Noviembre de 2025" */
function parse(value: string): { year: number; month: number } | null {
  const parts = value.split("-");
  const year = Number(parts[0]);
  const month = Number(parts[1]);
  if (!year || !month || month < 1 || month > 12) return null;
  return { year, month };
}

export function formatMonth(value: string): string {
  const p = parse(value);
  if (!p) return value;
  return `${MONTH_NAMES[p.month - 1]!} de ${p.year}`;
}

/** "2025-11" -> "Nov 25" (etiquetas compactas para gráficos) */
export function formatMonthShort(value: string): string {
  const p = parse(value);
  if (!p) return value;
  return `${MONTH_NAMES[p.month - 1]!.slice(0, 3)} ${String(p.year).slice(2)}`;
}

/** Mes siguiente al mes de referencia. "2025-12" -> "2026-01" */
export function getTargetMonth(value: string): string {
  const p = parse(value);
  if (!p) return value;
  const next = p.month === 12 ? 1 : p.month + 1;
  const nextYear = p.month === 12 ? p.year + 1 : p.year;
  return `${nextYear}-${String(next).padStart(2, "0")}`;
}

export function addMonths(value: string, delta: number): string {
  const p = parse(value);
  if (!p) return value;
  const total = p.year * 12 + (p.month - 1) + delta;
  const y = Math.floor(total / 12);
  const m = (total % 12) + 1;
  return `${y}-${String(m).padStart(2, "0")}`;
}

/** Meses de referencia disponibles: enero 2020 – diciembre 2025 (más recientes primero). */
export function getAvailableReferenceMonths(): string[] {
  const months: string[] = [];
  for (let total = 2025 * 12 + 11; total >= 2020 * 12; total--) {
    const year = Math.floor(total / 12);
    const month = (total % 12) + 1;
    months.push(`${year}-${String(month).padStart(2, "0")}`);
  }
  return months;
}

/** Meses objetivo disponibles: febrero 2020 – enero 2026 (más recientes primero). */
export function getAvailableTargetMonths(): string[] {
  return getAvailableReferenceMonths().map((month) => addMonths(month, 1));
}

export interface ThreatStyleConfig {
  level: ThreatLevel;
  label: string;
  description: string;
  /** clases de token semántico */
  text: string;
  bg: string;
  border: string;
  dot: string;
  chartColor: string;
}

export const THREAT_CONFIG: Record<ThreatLevel, ThreatStyleConfig> = {
  Baja: {
    level: "Baja",
    label: "Amenaza Baja",
    description:
      "Las condiciones estimadas se encuentran dentro de un nivel bajo de amenaza meteorológica asociada con la precipitación.",
    text: "text-threat-low",
    bg: "bg-threat-low-soft",
    border: "border-threat-low/35",
    dot: "bg-threat-low",
    chartColor: "var(--threat-low)",
  },
  Media: {
    level: "Media",
    label: "Amenaza Media",
    description:
      "Las condiciones estimadas indican un nivel medio de amenaza meteorológica asociada con la precipitación.",
    text: "text-threat-medium",
    bg: "bg-threat-medium-soft",
    border: "border-threat-medium/35",
    dot: "bg-threat-medium",
    chartColor: "var(--threat-medium)",
  },
  Alta: {
    level: "Alta",
    label: "Amenaza Alta",
    description:
      "Las condiciones estimadas indican un nivel alto de amenaza meteorológica asociada con la precipitación.",
    text: "text-threat-high",
    bg: "bg-threat-high-soft",
    border: "border-threat-high/35",
    dot: "bg-threat-high",
    chartColor: "var(--threat-high)",
  },
};
