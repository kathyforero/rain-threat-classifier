import { CITIES } from "@/data/cities";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface CitySelectorProps {
  value: string | null;
  onChange: (cityId: string) => void;
  showLabel?: boolean;
}

export function CitySelector({ value, onChange, showLabel = true }: CitySelectorProps) {
  return (
    <div className="space-y-2">
      {showLabel ? (
        <Label htmlFor="city-selector" className="text-sm font-semibold">
          Ciudad
        </Label>
      ) : null}
      <Select {...(value ? { value } : {})} onValueChange={onChange}>
        <SelectTrigger id="city-selector" className="min-h-11 w-full">
          <SelectValue placeholder="Selecciona una ciudad" />
        </SelectTrigger>
        <SelectContent className="max-h-72">
          {CITIES.map((city) => (
            <SelectItem key={city.id} value={city.id}>
              {city.name} — {city.province}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
