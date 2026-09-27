import os
import re

# 1. Create LanguageContext.tsx
os.makedirs('src/contexts', exist_ok=True)
with open('src/contexts/LanguageContext.tsx', 'w') as f:
    f.write(""""use client";

import React, { createContext, useContext, useState, ReactNode } from 'react';

type Language = 'en' | 'hi' | 'mr';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const translations: Record<Language, Record<string, string>> = {
  en: {
    'nav.home': 'Home',
    'nav.howItWorks': 'How it works',
    'nav.capabilities': 'Capabilities',
    'nav.pilotRegions': 'Pilot regions',
    'nav.resources': 'Resources',
    'nav.openDashboard': 'Open dashboard',
    
    'hero.title.1': 'Better decisions',
    'hero.title.2': 'begin with a better',
    'hero.title.3': 'understanding',
    'hero.title.4': 'of every field.',
    'hero.subtitle': 'AgroTwin AI provides evidence-grounded, field-specific fertilizer decision support using soil data, crop type, weather and farm history — helping farmers use the right nutrients, at the right time.',
    'hero.explore': 'Explore the platform',
    'hero.howItWorks': 'How it works',
    'hero.badge': 'AGROTWIN AI - SUSTAINABLE FERTILIZER USAGE OPTIMIZER',
    
    'hero.currentPlan': 'Current Plan',
    'hero.applyUrea': 'Apply Urea (46-0-0)',
    'hero.in2Days': 'in 2 days',
    'hero.weather': 'Weather',
    'hero.lightRain': 'Light Rain'
  },
  hi: {
    'nav.home': 'होम',
    'nav.howItWorks': 'यह कैसे काम करता है',
    'nav.capabilities': 'क्षमताएं',
    'nav.pilotRegions': 'पायलट क्षेत्र',
    'nav.resources': 'संसाधन',
    'nav.openDashboard': 'डैशबोर्ड खोलें',
    
    'hero.title.1': 'बेहतर निर्णय',
    'hero.title.2': 'हर खेत की',
    'hero.title.3': 'बेहतर समझ',
    'hero.title.4': 'से शुरू होते हैं।',
    'hero.subtitle': 'एग्रोट्विन एआई मिट्टी के डेटा, फसल के प्रकार, मौसम और खेत के इतिहास का उपयोग करके साक्ष्य-आधारित उर्वरक निर्णय समर्थन प्रदान करता है - जिससे किसानों को सही समय पर सही पोषक तत्वों का उपयोग करने में मदद मिलती है।',
    'hero.explore': 'प्लेटफ़ॉर्म एक्सप्लोर करें',
    'hero.howItWorks': 'यह कैसे काम करता है',
    'hero.badge': 'एग्रोट्विन एआई - सतत उर्वरक उपयोग अनुकूलक',
    
    'hero.currentPlan': 'वर्तमान योजना',
    'hero.applyUrea': 'यूरिया डालें (46-0-0)',
    'hero.in2Days': '2 दिन में',
    'hero.weather': 'मौसम',
    'hero.lightRain': 'हल्की बारिश'
  },
  mr: {
    'nav.home': 'मुख्यपृष्ठ',
    'nav.howItWorks': 'हे कसे काम करते',
    'nav.capabilities': 'क्षमता',
    'nav.pilotRegions': 'पायलट क्षेत्र',
    'nav.resources': 'संसाधने',
    'nav.openDashboard': 'डॅशबोर्ड उघडा',
    
    'hero.title.1': 'उत्तम निर्णय',
    'hero.title.2': 'प्रत्येक शेताच्या',
    'hero.title.3': 'उत्तम आकलनापासून',
    'hero.title.4': 'सुरू होतात.',
    'hero.subtitle': 'AgroTwin AI मातीचा डेटा, पिकाचा प्रकार, हवामान आणि शेताचा इतिहास वापरून पुराव्यावर आधारित खत निर्णय समर्थन प्रदान करते — शेतकऱ्यांना योग्य वेळी योग्य पोषक तत्वे वापरण्यास मदत करते.',
    'hero.explore': 'प्लॅटफॉर्म एक्सप्लोर करा',
    'hero.howItWorks': 'हे कसे काम करते',
    'hero.badge': 'ऍग्रोट्विन एआय - शाश्वत खत वापर ऑप्टिमायझर',
    
    'hero.currentPlan': 'सध्याची योजना',
    'hero.applyUrea': 'युरिया लागू करा (46-0-0)',
    'hero.in2Days': '2 दिवसांत',
    'hero.weather': 'हवामान',
    'hero.lightRain': 'हलका पाऊस'
  }
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>('en');

  const t = (key: string): string => {
    return translations[language][key] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
""")

# 2. Create LanguageSwitcher.tsx
os.makedirs('src/components/ui', exist_ok=True)
with open('src/components/ui/LanguageSwitcher.tsx', 'w') as f:
    f.write(""""use client";

import React, { useState, useRef, useEffect } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';

export default function LanguageSwitcher() {
  const { language, setLanguage } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const languages = [
    { code: 'en', label: 'English', short: 'EN' },
    { code: 'hi', label: 'हिंदी', short: 'HI' },
    { code: 'mr', label: 'मराठी', short: 'MR' }
  ];

  const currentLang = languages.find(l => l.code === language) || languages[0];

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[#0F4D35]/20 hover:bg-[#0F4D35]/5 transition-colors text-sm font-medium text-[#0F4D35]"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
        </svg>
        {currentLang.short}
        <svg className="w-3 h-3 ml-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-32 bg-white rounded-md shadow-lg border border-[#0F4D35]/10 z-50 overflow-hidden">
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => {
                setLanguage(lang.code as 'en' | 'hi' | 'mr');
                setIsOpen(false);
              }}
              className={`w-full text-left px-4 py-2 text-sm transition-colors hover:bg-[#FDFBF7] ${language === lang.code ? 'font-bold text-[#0F4D35] bg-[#0F4D35]/5' : 'text-[#1a1a1a]/70'}`}
            >
              {lang.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
""")

# 3. Update layout.tsx
layout_path = 'src/app/layout.tsx'
with open(layout_path, 'r') as f:
    layout_content = f.read()

if 'LanguageProvider' not in layout_content:
    layout_content = layout_content.replace(
        "import TopNavigation from '@/components/layout/TopNavigation';", 
        "import TopNavigation from '@/components/layout/TopNavigation';\nimport { LanguageProvider } from '@/contexts/LanguageContext';"
    )
    layout_content = layout_content.replace(
        "<TopNavigation />",
        "<LanguageProvider>\n          <TopNavigation />"
    )
    layout_content = layout_content.replace(
        "{children}\n        </div>\n      </body>",
        "{children}\n        </LanguageProvider>\n        </div>\n      </body>"
    )
    with open(layout_path, 'w') as f:
        f.write(layout_content)

# 4. Update LandingNav.tsx
nav_path = 'src/components/landing/LandingNav.tsx'
with open(nav_path, 'r') as f:
    nav_content = f.read()

nav_content = nav_content.replace(
    "import Link from 'next/link';",
    "import Link from 'next/link';\nimport LanguageSwitcher from '@/components/ui/LanguageSwitcher';\nimport { useLanguage } from '@/contexts/LanguageContext';"
)
nav_content = nav_content.replace(
    "export default function LandingNav() {",
    "export default function LandingNav() {\n  const { t } = useLanguage();"
)
nav_content = nav_content.replace(">Home<", ">{t('nav.home')}<")
nav_content = nav_content.replace(">How it works<", ">{t('nav.howItWorks')}<")
nav_content = nav_content.replace(">Capabilities<", ">{t('nav.capabilities')}<")
nav_content = nav_content.replace(">Pilot regions<", ">{t('nav.pilotRegions')}<")
nav_content = nav_content.replace(">Resources<", ">{t('nav.resources')}<")
nav_content = nav_content.replace(">Open dashboard", ">{t('nav.openDashboard')}")

if '<LanguageSwitcher />' not in nav_content:
    nav_content = nav_content.replace(
        '<Link href="/dashboard"',
        '<LanguageSwitcher />\n          <Link href="/dashboard"'
    )
    with open(nav_path, 'w') as f:
        f.write(nav_content)

# 5. Update HeroSection.tsx
hero_path = 'src/components/landing/HeroSection.tsx'
with open(hero_path, 'r') as f:
    hero_content = f.read()

hero_content = hero_content.replace(
    "import Link from 'next/link';",
    "import Link from 'next/link';\nimport { useLanguage } from '@/contexts/LanguageContext';"
)
hero_content = hero_content.replace(
    "export default function HeroSection() {",
    "export default function HeroSection() {\n  const { t } = useLanguage();"
)

# Text replacements in HeroSection
hero_content = hero_content.replace(
    "AGROTWIN AI - SUSTAINABLE FERTILIZER USAGE OPTIMIZER",
    "{t('hero.badge')}"
)
hero_content = hero_content.replace(
    "Better decisions<br/>",
    "{t('hero.title.1')}<br/>"
)
hero_content = hero_content.replace(
    "begin with a better<br/>",
    "{t('hero.title.2')}<br/>"
)
hero_content = hero_content.replace(
    "understanding<br/>",
    "{t('hero.title.3')}<br/>"
)
hero_content = hero_content.replace(
    "of every field.",
    "{t('hero.title.4')}"
)
hero_content = hero_content.replace(
    "AgroTwin AI provides evidence-grounded, field-specific fertilizer decision support using soil data, crop type, weather and farm history — helping farmers use the right nutrients, at the right time.",
    "{t('hero.subtitle')}"
)
hero_content = hero_content.replace(
    "Explore the platform",
    "{t('hero.explore')}"
)
hero_content = hero_content.replace(
    ">How it works<",
    ">{t('hero.howItWorks')}<"
)
hero_content = hero_content.replace(
    "Current Plan",
    "{t('hero.currentPlan')}"
)
hero_content = hero_content.replace(
    "Apply Urea (46-0-0)",
    "{t('hero.applyUrea')}"
)
hero_content = hero_content.replace(
    "in 2 days",
    "{t('hero.in2Days')}"
)
hero_content = hero_content.replace(
    "Weather",
    "{t('hero.weather')}"
)
hero_content = hero_content.replace(
    "Light Rain",
    "{t('hero.lightRain')}"
)

# Add "use client" to top of Nav and Hero since they use context hooks now
if '"use client"' not in nav_content:
    nav_content = '"use client";\n' + nav_content
    with open(nav_path, 'w') as f:
        f.write(nav_content)

if '"use client"' not in hero_content:
    hero_content = '"use client";\n' + hero_content
    with open(hero_path, 'w') as f:
        f.write(hero_content)

print("Multilingual support added successfully!")
