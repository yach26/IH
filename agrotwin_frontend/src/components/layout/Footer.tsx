"use client";

import { usePathname } from "next/navigation";
import { useLanguage } from "@/contexts/LanguageContext";

export default function Footer() {
  const pathname = usePathname();
  if (pathname === "/") return null; // landing page has its own FinalCTA/footer treatment

  const lastUpdated = new Date().toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

  const { t } = useLanguage();

  return (
    <footer className="no-print border-t border-border bg-surface text-[13px] text-muted">
      <div className="tricolor-bar" />
      <div className="container mx-auto px-4 py-6 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <p className="font-serif font-bold text-foreground mb-1">{t("fo.brand")}</p>
          <p>{t("fo.subtitle")}</p>
          <p className="mt-2">{t("fo.helpline")}: <a href="tel:18001801551" className="underline hover:text-primary">1800-180-1551</a> (Kisan Call Centre)</p>
          <p>{t("fo.lastUpdated")}: {lastUpdated}</p>
        </div>
        <div>
          <p className="font-semibold text-foreground mb-1">{t("fo.dataSources")}</p>
          <ul className="space-y-0.5">
            <li>MPKV / ICAR Recommended Dose of Fertilizer (RDF) guidelines</li>
            <li>Open-Meteo weather forecast API</li>
            <li>Fertilizer Control Order (FCO) product specifications</li>
          </ul>
        </div>
        <div>
          <p className="font-semibold text-foreground mb-1">{t("fo.important")}</p>
          <p className="mb-2">{t("fo.disclaimer")}</p>
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            <a href="#" className="underline hover:text-primary">{t("fo.accessibility")}</a>
            <a href="#" className="underline hover:text-primary">{t("fo.reportIssue")}</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
