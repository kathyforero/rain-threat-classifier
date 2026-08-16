import { createFileRoute } from "@tanstack/react-router";

import { AboutProjectSection } from "@/components/precipita/AboutProjectSection";
import { ConsultationSection } from "@/components/precipita/ConsultationSection";
import { Header } from "@/components/precipita/Header";
import { MethodologySection } from "@/components/precipita/MethodologySection";
import { ModelsSection } from "@/components/precipita/ModelsSection";

const TITLE = "Precipita EC - Amenaza por lluvias en Ecuador";
const DESCRIPTION =
  "Clasificación de amenaza meteorológica por precipitación para el mes siguiente en zonas seleccionadas del Ecuador.";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: TITLE },
      { name: "description", content: DESCRIPTION },
      { property: "og:title", content: TITLE },
      { property: "og:description", content: DESCRIPTION },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

function Index() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main>
        <ConsultationSection />
        <MethodologySection />
        <ModelsSection />
        <AboutProjectSection />
      </main>
    </div>
  );
}
