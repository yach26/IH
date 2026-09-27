"use client";
import { useLanguage } from "@/contexts/LanguageContext";
import React from 'react';

export default function DecisionLoopSection() {
  const { t } = useLanguage();

  const steps = [
    t("dl.s1"), t("dl.s2"), t("dl.s3"), t("dl.s4"), t("dl.s5"), t("dl.s6"), t("dl.s7"), t("dl.s8")
  ];

  return (
    <section id="how-it-works" className="py-32 bg-[#FDFBF7]">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="max-w-2xl mb-20">
          <div className="text-[11px] font-bold uppercase tracking-widest text-[#0F4D35] mb-6">{t("dl.badge")}</div>
          <h2 className="text-4xl md:text-5xl font-medium text-[#0F4D35] mb-6 leading-tight font-serif">
            {t("dl.title.1")}<br/>{t("dl.title.2")}
          </h2>
          <p className="text-lg text-[#1a1a1a]/70 font-light leading-relaxed">
            {t("dl.desc")}
          </p>
        </div>

        <div className="relative">
          {/* Connecting line */}
          <div className="absolute top-4 left-0 w-full h-[1px] bg-[#0F4D35]/20 hidden md:block"></div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-8">
            {steps.map((step, i) => (
              <div key={i} className="relative z-10">
                <div className="w-8 h-8 rounded-full bg-[#FDFBF7] border border-[#0F4D35] flex items-center justify-center text-[10px] font-mono text-[#0F4D35] mb-6 shadow-sm">
                  0{i+1}
                </div>
                <h4 className="text-sm font-medium text-[#0F4D35] mb-2">{step}</h4>
                <p className="text-xs text-[#1a1a1a]/50 font-light">{t("dl.step.desc")}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
