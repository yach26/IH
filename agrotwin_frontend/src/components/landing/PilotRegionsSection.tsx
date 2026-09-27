"use client";
import { useLanguage } from "@/contexts/LanguageContext";
import React from 'react';
import dynamic from 'next/dynamic';

const PilotRegionsMap = dynamic(() => import('@/components/ui/PilotRegionsMap'), { ssr: false });

export default function PilotRegionsSection() {
  const { t } = useLanguage();
  return (
    <section id="pilot-regions" className="py-32 bg-white">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start">
          {/* Left: copy */}
          <div>
            <div className="text-[11px] font-bold uppercase tracking-widest text-[#0F4D35] mb-6">{t("pi.badge")}</div>
            <h2 className="text-4xl md:text-5xl font-medium text-[#0F4D35] mb-6 leading-tight font-serif">
              {t("pi.title")}
            </h2>
            <p className="text-lg text-[#1a1a1a]/70 font-light leading-relaxed mb-10 max-w-md">
              {t("pi.subtitle")}
            </p>

            {/* Region chips */}
            <div className="space-y-4">
              {[
                { name: 'Jalgaon', crops: 'Banana, Cotton', color: '#d4af37' },
                { name: 'Kolhapur', crops: 'Sugarcane, Rice', color: '#d4af37' },
              ].map((r) => (
                <div key={r.name} className="flex items-center gap-4 p-4 rounded-sm border border-[#0F4D35]/10 bg-[#FDFBF7]">
                  <div
                    className="w-3 h-3 rounded-full flex-shrink-0 shadow-[0_0_0_4px_rgba(212,175,55,0.2)]"
                    style={{ background: r.color }}
                  />
                  <div>
                    <div className="text-sm font-bold text-[#0F4D35]">{r.name}</div>
                    <div className="text-xs text-[#1a1a1a]/50">{r.crops}</div>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-12">
              <p className="text-3xl font-serif text-[#0F4D35]/30 italic leading-relaxed">
                {t("pi.str1")}&nbsp;{t("pi.str2")}&nbsp;
                <span className="text-[#0F4D35]">{t("pi.str3")}</span>
              </p>
            </div>
          </div>

          {/* Right: live Leaflet map */}
          <div className="rounded-sm border border-[#0F4D35]/10 overflow-hidden shadow-sm">
            <PilotRegionsMap className="w-full h-[480px]" />
          </div>
        </div>
      </div>
    </section>
  );
}
