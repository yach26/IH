"use client";

import React, { useState } from 'react';

export interface CropModelProps {
  cropType: 'Banana' | 'Cotton' | 'Sugarcane' | 'Rice' | string;
  growthStage: string;
  vigor: 'thriving' | 'healthy' | 'below-average' | 'stressed';
  nutrientSufficiency: 'optimal' | 'suboptimal' | 'deficient' | 'unknown';
  waterStress: 'none' | 'moderate' | 'high' | 'unknown';
  confidence: 'HIGH' | 'MEDIUM' | 'LOW' | 'ABSTAIN';
  label?: string;
}

const SKETCHFAB_IDS: Record<string, { id: string; title: string }> = {
  Banana: { id: '5cb46e64d7fc40978c3d6798017eced1', title: 'Banana Tree' },
  Rice: { id: 'be6aa4ac9adc4f558cc789a0baed8ae3', title: 'Rice Plant' },
  Cotton: { id: '6c6c90de4626417a92f846ad06e551fa', title: 'Cotton Branch' },
  Sugarcane: { id: '9506c8f11aa6465d92f868086b367be4', title: 'Sugarcane' },
};

// A static Sketchfab scene can't be re-lit or deformed without the paid API,
// so vigor is shown as a CSS filter over the embed plus a text badge —
// deterministic from real scenario data, never a separate animation state.
const VIGOR_STYLE: Record<CropModelProps['vigor'], { filter: string; ring: string; badge: string; label: string }> = {
  thriving: { filter: 'saturate(1.15) brightness(1.05)', ring: 'ring-green-400', badge: 'bg-green-100 text-green-800', label: 'Thriving' },
  healthy: { filter: 'none', ring: 'ring-transparent', badge: 'bg-green-50 text-green-700', label: 'Healthy' },
  'below-average': { filter: 'saturate(0.7) brightness(0.95) sepia(0.08)', ring: 'ring-amber-400', badge: 'bg-amber-100 text-amber-800', label: 'Below Average' },
  stressed: { filter: 'saturate(0.4) brightness(0.85) sepia(0.15)', ring: 'ring-red-400', badge: 'bg-red-100 text-red-800', label: 'Stressed' },
};

export function CropModel({ cropType, growthStage, vigor, nutrientSufficiency, waterStress, confidence, label }: CropModelProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);

  // If model confidence is low, we degrade gracefully rather than showing a hallucinated plant
  if (confidence === 'LOW' || confidence === 'ABSTAIN') {
    return (
      <div className="w-full h-48 bg-surface-hover rounded-lg flex flex-col items-center justify-center border border-dashed border-border p-4 text-center">
        <svg className="w-8 h-8 text-muted mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="text-sm text-muted">Not enough data to project growth</span>
      </div>
    );
  }

  // Map vigor to visual colors/styles
  const styles = {
    thriving: { color: '#166534', height: 'h-40', leafCount: 5 },
    healthy: { color: '#22c55e', height: 'h-36', leafCount: 4 },
    'below-average': { color: '#eab308', height: 'h-28', leafCount: 3 },
    stressed: { color: '#c2410c', height: 'h-20', leafCount: 2 },
  };

  const style = styles[vigor] || styles.healthy;
  const vigorStyle = VIGOR_STYLE[vigor] || VIGOR_STYLE.healthy;
  const model = SKETCHFAB_IDS[cropType];
  const is3DModel = Boolean(model);

  let embedContent = null;

  if (model) {
    embedContent = (
      <div className="sketchfab-embed-wrapper w-full h-full relative z-0 transition-[filter] duration-700" style={{ filter: vigorStyle.filter }}>
        <iframe title={model.title} className="w-full h-full" frameBorder="0" allowFullScreen allow="autoplay; fullscreen; xr-spatial-tracking" xr-spatial-tracking="true" execution-while-out-of-viewport="true" execution-while-not-rendered="true" web-share="true" src={`https://sketchfab.com/models/${model.id}/embed`}> </iframe>
      </div>
    );
  } else {
    embedContent = (
      <>
        {/* Illustrative Plant SVG */}
        <div className={`relative w-24 flex justify-center items-end transition-all duration-700 ${style.height} z-0`}>
          {/* Stem */}
          <div className="absolute bottom-0 w-2 h-full rounded-t-full bg-current transition-colors duration-700" style={{ color: style.color }} />
          {/* Leaves */}
          {Array.from({ length: style.leafCount }).map((_, i) => (
            <div 
              key={i}
              className={`absolute w-12 h-4 rounded-full bg-current transition-colors duration-700 ${i % 2 === 0 ? 'origin-bottom-left -rotate-45 left-12' : 'origin-bottom-right rotate-45 right-12'}`}
              style={{ 
                color: style.color,
                bottom: `${(i + 1) * 20}%`,
                opacity: 1 - (i * 0.1) 
              }}
            />
          ))}
        </div>
        
        {/* Ground */}
        <div className="w-full h-4 bg-amber-900/20 z-0" />
      </>
    );
  }

  return (
    <>
      <div className={`w-full h-64 bg-blue-50/30 rounded-lg flex flex-col items-center justify-end overflow-hidden border border-border relative group ring-2 ${vigorStyle.ring} transition-colors duration-700`}>
        <div className="absolute top-2 left-2 px-2 py-1 bg-white/80 rounded text-xs font-semibold text-muted backdrop-blur-sm shadow-sm z-10 pointer-events-none">
          {label || cropType}{growthStage ? ` · ${growthStage}` : ''}
        </div>
        <div className={`absolute top-2 right-2 z-10 px-2 py-1 rounded text-[10px] font-bold backdrop-blur-sm shadow-sm pointer-events-none ${vigorStyle.badge} ${is3DModel ? 'mr-9' : ''}`}>
          {vigorStyle.label}
        </div>

        {is3DModel && (
          <button
            onClick={() => setIsFullscreen(true)}
            className="absolute top-2 right-2 z-20 p-2 bg-white/90 rounded-full shadow-sm text-primary hover:bg-primary hover:text-white transition-all opacity-0 group-hover:opacity-100 scale-95 group-hover:scale-100"
            title="View Fullscreen"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>
        )}

        {embedContent}
      </div>
      {(nutrientSufficiency !== 'unknown' || waterStress !== 'unknown') && (
        <div className="mt-2 flex flex-wrap gap-2 text-[11px]">
          {nutrientSufficiency !== 'unknown' && (
            <span className="rounded-full border border-border bg-surface px-2 py-0.5 text-muted">Nutrients: <span className="font-semibold text-foreground">{nutrientSufficiency}</span></span>
          )}
          {waterStress !== 'unknown' && (
            <span className="rounded-full border border-border bg-surface px-2 py-0.5 text-muted">Water stress: <span className="font-semibold text-foreground">{waterStress}</span></span>
          )}
        </div>
      )}

      {isFullscreen && is3DModel && (
        <div className="fixed inset-0 z-[100] bg-black/95 backdrop-blur-sm flex items-center justify-center p-4 md:p-12 animate-in fade-in duration-300">
          <button 
            onClick={() => setIsFullscreen(false)}
            className="absolute top-6 right-6 z-[110] p-3 bg-white/10 hover:bg-white/20 text-white rounded-full transition-colors backdrop-blur-md"
            title="Close Fullscreen"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          
          <div className="w-full max-w-6xl h-[80vh] md:h-[90vh] bg-[#1a1a1a] rounded-xl overflow-hidden relative shadow-2xl border border-white/10 flex flex-col">
            <div className="absolute top-4 left-4 z-10 px-4 py-2 bg-black/50 border border-white/10 rounded-md text-white/90 text-sm font-medium backdrop-blur-md">
              <span className="text-[#d4af37]">{cropType}</span> &middot; Interactive 3D Digital Twin
            </div>
            
            <div className="flex-1 w-full h-full">
              {embedContent}
            </div>
            
            <div className="absolute bottom-4 left-4 z-10 px-4 py-2 bg-black/50 border border-white/10 rounded-md text-white/70 text-xs backdrop-blur-md max-w-md hidden md:block">
              Drag to rotate &middot; Scroll to zoom &middot; Pan to inspect field details
            </div>
          </div>
        </div>
      )}
    </>
  );
}
