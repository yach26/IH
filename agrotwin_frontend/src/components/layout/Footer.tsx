"use client";

import { usePathname } from "next/navigation";

export default function Footer() {
  const pathname = usePathname();
  if (pathname === "/") return null; // landing page has its own FinalCTA/footer treatment

  const lastUpdated = new Date().toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

  return (
    <footer className="no-print border-t border-border bg-surface text-[13px] text-muted">
      <div className="tricolor-bar" />
      <div className="container mx-auto px-4 py-6 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <p className="font-serif font-bold text-foreground mb-1">Kisan Saathi — Digital Krishi Twin</p>
          <p>Farm nutrient decision support · Kolhapur pilot</p>
          <p className="mt-2">Helpline: <a href="tel:18001801551" className="underline hover:text-primary">1800-180-1551</a> (Kisan Call Centre)</p>
          <p>Last updated: {lastUpdated}</p>
        </div>
        <div>
          <p className="font-semibold text-foreground mb-1">Data sources</p>
          <ul className="space-y-0.5">
            <li>MPKV / ICAR Recommended Dose of Fertilizer (RDF) guidelines</li>
            <li>Open-Meteo weather forecast API</li>
            <li>Fertilizer Control Order (FCO) product specifications</li>
          </ul>
        </div>
        <div>
          <p className="font-semibold text-foreground mb-1">Important</p>
          <p className="mb-2">
            Recommendations shown are advisory in nature and generated from a deterministic
            nutrient ledger. Please consult your local Krishi Sevak / agronomist before final
            field application.
          </p>
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            <a href="#" className="underline hover:text-primary">Accessibility statement</a>
            <a href="#" className="underline hover:text-primary">Report an issue</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
