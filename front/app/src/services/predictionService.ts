import { getCityById } from "@/data/cities";
import { addMonths, formatMonth, formatMonthShort, getTargetMonth } from "@/lib/threat";
import type {
  HistoricalPoint,
  PredictionResult,
  PredictionService,
  ThreatLevel,
  WeatherIndicatorsData,
} from "@/types/prediction";

/**
 * Servicio local de clasificación.
 *
 * Es 100 % local y determinista: la misma combinación de ciudad y mes de
 * referencia produce siempre el mismo resultado. No hay backend, base de
 * datos ni APIs externas.
 *
 * Para integrar un modelo real en el futuro basta con crear otra
 * implementación de `PredictionService` (por ejemplo `HttpPredictionService`)
 * y cambiarla en `predictionService` — la interfaz de usuario no cambia.
 */

/* ---------- utilidades deterministas ---------- */

function hashString(input: string): number {
  let hash = 2166136261;
  for (let i = 0; i < input.length; i++) {
    hash ^= input.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

/** Generador pseudoaleatorio determinista (mulberry32). */
function createRandom(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const round = (value: number, decimals = 0): number => {
  const factor = 10 ** decimals;
  return Math.round(value * factor) / factor;
};

/** Estacionalidad aproximada por región (0 = mes seco, 1 = mes lluvioso). */
const COASTAL = new Set([
  "guayaquil",
  "babahoyo",
  "portoviejo",
  "machala",
  "esmeraldas",
  "salinas",
  "santo-domingo",
]);
const AMAZON = new Set(["macas", "puyo", "tena", "nueva-loja"]);

function seasonalFactor(cityId: string, month: number): number {
  const rainyCoast = [1, 0.98, 1, 0.85, 0.55, 0.3, 0.18, 0.12, 0.14, 0.2, 0.28, 0.6];
  const rainyAndes = [0.6, 0.72, 0.85, 0.95, 0.7, 0.4, 0.28, 0.25, 0.45, 0.8, 0.85, 0.7];
  const rainyAmazon = [0.7, 0.8, 0.9, 1, 0.95, 0.85, 0.75, 0.6, 0.6, 0.8, 0.85, 0.8];
  const table = COASTAL.has(cityId)
    ? rainyCoast
    : AMAZON.has(cityId)
      ? rainyAmazon
      : rainyAndes;
  return table[month - 1] ?? 0.5;
}

function baseMonthlyRain(cityId: string): number {
  if (cityId === "salinas") return 30;
  if (COASTAL.has(cityId)) return cityId === "esmeraldas" ? 120 : 150;
  if (AMAZON.has(cityId)) return 260;
  return 90;
}

function monthNumber(value: string): number {
  return Number(value.split("-")[1] ?? 1);
}

function yearNumber(value: string): number {
  return Number(value.split("-")[0] ?? 2025);
}

function precipitationFor(cityId: string, month: string): number {
  const rng = createRandom(hashString(`${cityId}|${month}|precip`));
  const base = baseMonthlyRain(cityId) * (0.35 + 1.3 * seasonalFactor(cityId, monthNumber(month)));
  const noise = 0.7 + rng() * 0.6;
  return Math.max(0, round(base * noise, 1));
}

function buildIndicators(cityId: string, month: string): WeatherIndicatorsData {
  const rng = createRandom(hashString(`${cityId}|${month}|ind`));
  const accumulated = precipitationFor(cityId, month);
  const maxDaily = round(accumulated * (0.14 + rng() * 0.16) + rng() * 4, 1);
  const maxFiveDay = round(Math.min(accumulated, maxDaily * (2.1 + rng() * 1.4)), 1);
  const rainyDays = Math.min(30, Math.round(accumulated / 12 + rng() * 4));
  const intenseRainDays = Math.max(0, Math.round(rainyDays * (0.08 + rng() * 0.22)));
  const isCoast = COASTAL.has(cityId);
  const isAmazon = AMAZON.has(cityId);
  const baseTemp = isCoast ? 26 : isAmazon ? 24.5 : 14.5;
  const basePressure = isCoast ? 1011 : isAmazon ? 1005 : 755;

  return {
    accumulatedPrecipitation: accumulated,
    maximumDailyPrecipitation: maxDaily,
    maximumFiveDayPrecipitation: maxFiveDay,
    rainyDays,
    intenseRainDays,
    averageTemperature: round(baseTemp + (rng() - 0.5) * 2.4, 1),
    relativeHumidity: Math.round(
      Math.min(98, (isCoast || isAmazon ? 79 : 72) + seasonalFactor(cityId, monthNumber(month)) * 10 + rng() * 4),
    ),
    windSpeed: round(6 + rng() * 12, 1),
    surfacePressure: round(basePressure + (rng() - 0.5) * 4, 1),
  };
}

function buildHistoricalSeries(cityId: string, referenceMonth: string): HistoricalPoint[] {
  const series: HistoricalPoint[] = [];
  for (let i = 11; i >= 0; i--) {
    const month = addMonths(referenceMonth, -i);
    series.push({
      month: formatMonthShort(month),
      precipitation: precipitationFor(cityId, month),
      isReference: i === 0,
    });
  }
  return series;
}

function classify(
  cityId: string,
  referenceMonth: string,
  indicators: WeatherIndicatorsData,
): { level: ThreatLevel; probabilities: { low: number; medium: number; high: number }; confidence: number } {
  const targetMonth = getTargetMonth(referenceMonth);
  const expected = precipitationFor(cityId, targetMonth);
  const normal = baseMonthlyRain(cityId) * (0.35 + 1.3 * seasonalFactor(cityId, monthNumber(targetMonth)));
  const ratio = normal > 0 ? expected / normal : 1;

  const rng = createRandom(hashString(`${cityId}|${referenceMonth}|clf`));
  let highScore = ratio * 42 + indicators.intenseRainDays * 3.2 + indicators.maximumFiveDayPrecipitation * 0.06;
  let mediumScore = 46 + (1 - Math.abs(ratio - 1)) * 22 + indicators.rainyDays * 0.7;
  let lowScore = 78 - ratio * 34 - indicators.intenseRainDays * 2.4;

  highScore += rng() * 12;
  mediumScore += rng() * 10;
  lowScore += rng() * 12;

  highScore = Math.max(1, highScore);
  mediumScore = Math.max(1, mediumScore);
  lowScore = Math.max(1, lowScore);

  const total = highScore + mediumScore + lowScore;
  let low = Math.round((lowScore / total) * 100);
  let medium = Math.round((mediumScore / total) * 100);
  let high = 100 - low - medium;

  // Garantiza valores no negativos y suma exacta de 100 %.
  if (high < 0) {
    medium += high;
    high = 0;
  }
  if (medium < 0) {
    low += medium;
    medium = 0;
  }
  low = Math.max(0, 100 - medium - high);

  const entries: Array<[ThreatLevel, number]> = [
    ["Baja", low],
    ["Media", medium],
    ["Alta", high],
  ];
  entries.sort((a, b) => b[1] - a[1]);
  const winner = entries[0]!;

  return {
    level: winner[0],
    probabilities: { low, medium, high },
    confidence: winner[1],
  };
}

/* ---------- servicio ---------- */

const SIMULATED_LATENCY_MS = 1600;

export const mockPredictionService: PredictionService = {
  async getPrediction(cityId: string, referenceMonth: string): Promise<PredictionResult> {
    const city = getCityById(cityId);
    if (!city) {
      throw new Error("Ciudad no admitida por el prototipo.");
    }

    await new Promise((resolve) => setTimeout(resolve, SIMULATED_LATENCY_MS));

    const targetMonth = getTargetMonth(referenceMonth);
    const seed = hashString(`${city.name}|${yearNumber(referenceMonth)}|${monthNumber(referenceMonth)}`);

    const base: PredictionResult = {
      city: city.name,
      province: city.province,
      referenceMonth: formatMonth(referenceMonth),
      targetMonth: formatMonth(targetMonth),
      dataAvailability: "sufficient",
    };

    // Estado determinista de antecedentes insuficientes (~7 % de los casos).
    if (seed % 14 === 3) {
      return { ...base, dataAvailability: "insufficient" };
    }

    const indicators = buildIndicators(cityId, referenceMonth);
    const { level, probabilities, confidence } = classify(cityId, referenceMonth, indicators);

    return {
      ...base,
      threatLevel: level,
      confidence,
      probabilities,
      indicators,
      historicalSeries: buildHistoricalSeries(cityId, referenceMonth),
    };
  },
};

/** Punto único de intercambio: reemplazar por el cliente HTTP real cuando exista la API. */
type LocalStaticPredictionEntry = Omit<PredictionResult, "referenceMonth" | "targetMonth"> & {
  referenceMonthRaw: string;
  targetMonthRaw: string;
};

interface LocalStaticPredictionPayload {
  entries: Record<string, LocalStaticPredictionEntry>;
}

let localPredictionsPromise: Promise<LocalStaticPredictionPayload> | null = null;

async function loadLocalPredictions(): Promise<LocalStaticPredictionPayload> {
  localPredictionsPromise ??= fetch("/predictions-local.json", {
    cache: "no-store",
  }).then((response) => {
    if (!response.ok) {
      throw new Error("No se encontro public/predictions-local.json.");
    }
    return response.json() as Promise<LocalStaticPredictionPayload>;
  });

  return localPredictionsPromise;
}

export const localStaticPredictionService: PredictionService = {
  async getPrediction(cityId: string, referenceMonth: string): Promise<PredictionResult> {
    const city = getCityById(cityId);
    if (!city) {
      throw new Error("Ciudad no admitida por el prototipo.");
    }

    const payload = await loadLocalPredictions();
    const entry = payload.entries[`${cityId}|${referenceMonth}`];
    const targetMonth = getTargetMonth(referenceMonth);

    if (!entry) {
      return {
        city: city.name,
        province: city.province,
        referenceMonth: formatMonth(referenceMonth),
        targetMonth: formatMonth(targetMonth),
        dataAvailability: "insufficient",
      };
    }

    return {
      ...entry,
      referenceMonth: formatMonth(entry.referenceMonthRaw),
      targetMonth: formatMonth(entry.targetMonthRaw),
    };
  },
};

export const predictionService: PredictionService = localStaticPredictionService;
