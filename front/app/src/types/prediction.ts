export type ThreatLevel = "Baja" | "Media" | "Alta";

export type DataAvailability = "sufficient" | "insufficient";

export interface City {
  id: string;
  name: string;
  province: string;
  latitude: number;
  longitude: number;
}

export interface WeatherIndicatorsData {
  accumulatedPrecipitation: number;
  maximumDailyPrecipitation: number;
  maximumFiveDayPrecipitation: number;
  rainyDays: number;
  intenseRainDays: number;
  averageTemperature: number;
  relativeHumidity: number;
  windSpeed: number;
  surfacePressure: number;
}

export interface HistoricalPoint {
  month: string;
  precipitation: number;
  isReference?: boolean;
}

export interface PredictionResult {
  city: string;
  province: string;
  referenceMonth: string;
  targetMonth: string;
  threatLevel?: ThreatLevel;
  confidence?: number;
  probabilities?: {
    low: number;
    medium: number;
    high: number;
  };
  dataAvailability: DataAvailability;
  indicators?: WeatherIndicatorsData;
  historicalSeries?: HistoricalPoint[];
}

/**
 * Contrato del servicio de prediccion que consume la interfaz.
 */
export interface PredictionService {
  getPrediction(cityId: string, referenceMonth: string): Promise<PredictionResult>;
}
