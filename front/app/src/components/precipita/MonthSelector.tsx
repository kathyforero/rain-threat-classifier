import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatMonth, getAvailableReferenceMonths, getTargetMonth } from "@/lib/threat";

interface MonthSelectorProps {
  value: string | null;
  onChange: (month: string) => void;
}

const MONTHS = getAvailableReferenceMonths();

export function MonthSelector({ value, onChange }: MonthSelectorProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor="month-selector" className="text-sm font-semibold">
        Mes de referencia
      </Label>
      <Select {...(value ? { value } : {})} onValueChange={onChange}>
        <SelectTrigger id="month-selector" className="min-h-11 w-full">
          <SelectValue placeholder="Selecciona un mes" />
        </SelectTrigger>
        <SelectContent className="max-h-72">
          {MONTHS.map((month) => (
            <SelectItem key={month} value={month}>
              {formatMonth(month)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <p className="text-xs leading-relaxed text-muted-foreground">
        El sistema estimará el nivel de amenaza meteorológica correspondiente al mes siguiente.
      </p>
      {value ? (
        <div className="rounded-lg border border-border bg-sky-soft px-3 py-2">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Mes objetivo
          </p>
          <p className="text-sm font-bold text-foreground">{formatMonth(getTargetMonth(value))}</p>
        </div>
      ) : null}
    </div>
  );
}
