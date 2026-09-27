import React from 'react';
import HeroSection from '@/components/landing/HeroSection';
import CapabilityStrip from '@/components/landing/CapabilityStrip';
import DigitalTwinSection from '@/components/landing/DigitalTwinSection';
import DecisionLoopSection from '@/components/landing/DecisionLoopSection';
import ProofSection from '@/components/landing/ProofSection';
import WhatIfPreview from '@/components/landing/WhatIfPreview';
import PilotRegionsSection from '@/components/landing/PilotRegionsSection';
import HumanOversightSection from '@/components/landing/HumanOversightSection';
import FinalCTA from '@/components/landing/FinalCTA';
import LandingFooter from '@/components/landing/LandingFooter';

export default function LandingPage() {
  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#FDFBF7] font-sans selection:bg-[#0F4D35] selection:text-white">
      <HeroSection />
      <CapabilityStrip />
      <DigitalTwinSection />
      <DecisionLoopSection />
      <ProofSection />
      <WhatIfPreview />
      <PilotRegionsSection />
      <HumanOversightSection />
      <FinalCTA />
      <LandingFooter />
    </div>
  );
}
