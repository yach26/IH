"use client";
import { useLanguage } from "@/contexts/LanguageContext";
import React from 'react';
import Link from 'next/link';

export default function FinalCTA() {
  const { t } = useLanguage();
  return (
    <section className="relative py-40 bg-[#15803D] text-[#FAFAFA] overflow-hidden text-center">
      <img 
        src="/image.png" 
        alt="Agricultural landscape" 
        className="absolute inset-0 w-full h-full object-cover opacity-30 mix-blend-luminosity"
      />
      <div className="absolute inset-0 bg-[#15803D]/70"></div>
      
      <div className="relative z-10 container mx-auto px-6 max-w-3xl">
        <h2 className="text-4xl md:text-6xl font-medium text-white mb-8 leading-tight font-serif">
          {t("fi.title1")}<br className="hidden md:block"/>
          <span className="text-[#d4af37] italic">{t("fi.title2")}</span>
        </h2>
        
        <div className="mt-12">
          <Link href="/dashboard" className="px-10 py-5 bg-[#FAFAFA] text-[#15803D] font-bold text-sm hover:bg-white transition-colors rounded-sm inline-flex items-center shadow-lg hover:shadow-xl hover:-translate-y-0.5 transform duration-200">
            {t("fi.btn")}
            <svg className="w-4 h-4 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </Link>
        </div>
      </div>
    </section>
  );
}
