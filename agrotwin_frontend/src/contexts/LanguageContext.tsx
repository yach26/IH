
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
    'fo.tag': 'Sustainable Fertilizer Usage Optimizer', 'fo.d1': 'Designed for Maharashtra.', 'fo.d2': 'Built for farmers, with care.',
    // ── Dashboard (Farm page) chrome — labels/buttons/status words only.
    // Backend-generated content (recommendation description, citations,
    // product/crop names, numbers) is never machine-translated here — it
    // stays in English rather than pretending to translate text this app
    // didn't actually generate in the selected language.
    'dash.uploadSoilReport': 'Upload Soil Report', 'dash.fieldOverview': 'Field Overview', 'dash.viewOnMap': 'View on Map',
    'dash.active': 'Active', 'dash.crop': 'Crop', 'dash.stage': 'Stage', 'dash.area': 'Area', 'dash.soilType': 'Soil Type',
    'dash.notRecorded': 'Not recorded', 'dash.soilHealth': 'Soil Health', 'dash.notAvailable': 'Not available',
    'dash.nitrogen': 'Nitrogen (N)', 'dash.phosphorus': 'Phosphorus (P)', 'dash.potassium': 'Potassium (K)',
    'dash.high': 'High', 'dash.moderate': 'Moderate', 'dash.low': 'Low', 'dash.good': 'Good',
    'dash.weather7d': 'Weather (Next 7 Days)', 'dash.forecastRainfall': 'Forecast rainfall',
    'dash.suitableForApplication': 'Suitable for application', 'dash.heavyRain': 'Heavy rain',
    'dash.weatherSource': 'Source: Open-Meteo via weather agent',
    'dash.dailyBreakdownUnavailable': 'Daily breakdown unavailable — only the 7-day total is reported by the API.',
    'dash.weatherUnavailableField': 'Weather unavailable — no weather agent run has been recorded for this field yet.',
    'dash.weatherUnavailableShort': 'Weather unavailable for this field',
    'dash.fieldStatus': 'Field Status', 'dash.cropCondition': 'Crop condition', 'dash.waterStress': 'Water stress',
    'dash.pestRisk': 'Pest risk', 'dash.diseaseRisk': 'Disease risk', 'dash.notAssessed': 'Not assessed',
    'dash.overallStatus': 'Overall status', 'dash.healthy': 'Healthy', 'dash.needsAttention': 'Needs Attention', 'dash.unknown': 'Unknown',
    'dash.fieldLocation': 'Field Location', 'dash.openInGoogleMaps': 'Open in Google Maps ↗',
    'dash.locationNotProvided': 'Location not provided for this field.',
    'dash.officialRecommendation': 'Official Recommendation', 'dash.fertilizerPlanFor': 'Fertilizer Application Plan — Field',
    'dash.confidence': 'Confidence', 'dash.nextSteps': 'Next Steps',
    'dash.reducedConfidence': 'Reduced confidence — hover a reason for detail', 'dash.source': 'Source',
    'dash.simulateInWhatIf': 'Simulate in What-If', 'dash.downloadPrint': 'Download / Print Official Recommendation',
    'dash.listen': 'Listen', 'dash.stop': 'Stop', 'dash.recentInsights': 'Recent Insights',
    'dash.noRecentAlerts': 'No recent alerts for this field.', 'dash.cropStageTimeline': 'Crop Stage Timeline', 'dash.current': 'Current',
    'dash.generateRecommendation': 'Generate Recommendation', 'dash.generating': 'Generating…',
    'dash.abstainedBadge': 'Low confidence — abstained', 'dash.abstainedTitle': 'A reliable fertilizer plan cannot currently be produced',
    'dash.requiredBeforePlan': 'Required before a plan can be issued:',
    'dash.noRecGenerated': 'Soil data confirmed. No recommendation has been generated yet.',
    'dash.runPipeline': 'Run the recommendation pipeline to get an evidence-backed fertilizer plan for this field.',
    'dash.loadingField': 'Loading field data…', 'dash.cantReachBackend': "Can't reach the backend", 'dash.retry': 'Retry',
    'dash.field': 'Field', 'dash.noSoilReport': 'No soil report on file for',
    'dash.soilTestNeeded': "The digital twin needs at least one soil test before it can show nutrient levels, a fertilizer recommendation, or a field health score. Upload a soil health card to unlock this field's dashboard.",
    'dash.estCost': 'Est. cost', 'dash.engineeringEstimate': 'Engineering-default estimate, not a sourced price.',
    'dash.applyAction': 'Apply', 'dash.quantity': 'Quantity', 'dash.note': 'Note',
    'dash.listenFullSummary': 'Field summary for', 'dash.listenSoilScore': 'Soil health score',
    'dash.listenOutOf100': 'out of 100', 'dash.listenNutrients': 'Nitrogen is',
    'dash.listenPhosphorusIs': 'Phosphorus is', 'dash.listenPotassiumIs': 'Potassium is',
    'dash.listenWeatherIs': 'This week\'s rainfall forecast is', 'dash.listenWeatherNone': 'Weather has not been checked for this field yet.',
    'dash.listenStepsIntro': 'Next steps are:',
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
    'fo.tag': 'सतत उर्वरक उपयोग अनुकूलक', 'fo.d1': 'महाराष्ट्र के लिए डिज़ाइन किया गया।', 'fo.d2': 'किसानों के लिए देखभाल के साथ बनाया गया।',
    'dash.uploadSoilReport': 'मिट्टी रिपोर्ट अपलोड करें', 'dash.fieldOverview': 'खेत का विवरण', 'dash.viewOnMap': 'मानचित्र पर देखें',
    'dash.active': 'सक्रिय', 'dash.crop': 'फसल', 'dash.stage': 'चरण', 'dash.area': 'क्षेत्रफल', 'dash.soilType': 'मिट्टी का प्रकार',
    'dash.notRecorded': 'दर्ज नहीं है', 'dash.soilHealth': 'मिट्टी का स्वास्थ्य', 'dash.notAvailable': 'उपलब्ध नहीं',
    'dash.nitrogen': 'नाइट्रोजन (N)', 'dash.phosphorus': 'फॉस्फोरस (P)', 'dash.potassium': 'पोटैशियम (K)',
    'dash.high': 'उच्च', 'dash.moderate': 'मध्यम', 'dash.low': 'कम', 'dash.good': 'अच्छा',
    'dash.weather7d': 'मौसम (अगले 7 दिन)', 'dash.forecastRainfall': 'अनुमानित वर्षा',
    'dash.suitableForApplication': 'उर्वरक डालने हेतु उपयुक्त', 'dash.heavyRain': 'भारी बारिश',
    'dash.weatherSource': 'स्रोत: वेदर एजेंट के माध्यम से Open-Meteo',
    'dash.dailyBreakdownUnavailable': 'दैनिक विवरण उपलब्ध नहीं — API केवल 7-दिन का कुल आंकड़ा देता है।',
    'dash.weatherUnavailableField': 'मौसम की जानकारी उपलब्ध नहीं — इस खेत के लिए अभी तक कोई वेदर एजेंट रन दर्ज नहीं हुआ।',
    'dash.weatherUnavailableShort': 'इस खेत के लिए मौसम उपलब्ध नहीं',
    'dash.fieldStatus': 'खेत की स्थिति', 'dash.cropCondition': 'फसल की स्थिति', 'dash.waterStress': 'जल तनाव',
    'dash.pestRisk': 'कीट जोखिम', 'dash.diseaseRisk': 'रोग जोखिम', 'dash.notAssessed': 'आकलन नहीं किया गया',
    'dash.overallStatus': 'समग्र स्थिति', 'dash.healthy': 'स्वस्थ', 'dash.needsAttention': 'ध्यान देने की आवश्यकता', 'dash.unknown': 'अज्ञात',
    'dash.fieldLocation': 'खेत का स्थान', 'dash.openInGoogleMaps': 'गूगल मैप्स में खोलें ↗',
    'dash.locationNotProvided': 'इस खेत के लिए स्थान दर्ज नहीं है।',
    'dash.officialRecommendation': 'आधिकारिक सिफारिश', 'dash.fertilizerPlanFor': 'उर्वरक अनुप्रयोग योजना — खेत',
    'dash.confidence': 'विश्वास स्तर', 'dash.nextSteps': 'अगले कदम',
    'dash.reducedConfidence': 'कम विश्वास स्तर — कारण देखने हेतु होवर करें', 'dash.source': 'स्रोत',
    'dash.simulateInWhatIf': 'व्हाट-इफ में सिम्युलेट करें', 'dash.downloadPrint': 'आधिकारिक सिफारिश डाउनलोड / प्रिंट करें',
    'dash.listen': 'सुनें', 'dash.stop': 'रोकें', 'dash.recentInsights': 'हाल की जानकारियां',
    'dash.noRecentAlerts': 'इस खेत के लिए कोई हालिया अलर्ट नहीं।', 'dash.cropStageTimeline': 'फसल चरण समयरेखा', 'dash.current': 'वर्तमान',
    'dash.generateRecommendation': 'सिफारिश तैयार करें', 'dash.generating': 'तैयार हो रहा है…',
    'dash.abstainedBadge': 'कम विश्वास स्तर — सिफारिश रोकी गई', 'dash.abstainedTitle': 'फिलहाल एक विश्वसनीय उर्वरक योजना तैयार नहीं की जा सकती',
    'dash.requiredBeforePlan': 'योजना जारी करने से पहले आवश्यक:',
    'dash.noRecGenerated': 'मिट्टी डेटा की पुष्टि हो चुकी है। अभी तक कोई सिफारिश तैयार नहीं हुई है।',
    'dash.runPipeline': 'इस खेत के लिए साक्ष्य-आधारित उर्वरक योजना पाने हेतु सिफारिश प्रक्रिया चलाएं।',
    'dash.loadingField': 'खेत का डेटा लोड हो रहा है…', 'dash.cantReachBackend': 'बैकएंड तक नहीं पहुंच पा रहे', 'dash.retry': 'पुनः प्रयास करें',
    'dash.field': 'खेत', 'dash.noSoilReport': 'इसके लिए कोई मिट्टी रिपोर्ट दर्ज नहीं है:',
    'dash.soilTestNeeded': 'नाइट्रोजन स्तर, उर्वरक सिफारिश या खेत स्वास्थ्य स्कोर दिखाने से पहले डिजिटल ट्विन को कम से कम एक मिट्टी परीक्षण चाहिए। इस खेत का डैशबोर्ड खोलने के लिए मिट्टी स्वास्थ्य कार्ड अपलोड करें।',
    'dash.estCost': 'अनुमानित लागत', 'dash.engineeringEstimate': 'यह एक इंजीनियरिंग-डिफ़ॉल्ट अनुमान है, स्रोतित मूल्य नहीं।',
    'dash.applyAction': 'लागू करें', 'dash.quantity': 'मात्रा', 'dash.note': 'टिप्पणी',
    'dash.listenFullSummary': 'खेत का सारांश', 'dash.listenSoilScore': 'मिट्टी स्वास्थ्य स्कोर',
    'dash.listenOutOf100': '100 में से', 'dash.listenNutrients': 'नाइट्रोजन है',
    'dash.listenPhosphorusIs': 'फॉस्फोरस है', 'dash.listenPotassiumIs': 'पोटैशियम है',
    'dash.listenWeatherIs': 'इस सप्ताह की वर्षा का अनुमान है', 'dash.listenWeatherNone': 'इस खेत के लिए अभी तक मौसम की जांच नहीं हुई है।',
    'dash.listenStepsIntro': 'अगले कदम हैं:',
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
    'fo.tag': 'शाश्वत खत वापर ऑप्टिमायझर', 'fo.d1': 'महाराष्ट्रासाठी डिझाइन केलेले.', 'fo.d2': 'शेतकऱ्यांसाठी काळजीपूर्वक बनवलेले.',
    'dash.uploadSoilReport': 'माती अहवाल अपलोड करा', 'dash.fieldOverview': 'शेताचा आढावा', 'dash.viewOnMap': 'नकाशावर पहा',
    'dash.active': 'सक्रिय', 'dash.crop': 'पीक', 'dash.stage': 'टप्पा', 'dash.area': 'क्षेत्रफळ', 'dash.soilType': 'मातीचा प्रकार',
    'dash.notRecorded': 'नोंद नाही', 'dash.soilHealth': 'मातीचे आरोग्य', 'dash.notAvailable': 'उपलब्ध नाही',
    'dash.nitrogen': 'नत्र (N)', 'dash.phosphorus': 'स्फुरद (P)', 'dash.potassium': 'पालाश (K)',
    'dash.high': 'उच्च', 'dash.moderate': 'मध्यम', 'dash.low': 'कमी', 'dash.good': 'चांगले',
    'dash.weather7d': 'हवामान (पुढील 7 दिवस)', 'dash.forecastRainfall': 'अंदाजित पाऊस',
    'dash.suitableForApplication': 'खत देण्यासाठी योग्य', 'dash.heavyRain': 'मुसळधार पाऊस',
    'dash.weatherSource': 'स्रोत: वेदर एजंटद्वारे Open-Meteo',
    'dash.dailyBreakdownUnavailable': 'दैनंदिन तपशील उपलब्ध नाही — API फक्त 7-दिवसांची एकूण आकडेवारी देते.',
    'dash.weatherUnavailableField': 'हवामान उपलब्ध नाही — या शेतासाठी अद्याप कोणताही वेदर एजंट रन नोंदवला गेला नाही.',
    'dash.weatherUnavailableShort': 'या शेतासाठी हवामान उपलब्ध नाही',
    'dash.fieldStatus': 'शेताची स्थिती', 'dash.cropCondition': 'पिकाची स्थिती', 'dash.waterStress': 'पाण्याचा ताण',
    'dash.pestRisk': 'कीड धोका', 'dash.diseaseRisk': 'रोग धोका', 'dash.notAssessed': 'मूल्यांकन केले नाही',
    'dash.overallStatus': 'एकूण स्थिती', 'dash.healthy': 'निरोगी', 'dash.needsAttention': 'लक्ष देणे आवश्यक', 'dash.unknown': 'अज्ञात',
    'dash.fieldLocation': 'शेताचे ठिकाण', 'dash.openInGoogleMaps': 'Google Maps मध्ये उघडा ↗',
    'dash.locationNotProvided': 'या शेतासाठी ठिकाण नोंदवलेले नाही.',
    'dash.officialRecommendation': 'अधिकृत शिफारस', 'dash.fertilizerPlanFor': 'खत वापर योजना — शेत',
    'dash.confidence': 'विश्वासार्हता', 'dash.nextSteps': 'पुढील पावले',
    'dash.reducedConfidence': 'कमी विश्वासार्हता — कारण पाहण्यासाठी होवर करा', 'dash.source': 'स्रोत',
    'dash.simulateInWhatIf': 'व्हॉट-इफ मध्ये सिम्युलेट करा', 'dash.downloadPrint': 'अधिकृत शिफारस डाउनलोड / प्रिंट करा',
    'dash.listen': 'ऐका', 'dash.stop': 'थांबवा', 'dash.recentInsights': 'अलीकडील माहिती',
    'dash.noRecentAlerts': 'या शेतासाठी अलीकडील सूचना नाहीत.', 'dash.cropStageTimeline': 'पीक टप्पा कालरेषा', 'dash.current': 'सध्याचा',
    'dash.generateRecommendation': 'शिफारस तयार करा', 'dash.generating': 'तयार होत आहे…',
    'dash.abstainedBadge': 'कमी विश्वासार्हता — शिफारस रोखली', 'dash.abstainedTitle': 'सध्या विश्वासार्ह खत योजना तयार करता येत नाही',
    'dash.requiredBeforePlan': 'योजना देण्यापूर्वी आवश्यक:',
    'dash.noRecGenerated': 'मातीचा डेटा पुष्टी केला आहे. अद्याप कोणतीही शिफारस तयार झालेली नाही.',
    'dash.runPipeline': 'या शेतासाठी पुराव्यावर आधारित खत योजना मिळवण्यासाठी शिफारस प्रक्रिया चालवा.',
    'dash.loadingField': 'शेताचा डेटा लोड होत आहे…', 'dash.cantReachBackend': 'बॅकएंडपर्यंत पोहोचता येत नाही', 'dash.retry': 'पुन्हा प्रयत्न करा',
    'dash.field': 'शेत', 'dash.noSoilReport': 'यासाठी कोणताही माती अहवाल नोंदवलेला नाही:',
    'dash.soilTestNeeded': 'पोषक पातळी, खत शिफारस किंवा शेत आरोग्य गुण दाखवण्यापूर्वी डिजिटल ट्विनला किमान एक माती चाचणी आवश्यक आहे. या शेताचे डॅशबोर्ड अनलॉक करण्यासाठी माती आरोग्य कार्ड अपलोड करा.',
    'dash.estCost': 'अंदाजित खर्च', 'dash.engineeringEstimate': 'हा इंजिनिअरिंग-डीफॉल्ट अंदाज आहे, स्रोतित किंमत नाही.',
    'dash.applyAction': 'वापरा', 'dash.quantity': 'प्रमाण', 'dash.note': 'टीप',
    'dash.listenFullSummary': 'शेताचा सारांश', 'dash.listenSoilScore': 'माती आरोग्य गुण',
    'dash.listenOutOf100': '100 पैकी', 'dash.listenNutrients': 'नत्र आहे',
    'dash.listenPhosphorusIs': 'स्फुरद आहे', 'dash.listenPotassiumIs': 'पालाश आहे',
    'dash.listenWeatherIs': 'या आठवड्याचा पावसाचा अंदाज आहे', 'dash.listenWeatherNone': 'या शेतासाठी अद्याप हवामान तपासले गेलेले नाही.',
    'dash.listenStepsIntro': 'पुढील पावले आहेत:',
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
