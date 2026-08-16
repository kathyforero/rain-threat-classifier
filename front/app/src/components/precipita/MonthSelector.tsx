import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { addMonths, getAvailableTargetMonths, MONTH_NAMES } from "@/lib/threat";

interface MonthSelectorProps {
  value: string | null;
  onChange: (month: string) => void;
}

const TARGET_MONTHS = getAvailableTargetMonths();
const MONTHS_BY_YEAR = TARGET_MONTHS.reduce<Record<string, string[]>>((acc, month) => {
  const [year] = month.split("-");
  if (!year) return acc;
  acc[year] ??= [];
  acc[year]!.push(month);
  return acc;
}, {});

const YEARS = Object.keys(MONTHS_BY_YEAR).sort((a, b) => Number(b) - Number(a));

function monthNumber(value: string | null): string | null {
  return value?.split("-")[1] ?? null;
}

function yearNumber(value: string | null): string | null {
  return value?.split("-")[0] ?? null;
}

function toReferenceMonth(targetMonth: string): string {
  return addMonths(targetMonth, -1);
}

export function MonthSelector({ value, onChange }: MonthSelectorProps) {
  const selectedTargetMonth = value ? addMonths(value, 1) : null;
  const selectedYear = yearNumber(selectedTargetMonth);
  const selectedMonth = monthNumber(selectedTargetMonth);
  const availableMonths = selectedYear ? (MONTHS_BY_YEAR[selectedYear] ?? []) : [];

  const handleYearChange = (year: string) => {
    const monthsForYear = MONTHS_BY_YEAR[year] ?? [];
    const sameMonth = selectedMonth
      ? monthsForYear.find((month) => month.endsWith(`-${selectedMonth}`))
      : null;
    const nextTargetMonth = sameMonth ?? monthsForYear[0];
    if (nextTargetMonth) onChange(toReferenceMonth(nextTargetMonth));
  };

  const handleMonthChange = (month: string) => {
    if (!selectedYear) return;
    onChange(toReferenceMonth(`${selectedYear}-${month}`));
  };

  return (
    <div className="space-y-2">
      <Label className="text-sm font-semibold">Mes a predecir</Label>
      <div className="flex gap-2">
        <Select {...(selectedYear ? { value: selectedYear } : {})} onValueChange={handleYearChange}>
          <SelectTrigger className="min-h-11 w-[42%]" aria-label="Año a predecir">
            <SelectValue placeholder="Año" />
          </SelectTrigger>
          <SelectContent>
            {YEARS.map((year) => (
              <SelectItem key={year} value={year}>
                {year}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          {...(selectedMonth ? { value: selectedMonth } : {})}
          onValueChange={handleMonthChange}
          disabled={!selectedYear}
        >
          <SelectTrigger className="min-h-11 flex-1" aria-label="Mes a predecir">
            <SelectValue placeholder="Mes" />
          </SelectTrigger>
          <SelectContent>
            {availableMonths.map((month) => {
              const monthValue = month.split("-")[1]!;
              const monthIndex = Number(monthValue) - 1;
              return (
                <SelectItem key={month} value={monthValue}>
                  {MONTH_NAMES[monthIndex]}
                </SelectItem>
              );
            })}
          </SelectContent>
        </Select>
      </div>

      <p className="text-xs leading-relaxed text-muted-foreground">
        La API usará como entrada los datos observados del mes anterior.
      </p>
    </div>
  );
}
