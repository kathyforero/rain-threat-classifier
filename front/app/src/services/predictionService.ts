import { getCityById } from "@/data/cities";
import { formatMonth, getTargetMonth } from "@/lib/threat";
import type { PredictionResult, PredictionService } from "@/types/prediction";

const API_BASE_URL = "http://127.0.0.1:8000";

type ApiPredictionResponse = Omit<PredictionResult, "referenceMonth" | "targetMonth"> & {
  referenceMonthRaw: string;
  targetMonthRaw: string;
};

export const apiPredictionService: PredictionService = {
  async getPrediction(cityId: string, referenceMonth: string): Promise<PredictionResult> {
    const city = getCityById(cityId);
    if (!city) {
      throw new Error("Ciudad no admitida por el prototipo.");
    }

    const response = await fetch(`${API_BASE_URL}/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        cityId,
        referenceMonth,
      }),
    });

    if (response.status === 404) {
      return {
        city: city.name,
        province: city.province,
        referenceMonth: formatMonth(referenceMonth),
        targetMonth: formatMonth(getTargetMonth(referenceMonth)),
        dataAvailability: "insufficient",
      };
    }

    if (!response.ok) {
      throw new Error("No se pudo consultar la API local.");
    }

    const prediction = (await response.json()) as ApiPredictionResponse;

    return {
      ...prediction,
      referenceMonth: formatMonth(prediction.referenceMonthRaw),
      targetMonth: formatMonth(prediction.targetMonthRaw),
    };
  },
};

export const predictionService: PredictionService = apiPredictionService;
