"use client";
import React from 'react';
import Link from 'next/link';
import { useLanguage } from '@/contexts/LanguageContext';

export default function HeroSection() {
  const { t } = useLanguage();

  return (
    <section className="relative pt-24 pb-32 overflow-hidden bg-[#FAFAFA]">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-8 items-center">
          <div className="max-w-xl">
            <div className="inline-flex items-center space-x-2 text-[11px] font-bold uppercase tracking-widest text-[#15803D] mb-8">
              <span>PSAI01 &middot; Sustainable Fertilizer Usage Optimizer</span>
            </div>
            <h1 className="text-5xl md:text-6xl font-medium tracking-tight text-[#15803D] mb-8 leading-[1.1] font-serif">
              {t('hero.title.1')}<br/>
              {t('hero.title.2')}<br/>
              {t('hero.title.3')}<br/>
              <span className="italic">{t('hero.title.4')}</span>
            </h1>
            <p className="text-lg text-[#1a1a1a]/80 mb-10 leading-relaxed font-light">
              Kisan Saathi provides evidence-grounded, field-specific fertilizer decision support using soil data, crop type, weather and farm history — helping farmers understand what to apply, how much, and when.
            </p>
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 mb-12">
              <Link href="/dashboard" className="px-8 py-4 bg-[#15803D] text-[#FAFAFA] font-medium text-sm hover:bg-[#0a3625] transition-colors rounded-sm shadow-sm flex items-center group">
                Set up your farm
                <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </Link>
              <Link href="#how-it-works" className="text-[#15803D] font-medium text-sm hover:underline underline-offset-4 decoration-[#15803D]/30">
                How it works
              </Link>
            </div>
            <div className="pt-8 border-t border-[#15803D]/10">
              <p className="text-sm text-[#1a1a1a]/60 font-light">
                Recommendations are explainable, confidence-rated, and designed with human oversight.
              </p>
            </div>
          </div>
          
          <div className="relative h-[600px] w-full rounded-sm overflow-hidden group">
            <img 
              src="/image copy 2.png" 
              alt="Indian agricultural field" 
              className="absolute inset-0 w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-[2s] ease-out"
            />
            {/* Live field info overlay */}
            <div className="absolute top-8 left-8 bg-[#FAFAFA]/95 backdrop-blur-sm p-4 rounded-sm shadow-lg border border-[#15803D]/10 w-64 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-300 fill-mode-both">
              <div className="text-[10px] uppercase tracking-wider text-[#1a1a1a]/50 font-bold mb-1">
                Start with your field
              </div>
              <div className="font-medium text-[#15803D] text-sm">
                Add your crop and farm details
              </div>
            </div>
            
            {/* Live soil health + weather overlay */}
            <div className="absolute bottom-12 right-8 bg-[#FAFAFA]/95 backdrop-blur-sm p-4 rounded-sm shadow-lg border border-[#15803D]/10 w-56 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-500 fill-mode-both">
              <div className="flex justify-between items-end mb-3 pb-3 border-b border-[#15803D]/10">
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-[#1a1a1a]/50 font-bold mb-1">Your soil data</div>
                  <div className="font-medium text-[#15803D] text-xl">
                    Upload & review
                  </div>
                </div>
                <div className="text-xs font-medium text-[#15803D]/70">N / P / K</div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-wider text-[#1a1a1a]/50 font-bold mb-1">You confirm first</div>
                <div className="font-medium text-[#15803D] text-sm">
                  Recommendations follow your confirmed soil data.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
