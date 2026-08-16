import { useRef } from "react";

import { ConsultationPanel } from "@/components/precipita/ConsultationPanel";
import { EcuadorMap } from "@/components/precipita/EcuadorMap";
import { ErrorState } from "@/components/precipita/ErrorState";
import { InsufficientDataState } from "@/components/precipita/InsufficientDataState";
import { InterpretationCard } from "@/components/precipita/InterpretationCard";
import { PredictionLoading } from "@/components/precipita/PredictionLoading";
import { ThreatResultCard } from "@/components/precipita/ThreatResultCard";
import { WeatherHistoryChart } from "@/components/precipita/WeatherHistoryChart";
import { WeatherIndicators } from "@/components/precipita/WeatherIndicators";
import { useConsultation } from "@/components/precipita/useConsultation";

export function ConsultationSection() {
  const panelRef = useRef<HTMLDivElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  const {
    selectedCityId,
    referenceMonth,
    status,
    result,
    selectCity,
    clearCity,
    selectMonth,
    runQuery,
    reset,
  } = useConsultation();

  const handleMapSelect = (cityId: string) => {
    selectCity(cityId);
    if (typeof window !== "undefined" && window.matchMedia("(max-width: 1023px)").matches) {
      window.setTimeout(
        () => panelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }),
        120,
      );
    }
  };

  const handleSubmit = () => {
    void runQuery();
    window.setTimeout(
      () => resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }),
      80,
    );
  };

  const focusPanel = () => {
    reset();
    panelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <section id="inicio" className="border-b border-border">
      <div className="mx-auto w-[94vw] max-w-[1480px] px-2 pb-8 pt-3 sm:px-4 md:pb-10 md:pt-4">
        <div className="relative min-h-[590px] overflow-hidden rounded-xl border border-border bg-sky-soft shadow-lift md:min-h-[630px]">
          <EcuadorMap
            selectedCityId={selectedCityId}
            onSelectCity={handleMapSelect}
            onResetView={clearCity}
            variant="hero"
          />

          <div className="pointer-events-none relative z-10 flex min-h-[590px] flex-col justify-between p-4 sm:p-6 md:min-h-[630px] lg:p-7">
            <div className="max-w-[980px]">
              <h1 className="text-xl font-bold leading-tight text-foreground sm:text-2xl lg:whitespace-nowrap lg:text-[2rem]">
                Amenaza mensual por precipitación en Ecuador
              </h1>
            </div>

            <div className="grid items-end gap-5 lg:grid-cols-[minmax(0,1fr)_380px]">
              <p className="max-w-[760px] rounded-lg bg-card/88 px-4 py-3 text-xs font-medium leading-relaxed text-foreground shadow-card ring-1 ring-border/70 backdrop-blur lg:whitespace-nowrap">
                El mapa muestra ciudades disponibles, provincia seleccionada y límites de referencia para orientar la consulta.
              </p>

              <div ref={panelRef} className="pointer-events-auto min-w-0 scroll-mt-24">
                <ConsultationPanel
                  selectedCityId={selectedCityId}
                  referenceMonth={referenceMonth}
                  status={status}
                  onCityChange={selectCity}
                  onCityClear={clearCity}
                  onMonthChange={selectMonth}
                  onSubmit={handleSubmit}
                />
              </div>
            </div>
          </div>
        </div>

        <div ref={resultsRef} className="mt-10 scroll-mt-24 space-y-6" aria-live="polite">
          {status === "idle" ? (
            <div className="rounded-xl border border-dashed border-border bg-card/60 p-5 text-center">
              <p className="text-sm text-muted-foreground">
                Los resultados aparecerán aqui después de ejecutar la consulta.
              </p>
            </div>
          ) : null}

          {status === "loading" ? <PredictionLoading /> : null}

          {status === "error" ? <ErrorState onRetry={() => void runQuery()} /> : null}

          {status === "success" && result ? (
            result.dataAvailability === "insufficient" ? (
              <InsufficientDataState result={result} onModifyQuery={focusPanel} />
            ) : (
              <>
                <ThreatResultCard result={result} />

                {result.indicators ? (
                  <section aria-labelledby="antecedentes-titulo">
                    <h2 id="antecedentes-titulo" className="text-xl font-bold text-foreground">
                      Antecedentes utilizados en la consulta
                    </h2>
                    <p className="mt-1.5 text-sm text-muted-foreground">
                      Indicadores correspondientes a {result.city} en {result.referenceMonth}.
                    </p>
                    <div className="mt-4">
                      <WeatherIndicators indicators={result.indicators} />
                    </div>
                  </section>
                ) : null}

                {result.historicalSeries ? (
                  <WeatherHistoryChart
                    series={result.historicalSeries}
                    referenceMonth={result.referenceMonth}
                  />
                ) : null}

                <InterpretationCard />
              </>
            )
          ) : null}
        </div>
      </div>
    </section>
  );
}
