import os

context = """
"use client";
import React, { createContext, useContext, useState, ReactNode } from 'react';

type Language = 'en' | 'hi' | 'mr';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const translations: Record<Language, Record<string, string>> = {
  en: {
    'nav.home': 'Home', 'nav.howItWorks': 'How it works', 'nav.capabilities': 'Capabilities', 'nav.pilotRegions': 'Pilot regions', 'nav.resources': 'Resources', 'nav.openDashboard': 'Open dashboard',
    'hero.badge': 'AGROTWIN AI - SUSTAINABLE FERTILIZER USAGE OPTIMIZER', 'hero.title.1': 'Better decisions', 'hero.title.2': 'begin with a better', 'hero.title.3': 'understanding', 'hero.title.4': 'of every field.', 'hero.subtitle': 'AgroTwin AI provides evidence-grounded, field-specific fertilizer decision support using soil data, crop type, weather and farm history — helping farmers use the right nutrients, at the right time.', 'hero.explore': 'Explore the platform', 'hero.howItWorks': 'How it works', 'hero.currentPlan': 'Current Plan', 'hero.applyUrea': 'Apply Urea (46-0-0)', 'hero.in2Days': 'in 2 days', 'hero.weather': 'Weather', 'hero.lightRain': 'Light Rain',
    'cap.1.t': 'Living Farm Digital Twin', 'cap.1.d': 'A persistent, evolving representation of field, soil, crop, environment and nutrient history.', 'cap.2.t': 'Continuous Monitoring', 'cap.2.d': 'AgroTwin monitors changing conditions and can trigger re-evaluation when assumptions change.', 'cap.3.t': 'Evidence-Grounded Recommendations', 'cap.3.d': 'Recommendations combine field data, agronomic constraints, optimization and trusted evidence.',
    'dl.badge': 'How it works', 'dl.title.1': 'The plan changes', 'dl.title.2': 'when the field changes.', 'dl.desc': 'A continuous system that monitors, detects changes and re-evaluates the plan when conditions evolve.', 'dl.step.desc': 'Continuous process step.', 'dl.s1': 'Observe', 'dl.s2': 'Understand', 'dl.s3': 'Predict', 'dl.s4': 'Optimize', 'dl.s5': 'Validate', 'dl.s6': 'Recommend', 'dl.s7': 'Monitor', 'dl.s8': 'Re-plan',
    'dt.badge': 'Digital Twin', 'dt.title': 'One field. One evolving picture.', 'dt.subtitle': 'AgroTwin creates a living digital twin of your field by combining soil, crop, weather, farm history and ongoing observations.', 'dt.s1': 'Soil state', 'dt.s1d': 'Nutrient levels, pH, organic carbon, moisture', 'dt.s2': 'Crop state', 'dt.s2d': 'Crop type, variety, growth stage, target yield', 'dt.s3': 'Weather & environment', 'dt.s3d': 'Past applications and nutrient ledger', 'dt.s4': 'Current plan', 'dt.s4d': 'Personalized, field-specific recommendation',
    'pr.badge': 'Explainability', 'pr.title1': 'Every recommendation', 'pr.title2': 'carries its proof.', 'pr.subtitle': 'See exactly why a recommendation is made — what data was used, which agronomic knowledge it draws from, and how confident we are.', 'pr.view': 'View an example', 'pr.q1': 'WHAT should I apply?', 'pr.q2': 'HOW MUCH is right for my field?', 'pr.q3': 'WHEN should I apply it?', 'pr.q4': 'WHY is this the right plan?', 'pr.q5': 'BASED ON WHAT evidence?', 'pr.q6': 'HOW SURE are we?',
    'wi.badge': 'What-If Simulator', 'wi.title1': 'Test a change', 'wi.title2': 'before it reaches', 'wi.title3': 'the field.', 'wi.subtitle': 'Simulate different fertilizer amounts, application timings or target yields and see the expected outcomes for your field.', 'wi.try': 'Try the simulator', 'wi.scen': 'What-If Scenario', 'wi.fert': 'Fertilizer Budget', 'wi.delay': 'Delay Application', 'wi.target': 'Target Yield', 'wi.plan': 'What-If Plan', 'wi.estY': 'Est. yield:', 'wi.estC': 'Est. cost:', 'wi.sup': 'Supported crops',
    'pi.badge': 'Pilot Regions', 'pi.title': 'Starting close to home.', 'pi.subtitle': 'AgroTwin is being piloted in key agricultural regions of Maharashtra, focusing on locally important crops and real farmer needs.', 'pi.str1': 'Stronger farms', 'pi.str2': 'for a stronger', 'pi.str3': 'Maharashtra.',
    'hu.badge': 'Human Oversight', 'hu.title1': 'Technology should know', 'hu.title2': 'when to pause.', 'hu.subtitle': 'AgroTwin is designed to surface low-confidence cases, missing data, conflicting evidence and unusual conditions rather than silently producing unsupported recommendations.', 'hu.c1': 'Confidence and data-quality checks', 'hu.c2': 'Clear reasons when a recommendation is not issued', 'hu.c3': 'Agronomist review and override support', 'hu.c4': 'Audit trail for important decisions', 'hu.rev': 'Needs Review', 'hu.revd': 'Conflicting soil test results detected. Agronomist review required before recommendation.',
    'fi.badge': 'A MORE RESILIENT AGRICULTURE', 'fi.title1': 'From one-time recommendations', 'fi.title2': 'to continuous farm intelligence.', 'fi.btn': 'Open AgroTwin',
    'fo.tag': 'Sustainable Fertilizer Usage Optimizer', 'fo.d1': 'Designed for Maharashtra.', 'fo.d2': 'Built for farmers, with care.'
  },
  hi: {
    'nav.home': 'होम', 'nav.howItWorks': 'यह कैसे काम करता है', 'nav.capabilities': 'क्षमताएं', 'nav.pilotRegions': 'पायलट क्षेत्र', 'nav.resources': 'संसाधन', 'nav.openDashboard': 'डैशबोर्ड खोलें',
    'hero.badge': 'एग्रोट्विन एआई - सतत उर्वरक उपयोग अनुकूलक', 'hero.title.1': 'बेहतर निर्णय', 'hero.title.2': 'हर खेत की', 'hero.title.3': 'बेहतर समझ', 'hero.title.4': 'से शुरू होते हैं।', 'hero.subtitle': 'एग्रोट्विन एआई मिट्टी के डेटा, फसल के प्रकार, मौसम और खेत के इतिहास का उपयोग करके साक्ष्य-आधारित उर्वरक निर्णय समर्थन प्रदान करता है - जिससे किसानों को सही समय पर सही पोषक तत्वों का उपयोग करने में मदद मिलती है।', 'hero.explore': 'प्लेटफ़ॉर्म एक्सप्लोर करें', 'hero.howItWorks': 'यह कैसे काम करता है', 'hero.currentPlan': 'वर्तमान योजना', 'hero.applyUrea': 'यूरिया डालें (46-0-0)', 'hero.in2Days': '2 दिन में', 'hero.weather': 'मौसम', 'hero.lightRain': 'हल्की बारिश',
    'cap.1.t': 'जीवंत खेत डिजिटल ट्विन', 'cap.1.d': 'खेत, मिट्टी, फसल, पर्यावरण और पोषक तत्वों के इतिहास का एक निरंतर प्रतिनिधित्व।', 'cap.2.t': 'निरंतर निगरानी', 'cap.2.d': 'एग्रोट्विन बदलती परिस्थितियों पर नज़र रखता है और मान्यताएं बदलने पर पुनर्मूल्यांकन कर सकता है।', 'cap.3.t': 'साक्ष्य-आधारित सिफारिशें', 'cap.3.d': 'सिफारिशें खेत के डेटा, कृषि संबंधी बाधाओं, अनुकूलन और विश्वसनीय साक्ष्यों को मिलाती हैं।',
    'dl.badge': 'यह कैसे काम करता है', 'dl.title.1': 'खेत बदलने पर', 'dl.title.2': 'योजना बदल जाती है।', 'dl.desc': 'एक निरंतर प्रणाली जो स्थिति विकसित होने पर निगरानी करती है, परिवर्तनों का पता लगाती है और योजना का पुनर्मूल्यांकन करती है।', 'dl.step.desc': 'सतत प्रक्रिया चरण।', 'dl.s1': 'अवलोकन', 'dl.s2': 'समझें', 'dl.s3': 'भविष्यवाणी', 'dl.s4': 'अनुकूलन', 'dl.s5': 'सत्यापन', 'dl.s6': 'सिफारिश', 'dl.s7': 'निगरानी', 'dl.s8': 'पुनः योजना',
    'dt.badge': 'डिजिटल ट्विन', 'dt.title': 'एक खेत। एक विकसित होती तस्वीर।', 'dt.subtitle': 'एग्रोट्विन मिट्टी, फसल, मौसम, खेत के इतिहास और चल रहे अवलोकनों को मिलाकर आपके खेत का एक जीवंत डिजिटल ट्विन बनाता है।', 'dt.s1': 'मिट्टी की स्थिति', 'dt.s1d': 'पोषक तत्व स्तर, पीएच, जैविक कार्बन, नमी', 'dt.s2': 'फसल की स्थिति', 'dt.s2d': 'फसल का प्रकार, किस्म, विकास चरण, लक्ष्य उपज', 'dt.s3': 'मौसम और पर्यावरण', 'dt.s3d': 'पिछले अनुप्रयोग और पोषक तत्व खाता', 'dt.s4': 'वर्तमान योजना', 'dt.s4d': 'व्यक्तिगत, खेत-विशिष्ट सिफारिश',
    'pr.badge': 'व्याख्यात्मकता', 'pr.title1': 'हर सिफारिश अपना', 'pr.title2': 'प्रमाण साथ लाती है।', 'pr.subtitle': 'देखें कि वास्तव में सिफारिश क्यों की गई है - किस डेटा का उपयोग किया गया था, यह किस कृषि ज्ञान से लिया गया है, और हम कितने आश्वस्त हैं।', 'pr.view': 'एक उदाहरण देखें', 'pr.q1': 'मुझे क्या डालना चाहिए?', 'pr.q2': 'मेरे खेत के लिए कितना सही है?', 'pr.q3': 'मुझे इसे कब लागू करना चाहिए?', 'pr.q4': 'यह सही योजना क्यों है?', 'pr.q5': 'किस साक्ष्य के आधार पर?', 'pr.q6': 'हम कितने सुनिश्चित हैं?',
    'wi.badge': 'व्हाट-इफ सिम्युलेटर', 'wi.title1': 'खेत में पहुंचने से पहले', 'wi.title2': 'बदलाव का', 'wi.title3': 'परीक्षण करें।', 'wi.subtitle': 'विभिन्न उर्वरक मात्रा, आवेदन समय या लक्ष्य उपज का अनुकरण करें और अपने खेत के लिए अपेक्षित परिणाम देखें।', 'wi.try': 'सिम्युलेटर आज़माएं', 'wi.scen': 'व्हाट-इफ परिदृश्य', 'wi.fert': 'उर्वरक बजट', 'wi.delay': 'आवेदन में देरी', 'wi.target': 'लक्ष्य उपज', 'wi.plan': 'व्हाट-इफ योजना', 'wi.estY': 'अनुमानित उपज:', 'wi.estC': 'अनुमानित लागत:', 'wi.sup': 'समर्थित फसलें',
    'pi.badge': 'पायलट क्षेत्र', 'pi.title': 'घर के करीब से शुरुआत।', 'pi.subtitle': 'एग्रोट्विन को महाराष्ट्र के प्रमुख कृषि क्षेत्रों में पायलट किया जा रहा है, जो स्थानीय रूप से महत्वपूर्ण फसलों और वास्तविक किसानों की जरूरतों पर ध्यान केंद्रित कर रहा है।', 'pi.str1': 'एक मजबूत', 'pi.str2': 'महाराष्ट्र के लिए', 'pi.str3': 'मजबूत खेत।',
    'hu.badge': 'मानव निरीक्षण', 'hu.title1': 'तकनीक को पता होना चाहिए', 'hu.title2': 'कि कब रुकना है।', 'hu.subtitle': 'एग्रोट्विन को चुपचाप असमर्थित सिफारिशें देने के बजाय कम आत्मविश्वास वाले मामलों, लापता डेटा, परस्पर विरोधी साक्ष्य और असामान्य स्थितियों को सामने लाने के लिए डिज़ाइन किया गया है।', 'hu.c1': 'विश्वास और डेटा-गुणवत्ता की जांच', 'hu.c2': 'सिफारिश जारी न होने पर स्पष्ट कारण', 'hu.c3': 'कृषिविज्ञानी समीक्षा और ओवरराइड समर्थन', 'hu.c4': 'महत्वपूर्ण निर्णयों के लिए ऑडिट ट्रेल', 'hu.rev': 'समीक्षा की आवश्यकता है', 'hu.revd': 'परस्पर विरोधी मिट्टी परीक्षण परिणाम पाए गए। सिफारिश से पहले कृषिविज्ञानी समीक्षा आवश्यक है।',
    'fi.badge': 'एक अधिक लचीली कृषि', 'fi.title1': 'एक बार की सिफारिशों से', 'fi.title2': 'निरंतर खेत खुफिया तक।', 'fi.btn': 'एग्रोट्विन खोलें',
    'fo.tag': 'सतत उर्वरक उपयोग अनुकूलक', 'fo.d1': 'महाराष्ट्र के लिए डिज़ाइन किया गया।', 'fo.d2': 'किसानों के लिए देखभाल के साथ बनाया गया।'
  },
  mr: {
    'nav.home': 'मुख्यपृष्ठ', 'nav.howItWorks': 'हे कसे काम करते', 'nav.capabilities': 'क्षमता', 'nav.pilotRegions': 'पायलट क्षेत्र', 'nav.resources': 'संसाधने', 'nav.openDashboard': 'डॅशबोर्ड उघडा',
    'hero.badge': 'ऍग्रोट्विन एआय - शाश्वत खत वापर ऑप्टिमायझर', 'hero.title.1': 'उत्तम निर्णय', 'hero.title.2': 'प्रत्येक शेताच्या', 'hero.title.3': 'उत्तम आकलनापासून', 'hero.title.4': 'सुरू होतात.', 'hero.subtitle': 'AgroTwin AI मातीचा डेटा, पिकाचा प्रकार, हवामान आणि शेताचा इतिहास वापरून पुराव्यावर आधारित खत निर्णय समर्थन प्रदान करते — शेतकऱ्यांना योग्य वेळी योग्य पोषक तत्वे वापरण्यास मदत करते.', 'hero.explore': 'प्लॅटफॉर्म एक्सप्लोर करा', 'hero.howItWorks': 'हे कसे काम करते', 'hero.currentPlan': 'सध्याची योजना', 'hero.applyUrea': 'युरिया लागू करा (46-0-0)', 'hero.in2Days': '2 दिवसांत', 'hero.weather': 'हवामान', 'hero.lightRain': 'हलका पाऊस',
    'cap.1.t': 'जिवंत शेत डिजिटल ट्विन', 'cap.1.d': 'शेत, माती, पीक, पर्यावरण आणि पोषक तत्वांच्या इतिहासाचे सतत प्रतिनिधित्व.', 'cap.2.t': 'सतत निरीक्षण', 'cap.2.d': 'AgroTwin बदलत्या परिस्थितींवर लक्ष ठेवते आणि परिस्थिती बदलल्यावर पुनर्मूल्यांकन करू शकते.', 'cap.3.t': 'पुराव्यावर आधारित शिफारसी', 'cap.3.d': 'शिफारसी शेतातील डेटा, कृषीविषयक मर्यादा, ऑप्टिमायझेशन आणि विश्वसनीय पुरावे एकत्र करतात.',
    'dl.badge': 'हे कसे काम करते', 'dl.title.1': 'शेत बदलले की', 'dl.title.2': 'योजना बदलते.', 'dl.desc': 'एक सतत प्रणाली जी परिस्थिती विकसित होताना निरीक्षण करते, बदल शोधते आणि योजनेचे पुनर्मूल्यांकन करते.', 'dl.step.desc': 'सतत प्रक्रिया टप्पा.', 'dl.s1': 'निरीक्षण', 'dl.s2': 'समजून घ्या', 'dl.s3': 'अंदाज', 'dl.s4': 'ऑप्टिमाइझ', 'dl.s5': 'पडताळणी', 'dl.s6': 'शिफारस', 'dl.s7': 'निरीक्षण', 'dl.s8': 'पुन्हा योजना',
    'dt.badge': 'डिजिटल ट्विन', 'dt.title': 'एक शेत. एक विकसित होणारे चित्र.', 'dt.subtitle': 'AgroTwin माती, पीक, हवामान, शेताचा इतिहास आणि चालू निरीक्षणांचे एकत्रीकरण करून तुमच्या शेताचे जिवंत डिजिटल ट्विन तयार करते.', 'dt.s1': 'मातीची स्थिती', 'dt.s1d': 'पोषक तत्वांची पातळी, सामू, सेंद्रिय कर्ब, ओलावा', 'dt.s2': 'पिकाची स्थिती', 'dt.s2d': 'पिकाचा प्रकार, वाण, वाढीचा टप्पा, लक्ष्य उत्पन्न', 'dt.s3': 'हवामान आणि पर्यावरण', 'dt.s3d': 'मागील अनुप्रयोग आणि पोषक तत्व खाते', 'dt.s4': 'सध्याची योजना', 'dt.s4d': 'वैयक्तिकृत, शेत-विशिष्ट शिफारस',
    'pr.badge': 'स्पष्टीकरणक्षमता', 'pr.title1': 'प्रत्येक शिफारस आपला', 'pr.title2': 'पुरावा सोबत आणते.', 'pr.subtitle': 'शिफारस नक्की का केली आहे ते पहा — कोणता डेटा वापरला गेला, तो कोणत्या कृषी ज्ञानातून घेतला आहे आणि आम्हाला किती खात्री आहे.', 'pr.view': 'एक उदाहरण पहा', 'pr.q1': 'मी काय लागू करावे?', 'pr.q2': 'माझ्या शेतासाठी किती योग्य आहे?', 'pr.q3': 'मी ते कधी लागू करावे?', 'pr.q4': 'ही योग्य योजना का आहे?', 'pr.q5': 'कोणत्या पुराव्यांवर आधारित?', 'pr.q6': 'आम्हाला किती खात्री आहे?',
    'wi.badge': 'व्हॉट-इफ सिम्युलेटर', 'wi.title1': 'बदल शेतात पोहोचण्यापूर्वी', 'wi.title2': 'त्याची', 'wi.title3': 'चाचणी करा.', 'wi.subtitle': 'विविध खतांचे प्रमाण, अर्जाच्या वेळा किंवा लक्ष्यित उत्पन्नाचे अनुकरण करा आणि तुमच्या शेतासाठी अपेक्षित परिणाम पहा.', 'wi.try': 'सिम्युलेटर वापरून पहा', 'wi.scen': 'व्हॉट-इफ परिस्थिती', 'wi.fert': 'खत बजेट', 'wi.delay': 'अर्जास विलंब', 'wi.target': 'लक्ष्य उत्पन्न', 'wi.plan': 'व्हॉट-इफ योजना', 'wi.estY': 'अंदाजित उत्पन्न:', 'wi.estC': 'अंदाजित खर्च:', 'wi.sup': 'समर्थित पिके',
    'pi.badge': 'पायलट क्षेत्र', 'pi.title': 'घराजवळून सुरुवात.', 'pi.subtitle': 'AgroTwin महाराष्ट्रातील प्रमुख कृषी क्षेत्रांमध्ये प्रायोगिक तत्त्वावर राबवले जात आहे, स्थानिक पातळीवर महत्त्वाची पिके आणि वास्तविक शेतकऱ्यांच्या गरजांवर लक्ष केंद्रित करून.', 'pi.str1': 'सशक्त महाराष्ट्रासाठी', 'pi.str2': 'सशक्त', 'pi.str3': 'शेती.',
    'hu.badge': 'मानवी निरीक्षण', 'hu.title1': 'तंत्रज्ञानाला माहित असले पाहिजे', 'hu.title2': 'कधी थांबायचे.', 'hu.subtitle': 'AgroTwin चुपचाप असमर्थित शिफारसी देण्याऐवजी कमी आत्मविश्वासाची प्रकरणे, गहाळ डेटा, परस्परविरोधी पुरावे आणि असामान्य परिस्थिती समोर आणण्यासाठी डिझाइन केले आहे.', 'hu.c1': 'आत्मविश्वास आणि डेटा-गुणवत्तेची तपासणी', 'hu.c2': 'शिफारस न दिल्यास स्पष्ट कारणे', 'hu.c3': 'कृषीशास्त्रज्ञांचे पुनरावलोकन आणि समर्थन', 'hu.c4': 'महत्त्वाच्या निर्णयांसाठी ऑडिट ट्रेल', 'hu.rev': 'पुनरावलोकन आवश्यक', 'hu.revd': 'परस्परविरोधी माती परीक्षण परिणाम आढळले. शिफारसीपूर्वी कृषीशास्त्रज्ञांचे पुनरावलोकन आवश्यक.',
    'fi.badge': 'अधिक लवचिक शेती', 'fi.title1': 'एकवेळच्या शिफारसींपासून ते', 'fi.title2': 'सतत शेत बुद्धिमत्तेपर्यंत.', 'fi.btn': 'AgroTwin उघडा',
    'fo.tag': 'शाश्वत खत वापर ऑप्टिमायझर', 'fo.d1': 'महाराष्ट्रासाठी डिझाइन केलेले.', 'fo.d2': 'शेतकऱ्यांसाठी काळजीपूर्वक बनवलेले.'
  }
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>('en');
  const t = (key: string): string => translations[language][key] || key;
  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) { throw new Error('useLanguage must be used within a LanguageProvider'); }
  return context;
}
"""
with open('src/contexts/LanguageContext.tsx', 'w') as f:
    f.write(context)


# Component Replacements using the precise layout they currently have

components = {
    'src/components/landing/CapabilityStrip.tsx': """
"use client";
import { useLanguage } from "@/contexts/LanguageContext";
import React from 'react';

export default function CapabilityStrip() {
  const { t } = useLanguage();

  return (
    <section id="capabilities" className="py-24 bg-[#FDFBF7] border-t border-[#0F4D35]/10">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 lg:gap-24">
          <div className="space-y-4">
            <div className="text-xs font-mono text-[#0F4D35]/40 mb-6">01</div>
            <h3 className="text-xl font-medium text-[#0F4D35]">{t("cap.1.t")}</h3>
            <p className="text-[#1a1a1a]/70 font-light leading-relaxed text-sm">
              {t("cap.1.d")}
            </p>
          </div>
          <div className="space-y-4">
            <div className="text-xs font-mono text-[#0F4D35]/40 mb-6">02</div>
            <h3 className="text-xl font-medium text-[#0F4D35]">{t("cap.2.t")}</h3>
            <p className="text-[#1a1a1a]/70 font-light leading-relaxed text-sm">
              {t("cap.2.d")}
            </p>
          </div>
          <div className="space-y-4">
            <div className="text-xs font-mono text-[#0F4D35]/40 mb-6">03</div>
            <h3 className="text-xl font-medium text-[#0F4D35]">{t("cap.3.t")}</h3>
            <p className="text-[#1a1a1a]/70 font-light leading-relaxed text-sm">
              {t("cap.3.d")}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
""",
    'src/components/landing/DecisionLoopSection.tsx': """
"use client";
import { useLanguage } from "@/contexts/LanguageContext";
import React from 'react';

export default function DecisionLoopSection() {
  const { t } = useLanguage();

  const steps = [
    t("dl.s1"), t("dl.s2"), t("dl.s3"), t("dl.s4"), t("dl.s5"), t("dl.s6"), t("dl.s7"), t("dl.s8")
  ];

  return (
    <section id="how-it-works" className="py-32 bg-[#FDFBF7]">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="max-w-2xl mb-20">
          <div className="text-[11px] font-bold uppercase tracking-widest text-[#0F4D35] mb-6">{t("dl.badge")}</div>
          <h2 className="text-4xl md:text-5xl font-medium text-[#0F4D35] mb-6 leading-tight font-serif">
            {t("dl.title.1")}<br/>{t("dl.title.2")}
          </h2>
          <p className="text-lg text-[#1a1a1a]/70 font-light leading-relaxed">
            {t("dl.desc")}
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
                <p className="text-xs text-[#1a1a1a]/50 font-light">{t("dl.step.desc")}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
""",
    'src/components/landing/DigitalTwinSection.tsx': """
"use client";
import { useLanguage } from "@/contexts/LanguageContext";
import React from 'react';

export default function DigitalTwinSection() {
  const { t } = useLanguage();
  return (
    <section className="py-32 bg-white">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
          <div className="order-2 lg:order-1 h-[700px] w-full bg-[#f4f2eb] rounded-sm overflow-hidden flex items-center justify-center">
            <img 
              src="/image copy 4.png" 
              alt="Soil and crop seedlings" 
              className="w-full h-full object-cover"
            />
          </div>
          <div className="order-1 lg:order-2">
            <div className="text-[11px] font-bold uppercase tracking-widest text-[#0F4D35] mb-6">{t("dt.badge")}</div>
            <h2 className="text-4xl md:text-5xl font-medium text-[#0F4D35] mb-8 leading-tight font-serif">
              {t("dt.title")}
            </h2>
            <p className="text-lg text-[#1a1a1a]/70 mb-12 font-light leading-relaxed">
              {t("dt.subtitle")}
            </p>
            
            <div className="space-y-8">
              <div className="flex gap-4 border-b border-[#0F4D35]/10 pb-6">
                <div className="text-xs font-mono text-[#0F4D35]/40 mt-1">01</div>
                <div>
                  <h4 className="text-sm font-bold text-[#1a1a1a] mb-1">{t("dt.s1")}</h4>
                  <p className="text-sm text-[#1a1a1a]/60">{t("dt.s1d")}</p>
                </div>
              </div>
              <div className="flex gap-4 border-b border-[#0F4D35]/10 pb-6">
                <div className="text-xs font-mono text-[#0F4D35]/40 mt-1">02</div>
                <div>
                  <h4 className="text-sm font-bold text-[#1a1a1a] mb-1">{t("dt.s2")}</h4>
                  <p className="text-sm text-[#1a1a1a]/60">{t("dt.s2d")}</p>
                </div>
              </div>
              <div className="flex gap-4 border-b border-[#0F4D35]/10 pb-6">
                <div className="text-xs font-mono text-[#0F4D35]/40 mt-1">03</div>
                <div>
                  <h4 className="text-sm font-bold text-[#1a1a1a] mb-1">{t("dt.s3")}</h4>
                  <p className="text-sm text-[#1a1a1a]/60">{t("dt.s3d")}</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="text-xs font-mono text-[#0F4D35]/40 mt-1">04</div>
                <div>
                  <h4 className="text-sm font-bold text-[#1a1a1a] mb-1">{t("dt.s4")}</h4>
                  <p className="text-sm text-[#1a1a1a]/60">{t("dt.s4d")}</p>
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
    'src/components/landing/ProofSection.tsx': """
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
""",
    'src/components/landing/WhatIfPreview.tsx': """
"use client";
import { useLanguage } from "@/contexts/LanguageContext";
import React from 'react';
import Link from 'next/link';

export default function WhatIfPreview() {
  const { t } = useLanguage();
  return (
    <section className="py-32 bg-[#FDFBF7]">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_2fr] gap-16 items-center">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-widest text-[#0F4D35] mb-6">{t("wi.badge")}</div>
            <h2 className="text-4xl md:text-5xl font-medium text-[#0F4D35] mb-8 leading-tight font-serif">
              {t("wi.title1")}<br/>
              {t("wi.title2")}<br/>
              {t("wi.title3")}
            </h2>
            <p className="text-lg text-[#1a1a1a]/70 mb-12 font-light leading-relaxed">
              {t("wi.subtitle")}
            </p>
            <Link href="/simulator" className="px-8 py-4 bg-[#0F4D35] text-white font-medium text-sm hover:bg-[#0a3625] transition-colors rounded-sm inline-flex items-center group shadow-sm">
              {t("wi.try")}
              <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </Link>
          </div>
          
          <div className="flex flex-col md:flex-row gap-4 items-stretch">
            {/* Scenario Controls */}
            <div className="flex-1 bg-white p-6 rounded-sm border border-[#0F4D35]/10 shadow-sm">
              <div className="text-sm font-bold text-[#1a1a1a] mb-6">{t("wi.scen")}</div>
              
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between text-xs text-[#1a1a1a]/70 mb-2">
                    <span>{t("wi.fert")}</span>
                  </div>
                  <div className="font-medium text-sm mb-2">₹ 3,500 / acre</div>
                  <div className="h-1.5 w-full bg-[#FDFBF7] border border-[#0F4D35]/10 rounded-full relative">
                    <div className="absolute left-0 top-0 bottom-0 w-3/4 bg-[#0F4D35] rounded-full"></div>
                    <div className="absolute left-[75%] top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 border-[#0F4D35] rounded-full shadow-sm"></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs text-[#1a1a1a]/70 mb-2">
                    <span>{t("wi.delay")}</span>
                  </div>
                  <div className="font-medium text-sm mb-2">0 days</div>
                  <div className="h-1.5 w-full bg-[#FDFBF7] border border-[#0F4D35]/10 rounded-full relative">
                    <div className="absolute left-0 top-0 bottom-0 w-[10%] bg-[#0F4D35] rounded-full"></div>
                    <div className="absolute left-[10%] top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 border-[#0F4D35] rounded-full shadow-sm"></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs text-[#1a1a1a]/70 mb-2">
                    <span>{t("wi.target")}</span>
                  </div>
                  <div className="font-medium text-sm mb-2">6.8 t/acre</div>
                  <div className="h-1.5 w-full bg-[#FDFBF7] border border-[#0F4D35]/10 rounded-full relative">
                    <div className="absolute left-0 top-0 bottom-0 w-[60%] bg-[#0F4D35] rounded-full"></div>
                    <div className="absolute left-[60%] top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 border-[#0F4D35] rounded-full shadow-sm"></div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* 3D Model Visualization */}
            <div className="flex-[2] bg-white p-6 rounded-sm border border-[#0F4D35]/10 shadow-sm flex flex-col">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <div className="text-sm font-bold text-[#1a1a1a]">{t("wi.plan")}</div>
                  <div className="text-[10px] text-[#1a1a1a]/50">+ 20% Fertilizer</div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-[#1a1a1a]/50">Rice &middot; A-104</div>
                </div>
              </div>
              
              <div className="flex-1 bg-blue-50/20 rounded-sm relative overflow-hidden min-h-[250px] border border-[#0F4D35]/5 mb-4">
                <div className="sketchfab-embed-wrapper absolute inset-0 w-full h-full">
                  <iframe 
                    title="Rice Plant" 
                    className="w-full h-full" 
                    frameBorder="0" 
                    allowFullScreen 
                    mozallowfullscreen="true" 
                    webkitallowfullscreen="true" 
                    allow="autoplay; fullscreen; xr-spatial-tracking" 
                    xr-spatial-tracking="true" 
                    execution-while-out-of-viewport="true" 
                    execution-while-not-rendered="true" 
                    web-share="true" 
                    src="https://sketchfab.com/models/be6aa4ac9adc4f558cc789a0baed8ae3/embed">
                  </iframe>
                </div>
                <div className="absolute top-2 right-2 bg-white/80 backdrop-blur-sm px-2 py-1 text-[9px] font-bold text-[#0F4D35] rounded-sm pointer-events-none">
                  Heading (Projected)
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-[#1a1a1a]/50">{t("wi.estY")}</span> <span className="font-medium text-[#0F4D35]">6.8 t/acre</span>
                </div>
                <div>
                  <span className="text-[#1a1a1a]/50">{t("wi.estC")}</span> <span className="font-medium text-[#0F4D35]">₹ 3,450/acre</span>
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
                  <div className="w-8 h-8 rounded-full bg-[#0F4D35]/5 border border-[#0F4D35]/10 flex items-center justify-center text-[#0F4D35] shadow-sm">
                    {/* Tiny dot icon as placeholder for plant icon */}
                    <div className="w-2 h-2 rounded-full bg-[#0F4D35]/60"></div>
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
""",
    'src/components/landing/PilotRegionsSection.tsx': """
"use client";
import { useLanguage } from "@/contexts/LanguageContext";
import React from 'react';

export default function PilotRegionsSection() {
  const { t } = useLanguage();
  return (
    <section id="pilot-regions" className="py-32 bg-white">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="mb-20 text-center md:text-left">
          <div className="text-[11px] font-bold uppercase tracking-widest text-[#0F4D35] mb-6">{t("pi.badge")}</div>
          <h2 className="text-4xl md:text-5xl font-medium text-[#0F4D35] mb-6 leading-tight font-serif">
            {t("pi.title")}
          </h2>
          <p className="text-lg text-[#1a1a1a]/70 font-light leading-relaxed max-w-2xl mx-auto md:mx-0">
            {t("pi.subtitle")}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
          <div className="bg-[#f4f2eb] rounded-sm p-8 h-[400px] relative border border-[#0F4D35]/5 flex items-center justify-center">
            <svg viewBox="0 0 400 400" className="w-full h-full text-[#0F4D35]/10">
              <path fill="currentColor" d="M100,50 L300,50 L350,150 L300,300 L150,350 L50,200 Z" className="drop-shadow-sm" />
            </svg>
            <div className="absolute inset-0 p-8 flex flex-col justify-between">
              <div className="text-sm font-medium text-[#0F4D35]/50 uppercase tracking-widest">Maharashtra</div>
              
              <div className="absolute top-1/4 left-1/3 flex items-center gap-3">
                <div className="w-3 h-3 bg-[#d4af37] rounded-full shadow-[0_0_0_4px_rgba(212,175,55,0.2)]"></div>
                <div>
                  <div className="text-sm font-bold text-[#1a1a1a]">Jalgaon</div>
                  <div className="text-[10px] text-[#1a1a1a]/50">Banana, Cotton</div>
                </div>
              </div>
              
              <div className="absolute bottom-1/3 left-1/4 flex items-center gap-3">
                <div className="w-3 h-3 bg-[#d4af37] rounded-full shadow-[0_0_0_4px_rgba(212,175,55,0.2)]"></div>
                <div>
                  <div className="text-sm font-bold text-[#1a1a1a]">Kolhapur</div>
                  <div className="text-[10px] text-[#1a1a1a]/50">Sugarcane, Rice</div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="flex flex-col justify-center">
            <h3 className="text-3xl font-serif text-[#0F4D35]/40 italic leading-relaxed">
              {t("pi.str1")}<br/>
              {t("pi.str2")}<br/>
              <span className="text-[#0F4D35]">{t("pi.str3")}</span>
            </h3>
          </div>
        </div>
      </div>
    </section>
  );
}
""",
    'src/components/landing/HumanOversightSection.tsx': """
"use client";
import { useLanguage } from "@/contexts/LanguageContext";
import React from 'react';

export default function HumanOversightSection() {
  const { t } = useLanguage();
  const checks = [
    t("hu.c1"),
    t("hu.c2"),
    t("hu.c3"),
    t("hu.c4")
  ];

  return (
    <section className="py-32 bg-white">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
          <div className="h-[600px] w-full bg-[#f4f2eb] rounded-sm overflow-hidden relative">
            <img 
              src="/image copy.png" 
              alt="Agronomist reviewing data" 
              className="w-full h-full object-cover"
            />
            <div className="absolute bottom-8 left-8 bg-[#FDFBF7] p-4 rounded-sm shadow-lg border-l-2 border-[#d4af37] w-64">
              <div className="flex items-center gap-2 mb-2">
                <svg className="w-4 h-4 text-[#d4af37]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span className="text-xs font-bold text-[#1a1a1a]">{t("hu.rev")}</span>
              </div>
              <p className="text-[11px] text-[#1a1a1a]/70">{t("hu.revd")}</p>
            </div>
          </div>
          
          <div>
            <div className="text-[11px] font-bold uppercase tracking-widest text-[#0F4D35] mb-6">{t("hu.badge")}</div>
            <h2 className="text-4xl md:text-5xl font-medium text-[#0F4D35] mb-8 leading-tight font-serif">
              {t("hu.title1")}<br/>
              {t("hu.title2")}
            </h2>
            <p className="text-lg text-[#1a1a1a]/70 mb-10 font-light leading-relaxed max-w-md">
              {t("hu.subtitle")}
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
    'src/components/landing/FinalCTA.tsx': """
"use client";
import { useLanguage } from "@/contexts/LanguageContext";
import React from 'react';
import Link from 'next/link';

export default function FinalCTA() {
  const { t } = useLanguage();
  return (
    <section className="relative py-40 bg-[#0F4D35] text-[#FDFBF7] overflow-hidden text-center">
      <img 
        src="/image.png" 
        alt="Agricultural landscape" 
        className="absolute inset-0 w-full h-full object-cover opacity-30 mix-blend-luminosity"
      />
      <div className="absolute inset-0 bg-[#0F4D35]/70"></div>
      
      <div className="relative z-10 container mx-auto px-6 max-w-3xl">
        <h2 className="text-4xl md:text-6xl font-medium text-white mb-8 leading-tight font-serif">
          {t("fi.title1")}<br className="hidden md:block"/>
          <span className="text-[#d4af37] italic">{t("fi.title2")}</span>
        </h2>
        
        <div className="mt-12">
          <Link href="/dashboard" className="px-10 py-5 bg-[#FDFBF7] text-[#0F4D35] font-bold text-sm hover:bg-white transition-colors rounded-sm inline-flex items-center shadow-lg hover:shadow-xl hover:-translate-y-0.5 transform duration-200">
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
""",
    'src/components/landing/LandingFooter.tsx': """
"use client";
import { useLanguage } from "@/contexts/LanguageContext";
import React from 'react';
import Link from 'next/link';

export default function LandingFooter() {
  const { t } = useLanguage();
  return (
    <footer className="bg-[#0a3625] text-[#FDFBF7]/60 py-12 border-t border-white/10">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex flex-col items-center md:items-start gap-2">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-[#d4af37]" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z" />
              </svg>
              <span className="font-bold text-white text-lg tracking-tight">AgroTwin AI</span>
            </div>
            <p className="text-[10px] uppercase tracking-widest text-[#FDFBF7]/40">{t("fo.tag")}</p>
          </div>
          
          <div className="text-[11px] text-center md:text-right font-light">
            {t("fo.d1")}<br/>{t("fo.d2")}
          </div>
        </div>
      </div>
    </footer>
  );
}
"""
}

for filepath, content in components.items():
    with open(filepath, 'w') as f:
        f.write(content.strip() + "\n")

print("All components rewritten exactly and strongly bound to translations!")
