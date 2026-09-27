"use client";

import React, { useState } from 'react';

export interface CropModelProps {
  cropType: 'Banana' | 'Cotton' | 'Sugarcane' | 'Rice' | string;
  growthStage: string;
  vigor: 'thriving' | 'healthy' | 'below-average' | 'stressed';
  nutrientSufficiency: 'optimal' | 'suboptimal' | 'deficient';
  waterStress: 'none' | 'moderate' | 'high';
  confidence: 'HIGH' | 'MEDIUM' | 'LOW' | 'ABSTAIN';
}

export function CropModel({ cropType, vigor, confidence }: CropModelProps) {
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

  let embedContent = null;
  const is3DModel = ['Banana', 'Rice', 'Cotton'].includes(cropType);
  
  if (cropType === 'Banana') {
    embedContent = (
      <div className="sketchfab-embed-wrapper w-full h-full relative z-0">
        <iframe title="Banana Tree" className="w-full h-full" frameBorder="0" allowFullScreen allow="autoplay; fullscreen; xr-spatial-tracking" xr-spatial-tracking="true" execution-while-out-of-viewport="true" execution-while-not-rendered="true" web-share="true" src="https://sketchfab.com/models/5cb46e64d7fc40978c3d6798017eced1/embed"> </iframe>
      </div>
    );
  } else if (cropType === 'Rice') {
    embedContent = (
      <div className="sketchfab-embed-wrapper w-full h-full relative z-0">
        <iframe title="Rice Plant" className="w-full h-full" frameBorder="0" allowFullScreen allow="autoplay; fullscreen; xr-spatial-tracking" xr-spatial-tracking="true" execution-while-out-of-viewport="true" execution-while-not-rendered="true" web-share="true" src="https://sketchfab.com/models/be6aa4ac9adc4f558cc789a0baed8ae3/embed"> </iframe>
      </div>
    );
  } else if (cropType === 'Cotton') {
    embedContent = (
      <div className="sketchfab-embed-wrapper w-full h-full relative z-0">
        <iframe title="Cotton branch" className="w-full h-full" frameBorder="0" allowFullScreen allow="autoplay; fullscreen; xr-spatial-tracking" xr-spatial-tracking="true" execution-while-out-of-viewport="true" execution-while-not-rendered="true" web-share="true" src="https://sketchfab.com/models/6c6c90de4626417a92f846ad06e551fa/embed"> </iframe>
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
      <div className="w-full h-64 bg-blue-50/30 rounded-lg flex flex-col items-center justify-end overflow-hidden border border-border relative group">
        <div className="absolute top-2 left-2 px-2 py-1 bg-white/80 rounded text-xs font-semibold text-muted backdrop-blur-sm shadow-sm z-10 pointer-events-none">
          {cropType} Projection
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
