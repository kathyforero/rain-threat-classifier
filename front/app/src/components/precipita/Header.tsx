import { MapPin, Menu, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";

const NAV_ITEMS = [
  { href: "#inicio", label: "Mapa" },
  { href: "#metodologia", label: "Como funciona" },
  { href: "#modelo", label: "Modelo" },
  { href: "#acerca", label: "Proyecto académico" },
];

export function Header() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-primary/40 bg-primary text-primary-foreground shadow-card">
      <div className="mx-auto flex h-16 w-[94vw] max-w-[1480px] items-center justify-between gap-4 px-2 sm:px-4">
        <a href="#inicio" className="flex min-w-0 items-center gap-2.5">
          <span
            aria-hidden="true"
            className="grid size-9 shrink-0 place-items-center rounded-xl bg-primary-foreground/12 text-primary-foreground ring-1 ring-primary-foreground/20"
          >
            <MapPin className="size-5" />
          </span>
          <span className="min-w-0">
            <span className="block truncate font-display text-base font-bold leading-tight text-primary-foreground">
              Precipita EC
            </span>
            <span className="block truncate text-[11px] leading-tight text-primary-foreground/75">
              Amenaza por precipitación
            </span>
          </span>
        </a>

        <nav aria-label="Navegación principal" className="hidden items-center gap-1 md:flex">
          {NAV_ITEMS.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="rounded-md px-3 py-2 text-sm font-medium text-primary-foreground/80 transition-colors hover:bg-primary-foreground/12 hover:text-primary-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-foreground/70"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <Button
          variant="ghost"
          size="icon"
          className="min-h-11 min-w-11 text-primary-foreground hover:bg-primary-foreground/12 hover:text-primary-foreground md:hidden"
          aria-label={open ? "Cerrar menú de navegación" : "Abrir menú de navegación"}
          aria-expanded={open}
          onClick={() => setOpen((value) => !value)}
        >
          {open ? <X /> : <Menu />}
        </Button>
      </div>

      {open ? (
        <nav
          aria-label="Navegación movil"
          className="border-t border-primary-foreground/15 bg-primary md:hidden"
        >
          <ul className="mx-auto w-[94vw] max-w-[1480px] px-2 py-2 sm:px-4">
            {NAV_ITEMS.map((item) => (
              <li key={item.href}>
                <a
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className="block rounded-md px-3 py-3 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary-foreground/12"
                >
                  {item.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      ) : null}
    </header>
  );
}
