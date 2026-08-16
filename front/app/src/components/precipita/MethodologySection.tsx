import { BarChart3, Brain, CalendarSearch, CheckCircle2, Database, SlidersHorizontal } from "lucide-react";

const STEPS = [
  {
    icon: CalendarSearch,
    title: "Seleccionar ciudad y mes",
    detail: "El usuario elige una zona y el mes de referencia para consultar el mes siguiente.",
  },
  {
    icon: Database,
    title: "Leer antecedentes",
    detail: "Se usan indicadores meteorológicos mensuales disponibles para la zona seleccionada.",
  },
  {
    icon: CheckCircle2,
    title: "Verificar datos",
    detail: "Se comprueba que exista historial suficiente para construir las variables requeridas.",
  },
  {
    icon: SlidersHorizontal,
    title: "Preparar features",
    detail: "Las variables se organizan como entrada tabular compatible con el clasificador.",
  },
  {
    icon: Brain,
    title: "Ejecutar clasificador",
    detail: "El modelo estima la clase de amenaza para el mes siguiente.",
  },
  {
    icon: BarChart3,
    title: "Mostrar resultado",
    detail: "La interfaz presenta la categoría Baja, Media o Alta y sus indicadores asociados.",
  },
];

export function MethodologySection() {
  return (
    <section id="metodologia" className="border-t border-border bg-card/60">
      <div className="mx-auto w-[94vw] max-w-[1480px] px-2 py-14 sm:px-4 md:py-20">
        <h2 className="text-2xl font-bold text-foreground sm:text-3xl">Como funciona</h2>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground sm:text-base">
          La consulta resume el flujo del proyecto: datos meteorológicos, preparación de variables,
          clasificación y visualización del resultado.
        </p>

        <ol className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {STEPS.map(({ icon: Icon, title, detail }, index) => (
            <li key={title} className="relative rounded-xl border border-border bg-card p-5 shadow-card">
              <div className="flex items-center gap-3">
                <span
                  aria-hidden="true"
                  className="grid size-9 shrink-0 place-items-center rounded-xl bg-sky-soft text-primary"
                >
                  <Icon className="size-4.5" />
                </span>
                <span className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
                  Paso {index + 1}
                </span>
              </div>
              <h3 className="mt-3 text-base font-bold text-foreground">{title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{detail}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
