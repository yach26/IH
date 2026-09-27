import os

# 1. Update LanguageContext.tsx
context_content = """
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
    // Nav
    'nav.home': 'Home', 'nav.howItWorks': 'How it works', 'nav.capabilities': 'Capabilities', 'nav.pilotRegions': 'Pilot regions', 'nav.resources': 'Resources', 'nav.openDashboard': 'Open dashboard',
    // Hero
    'hero.badge': 'AGROTWIN AI - SUSTAINABLE FERTILIZER USAGE OPTIMIZER', 'hero.title.1': 'Better decisions', 'hero.title.2': 'begin with a better', 'hero.title.3': 'understanding', 'hero.title.4': 'of every field.', 'hero.subtitle': 'AgroTwin AI provides evidence-grounded, field-specific fertilizer decision support using soil data, crop type, weather and farm history — helping farmers use the right nutrients, at the right time.', 'hero.explore': 'Explore the platform', 'hero.howItWorks': 'How it works', 'hero.currentPlan': 'Current Plan', 'hero.applyUrea': 'Apply Urea (46-0-0)', 'hero.in2Days': 'in 2 days', 'hero.weather': 'Weather', 'hero.lightRain': 'Light Rain',
    // CapabilityStrip
    'cap.title1': 'Living farm digital twin', 'cap.desc1': 'A persistent, evolving view of your field.', 'cap.title2': 'Continuous monitoring', 'cap.desc2': 'Adapts when weather, soil or crop conditions change.', 'cap.title3': 'Evidence-grounded recommendations', 'cap.desc3': 'Based on agronomic science, real field data and trusted sources.',
    // DigitalTwinSection
    'dt.badge': 'Digital Twin', 'dt.title': 'One field. One evolving picture.', 'dt.subtitle': 'AgroTwin creates a living digital twin of your field by combining soil, crop, weather, farm history and ongoing observations.', 'dt.s1': 'Soil state', 'dt.s1d': 'Nutrient levels, pH, organic carbon, moisture', 'dt.s2': 'Crop state', 'dt.s2d': 'Crop type, variety, growth stage, target yield', 'dt.s3': 'Weather & env', 'dt.s3d': 'Past applications and nutrient ledger', 'dt.s4': 'Current plan', 'dt.s4d': 'Personalized, field-specific recommendation',
    // DecisionLoop
    'dl.badge': 'How it works', 'dl.title': 'The plan changes when the field changes.', 'dl.subtitle': 'A continuous, agentic system that monitors, detects and re-plans as conditions evolve.', 'dl.obs': 'Observe', 'dl.obsd': 'Field, soil, crop and weather data', 'dl.und': 'Understand', 'dl.undd': 'Build current field state', 'dl.pre': 'Predict', 'dl.pred': 'Estimate needs and risks', 'dl.opt': 'Optimize', 'dl.optd': 'Find best plan under agronomic constraints', 'dl.val': 'Validate', 'dl.vald': 'Check safety, rules and confidence', 'dl.rec': 'Recommend', 'dl.recd': 'Provide clear application plan', 'dl.mon': 'Monitor', 'dl.mond': 'Track conditions after recommendation', 'dl.rep': 'Re-plan', 'dl.repd': 'Update plan when conditions change',
    // Proof
    'pr.badge': 'Explainability', 'pr.title1': 'Every recommendation', 'pr.title2': 'carries its proof.', 'pr.subtitle': 'See exactly why a recommendation is made — what data was used, which agronomic knowledge it draws from, and how confident we are.', 'pr.view': 'View an example', 'pr.q1': 'WHAT should I apply?', 'pr.q2': 'HOW MUCH is right for my field?', 'pr.q3': 'WHEN should I apply it?', 'pr.q4': 'WHY is this the right plan?', 'pr.q5': 'BASED ON WHAT evidence?', 'pr.q6': 'HOW SURE are we?',
    // WhatIf
    'wi.badge': 'What-If Simulator', 'wi.title1': 'Test a change', 'wi.title2': 'before it reaches', 'wi.title3': 'the field.', 'wi.subtitle': 'Simulate different fertilizer amounts, application timings or target yields and see the expected outcomes for your field.', 'wi.try': 'Try the simulator', 'wi.scen': 'What-If Scenario', 'wi.fert': 'Fertilizer Budget', 'wi.delay': 'Delay Application', 'wi.target': 'Target Yield', 'wi.plan': 'What-If Plan', 'wi.estY': 'Est. yield:', 'wi.estC': 'Est. cost:', 'wi.sup': 'Supported crops',
    // Pilot
    'pi.badge': 'Pilot Regions', 'pi.title': 'Starting close to home.', 'pi.subtitle': 'AgroTwin is being piloted in key agricultural regions of Maharashtra, focusing on locally important crops and real farmer needs.', 'pi.str': 'Stronger farms for a stronger Maharashtra.',
    // Human
    'hu.badge': 'Human Oversight', 'hu.title1': 'Technology should know', 'hu.title2': 'when to pause.', 'hu.subtitle': 'AgroTwin is designed to surface low-confidence cases, missing data, conflicting evidence and unusual conditions rather than silently producing unsupported recommendations.', 'hu.c1': 'Confidence and data-quality checks', 'hu.c2': 'Clear reasons when a recommendation is not issued', 'hu.c3': 'Agronomist review and override support', 'hu.c4': 'Audit trail for important decisions', 'hu.rev': 'Needs Review', 'hu.revd': 'Conflicting soil test results detected. Agronomist review required before recommendation.',
    // Final
    'fi.badge': 'A more resilient agriculture', 'fi.title1': 'From one-time recommendations', 'fi.title2': 'to continuous farm intelligence.', 'fi.btn': 'Open AgroTwin',
    // Footer
    'fo.tag': 'Sustainable Fertilizer Usage Optimizer', 'fo.d1': 'Designed for Maharashtra.', 'fo.d2': 'Built for farmers, with care.'
  },
  hi: {
    'nav.home': 'होम', 'nav.howItWorks': 'यह कैसे काम करता है', 'nav.capabilities': 'क्षमताएं', 'nav.pilotRegions': 'पायलट क्षेत्र', 'nav.resources': 'संसाधन', 'nav.openDashboard': 'डैशबोर्ड खोलें',
    'hero.badge': 'एग्रोट्विन एआई - सतत उर्वरक उपयोग अनुकूलक', 'hero.title.1': 'बेहतर निर्णय', 'hero.title.2': 'हर खेत की', 'hero.title.3': 'बेहतर समझ', 'hero.title.4': 'से शुरू होते हैं।', 'hero.subtitle': 'एग्रोट्विन एआई मिट्टी के डेटा, फसल के प्रकार, मौसम और खेत के इतिहास का उपयोग करके साक्ष्य-आधारित उर्वरक निर्णय समर्थन प्रदान करता है - जिससे किसानों को सही समय पर सही पोषक तत्वों का उपयोग करने में मदद मिलती है।', 'hero.explore': 'प्लेटफ़ॉर्म एक्सप्लोर करें', 'hero.howItWorks': 'यह कैसे काम करता है', 'hero.currentPlan': 'वर्तमान योजना', 'hero.applyUrea': 'यूरिया डालें (46-0-0)', 'hero.in2Days': '2 दिन में', 'hero.weather': 'मौसम', 'hero.lightRain': 'हल्की बारिश',
    'cap.title1': 'जीवंत खेत डिजिटल ट्विन', 'cap.desc1': 'आपके खेत का एक निरंतर विकसित होने वाला दृश्य।', 'cap.title2': 'निरंतर निगरानी', 'cap.desc2': 'मौसम, मिट्टी या फसल की स्थिति बदलने पर अनुकूलित होता है।', 'cap.title3': 'साक्ष्य-आधारित सिफारिशें', 'cap.desc3': 'कृषि विज्ञान, वास्तविक खेत डेटा और विश्वसनीय स्रोतों पर आधारित।',
    'dt.badge': 'डिजिटल ट्विन', 'dt.title': 'एक खेत। एक विकसित होती तस्वीर।', 'dt.subtitle': 'एग्रोट्विन मिट्टी, फसल, मौसम, खेत के इतिहास और चल रहे अवलोकनों को मिलाकर आपके खेत का एक जीवंत डिजिटल ट्विन बनाता है।', 'dt.s1': 'मिट्टी की स्थिति', 'dt.s1d': 'पोषक तत्व स्तर, पीएच, जैविक कार्बन, नमी', 'dt.s2': 'फसल की स्थिति', 'dt.s2d': 'फसल का प्रकार, किस्म, विकास चरण, लक्ष्य उपज', 'dt.s3': 'मौसम और पर्यावरण', 'dt.s3d': 'पिछले अनुप्रयोग और पोषक तत्व खाता', 'dt.s4': 'वर्तमान योजना', 'dt.s4d': 'व्यक्तिगत, खेत-विशिष्ट सिफारिश',
    'dl.badge': 'यह कैसे काम करता है', 'dl.title': 'खेत बदलने पर योजना बदल जाती है।', 'dl.subtitle': 'एक निरंतर, एजेंटिक प्रणाली जो स्थिति विकसित होने पर निगरानी, ​​पता लगाती है और फिर से योजना बनाती है।', 'dl.obs': 'अवलोकन', 'dl.obsd': 'खेत, मिट्टी, फसल और मौसम डेटा', 'dl.und': 'समझें', 'dl.undd': 'वर्तमान खेत की स्थिति बनाएं', 'dl.pre': 'भविष्यवाणी', 'dl.pred': 'जरूरतों और जोखिमों का अनुमान लगाएं', 'dl.opt': 'अनुकूलन', 'dl.optd': 'कृषि संबंधी बाधाओं के तहत सर्वोत्तम योजना खोजें', 'dl.val': 'सत्यापन', 'dl.vald': 'सुरक्षा, नियमों और आत्मविश्वास की जांच करें', 'dl.rec': 'सिफारिश', 'dl.recd': 'स्पष्ट आवेदन योजना प्रदान करें', 'dl.mon': 'निगरानी', 'dl.mond': 'सिफारिश के बाद स्थितियों को ट्रैक करें', 'dl.rep': 'पुनः योजना', 'dl.repd': 'स्थितियां बदलने पर योजना अपडेट करें',
    'pr.badge': 'व्याख्यात्मकता', 'pr.title1': 'हर सिफारिश अपना', 'pr.title2': 'प्रमाण साथ लाती है।', 'pr.subtitle': 'देखें कि वास्तव में सिफारिश क्यों की गई है - किस डेटा का उपयोग किया गया था, यह किस कृषि ज्ञान से लिया गया है, और हम कितने आश्वस्त हैं।', 'pr.view': 'एक उदाहरण देखें', 'pr.q1': 'मुझे क्या डालना चाहिए?', 'pr.q2': 'मेरे खेत के लिए कितना सही है?', 'pr.q3': 'मुझे इसे कब लागू करना चाहिए?', 'pr.q4': 'यह सही योजना क्यों है?', 'pr.q5': 'किस साक्ष्य के आधार पर?', 'pr.q6': 'हम कितने सुनिश्चित हैं?',
    'wi.badge': 'व्हाट-इफ सिम्युलेटर', 'wi.title1': 'खेत में पहुंचने से पहले', 'wi.title2': 'बदलाव का', 'wi.title3': 'परीक्षण करें।', 'wi.subtitle': 'विभिन्न उर्वरक मात्रा, आवेदन समय या लक्ष्य उपज का अनुकरण करें और अपने खेत के लिए अपेक्षित परिणाम देखें।', 'wi.try': 'सिम्युलेटर आज़माएं', 'wi.scen': 'व्हाट-इफ परिदृश्य', 'wi.fert': 'उर्वरक बजट', 'wi.delay': 'आवेदन में देरी', 'wi.target': 'लक्ष्य उपज', 'wi.plan': 'व्हाट-इफ योजना', 'wi.estY': 'अनुमानित उपज:', 'wi.estC': 'अनुमानित लागत:', 'wi.sup': 'समर्थित फसलें',
    'pi.badge': 'पायलट क्षेत्र', 'pi.title': 'घर के करीब से शुरुआत।', 'pi.subtitle': 'एग्रोट्विन को महाराष्ट्र के प्रमुख कृषि क्षेत्रों में पायलट किया जा रहा है, जो स्थानीय रूप से महत्वपूर्ण फसलों और वास्तविक किसानों की जरूरतों पर ध्यान केंद्रित कर रहा है।', 'pi.str': 'एक मजबूत महाराष्ट्र के लिए मजबूत खेत।',
    'hu.badge': 'मानव निरीक्षण', 'hu.title1': 'तकनीक को पता होना चाहिए', 'hu.title2': 'कि कब रुकना है।', 'hu.subtitle': 'एग्रोट्विन को चुपचाप असमर्थित सिफारिशें देने के बजाय कम आत्मविश्वास वाले मामलों, लापता डेटा, परस्पर विरोधी साक्ष्य और असामान्य स्थितियों को सामने लाने के लिए डिज़ाइन किया गया है।', 'hu.c1': 'विश्वास और डेटा-गुणवत्ता की जांच', 'hu.c2': 'सिफारिश जारी न होने पर स्पष्ट कारण', 'hu.c3': 'कृषिविज्ञानी समीक्षा और ओवरराइड समर्थन', 'hu.c4': 'महत्वपूर्ण निर्णयों के लिए ऑडिट ट्रेल', 'hu.rev': 'समीक्षा की आवश्यकता है', 'hu.revd': 'परस्पर विरोधी मिट्टी परीक्षण परिणाम पाए गए। सिफारिश से पहले कृषिविज्ञानी समीक्षा आवश्यक है।',
    'fi.badge': 'एक अधिक लचीली कृषि', 'fi.title1': 'एक बार की सिफारिशों से', 'fi.title2': 'निरंतर खेत खुफिया तक।', 'fi.btn': 'एग्रोट्विन खोलें',
    'fo.tag': 'सतत उर्वरक उपयोग अनुकूलक', 'fo.d1': 'महाराष्ट्र के लिए डिज़ाइन किया गया।', 'fo.d2': 'किसानों के लिए देखभाल के साथ बनाया गया।'
  },
  mr: {
    'nav.home': 'मुख्यपृष्ठ', 'nav.howItWorks': 'हे कसे काम करते', 'nav.capabilities': 'क्षमता', 'nav.pilotRegions': 'पायलट क्षेत्र', 'nav.resources': 'संसाधने', 'nav.openDashboard': 'डॅशबोर्ड उघडा',
    'hero.badge': 'ऍग्रोट्विन एआय - शाश्वत खत वापर ऑप्टिमायझर', 'hero.title.1': 'उत्तम निर्णय', 'hero.title.2': 'प्रत्येक शेताच्या', 'hero.title.3': 'उत्तम आकलनापासून', 'hero.title.4': 'सुरू होतात.', 'hero.subtitle': 'AgroTwin AI मातीचा डेटा, पिकाचा प्रकार, हवामान आणि शेताचा इतिहास वापरून पुराव्यावर आधारित खत निर्णय समर्थन प्रदान करते — शेतकऱ्यांना योग्य वेळी योग्य पोषक तत्वे वापरण्यास मदत करते.', 'hero.explore': 'प्लॅटफॉर्म एक्सप्लोर करा', 'hero.howItWorks': 'हे कसे काम करते', 'hero.currentPlan': 'सध्याची योजना', 'hero.applyUrea': 'युरिया लागू करा (46-0-0)', 'hero.in2Days': '2 दिवसांत', 'hero.weather': 'हवामान', 'hero.lightRain': 'हलका पाऊस',
    'cap.title1': 'जिवंत शेत डिजिटल ट्विन', 'cap.desc1': 'तुमच्या शेताचे सतत विकसित होणारे दृश्य.', 'cap.title2': 'सतत निरीक्षण', 'cap.desc2': 'हवामान, माती किंवा पिकाची स्थिती बदलल्यावर जुळवून घेते.', 'cap.title3': 'पुराव्यावर आधारित शिफारसी', 'cap.desc3': 'कृषी विज्ञान, वास्तविक शेतातील डेटा आणि विश्वसनीय स्रोतांवर आधारित.',
    'dt.badge': 'डिजिटल ट्विन', 'dt.title': 'एक शेत. एक विकसित होणारे चित्र.', 'dt.subtitle': 'AgroTwin माती, पीक, हवामान, शेताचा इतिहास आणि चालू निरीक्षणांचे एकत्रीकरण करून तुमच्या शेताचे जिवंत डिजिटल ट्विन तयार करते.', 'dt.s1': 'मातीची स्थिती', 'dt.s1d': 'पोषक तत्वांची पातळी, सामू, सेंद्रिय कर्ब, ओलावा', 'dt.s2': 'पिकाची स्थिती', 'dt.s2d': 'पिकाचा प्रकार, वाण, वाढीचा टप्पा, लक्ष्य उत्पन्न', 'dt.s3': 'हवामान आणि पर्यावरण', 'dt.s3d': 'मागील अनुप्रयोग आणि पोषक तत्व खाते', 'dt.s4': 'सध्याची योजना', 'dt.s4d': 'वैयक्तिकृत, शेत-विशिष्ट शिफारस',
    'dl.badge': 'हे कसे काम करते', 'dl.title': 'शेत बदलले की योजना बदलते.', 'dl.subtitle': 'एक सतत, एजंटिक प्रणाली जी परिस्थिती विकसित होताना निरीक्षण करते, शोधते आणि पुन्हा योजना बनवते.', 'dl.obs': 'निरीक्षण', 'dl.obsd': 'शेत, माती, पीक आणि हवामान डेटा', 'dl.und': 'समजून घ्या', 'dl.undd': 'सध्याची शेताची स्थिती तयार करा', 'dl.pre': 'अंदाज', 'dl.pred': 'गरजा आणि धोक्यांचा अंदाज लावा', 'dl.opt': 'ऑप्टिमाइझ', 'dl.optd': 'कृषीविषयक मर्यादांखाली सर्वोत्तम योजना शोधा', 'dl.val': 'पडताळणी', 'dl.vald': 'सुरक्षा, नियम आणि आत्मविश्वासाची तपासणी करा', 'dl.rec': 'शिफारस', 'dl.recd': 'स्पष्ट अर्ज योजना प्रदान करा', 'dl.mon': 'निरीक्षण', 'dl.mond': 'शिफारसीनंतर परिस्थितीचा मागोवा घ्या', 'dl.rep': 'पुन्हा योजना', 'dl.repd': 'परिस्थिती बदलल्यावर योजना अपडेट करा',
    'pr.badge': 'स्पष्टीकरणक्षमता', 'pr.title1': 'प्रत्येक शिफारस आपला', 'pr.title2': 'पुरावा सोबत आणते.', 'pr.subtitle': 'शिफारस नक्की का केली आहे ते पहा — कोणता डेटा वापरला गेला, तो कोणत्या कृषी ज्ञानातून घेतला आहे आणि आम्हाला किती खात्री आहे.', 'pr.view': 'एक उदाहरण पहा', 'pr.q1': 'मी काय लागू करावे?', 'pr.q2': 'माझ्या शेतासाठी किती योग्य आहे?', 'pr.q3': 'मी ते कधी लागू करावे?', 'pr.q4': 'ही योग्य योजना का आहे?', 'pr.q5': 'कोणत्या पुराव्यांवर आधारित?', 'pr.q6': 'आम्हाला किती खात्री आहे?',
    'wi.badge': 'व्हॉट-इफ सिम्युलेटर', 'wi.title1': 'बदल शेतात पोहोचण्यापूर्वी', 'wi.title2': 'त्याची', 'wi.title3': 'चाचणी करा.', 'wi.subtitle': 'विविध खतांचे प्रमाण, अर्जाच्या वेळा किंवा लक्ष्यित उत्पन्नाचे अनुकरण करा आणि तुमच्या शेतासाठी अपेक्षित परिणाम पहा.', 'wi.try': 'सिम्युलेटर वापरून पहा', 'wi.scen': 'व्हॉट-इफ परिस्थिती', 'wi.fert': 'खत बजेट', 'wi.delay': 'अर्जास विलंब', 'wi.target': 'लक्ष्य उत्पन्न', 'wi.plan': 'व्हॉट-इफ योजना', 'wi.estY': 'अंदाजित उत्पन्न:', 'wi.estC': 'अंदाजित खर्च:', 'wi.sup': 'समर्थित पिके',
    'pi.badge': 'पायलट क्षेत्र', 'pi.title': 'घराजवळून सुरुवात.', 'pi.subtitle': 'AgroTwin महाराष्ट्रातील प्रमुख कृषी क्षेत्रांमध्ये प्रायोगिक तत्त्वावर राबवले जात आहे, स्थानिक पातळीवर महत्त्वाची पिके आणि वास्तविक शेतकऱ्यांच्या गरजांवर लक्ष केंद्रित करून.', 'pi.str': 'सशक्त महाराष्ट्रासाठी सशक्त शेती.',
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
    f.write(context_content)


# Apply simple text replacements in each component via regex/replace
def patch_file(filepath, replacements):
    with open(filepath, 'r') as f:
        content = f.read()
    
    if "useLanguage" not in content:
        content = '"use client";\nimport { useLanguage } from "@/contexts/LanguageContext";\n' + content
    
    if "const { t } = useLanguage();" not in content:
        content = content.replace("export default function", "export default function", 1)
        # Find the opening brace of the default function
        parts = content.split("export default function")
        if len(parts) > 1:
            name_and_rest = parts[1]
            idx = name_and_rest.find('{')
            if idx != -1:
                content = parts[0] + "export default function" + name_and_rest[:idx+1] + "\n  const { t } = useLanguage();\n" + name_and_rest[idx+1:]

    for old, new in replacements.items():
        content = content.replace(old, new)
        
    with open(filepath, 'w') as f:
        f.write(content)

# CapabilityStrip
patch_file('src/components/landing/CapabilityStrip.tsx', {
    '>Living farm digital twin<': '>{t("cap.title1")}<',
    '>A persistent, evolving view of your field.<': '>{t("cap.desc1")}<',
    '>Continuous monitoring<': '>{t("cap.title2")}<',
    '>Adapts when weather, soil or crop conditions change.<': '>{t("cap.desc2")}<',
    '>Evidence-grounded recommendations<': '>{t("cap.title3")}<',
    '>Based on agronomic science, real field data and trusted sources.<': '>{t("cap.desc3")}<'
})

# DigitalTwinSection
patch_file('src/components/landing/DigitalTwinSection.tsx', {
    '>Digital Twin<': '>{t("dt.badge")}<',
    '>One field. One evolving picture.<': '>{t("dt.title")}<',
    '>AgroTwin creates a living digital twin of your field by combining soil, crop, weather, farm history and ongoing observations.<': '>{t("dt.subtitle")}<',
    '>Soil state<': '>{t("dt.s1")}<',
    '>Nutrient levels, pH, organic carbon, moisture<': '>{t("dt.s1d")}<',
    '>Crop state<': '>{t("dt.s2")}<',
    '>Crop type, variety, growth stage, target yield<': '>{t("dt.s2d")}<',
    '>Weather & environment<': '>{t("dt.s3")}<',
    '>Past applications and nutrient ledger<': '>{t("dt.s3d")}<',
    '>Current plan<': '>{t("dt.s4")}<',
    '>Personalized, field-specific recommendation<': '>{t("dt.s4d")}<'
})

# DecisionLoopSection
patch_file('src/components/landing/DecisionLoopSection.tsx', {
    '>How it works<': '>{t("dl.badge")}<',
    '>The plan changes when the field changes.<': '>{t("dl.title")}<',
    '>A continuous, agentic system that monitors, detects and re-plans as conditions evolve.<': '>{t("dl.subtitle")}<',
    '>Observe<': '>{t("dl.obs")}<',
    '>Field, soil, crop and weather data<': '>{t("dl.obsd")}<',
    '>Understand<': '>{t("dl.und")}<',
    '>Build current field state<': '>{t("dl.undd")}<',
    '>Predict<': '>{t("dl.pre")}<',
    '>Estimate needs and risks<': '>{t("dl.pred")}<',
    '>Optimize<': '>{t("dl.opt")}<',
    '>Find best plan under agronomic & cost constraints<': '>{t("dl.optd")}<',
    '>Validate<': '>{t("dl.val")}<',
    '>Check safety, rules and confidence<': '>{t("dl.vald")}<',
    '>Recommend<': '>{t("dl.rec")}<',
    '>Provide clear application plan<': '>{t("dl.recd")}<',
    '>Monitor<': '>{t("dl.mon")}<',
    '>Track conditions after recommendation<': '>{t("dl.mond")}<',
    '>Re-plan<': '>{t("dl.rep")}<',
    '>Update plan when conditions change<': '>{t("dl.repd")}<'
})

# ProofSection
patch_file('src/components/landing/ProofSection.tsx', {
    '>Explainability<': '>{t("pr.badge")}<',
    'Every recommendation<br/>': '{t("pr.title1")}<br/>',
    'carries its proof.': '{t("pr.title2")}',
    'See exactly why a recommendation is made — what data was used, which agronomic knowledge it draws from, and how confident we are.': '{t("pr.subtitle")}',
    '>View an example': '>{t("pr.view")}',
    '>WHAT should I apply?<': '>{t("pr.q1")}<',
    '>HOW MUCH is right for my field?<': '>{t("pr.q2")}<',
    '>WHEN should I apply it?<': '>{t("pr.q3")}<',
    '>WHY is this the right plan?<': '>{t("pr.q4")}<',
    '>BASED ON WHAT evidence?<': '>{t("pr.q5")}<',
    '>HOW SURE are we?<': '>{t("pr.q6")}<'
})

# WhatIfPreview
patch_file('src/components/landing/WhatIfPreview.tsx', {
    '>What-If Simulator<': '>{t("wi.badge")}<',
    'Test a change<br/>': '{t("wi.title1")}<br/>',
    'before it reaches<br/>': '{t("wi.title2")}<br/>',
    'the field.': '{t("wi.title3")}',
    'Simulate different fertilizer amounts, application timings or target yields and see the expected outcomes for your field.': '{t("wi.subtitle")}',
    '>Try the simulator': '>{t("wi.try")}',
    '>What-If Scenario<': '>{t("wi.scen")}<',
    '>Fertilizer Budget<': '>{t("wi.fert")}<',
    '>Delay Application<': '>{t("wi.delay")}<',
    '>Target Yield<': '>{t("wi.target")}<',
    '>What-If Plan<': '>{t("wi.plan")}<',
    '>Est. yield:<': '>{t("wi.estY")}<',
    '>Est. cost:<': '>{t("wi.estC")}<',
    '>Supported crops<': '>{t("wi.sup")}<'
})

# PilotRegionsSection
patch_file('src/components/landing/PilotRegionsSection.tsx', {
    '>Pilot Regions<': '>{t("pi.badge")}<',
    '>Starting close to home.<': '>{t("pi.title")}<',
    '>AgroTwin is being piloted in key agricultural regions of Maharashtra, focusing on locally important crops and real farmer needs.<': '>{t("pi.subtitle")}<',
    '>Stronger farms<br/>for a stronger<br/>Maharashtra.<': ' dangerouslySetInnerHTML={{__html: t("pi.str")}}>'
})

# HumanOversightSection
patch_file('src/components/landing/HumanOversightSection.tsx', {
    '>Human Oversight<': '>{t("hu.badge")}<',
    'Technology should know<br/>': '{t("hu.title1")}<br/>',
    'when to pause.': '{t("hu.title2")}',
    'AgroTwin is designed to surface low-confidence cases, missing data, conflicting evidence and unusual conditions rather than silently producing unsupported recommendations.': '{t("hu.subtitle")}',
    '"Confidence and data-quality checks"': 't("hu.c1")',
    '"Clear reasons when a recommendation is not issued"': 't("hu.c2")',
    '"Agronomist review and override support"': 't("hu.c3")',
    '"Audit trail for important decisions"': 't("hu.c4")',
    '>Needs Review<': '>{t("hu.rev")}<',
    '>Conflicting soil test results detected. Agronomist review required before recommendation.<': '>{t("hu.revd")}<'
})

# FinalCTA
patch_file('src/components/landing/FinalCTA.tsx', {
    '>A MORE RESILIENT AGRICULTURE<': '>{t("fi.badge")}<',
    'From one-time recommendations<br className="hidden md:block"/>': '{t("fi.title1")}<br className="hidden md:block"/>',
    'to continuous farm intelligence.': '{t("fi.title2")}',
    '>Open AgroTwin': '>{t("fi.btn")}'
})

# LandingFooter
patch_file('src/components/landing/LandingFooter.tsx', {
    '>Sustainable Fertilizer Usage Optimizer<': '>{t("fo.tag")}<',
    '>Designed for Maharashtra.<br/>Built for farmers, with care.<': ' dangerouslySetInnerHTML={{__html: t("fo.d1") + "<br/>" + t("fo.d2")}}>'
})

print("All components fully translated!")
