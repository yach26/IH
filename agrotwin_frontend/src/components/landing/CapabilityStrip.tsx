"use client";
import { useLanguage } from "@/contexts/LanguageContext";
import React from 'react';

export default function CapabilityStrip() {
  const { t } = useLanguage();

  return (
    <section id="capabilities" className="py-24 bg-[#FAFAFA] border-t border-[#15803D]/10">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 lg:gap-24">
          <div className="space-y-4">
            <div className="text-xs font-mono text-[#15803D]/40 mb-6">01</div>
            <h3 className="text-xl font-medium text-[#15803D]">{t("cap.1.t")}</h3>
            <p className="text-[#1a1a1a]/70 font-light leading-relaxed text-sm">
              {t("cap.1.d")}
            </p>
          </div>
          <div className="space-y-4">
            <div className="text-xs font-mono text-[#15803D]/40 mb-6">02</div>
            <h3 className="text-xl font-medium text-[#15803D]">{t("cap.2.t")}</h3>
            <p className="text-[#1a1a1a]/70 font-light leading-relaxed text-sm">
              {t("cap.2.d")}
            </p>
          </div>
          <div className="space-y-4">
            <div className="text-xs font-mono text-[#15803D]/40 mb-6">03</div>
            <h3 className="text-xl font-medium text-[#15803D]">{t("cap.3.t")}</h3>
            <p className="text-[#1a1a1a]/70 font-light leading-relaxed text-sm">
              {t("cap.3.d")}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
