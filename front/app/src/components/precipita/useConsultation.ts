import { useCallback, useRef, useState } from "react";

import { predictionService } from "@/services/predictionService";
import type { PredictionResult } from "@/types/prediction";

export type QueryStatus = "idle" | "loading" | "success" | "error";

/**
 * Estado de la consulta interactiva. Depende unicamente del contrato
 * `PredictionService`, por lo que la UI queda separada de la fuente de datos.
 */
export function useConsultation() {
  const [selectedCityId, setSelectedCityId] = useState<string | null>(null);
  const [referenceMonth, setReferenceMonth] = useState<string | null>(null);
  const [status, setStatus] = useState<QueryStatus>("idle");
  const [result, setResult] = useState<PredictionResult | null>(null);
  const requestId = useRef(0);

  const runQuery = useCallback(async () => {
    if (!selectedCityId || !referenceMonth) return;
    const currentRequest = ++requestId.current;
    setStatus("loading");
    setResult(null);
    try {
      const prediction = await predictionService.getPrediction(selectedCityId, referenceMonth);
      if (currentRequest !== requestId.current) return;
      setResult(prediction);
      setStatus("success");
    } catch {
      if (currentRequest !== requestId.current) return;
      setResult(null);
      setStatus("error");
    }
  }, [selectedCityId, referenceMonth]);

  const selectCity = useCallback((cityId: string) => {
    setSelectedCityId(cityId);
    setStatus("idle");
    setResult(null);
  }, []);

  const clearCity = useCallback(() => {
    setSelectedCityId(null);
    requestId.current += 1;
    setStatus("idle");
    setResult(null);
  }, []);

  const selectMonth = useCallback((month: string) => {
    setReferenceMonth(month);
    setStatus("idle");
    setResult(null);
  }, []);

  const reset = useCallback(() => {
    setStatus("idle");
    setResult(null);
  }, []);

  return {
    selectedCityId,
    referenceMonth,
    status,
    result,
    selectCity,
    clearCity,
    selectMonth,
    runQuery,
    reset,
  };
}
