"use client";
import { useLanguage } from "@/contexts/LanguageContext";
import React from 'react';
import Link from 'next/link';

export default function WhatIfPreview() {
  const { t } = useLanguage();
  return (
    <section className="py-32 bg-[#FAFAFA]">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_2fr] gap-16 items-center">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-widest text-[#15803D] mb-6">{t("wi.badge")}</div>
            <h2 className="text-4xl md:text-5xl font-medium text-[#15803D] mb-8 leading-tight font-serif">
              {t("wi.title1")}<br/>
              {t("wi.title2")}<br/>
              {t("wi.title3")}
            </h2>
            <p className="text-lg text-[#1a1a1a]/70 mb-12 font-light leading-relaxed">
              {t("wi.subtitle")}
            </p>
            <Link href="/simulator" className="px-8 py-4 bg-[#15803D] text-white font-medium text-sm hover:bg-[#0a3625] transition-colors rounded-sm inline-flex items-center group shadow-sm">
              {t("wi.try")}
              <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </Link>
          </div>
          
          <div className="flex flex-col md:flex-row gap-4 items-stretch">
            {/* Scenario Controls */}
            <div className="flex-1 bg-white p-6 rounded-sm border border-[#15803D]/10 shadow-sm">
              <div className="text-sm font-bold text-[#1a1a1a] mb-6">{t("wi.scen")}</div>
              
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between text-xs text-[#1a1a1a]/70 mb-2">
                    <span>{t("wi.fert")}</span>
                  </div>
                  <div className="font-medium text-sm mb-2">₹ 3,500 / acre</div>
                  <div className="h-1.5 w-full bg-[#FAFAFA] border border-[#15803D]/10 rounded-full relative">
                    <div className="absolute left-0 top-0 bottom-0 w-3/4 bg-[#15803D] rounded-full"></div>
                    <div className="absolute left-[75%] top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 border-[#15803D] rounded-full shadow-sm"></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs text-[#1a1a1a]/70 mb-2">
                    <span>{t("wi.delay")}</span>
                  </div>
                  <div className="font-medium text-sm mb-2">0 days</div>
                  <div className="h-1.5 w-full bg-[#FAFAFA] border border-[#15803D]/10 rounded-full relative">
                    <div className="absolute left-0 top-0 bottom-0 w-[10%] bg-[#15803D] rounded-full"></div>
                    <div className="absolute left-[10%] top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 border-[#15803D] rounded-full shadow-sm"></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs text-[#1a1a1a]/70 mb-2">
                    <span>{t("wi.target")}</span>
                  </div>
                  <div className="font-medium text-sm mb-2">6.8 t/acre</div>
                  <div className="h-1.5 w-full bg-[#FAFAFA] border border-[#15803D]/10 rounded-full relative">
                    <div className="absolute left-0 top-0 bottom-0 w-[60%] bg-[#15803D] rounded-full"></div>
                    <div className="absolute left-[60%] top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 border-[#15803D] rounded-full shadow-sm"></div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* 3D Model Visualization */}
            <div className="flex-[2] bg-white p-6 rounded-sm border border-[#15803D]/10 shadow-sm flex flex-col">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <div className="text-sm font-bold text-[#1a1a1a]">{t("wi.plan")}</div>
                  <div className="text-[10px] text-[#1a1a1a]/50">+ 20% Fertilizer</div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-[#1a1a1a]/50">Rice &middot; A-104</div>
                </div>
              </div>
              
              <div className="flex-1 bg-blue-50/20 rounded-sm relative overflow-hidden min-h-[250px] border border-[#15803D]/5 mb-4">
                <div className="sketchfab-embed-wrapper absolute inset-0 w-full h-full">
                  <iframe 
                    title="Rice Plant" 
                    className="w-full h-full" 
                    frameBorder="0" 
                    allowFullScreen
                    allow="autoplay; fullscreen; xr-spatial-tracking"
                    xr-spatial-tracking="true" 
                    execution-while-out-of-viewport="true" 
                    execution-while-not-rendered="true" 
                    web-share="true" 
                    src="https://sketchfab.com/models/be6aa4ac9adc4f558cc789a0baed8ae3/embed">
                  </iframe>
                </div>
                <div className="absolute top-2 right-2 bg-white/80 backdrop-blur-sm px-2 py-1 text-[9px] font-bold text-[#15803D] rounded-sm pointer-events-none">
                  Heading (Projected)
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-[#1a1a1a]/50">{t("wi.estY")}</span> <span className="font-medium text-[#15803D]">6.8 t/acre</span>
                </div>
                <div>
                  <span className="text-[#1a1a1a]/50">{t("wi.estC")}</span> <span className="font-medium text-[#15803D]">₹ 3,450/acre</span>
                </div>
              </div>
            </div>

            {/* Supported Crops */}
            <div className="hidden lg:flex flex-col gap-4 py-4 px-2 justify-center">
              <div className="text-[10px] font-bold uppercase tracking-widest text-[#1a1a1a]/40 mb-2">{t("wi.sup")}</div>
              {[
                { name: 'Banana', region: 'Jalgaon' },
                { name: 'Cotton', region: 'Jalgaon' },
                { name: 'Sugarcane', region: 'Kolhapur' },
                { name: 'Rice', region: 'Kolhapur' }
              ].map(crop => (
                <div key={crop.name} className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#15803D]/5 border border-[#15803D]/10 flex items-center justify-center text-[#15803D] shadow-sm">
                    {/* Tiny dot icon as placeholder for plant icon */}
                    <div className="w-2 h-2 rounded-full bg-[#15803D]/60"></div>
                  </div>
                  <div>
                    <div className="text-xs font-medium text-[#1a1a1a]">{crop.name}</div>
                    <div className="text-[9px] text-[#1a1a1a]/40">{crop.region}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
