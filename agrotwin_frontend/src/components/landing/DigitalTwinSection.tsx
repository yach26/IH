"use client";
import { useLanguage } from "@/contexts/LanguageContext";
import React from 'react';

export default function DigitalTwinSection() {
  const { t } = useLanguage();
  return (
    <section className="py-32 bg-white">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
          <div className="order-2 lg:order-1 h-[700px] w-full bg-[#f4f2eb] rounded-sm overflow-hidden flex items-center justify-center">
            <img 
              src="/image copy 4.png" 
              alt="Soil and crop seedlings" 
              className="w-full h-full object-cover"
            />
          </div>
          <div className="order-1 lg:order-2">
            <div className="text-[11px] font-bold uppercase tracking-widest text-[#0F4D35] mb-6">{t("dt.badge")}</div>
            <h2 className="text-4xl md:text-5xl font-medium text-[#0F4D35] mb-8 leading-tight font-serif">
              {t("dt.title")}
            </h2>
            <p className="text-lg text-[#1a1a1a]/70 mb-12 font-light leading-relaxed">
              {t("dt.subtitle")}
            </p>
            
            <div className="space-y-8">
              <div className="flex gap-4 border-b border-[#0F4D35]/10 pb-6">
                <div className="text-xs font-mono text-[#0F4D35]/40 mt-1">01</div>
                <div>
                  <h4 className="text-sm font-bold text-[#1a1a1a] mb-1">{t("dt.s1")}</h4>
                  <p className="text-sm text-[#1a1a1a]/60">{t("dt.s1d")}</p>
                </div>
              </div>
              <div className="flex gap-4 border-b border-[#0F4D35]/10 pb-6">
                <div className="text-xs font-mono text-[#0F4D35]/40 mt-1">02</div>
                <div>
                  <h4 className="text-sm font-bold text-[#1a1a1a] mb-1">{t("dt.s2")}</h4>
                  <p className="text-sm text-[#1a1a1a]/60">{t("dt.s2d")}</p>
                </div>
              </div>
              <div className="flex gap-4 border-b border-[#0F4D35]/10 pb-6">
                <div className="text-xs font-mono text-[#0F4D35]/40 mt-1">03</div>
                <div>
                  <h4 className="text-sm font-bold text-[#1a1a1a] mb-1">{t("dt.s3")}</h4>
                  <p className="text-sm text-[#1a1a1a]/60">{t("dt.s3d")}</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="text-xs font-mono text-[#0F4D35]/40 mt-1">04</div>
                <div>
                  <h4 className="text-sm font-bold text-[#1a1a1a] mb-1">{t("dt.s4")}</h4>
                  <p className="text-sm text-[#1a1a1a]/60">{t("dt.s4d")}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
