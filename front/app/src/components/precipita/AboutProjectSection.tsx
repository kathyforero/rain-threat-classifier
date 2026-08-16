import { BookOpen, ExternalLink, GraduationCap, Users } from "lucide-react";

const MEMBERS = ["Katherine Forero", "David Ramirez", "Anthony Herrera"];
const REPOSITORY_URL = "https://github.com/kathyforero/rain-threat-classifier/tree/main";

export function AboutProjectSection() {
  return (
    <section id="acerca" className="border-t border-border bg-card/60">
      <div className="mx-auto grid w-[94vw] max-w-[1480px] gap-8 px-2 py-14 sm:px-4 md:py-20 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="min-w-0">
          <h2 className="text-2xl font-bold text-foreground sm:text-3xl">
            Proyecto académico de inteligencia artificial
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground sm:text-base">
            Desarrollo orientado a la clasificación anticipada de amenaza meteorológica por
            precipitación para el mes siguiente en zonas seleccionadas del Ecuador.
          </p>

          <dl className="mt-7 grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-border bg-card p-4 shadow-card">
              <dt className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-muted-foreground">
                <GraduationCap aria-hidden="true" className="size-4" />
                Institución
              </dt>
              <dd className="mt-1.5 text-sm font-semibold text-foreground">
                Escuela Superior Politécnica del Litoral
              </dd>
            </div>
            <div className="rounded-xl border border-border bg-card p-4 shadow-card">
              <dt className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-muted-foreground">
                <BookOpen aria-hidden="true" className="size-4" />
                Facultad
              </dt>
              <dd className="mt-1.5 text-sm font-semibold text-foreground">
                Facultad de Ingeniería en Electricidad y Computación
              </dd>
            </div>
            <div className="rounded-xl border border-border bg-card p-4 shadow-card">
              <dt className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-muted-foreground">
                <BookOpen aria-hidden="true" className="size-4" />
                Asignatura - Grupo
              </dt>
              <dd className="mt-1.5 text-sm font-semibold text-foreground">
                Inteligencia Artificial
                <span className="block">- Grupo 6</span>
              </dd>
            </div>
            <div className="rounded-xl border border-border bg-card p-4 shadow-card">
              <dt className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-muted-foreground">
                <Users aria-hidden="true" className="size-4" />
                Integrantes
              </dt>
              <dd className="mt-1.5 space-y-0.5 text-sm font-semibold text-foreground">
                {MEMBERS.map((member) => (
                  <span key={member} className="block">
                    {member}
                  </span>
                ))}
              </dd>
            </div>
          </dl>
        </div>

        <div className="min-w-0 rounded-xl border border-border bg-card p-5 shadow-card">
          <h3 className="text-base font-bold text-foreground">Repositorio del proyecto</h3>
          <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
            Código, pipeline de modelo, datos procesados y documentación técnica del clasificador.
          </p>
          <a
            href={REPOSITORY_URL}
            target="_blank"
            rel="noreferrer"
            className="mt-5 inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            Ver repositorio
            <ExternalLink aria-hidden="true" className="size-4" />
          </a>
        </div>
      </div>
    </section>
  );
}
