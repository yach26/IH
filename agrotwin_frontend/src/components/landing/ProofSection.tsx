"use client";
import { useLanguage } from "@/contexts/LanguageContext";
import React from 'react';
import Link from 'next/link';

export default function ProofSection() {
  const { t } = useLanguage();
  return (
    <section className="bg-[#0F4D35] text-[#FDFBF7] relative overflow-hidden flex flex-col md:flex-row">
      <div className="md:w-1/2 min-h-[400px] md:min-h-[800px] relative">
        <img 
          src="/image copy 3.png" 
          alt="Soil detail" 
          className="absolute inset-0 w-full h-full object-cover mix-blend-overlay opacity-80"
        />
        <div className="absolute inset-0 bg-[#0F4D35]/80 mix-blend-multiply"></div>
        <div className="absolute inset-0 p-12 md:p-24 flex flex-col justify-center max-w-xl mx-auto md:ml-auto md:mr-0 z-10">
          <div className="text-[11px] font-bold uppercase tracking-widest text-[#FDFBF7]/60 mb-6">{t("pr.badge")}</div>
          <h2 className="text-4xl md:text-5xl font-medium text-white mb-8 leading-tight font-serif">
            {t("pr.title1")}<br/>
            <span className="text-[#d4af37] italic">{t("pr.title2")}</span>
          </h2>
          <p className="text-lg text-white/80 mb-12 font-light leading-relaxed">
            {t("pr.subtitle")}
          </p>
          <Link href="/simulator" className="inline-flex items-center text-sm font-bold text-[#FDFBF7] group bg-white/10 px-6 py-3 rounded-sm border border-white/20 hover:bg-white/20 transition-colors w-max">
            {t("pr.view")}
            <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </Link>
        </div>
      </div>
      
      <div className="md:w-1/2 bg-[#0a3625] p-12 md:p-24 flex flex-col justify-center">
        <div className="max-w-xl mx-auto md:ml-0 md:mr-auto w-full">
          {[
            t("pr.q1"),
            t("pr.q2"),
            t("pr.q3"),
            t("pr.q4"),
            t("pr.q5"),
            t("pr.q6")
          ].map((q, i) => (
            <div key={i} className="border-b border-white/10 py-6 flex justify-between items-center group cursor-pointer hover:border-white/30 transition-colors">
              <div className="flex gap-6 items-center">
                <span className="text-xs font-mono text-white/30 group-hover:text-white/50 transition-colors">0{i+1}</span>
                <span className="text-sm font-bold tracking-wide">{q}</span>
              </div>
              <svg className="w-4 h-4 text-white/30 group-hover:text-white/70 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
