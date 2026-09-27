import os

components_dir = "/Users/lavesh/Documents/IH/agrotwin_frontend/src/components/landing"
os.makedirs(components_dir, exist_ok=True)

files = {
  "LandingNav.tsx": """import Link from 'next/link';
export default function LandingNav() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-[#e5e0d8] bg-[#FDFBF7]/90 backdrop-blur-md">
      <div className="container mx-auto px-6 h-20 flex items-center justify-between">
        <div className="flex items-center space-x-12">
          <Link href="/" className="flex flex-col">
            <span className="text-xl font-semibold text-[#0F4D35] tracking-tight">AgroTwin AI</span>
            <span className="text-[10px] text-[#0F4D35]/70 uppercase tracking-widest font-medium">Sustainable Fertilizer Support</span>
          </Link>
          <nav className="hidden md:flex items-center space-x-8 text-sm font-medium text-[#1a1a1a]/80">
            <Link href="#how-it-works" className="hover:text-[#0F4D35] transition-colors">How it works</Link>
            <Link href="#capabilities" className="hover:text-[#0F4D35] transition-colors">Capabilities</Link>
            <Link href="#pilot-regions" className="hover:text-[#0F4D35] transition-colors">Pilot regions</Link>
            <Link href="#resources" className="hover:text-[#0F4D35] transition-colors">Resources</Link>
          </nav>
        </div>
        <div className="flex items-center space-x-6">
          <Link href="/dashboard" className="hidden sm:block text-sm font-medium text-[#0F4D35] hover:text-[#0F4D35]/80 transition-colors">
            Sign In
          </Link>
          <Link href="/dashboard" className="px-5 py-2.5 rounded-sm bg-[#0F4D35] text-[#FDFBF7] text-sm font-medium hover:bg-[#0F4D35]/90 transition-colors shadow-sm">
            Open Dashboard
          </Link>
        </div>
      </div>
    </header>
  );
}
""",
  "HeroSection.tsx": """import React from 'react';
import Link from 'next/link';

export default function HeroSection() {
  return (
    <section className="relative pt-24 pb-32 overflow-hidden bg-[#FDFBF7]">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-8 items-center">
          <div className="max-w-xl">
            <div className="inline-flex items-center space-x-2 text-[11px] font-bold uppercase tracking-widest text-[#0F4D35] mb-8">
              <span>PSAI01 &middot; Sustainable Fertilizer Usage Optimizer</span>
            </div>
            <h1 className="text-5xl md:text-6xl font-medium tracking-tight text-[#0F4D35] mb-8 leading-[1.1] font-serif">
              Better decisions<br/>
              begin with a better<br/>
              understanding<br/>
              <span className="italic">of every field.</span>
            </h1>
            <p className="text-lg text-[#1a1a1a]/80 mb-10 leading-relaxed font-light">
              AgroTwin AI provides evidence-grounded, field-specific fertilizer decision support using soil data, crop type, weather and farm history — helping farmers understand what to apply, how much, and when.
            </p>
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 mb-12">
              <Link href="/dashboard" className="px-8 py-4 bg-[#0F4D35] text-[#FDFBF7] font-medium text-sm hover:bg-[#0a3625] transition-colors rounded-sm shadow-sm flex items-center group">
                Explore the platform
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
              src="https://images.unsplash.com/photo-1599839619722-39751411ea63?q=80&w=2000&auto=format&fit=crop" 
              alt="Indian agricultural field" 
              className="absolute inset-0 w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-[2s] ease-out"
            />
            {/* UI Overlays */}
            <div className="absolute top-8 left-8 bg-[#FDFBF7]/95 backdrop-blur-sm p-4 rounded-sm shadow-lg border border-[#0F4D35]/10 w-64 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-300 fill-mode-both">
              <div className="text-[10px] uppercase tracking-wider text-[#1a1a1a]/50 font-bold mb-1">Field A-104</div>
              <div className="font-medium text-[#0F4D35] text-sm">Rice &middot; Tillering Stage</div>
            </div>
            
            <div className="absolute bottom-12 right-8 bg-[#FDFBF7]/95 backdrop-blur-sm p-4 rounded-sm shadow-lg border border-[#0F4D35]/10 w-56 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-500 fill-mode-both">
              <div className="flex justify-between items-end mb-3 pb-3 border-b border-[#0F4D35]/10">
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-[#1a1a1a]/50 font-bold mb-1">Soil Health</div>
                  <div className="font-medium text-[#0F4D35] text-xl">72<span className="text-sm text-[#1a1a1a]/40">/100</span></div>
                </div>
                <div className="text-xs font-medium text-[#0F4D35]/70">N / P / K</div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-wider text-[#1a1a1a]/50 font-bold mb-1">Weather</div>
                <div className="font-medium text-[#0F4D35] text-sm">28&deg;C &middot; Rain forecast</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
""",
  "CapabilityStrip.tsx": """import React from 'react';

export default function CapabilityStrip() {
  return (
    <section id="capabilities" className="py-24 bg-[#FDFBF7] border-t border-[#0F4D35]/10">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 lg:gap-24">
          <div className="space-y-4">
            <div className="text-xs font-mono text-[#0F4D35]/40 mb-6">01</div>
            <h3 className="text-xl font-medium text-[#0F4D35]">Living Farm Digital Twin</h3>
            <p className="text-[#1a1a1a]/70 font-light leading-relaxed text-sm">
              A persistent, evolving representation of field, soil, crop, environment and nutrient history.
            </p>
          </div>
          <div className="space-y-4">
            <div className="text-xs font-mono text-[#0F4D35]/40 mb-6">02</div>
            <h3 className="text-xl font-medium text-[#0F4D35]">Continuous Monitoring</h3>
            <p className="text-[#1a1a1a]/70 font-light leading-relaxed text-sm">
              AgroTwin monitors changing conditions and can trigger re-evaluation when assumptions change.
            </p>
          </div>
          <div className="space-y-4">
            <div className="text-xs font-mono text-[#0F4D35]/40 mb-6">03</div>
            <h3 className="text-xl font-medium text-[#0F4D35]">Evidence-Grounded Recommendations</h3>
            <p className="text-[#1a1a1a]/70 font-light leading-relaxed text-sm">
              Recommendations combine field data, agronomic constraints, optimization and trusted evidence.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
""",
  "DigitalTwinSection.tsx": """import React from 'react';

export default function DigitalTwinSection() {
  const points = [
    { num: '01', title: 'Soil state', desc: 'Nutrient levels, pH, organic carbon, moisture and related signals' },
    { num: '02', title: 'Crop state', desc: 'Crop type, variety, growth stage and target yield' },
    { num: '03', title: 'Weather & environment', desc: 'Current and forecast conditions' },
    { num: '04', title: 'Farm history', desc: 'Previous applications, soil tests and yield history' },
    { num: '05', title: 'Current plan', desc: 'Field-specific fertilizer recommendation and application window' }
  ];

  return (
    <section className="py-32 bg-white">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
          <div className="order-2 lg:order-1 h-[700px] w-full bg-[#f4f2eb] rounded-sm overflow-hidden">
            <img 
              src="https://images.unsplash.com/photo-1464226184884-fa280b87c399?q=80&w=2000&auto=format&fit=crop" 
              alt="Soil and crop seedlings" 
              className="w-full h-full object-cover grayscale-[20%] sepia-[10%]"
            />
          </div>
          <div className="order-1 lg:order-2">
            <div className="text-[11px] font-bold uppercase tracking-widest text-[#0F4D35] mb-6">Digital Twin</div>
            <h2 className="text-4xl md:text-5xl font-medium text-[#0F4D35] mb-8 leading-tight font-serif">
              One field.<br/>
              One evolving picture.
            </h2>
            <p className="text-lg text-[#1a1a1a]/70 mb-12 font-light leading-relaxed max-w-md">
              AgroTwin creates a living digital twin of each field by combining soil, crop, weather, historical and ongoing observations.
            </p>
            
            <div className="space-y-0">
              {points.map((p, i) => (
                <div key={i} className="flex items-start py-6 border-t border-[#0F4D35]/10 group">
                  <div className="text-xs font-mono text-[#0F4D35]/40 w-12 pt-1 group-hover:text-[#0F4D35] transition-colors">{p.num}</div>
                  <div>
                    <h4 className="text-base font-medium text-[#0F4D35] mb-2">{p.title}</h4>
                    <p className="text-sm text-[#1a1a1a]/60 font-light">{p.desc}</p>
                  </div>
                </div>
              ))}
              <div className="border-t border-[#0F4D35]/10"></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
""",
  "DecisionLoopSection.tsx": """import React from 'react';

export default function DecisionLoopSection() {
  const steps = [
    'Observe', 'Understand', 'Predict', 'Optimize', 'Validate', 'Recommend', 'Monitor', 'Re-plan'
  ];

  return (
    <section id="how-it-works" className="py-32 bg-[#FDFBF7]">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="max-w-2xl mb-20">
          <div className="text-[11px] font-bold uppercase tracking-widest text-[#0F4D35] mb-6">How it works</div>
          <h2 className="text-4xl md:text-5xl font-medium text-[#0F4D35] mb-6 leading-tight font-serif">
            The plan changes<br/>when the field changes.
          </h2>
          <p className="text-lg text-[#1a1a1a]/70 font-light leading-relaxed">
            A continuous system that monitors, detects changes and re-evaluates the plan when conditions evolve.
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
                <p className="text-xs text-[#1a1a1a]/50 font-light">Continuous process step.</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
""",
  "ProofSection.tsx": """import React from 'react';
import Link from 'next/link';

export default function ProofSection() {
  const questions = [
    "WHAT should I apply?",
    "HOW MUCH is right for my field?",
    "WHEN should I apply it?",
    "WHY is this the right plan?",
    "BASED ON WHAT evidence?",
    "HOW SURE are we?"
  ];

  return (
    <section className="bg-[#0F4D35] text-[#FDFBF7] relative overflow-hidden flex flex-col md:flex-row">
      <div className="md:w-1/2 min-h-[400px] md:min-h-[800px] relative">
        <img 
          src="https://images.unsplash.com/photo-1592982537447-6f296317bc30?q=80&w=1500&auto=format&fit=crop" 
          alt="Soil detail" 
          className="absolute inset-0 w-full h-full object-cover mix-blend-overlay opacity-50 grayscale"
        />
        <div className="absolute inset-0 bg-[#0F4D35]/60 mix-blend-multiply"></div>
        <div className="absolute inset-0 p-12 md:p-24 flex flex-col justify-center max-w-xl mx-auto md:ml-auto md:mr-0 z-10">
          <div className="text-[11px] font-bold uppercase tracking-widest text-[#FDFBF7]/60 mb-6">Explainability</div>
          <h2 className="text-4xl md:text-5xl font-medium text-white mb-8 leading-tight font-serif">
            Every recommendation<br/>carries its proof.
          </h2>
          <p className="text-lg text-[#FDFBF7]/80 mb-12 font-light leading-relaxed">
            A good recommendation should make its reasoning visible — what was used, which agronomic knowledge it draws from, and how confident the system is.
          </p>
          <Link href="/dashboard" className="inline-flex items-center text-[#d4af37] font-medium text-sm hover:text-white transition-colors group">
            View an example
            <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </Link>
        </div>
      </div>
      
      <div className="md:w-1/2 bg-[#0a3625] p-12 md:p-24 flex flex-col justify-center">
        <div className="max-w-xl mx-auto md:mx-0 w-full">
          {questions.map((q, i) => (
            <div key={i} className="group border-b border-white/10 last:border-0">
              <button className="w-full flex items-center justify-between py-8 text-left focus:outline-none">
                <div className="flex items-center">
                  <span className="text-xs font-mono text-white/30 mr-6">0{i+1}</span>
                  <span className="text-lg font-medium text-white/90 group-hover:text-white transition-colors">{q}</span>
                </div>
                <svg className="w-5 h-5 text-white/30 group-hover:text-white transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
""",
  "WhatIfPreview.tsx": """import React from 'react';
import Link from 'next/link';

export default function WhatIfPreview() {
  return (
    <section className="py-32 bg-white">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-widest text-[#0F4D35] mb-6">What-If Simulator</div>
            <h2 className="text-4xl md:text-5xl font-medium text-[#0F4D35] mb-8 leading-tight font-serif">
              Test a change<br/>
              before it reaches<br/>
              the field.
            </h2>
            <p className="text-lg text-[#1a1a1a]/70 mb-12 font-light leading-relaxed max-w-md">
              Explore supported changes to fertilizer, application timing, rainfall, irrigation or target yield and compare the resulting scenario with the current plan.
            </p>
            <div className="mb-12">
              <h4 className="text-xs font-bold uppercase tracking-widest text-[#1a1a1a]/40 mb-4">Supported Pilot Crops</h4>
              <div className="flex gap-4">
                {['Banana', 'Cotton', 'Sugarcane', 'Rice'].map(c => (
                  <span key={c} className="px-3 py-1 bg-[#FDFBF7] border border-[#0F4D35]/10 text-xs font-medium text-[#0F4D35] rounded-sm">{c}</span>
                ))}
              </div>
            </div>
            <Link href="/simulator" className="px-8 py-4 bg-[#FDFBF7] border border-[#0F4D35] text-[#0F4D35] font-medium text-sm hover:bg-[#0F4D35] hover:text-white transition-colors rounded-sm inline-flex items-center group">
              Try the simulator
              <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </Link>
          </div>
          
          <div className="bg-[#FDFBF7] rounded-sm p-8 border border-[#0F4D35]/10 shadow-sm relative">
            <div className="space-y-6">
              <div className="p-4 bg-white border border-[#0F4D35]/10 rounded-sm">
                <div className="text-xs font-medium text-[#0F4D35] mb-4">Scenario Controls</div>
                <div className="h-1 w-full bg-[#0F4D35]/10 rounded-full mb-2">
                  <div className="h-1 w-2/3 bg-[#0F4D35] rounded-full"></div>
                </div>
                <div className="text-[10px] text-[#1a1a1a]/50">Fertilizer Target: -20%</div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-white border border-[#0F4D35]/10 rounded-sm">
                  <div className="text-[10px] uppercase tracking-widest text-[#1a1a1a]/50 mb-2">Current Plan</div>
                  <div className="text-sm font-medium text-[#0F4D35] mb-1">120kg N / ha</div>
                  <div className="text-xs text-[#1a1a1a]/50">Yield: High</div>
                </div>
                <div className="p-4 bg-[#0F4D35]/5 border border-[#0F4D35]/20 rounded-sm relative">
                  <div className="absolute -top-2 right-2 px-2 py-0.5 bg-[#0F4D35] text-white text-[9px] font-bold rounded-sm">WHAT-IF</div>
                  <div className="text-[10px] uppercase tracking-widest text-[#0F4D35]/70 mb-2">Projection</div>
                  <div className="text-sm font-medium text-[#0F4D35] mb-1">96kg N / ha</div>
                  <div className="text-xs text-[#0F4D35]/70">Yield: Maintained</div>
                </div>
              </div>
              
              <div className="h-32 bg-white border border-[#0F4D35]/10 rounded-sm flex items-end justify-center pb-4 relative overflow-hidden">
                <div className="absolute inset-0 bg-[#0F4D35]/5"></div>
                <div className="w-1 h-16 bg-[#0F4D35] rounded-t-full relative z-10">
                  <div className="absolute bottom-4 left-1 w-4 h-1 rounded-full bg-[#0F4D35] origin-left -rotate-45"></div>
                  <div className="absolute bottom-8 right-1 w-4 h-1 rounded-full bg-[#0F4D35] origin-right rotate-45"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
""",
  "PilotRegionsSection.tsx": """import React from 'react';

export default function PilotRegionsSection() {
  return (
    <section id="pilot-regions" className="py-32 bg-[#FDFBF7] border-t border-[#0F4D35]/10">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-widest text-[#0F4D35] mb-6">Pilot Regions</div>
            <h2 className="text-4xl md:text-5xl font-medium text-[#0F4D35] mb-8 leading-tight font-serif">
              Starting close<br/>to home.
            </h2>
            <p className="text-lg text-[#1a1a1a]/70 mb-12 font-light leading-relaxed max-w-md">
              AgroTwin is being piloted in key agricultural regions of Maharashtra, with crop-specific configurations and regional context.
            </p>
            
            <div className="space-y-8">
              <div className="flex gap-6 items-start">
                <div className="w-2 h-2 rounded-full bg-[#0F4D35] mt-2"></div>
                <div>
                  <h4 className="text-lg font-medium text-[#0F4D35] mb-1">Jalgaon</h4>
                  <p className="text-sm text-[#1a1a1a]/60">Banana &middot; Cotton</p>
                </div>
              </div>
              <div className="flex gap-6 items-start">
                <div className="w-2 h-2 rounded-full bg-[#0F4D35] mt-2"></div>
                <div>
                  <h4 className="text-lg font-medium text-[#0F4D35] mb-1">Kolhapur</h4>
                  <p className="text-sm text-[#1a1a1a]/60">Sugarcane &middot; Rice</p>
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-[#eaddce]/30 aspect-square rounded-full flex items-center justify-center p-12 relative max-w-md mx-auto w-full">
             <div className="w-full h-full rounded-full border border-[#0F4D35]/20 absolute animate-pulse duration-[3000ms]"></div>
             <div className="w-3/4 h-3/4 rounded-full border border-[#0F4D35]/10 absolute"></div>
             <div className="relative text-center">
                <div className="text-xs font-mono text-[#0F4D35]/60 mb-2">MAHARASHTRA</div>
                <div className="w-48 h-48 bg-[#FDFBF7] shadow-sm rounded-sm border border-[#0F4D35]/10 flex flex-col justify-between p-4">
                  <div className="text-left">
                    <div className="w-2 h-2 bg-[#d4af37] rounded-full mb-1"></div>
                    <div className="text-[9px] font-bold text-[#1a1a1a]/60">JALGAON</div>
                  </div>
                  <div className="text-right">
                    <div className="w-2 h-2 bg-[#0F4D35] rounded-full mb-1 inline-block"></div>
                    <div className="text-[9px] font-bold text-[#1a1a1a]/60">KOLHAPUR</div>
                  </div>
                </div>
             </div>
          </div>
        </div>
      </div>
    </section>
  );
}
""",
  "HumanOversightSection.tsx": """import React from 'react';

export default function HumanOversightSection() {
  const checks = [
    "Confidence and data-quality checks",
    "Clear reasons when a recommendation is not issued",
    "Agronomist review and override support",
    "Audit trail for important decisions"
  ];

  return (
    <section className="py-32 bg-white">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
          <div className="h-[600px] w-full bg-[#f4f2eb] rounded-sm overflow-hidden relative">
            <img 
              src="https://images.unsplash.com/photo-1595801323386-8153406e231e?q=80&w=2000&auto=format&fit=crop" 
              alt="Agronomist reviewing data" 
              className="w-full h-full object-cover grayscale-[10%]"
            />
            <div className="absolute bottom-8 left-8 bg-[#FDFBF7] p-4 rounded-sm shadow-lg border-l-2 border-[#d4af37] w-64">
              <div className="flex items-center gap-2 mb-2">
                <svg className="w-4 h-4 text-[#d4af37]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span className="text-xs font-bold text-[#1a1a1a]">Needs Review</span>
              </div>
              <p className="text-[11px] text-[#1a1a1a]/70">Conflicting soil test results detected. Agronomist review required before recommendation.</p>
            </div>
          </div>
          
          <div>
            <div className="text-[11px] font-bold uppercase tracking-widest text-[#0F4D35] mb-6">Human Oversight</div>
            <h2 className="text-4xl md:text-5xl font-medium text-[#0F4D35] mb-8 leading-tight font-serif">
              Technology should know<br/>
              when to pause.
            </h2>
            <p className="text-lg text-[#1a1a1a]/70 mb-10 font-light leading-relaxed max-w-md">
              AgroTwin is designed to surface low-confidence cases, missing data, conflicting evidence and unusual conditions rather than silently producing unsupported recommendations.
            </p>
            
            <ul className="space-y-4">
              {checks.map((check, i) => (
                <li key={i} className="flex items-center text-sm text-[#1a1a1a]/80 font-medium">
                  <svg className="w-4 h-4 text-[#0F4D35] mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
""",
  "FinalCTA.tsx": """import React from 'react';
import Link from 'next/link';

export default function FinalCTA() {
  return (
    <section className="relative py-40 bg-[#0F4D35] text-[#FDFBF7] overflow-hidden text-center">
      <img 
        src="https://images.unsplash.com/photo-1500382017468-9049fed747ef?q=80&w=2500&auto=format&fit=crop" 
        alt="Agricultural landscape" 
        className="absolute inset-0 w-full h-full object-cover opacity-20 mix-blend-luminosity"
      />
      <div className="absolute inset-0 bg-[#0F4D35]/80"></div>
      
      <div className="relative z-10 container mx-auto px-6 max-w-3xl">
        <h2 className="text-4xl md:text-6xl font-medium text-white mb-8 leading-tight font-serif">
          From one-time recommendations to continuous farm intelligence.
        </h2>
        <p className="text-xl text-[#FDFBF7]/80 mb-12 font-light leading-relaxed max-w-2xl mx-auto">
          AgroTwin continuously connects field conditions, evidence and decision support.
        </p>
        <Link href="/dashboard" className="inline-flex px-10 py-5 bg-[#FDFBF7] text-[#0F4D35] font-medium hover:bg-white transition-colors rounded-sm shadow-lg items-center group">
          Open AgroTwin
          <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        </Link>
      </div>
    </section>
  );
}
""",
  "LandingFooter.tsx": """import React from 'react';
import Link from 'next/link';

export default function LandingFooter() {
  return (
    <footer className="bg-[#FDFBF7] border-t border-[#0F4D35]/10 py-16">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
          
          <div>
            <div className="text-xl font-semibold text-[#0F4D35] mb-2 tracking-tight">AgroTwin AI</div>
            <p className="text-sm text-[#1a1a1a]/60 font-light mb-6">Sustainable fertilizer decision support</p>
            <div className="text-[10px] uppercase tracking-widest text-[#1a1a1a]/40 font-bold">
              Problem Statement:<br/>
              <span className="text-[#0F4D35]">PSAI01</span>
            </div>
          </div>
          
          <div className="flex flex-col space-y-4 text-sm font-medium text-[#1a1a1a]/70">
            <Link href="/" className="hover:text-[#0F4D35] transition-colors w-fit">Home</Link>
            <Link href="#how-it-works" className="hover:text-[#0F4D35] transition-colors w-fit">How it works</Link>
            <Link href="#capabilities" className="hover:text-[#0F4D35] transition-colors w-fit">Capabilities</Link>
            <Link href="#pilot-regions" className="hover:text-[#0F4D35] transition-colors w-fit">Pilot regions</Link>
            <Link href="/resources" className="hover:text-[#0F4D35] transition-colors w-fit">Resources</Link>
          </div>
          
          <div className="md:text-right text-sm text-[#1a1a1a]/50 font-light">
            <p className="mb-2">Built for sustainable agriculture</p>
            <p>Maharashtra pilot</p>
          </div>
          
        </div>
      </div>
    </footer>
  );
}
"""
}

for filename, content in files.items():
    filepath = os.path.join(components_dir, filename)
    with open(filepath, 'w') as f:
        f.write(content)

print(f"Created {len(files)} components in {components_dir}")
