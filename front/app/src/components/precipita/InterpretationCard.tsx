import { Info } from "lucide-react";

export function InterpretationCard() {
  return (
    <section
      aria-labelledby="interpretacion-titulo"
      className="rounded-2xl border border-border bg-sky-soft p-5 shadow-card sm:p-6"
    >
      <div className="flex items-start gap-3">
        <Info aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-primary" />
        <div className="min-w-0">
          <h3 id="interpretacion-titulo" className="text-base font-bold text-foreground">
            ¿Cómo interpretar este resultado?
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-foreground/90">
            La categoría representa el comportamiento esperado de la precipitación respecto a los
            antecedentes históricos de la ciudad y la época del año. No representa por sí sola el
            riesgo integral de desastre.
          </p>
          <p className="mt-3 text-sm leading-relaxed text-foreground/90">
            El riesgo también depende de factores como la exposición, la vulnerabilidad, la
            infraestructura y la capacidad de respuesta.
          </p>
          <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
            La clasificación utiliza únicamente información disponible hasta el mes de referencia y
            estima la categoría correspondiente al mes siguiente.
          </p>
        </div>
      </div>
    </section>
  );
}
