"use client";
import React from 'react';
import Link from 'next/link';
import { useLanguage } from '@/contexts/LanguageContext';

export default function HeroSection() {
  const { t } = useLanguage();
  const [liveField, setLiveField] = React.useState<{
    fieldId: string;
    crop: string;
    growthStage: string;
    soilHealthScore: number;
    weather: { rainfall_mm_next_7d: number; condition: string };
  } | null>(null);

  React.useEffect(() => {
    const apiHost = window.location.hostname;
    fetch(`http://${apiHost}:8000/fields/REAL-001/twin`)
      .then(r => r.json())
      .then(data => setLiveField({
        fieldId: data.fieldId,
        crop: data.crop,
        growthStage: data.growthStage,
        soilHealthScore: data.soilHealthScore ?? 0,
        weather: data.weather ?? { rainfall_mm_next_7d: 17, condition: 'Clear' },
      }))
      .catch(() => null);
  }, []);

  return (
    <section className="relative pt-24 pb-32 overflow-hidden bg-[#FDFBF7]">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-8 items-center">
          <div className="max-w-xl">
            <div className="inline-flex items-center space-x-2 text-[11px] font-bold uppercase tracking-widest text-[#0F4D35] mb-8">
              <span>PSAI01 &middot; Sustainable Fertilizer Usage Optimizer</span>
            </div>
            <h1 className="text-5xl md:text-6xl font-medium tracking-tight text-[#0F4D35] mb-8 leading-[1.1] font-serif">
              {t('hero.title.1')}<br/>
              {t('hero.title.2')}<br/>
              {t('hero.title.3')}<br/>
              <span className="italic">{t('hero.title.4')}</span>
            </h1>
            <p className="text-lg text-[#1a1a1a]/80 mb-10 leading-relaxed font-light">
              AgroTwin AI provides evidence-grounded, field-specific fertilizer decision support using soil data, crop type, weather and farm history — helping farmers understand what to apply, how much, and when.
            </p>
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 mb-12">
              <Link href="/dashboard" className="px-8 py-4 bg-[#0F4D35] text-[#FDFBF7] font-medium text-sm hover:bg-[#0a3625] transition-colors rounded-sm shadow-sm flex items-center group">
                {t('hero.explore')}
                <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </Link>
              <Link href="#how-it-works" className="text-[#0F4D35] font-medium text-sm hover:underline underline-offset-4 decoration-[#0F4D35]/30">
                How it works
              </Link>
            </div>
            <div className="pt-8 border-t border-[#0F4D35]/10">
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
            <div className="absolute top-8 left-8 bg-[#FDFBF7]/95 backdrop-blur-sm p-4 rounded-sm shadow-lg border border-[#0F4D35]/10 w-64 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-300 fill-mode-both">
              <div className="text-[10px] uppercase tracking-wider text-[#1a1a1a]/50 font-bold mb-1">
                {liveField ? `Field ${liveField.fieldId}` : 'Field REAL-001'}
              </div>
              <div className="font-medium text-[#0F4D35] text-sm">
                {liveField ? `${liveField.crop} · ${liveField.growthStage}` : 'Loading live data…'}
              </div>
            </div>
            
            {/* Live soil health + weather overlay */}
            <div className="absolute bottom-12 right-8 bg-[#FDFBF7]/95 backdrop-blur-sm p-4 rounded-sm shadow-lg border border-[#0F4D35]/10 w-56 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-500 fill-mode-both">
              <div className="flex justify-between items-end mb-3 pb-3 border-b border-[#0F4D35]/10">
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-[#1a1a1a]/50 font-bold mb-1">Soil Health</div>
                  <div className="font-medium text-[#0F4D35] text-xl">
                    {liveField ? liveField.soilHealthScore : '…'}
                    <span className="text-sm text-[#1a1a1a]/40">/100</span>
                  </div>
                </div>
                <div className="text-xs font-medium text-[#0F4D35]/70">N / P / K</div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-wider text-[#1a1a1a]/50 font-bold mb-1">{t('hero.weather')}</div>
                <div className="font-medium text-[#0F4D35] text-sm">
                  {liveField
                    ? `${liveField.weather.rainfall_mm_next_7d}mm forecast · ${liveField.weather.condition}`
                    : '28°C · Rain forecast'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
