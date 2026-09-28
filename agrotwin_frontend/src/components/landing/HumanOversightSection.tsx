"use client";
import { useLanguage } from "@/contexts/LanguageContext";
import React from 'react';

export default function HumanOversightSection() {
  const { t } = useLanguage();
  const checks = [
    t("hu.c1"),
    t("hu.c2"),
    t("hu.c3"),
    t("hu.c4")
  ];

  return (
    <section id="resources" className="py-32 bg-white">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
          <div className="h-[600px] w-full bg-[#f4f2eb] rounded-sm overflow-hidden relative">
            <img 
              src="/image copy.png" 
              alt="Agronomist reviewing data" 
              className="w-full h-full object-cover"
            />
            <div className="absolute bottom-8 left-8 bg-[#FAFAFA] p-4 rounded-sm shadow-lg border-l-2 border-[#d4af37] w-64">
              <div className="flex items-center gap-2 mb-2">
                <svg className="w-4 h-4 text-[#d4af37]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span className="text-xs font-bold text-[#1a1a1a]">{t("hu.rev")}</span>
              </div>
              <p className="text-[11px] text-[#1a1a1a]/70">{t("hu.revd")}</p>
            </div>
          </div>
          
          <div>
            <div className="text-[11px] font-bold uppercase tracking-widest text-[#15803D] mb-6">{t("hu.badge")}</div>
            <h2 className="text-4xl md:text-5xl font-medium text-[#15803D] mb-8 leading-tight font-serif">
              {t("hu.title1")}<br/>
              {t("hu.title2")}
            </h2>
            <p className="text-lg text-[#1a1a1a]/70 mb-10 font-light leading-relaxed max-w-md">
              {t("hu.subtitle")}
            </p>
            
            <ul className="space-y-4">
              {checks.map((check, i) => (
                <li key={i} className="flex items-center text-sm text-[#1a1a1a]/80 font-medium">
                  <svg className="w-4 h-4 text-[#15803D] mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  {check}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
