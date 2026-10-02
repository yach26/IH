"use client";
import { useLanguage } from "@/contexts/LanguageContext";
import React from 'react';

export default function LandingFooter() {
  const { t } = useLanguage();
  return (
    <footer className="bg-[#0a3625] text-[#FAFAFA]/60 py-12 border-t border-white/10">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex flex-col items-center md:items-start gap-2">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-[#d4af37]" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z" />
              </svg>
              <span className="font-bold text-white text-lg tracking-tight">Kisan Saathi</span>
            </div>
            <p className="text-[10px] uppercase tracking-widest text-[#FAFAFA]/40">{t("fo.tag")}</p>
          </div>
          
          <div className="text-[11px] text-center md:text-right font-light">
            {t("fo.d1")}<br/>{t("fo.d2")}
          </div>
        </div>
      </div>
    </footer>
  );
}
