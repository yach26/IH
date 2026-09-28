// English source text -> Hindi, Marathi. Numbers, identifiers and citations stay intact.
export const uiTranslations: Record<string, [string, string]> = Object.fromEntries(`
Overview|अवलोकन|आढावा
Farm|खेत|शेत
Simulator|परिदृश्य तुलना|परिस्थिती तुलना
Upload|रिपोर्ट अपलोड|अहवाल अपलोड
Insights|जानकारी|माहिती
Command Center|नियंत्रण केंद्र|नियंत्रण केंद्र
New field|नया खेत|नवीन शेत
Notifications|सूचनाएँ|सूचना
Select language|भाषा चुनें|भाषा निवडा
Kisan Saathi|किसान साथी|किसान साथी
Digital Krishi Twin|खेत का डिजिटल मॉडल|शेताचे डिजिटल मॉडेल
Kisan Saathi · Farm nutrient decision support · Kolhapur pilot|किसान साथी · खेत के पोषक तत्वों पर निर्णय सहायता · कोल्हापुर पायलट|किसान साथी · शेतातील पोषक घटकांसाठी निर्णय सहाय्य · कोल्हापूर पायलट
Step 1 of 3 · Your field|चरण 1 / 3 · आपका खेत|टप्पा 1 / 3 · तुमचे शेत
Tell us about your farm|अपने खेत की जानकारी दें|तुमच्या शेताची माहिती द्या
Add your field details, upload your Soil Health Card, then review and confirm the extracted values. Your dashboard will use that confirmed data.|खेत की जानकारी भरें, मृदा स्वास्थ्य कार्ड अपलोड करें और निकाले गए मान जाँचकर पुष्टि करें। डैशबोर्ड इसी पुष्ट डेटा का उपयोग करेगा।|शेताची माहिती भरा, मृदा आरोग्य पत्रिका अपलोड करा आणि काढलेली मूल्ये तपासून पुष्टी करा. डॅशबोर्ड हाच पुष्टी केलेला डेटा वापरेल.
Farmer name|किसान का नाम|शेतकऱ्याचे नाव
District and state|जिला और राज्य|जिल्हा आणि राज्य
Select your location|स्थान चुनें|ठिकाण निवडा
Field area (hectares)|खेत का क्षेत्रफल (हेक्टेयर)|शेताचे क्षेत्रफळ (हेक्टर)
Irrigation|सिंचाई|सिंचन
Select irrigation|सिंचाई चुनें|सिंचन निवडा
Irrigated|सिंचित|बागायती
Rainfed|वर्षा आधारित|जिरायती
Latitude (optional)|अक्षांश (वैकल्पिक)|अक्षांश (ऐच्छिक)
Longitude (optional)|देशांतर (वैकल्पिक)|रेखांश (ऐच्छिक)
Crop and season|फसल और मौसम|पीक आणि हंगाम
Select your crop|फसल चुनें|पीक निवडा
Current crop stage|फसल की वर्तमान अवस्था|पिकाचा सध्याचा टप्पा
Select current stage|वर्तमान अवस्था चुनें|सध्याचा टप्पा निवडा
No supported stages available|समर्थित अवस्थाएँ उपलब्ध नहीं हैं|समर्थित टप्पे उपलब्ध नाहीत
Sowing date|बुवाई की तारीख|पेरणीची तारीख
Only currently supported locations and crop seasons are listed. Leave coordinates blank if you do not know them.|केवल समर्थित स्थान और फसल मौसम सूचीबद्ध हैं। निर्देशांक पता न हों तो खाली छोड़ें।|फक्त समर्थित ठिकाणे आणि पीक हंगाम दिले आहेत. निर्देशांक माहीत नसल्यास रिकामे ठेवा.
Reload available options|विकल्प फिर लोड करें|पर्याय पुन्हा लोड करा
Your field has been saved. Retry to finish its crop details.|खेत सहेज लिया गया है। फसल की जानकारी पूरी करने के लिए फिर प्रयास करें।|शेत जतन झाले आहे. पिकाची माहिती पूर्ण करण्यासाठी पुन्हा प्रयत्न करा.
Saving your field…|खेत सहेजा जा रहा है…|शेत जतन होत आहे…
Save field & upload soil report|खेत सहेजें और मृदा रिपोर्ट अपलोड करें|शेत जतन करा व मातीचा अहवाल अपलोड करा
Open an existing farmer field|पहले से दर्ज किसान का खेत खोलें|आधी नोंदवलेले शेत उघडा
Select a field previously created through farmer onboarding.|पहले दर्ज किया गया खेत चुनें।|आधी नोंदवलेले शेत निवडा.
Open an existing field|दर्ज खेत खोलें|नोंदवलेले शेत उघडा
Choose a field|खेत चुनें|शेत निवडा
View separate pilot demo (sample data)|अलग पायलट डेमो देखें (नमूना डेटा)|स्वतंत्र पायलट नमुना पाहा (नमुना डेटा)
Field|खेत|शेत
Fields|खेत|शेते
Crop|फसल|पीक
Crop / Stage|फसल / अवस्था|पीक / टप्पा
Soil Health|मृदा स्वास्थ्य|मातीचे आरोग्य
Soil score unavailable|मृदा स्कोर उपलब्ध नहीं|मातीचे गुण उपलब्ध नाहीत
No fields available.|कोई खेत उपलब्ध नहीं।|कोणतेही शेत उपलब्ध नाही.
Sugarcane|गन्ना|ऊस
Banana|केला|केळी
Cotton|कपास|कापूस
Rice|धान|भात
Wheat|गेहूँ|गहू
Soybean|सोयाबीन|सोयाबीन
Kolhapur|कोल्हापुर|कोल्हापूर
Jalgaon|जलगाँव|जळगाव
Maharashtra|महाराष्ट्र|महाराष्ट्र
pre seasonal|पूर्व मौसमी|पूर्वहंगामी
grand growth|मुख्य वृद्धि|मुख्य वाढ
tillering|कल्ले निकलना|फुटवे येणे
germination|अंकुरण|उगवण
maturity|परिपक्वता|परिपक्वता
harvest|कटाई|कापणी
Status|स्थिति|स्थिती
Confidence|विश्वसनीयता|विश्वासार्हता
HIGH|उच्च|उच्च
MEDIUM|मध्यम|मध्यम
LOW|कम|कमी
High|उच्च|उच्च
Medium|मध्यम|मध्यम
Low|कम|कमी
Not available|उपलब्ध नहीं|उपलब्ध नाही
Unavailable|अनुपलब्ध|अनुपलब्ध
Not recorded|दर्ज नहीं|नोंद नाही
None|कोई नहीं|काही नाही
Retry|फिर प्रयास करें|पुन्हा प्रयत्न करा
Refresh|ताज़ा करें|पुन्हा लोड करा
Loading…|लोड हो रहा है…|लोड होत आहे…
Loading fields…|खेत लोड हो रहे हैं…|शेते लोड होत आहेत…
Loading your fields...|आपके खेत लोड हो रहे हैं…|तुमची शेते लोड होत आहेत…
Loading field...|खेत लोड हो रहा है…|शेत लोड होत आहे…
Cancel|रद्द करें|रद्द करा
Kisan Saathi · Soil report|किसान साथी · मृदा रिपोर्ट|किसान साथी · मातीचा अहवाल
Upload and verify your soil test|मृदा परीक्षण अपलोड करें और जाँचें|मातीची चाचणी अपलोड करा आणि तपासा
Upload report|रिपोर्ट अपलोड करें|अहवाल अपलोड करा
Review and confirm|जाँचें और पुष्टि करें|तपासा आणि पुष्टी करा
Field updated|खेत अपडेट हुआ|शेत अद्ययावत झाले
Drag and drop your soil health card or laboratory report|मृदा स्वास्थ्य कार्ड या प्रयोगशाला रिपोर्ट यहाँ डालें|मृदा आरोग्य पत्रिका किंवा प्रयोगशाळेचा अहवाल येथे टाका
Choose report|रिपोर्ट चुनें|अहवाल निवडा
Choose soil report|मृदा रिपोर्ट चुनें|मातीचा अहवाल निवडा
Uploading and reading report…|रिपोर्ट अपलोड करके पढ़ी जा रही है…|अहवाल अपलोड करून वाचला जात आहे…
Uploading and reading soil report|मृदा रिपोर्ट अपलोड और पढ़ रहे हैं|मातीचा अहवाल अपलोड करून वाचत आहोत
Review extracted values|निकाले गए मान जाँचें|काढलेली मूल्ये तपासा
Use a different report|दूसरी रिपोर्ट चुनें|दुसरा अहवाल निवडा
Provisional values — farmer verification required|अस्थायी मान — किसान की पुष्टि आवश्यक|तात्पुरती मूल्ये — शेतकऱ्याची पुष्टी आवश्यक
The report could not be read. Enter the laboratory values below manually.|रिपोर्ट पढ़ी नहीं जा सकी। प्रयोगशाला के मान नीचे स्वयं भरें।|अहवाल वाचता आला नाही. प्रयोगशाळेची मूल्ये खाली स्वतः भरा.
OCR can misread numbers and units. Compare every value with your original report, including values marked high confidence.|OCR संख्याएँ और इकाइयाँ गलत पढ़ सकता है। उच्च विश्वसनीयता वाले मान भी मूल रिपोर्ट से जाँचें।|OCR संख्या आणि एकके चुकीची वाचू शकतो. उच्च विश्वासार्हतेची मूल्येही मूळ अहवालाशी तपासा.
These values enter your soil record only after you confirm.|आपकी पुष्टि के बाद ही ये मान मृदा रिकॉर्ड में जुड़ेंगे।|तुमच्या पुष्टीनंतरच ही मूल्ये मातीच्या नोंदीत जोडली जातील.
Nitrogen (N)|नाइट्रोजन (N)|नत्र (N)
Phosphorus|फॉस्फोरस|स्फुरद
Potassium|पोटैशियम|पालाश
Soil pH|मृदा pH|मातीचा pH
Organic carbon|जैविक कार्बन|सेंद्रिय कर्ब
Electrical conductivity|विद्युत चालकता|विद्युत वाहकता
(optional)|(वैकल्पिक)|(ऐच्छिक)
Not detected · enter from report|नहीं मिला · रिपोर्ट से भरें|आढळले नाही · अहवालातून भरा
Needs review|जाँच आवश्यक|तपासणी आवश्यक
High confidence|उच्च विश्वसनीयता|उच्च विश्वासार्हता
Enter the value on your report|रिपोर्ट का मान भरें|अहवालातील मूल्य भरा
Phosphorus basis on report *|रिपोर्ट में फॉस्फोरस का रूप *|अहवालातील स्फुरदाचे स्वरूप *
Potassium basis on report *|रिपोर्ट में पोटैशियम का रूप *|अहवालातील पालाशाचे स्वरूप *
Check report and select|रिपोर्ट देखकर चुनें|अहवाल तपासून निवडा
Elemental P (kg/ha)|तत्वीय P (kg/ha)|मूलद्रव्य P (kg/ha)
Elemental K (kg/ha)|तत्वीय K (kg/ha)|मूलद्रव्य K (kg/ha)
Use kg/ha as printed on the report. If it uses ppm, mg/kg or another unit, ask the laboratory for kg/ha values. Do not copy those numbers directly. Oxide values are converted by Kisan Saathi after confirmation.|रिपोर्ट में दिए kg/ha मान ही भरें। ppm, mg/kg या अन्य इकाई हो तो प्रयोगशाला से kg/ha मान माँगें। उन्हें सीधे न भरें। पुष्टि के बाद ऑक्साइड मान बदले जाते हैं।|अहवालातील kg/ha मूल्येच भरा. ppm, mg/kg किंवा दुसरे एकक असल्यास प्रयोगशाळेकडून kg/ha मूल्ये मागा. ती थेट भरू नका. पुष्टीनंतर ऑक्साइड मूल्यांचे रूपांतर होते.
Soil sample / test date on report *|रिपोर्ट में नमूने / परीक्षण की तारीख *|अहवालातील नमुन्याची / चाचणीची तारीख *
Use the actual sample or test date, which may differ from the upload date.|वास्तविक नमूने या परीक्षण की तारीख भरें; यह अपलोड की तारीख से अलग हो सकती है।|नमुन्याची किंवा चाचणीची खरी तारीख भरा; ती अपलोडच्या तारखेपेक्षा वेगळी असू शकते.
Review summary|जाँच का सारांश|तपासणीचा सारांश
No numeric values changed since extraction.|निकाले गए संख्यात्मक मान बदले नहीं गए।|काढलेली संख्यात्मक मूल्ये बदललेली नाहीत.
Confirming records these values for|पुष्टि करने पर ये मान दर्ज होंगे:|पुष्टी केल्यावर ही मूल्ये नोंदवली जातील:
Sample/test date:|नमूना/परीक्षण तारीख:|नमुना/चाचणी तारीख:
· P basis:|· P का रूप:|· P चे स्वरूप:
· K basis:|· K का रूप:|· K चे स्वरूप:
I have verified these values|मैंने इन मानों की जाँच की है|मी ही मूल्ये तपासली आहेत
I checked every value, the kg/ha units, nutrient basis and sample/test date against my report.|मैंने हर मान, kg/ha इकाई, पोषक तत्व का रूप और तारीख अपनी रिपोर्ट से जाँची है।|मी प्रत्येक मूल्य, kg/ha एकक, पोषक घटकाचे स्वरूप आणि तारीख माझ्या अहवालाशी तपासली आहे.
Refreshing field…|खेत ताज़ा हो रहा है…|शेत अद्ययावत होत आहे…
Saving verified values…|पुष्ट मान सहेजे जा रहे हैं…|पुष्टी केलेली मूल्ये जतन होत आहेत…
Retry field refresh|खेत फिर ताज़ा करें|शेत पुन्हा अद्ययावत करा
Confirm and update field|पुष्टि करके खेत अपडेट करें|पुष्टी करून शेत अद्ययावत करा
Verified soil data saved|पुष्ट मृदा डेटा सहेजा गया|पुष्टी केलेला मातीचा डेटा जतन झाला
View dashboard|डैशबोर्ड देखें|डॅशबोर्ड पाहा
Fertilizer scenario report|उर्वरक परिदृश्य रिपोर्ट|खत परिस्थिती तुलना अहवाल
See how changing your saved fertilizer mix affects nutrient supply and product cost. This comparison does not record an application.|सहेजे उर्वरक मिश्रण को बदलने से पोषक आपूर्ति और लागत कैसे बदलती है, देखें। यह तुलना उर्वरक उपयोग दर्ज नहीं करती।|जतन केलेले खत मिश्रण बदलल्यावर पोषक पुरवठा व खर्च कसा बदलतो ते पाहा. ही तुलना खत वापराची नोंद करत नाही.
View field data and Proof Trace|खेत का डेटा और प्रमाण देखें|शेताचा डेटा आणि पुरावे पाहा
1. Confirm soil and crop|1. मृदा और फसल की पुष्टि करें|1. माती व पिकाची पुष्टी करा
2. Generate a baseline plan|2. आधार योजना बनाएँ|2. आधार योजना तयार करा
3. Compare nutrients and cost|3. पोषक तत्व और लागत की तुलना करें|3. पोषक घटक व खर्चाची तुलना करा
Change all fertilizer quantities (%)|सभी उर्वरकों की मात्रा में बदलाव (%)|सर्व खतांच्या प्रमाणातील बदल (%)
Hypothetical seven-day rain (mm)|काल्पनिक सात दिनों की वर्षा (mm)|काल्पनिक सात दिवसांचा पाऊस (mm)
Use saved weather context|सहेजे मौसम का उपयोग करें|जतन केलेले हवामान वापरा
Compare scenario|परिदृश्य की तुलना करें|परिस्थितीची तुलना करा
Reset to baseline|आधार योजना पर लौटें|आधार योजनेवर परत या
For example, -20% compares 80% of each baseline product. Rainfall changes the precaution checks, not the nutrient quantities or a yield forecast.|उदाहरण: -20% हर आधार उत्पाद की 80% मात्रा की तुलना करता है। वर्षा सावधानी जाँच बदलती है, पोषक मात्रा या उपज का पूर्वानुमान नहीं।|उदाहरण: -20% प्रत्येक आधार उत्पादनाच्या 80% प्रमाणाची तुलना करते. पावसामुळे खबरदारी तपासणी बदलते; पोषक प्रमाण किंवा उत्पादन अंदाज बदलत नाही.
Preparing the comparison...|तुलना तैयार हो रही है…|तुलना तयार होत आहे…
A current baseline is needed|वर्तमान आधार योजना आवश्यक है|सध्याची आधार योजना आवश्यक आहे
Generate baseline and compare|आधार योजना बनाएँ और तुलना करें|आधार योजना तयार करून तुलना करा
This saves a new recommendation from your current field data, then reruns the comparison. It does not record fertilizer application.|यह वर्तमान खेत डेटा से नई सिफारिश सहेजकर तुलना करता है। इससे उर्वरक उपयोग दर्ज नहीं होता।|हे सध्याच्या शेत डेटावरून नवीन शिफारस जतन करून तुलना करते. यात खत वापराची नोंद होत नाही.
Inputs changed. Select Compare scenario to update the report.|जानकारी बदली है। रिपोर्ट अपडेट करने के लिए तुलना करें।|माहिती बदलली आहे. अहवाल अद्ययावत करण्यासाठी तुलना करा.
Does the mix cover the remaining nutrient need?|क्या मिश्रण बची हुई पोषक जरूरत पूरी करता है?|मिश्रण उरलेली पोषक गरज पूर्ण करते का?
Remaining need is the crop requirement after soil nutrients and supported application credits. All amounts are kg/ha, on the same N / P2O5 / K2O basis.|मृदा पोषक तत्व और समर्थित पूर्व उपयोग घटाने के बाद बची फसल की जरूरत दिखाई गई है। सभी मात्राएँ समान N / P2O5 / K2O आधार पर kg/ha में हैं।|मातीतील पोषक घटक व समर्थित आधीचा वापर वजा केल्यानंतरची पिकाची गरज दाखवली आहे. सर्व प्रमाण समान N / P2O5 / K2O आधारावर kg/ha मध्ये आहे.
Remaining need|बची हुई जरूरत|उरलेली गरज
Baseline supplies|आधार योजना की आपूर्ति|आधार योजनेचा पुरवठा
Scenario supplies|परिदृश्य की आपूर्ति|परिस्थितीतील पुरवठा
Scenario excess:|परिदृश्य में अधिकता:|परिस्थितीतील अधिकता:
Scenario shortfall:|परिदृश्य में कमी:|परिस्थितीतील कमतरता:
Each nutrient uses its own scale. Values are calculated nutrient supply, not a prediction of plant uptake or yield.|हर पोषक तत्व का पैमाना अलग है। मान गणना की गई आपूर्ति हैं, पौधों के अवशोषण या उपज का पूर्वानुमान नहीं।|प्रत्येक पोषक घटकाचे प्रमाणपट वेगळे आहे. मूल्ये गणिती पुरवठ्याची आहेत; शोषण किंवा उत्पादनाचा अंदाज नाही.
Calculated comparison /|गणना पर आधारित तुलना /|गणनेवर आधारित तुलना /
What changes in this scenario?|इस परिदृश्य में क्या बदलता है?|या परिस्थितीत काय बदलते?
A complete price is unavailable for this mix.|इस मिश्रण की पूरी कीमत उपलब्ध नहीं है।|या मिश्रणाची पूर्ण किंमत उपलब्ध नाही.
The product cost is unchanged from the baseline.|उत्पाद लागत आधार योजना जितनी ही है।|उत्पादन खर्च आधार योजनेइतकाच आहे.
A lower cost alone does not make the mix agronomically suitable. Check the nutrient shortfalls and constraints below.|केवल कम लागत से मिश्रण कृषि की दृष्टि से उचित नहीं हो जाता। नीचे पोषक कमी और सीमाएँ जाँचें।|केवळ कमी खर्चामुळे मिश्रण कृषीदृष्ट्या योग्य ठरत नाही. खालील पोषक कमतरता आणि मर्यादा तपासा.
Baseline product cost|आधार योजना की उत्पाद लागत|आधार योजनेचा उत्पादन खर्च
Scenario product cost|परिदृश्य की उत्पाद लागत|परिस्थितीतील उत्पादन खर्च
Cost difference|लागत में अंतर|खर्चातील फरक
Not priced|कीमत उपलब्ध नहीं|किंमत उपलब्ध नाही
Product-by-product comparison|उत्पादवार तुलना|उत्पादननिहाय तुलना
Product|उत्पाद|उत्पादन
Baseline|आधार योजना|आधार योजना
Scenario|परिदृश्य|परिस्थिती
Change|बदलाव|बदल
All quantities in kg/ha. A zero mix means no fertilizer in this hypothetical comparison, not a recommendation to stop fertilizing.|सभी मात्राएँ kg/ha में हैं। शून्य मिश्रण केवल इस काल्पनिक तुलना में कोई उर्वरक नहीं दर्शाता; उर्वरक रोकने की सलाह नहीं है।|सर्व प्रमाण kg/ha मध्ये आहे. शून्य मिश्रण फक्त या काल्पनिक तुलनेत खत नसल्याचे दर्शवते; खत थांबवण्याची शिफारस नाही.
Constraints and rainfall precautions|सीमाएँ और वर्षा संबंधी सावधानियाँ|मर्यादा आणि पावसाबाबत खबरदारी
No blocking constraint detected by the configured checks.|निर्धारित जाँचों में कोई रोक लगाने वाली सीमा नहीं मिली।|निर्धारित तपासण्यांत कोणतीही प्रतिबंधक मर्यादा आढळली नाही.
This scenario fails a constraint check. Do not treat it as an application recommendation.|यह परिदृश्य सीमा जाँच में असफल है। इसे उर्वरक उपयोग की सिफारिश न मानें।|ही परिस्थिती मर्यादा तपासणीत अयशस्वी आहे. याला खत वापरण्याची शिफारस मानू नका.
Baseline timing:|आधार योजना का समय:|आधार योजनेची वेळ:
Scenario seven-day rain:|परिदृश्य की सात दिन की वर्षा:|परिस्थितीतील सात दिवसांचा पाऊस:
Sources, confidence and limits of this report|इस रिपोर्ट के स्रोत, विश्वसनीयता और सीमाएँ|या अहवालाचे स्रोत, विश्वासार्हता व मर्यादा
Saved recommendation confidence:|सहेजी सिफारिश की विश्वसनीयता:|जतन केलेल्या शिफारशीची विश्वासार्हता:
. Scenario confidence is not assessed: scaling quantities does not transfer the baseline confidence to this new mix.|. परिदृश्य की विश्वसनीयता नहीं आँकी गई: मात्रा बदलने से आधार योजना की विश्वसनीयता नए मिश्रण पर लागू नहीं होती।|. परिस्थितीची विश्वासार्हता तपासलेली नाही: प्रमाण बदलल्याने आधार योजनेची विश्वासार्हता नवीन मिश्रणाला लागू होत नाही.
Formula: sum of product quantity (kg/ha) multiplied by its price (INR/kg). Both sides use the same price table; labour and transport are excluded.|सूत्र: हर उत्पाद की मात्रा (kg/ha) × कीमत (INR/kg) का योग। दोनों ओर एक ही कीमत सूची है; मजदूरी और परिवहन शामिल नहीं हैं।|सूत्र: प्रत्येक उत्पादनाचे प्रमाण (kg/ha) × किंमत (INR/kg) यांची बेरीज. दोन्ही बाजूंना समान किंमत सूची आहे; मजुरी व वाहतूक समाविष्ट नाही.
Yield effect is not calculated.|उपज पर प्रभाव की गणना नहीं की गई है।|उत्पादनावरील परिणाम मोजलेला नाही.
Seasonal savings versus farmer practice cannot be calculated because the 47-farmer survey does not establish the quantity basis or season.|47 किसानों के सर्वेक्षण में मात्रा का आधार या मौसम स्पष्ट नहीं है, इसलिए मौसमी बचत नहीं निकाली जा सकती।|47 शेतकऱ्यांच्या सर्वेक्षणात प्रमाणाचा आधार किंवा हंगाम स्पष्ट नाही, म्हणून हंगामी बचत मोजता येत नाही.
Previous fertilizer applications|पहले किए गए उर्वरक उपयोग|आधी केलेले खताचे वापर
Record what was actually applied. Recommendations are not proof of application. Missing history does not mean no fertilizer was used.|वास्तव में दिया गया उर्वरक दर्ज करें। सिफारिश उपयोग का प्रमाण नहीं है। इतिहास न होने का अर्थ उर्वरक न देना नहीं है।|प्रत्यक्ष दिलेल्या खताची नोंद करा. शिफारस हा वापराचा पुरावा नाही. इतिहास नसणे म्हणजे खत दिले नाही असे नाही.
Loading application history...|उर्वरक उपयोग का इतिहास लोड हो रहा है…|खत वापराचा इतिहास लोड होत आहे…
No applications recorded for this field.|इस खेत में उर्वरक उपयोग दर्ज नहीं है।|या शेतासाठी खत वापराची नोंद नाही.
Select product|उत्पाद चुनें|उत्पादन निवडा
Application date|उपयोग की तारीख|वापराची तारीख
Quantity (kg/ha)|मात्रा (kg/ha)|प्रमाण (kg/ha)
Saving...|सहेजा जा रहा है…|जतन होत आहे…
Record application|उर्वरक उपयोग दर्ज करें|खत वापर नोंदवा
Kisan Saathi · Evidence-based recommendation|किसान साथी · प्रमाण आधारित सिफारिश|किसान साथी · पुराव्यावर आधारित शिफारस
Generate new recommendation|नई सिफारिश बनाएँ|नवीन शिफारस तयार करा
Generating recommendation…|सिफारिश तैयार हो रही है…|शिफारस तयार होत आहे…
Checking field data, nutrient gaps, evidence and weather…|खेत डेटा, पोषक कमी, प्रमाण और मौसम जाँचे जा रहे हैं…|शेत डेटा, पोषक कमतरता, पुरावे आणि हवामान तपासत आहोत…
More information is needed before applying fertilizer|उर्वरक देने से पहले अधिक जानकारी चाहिए|खत देण्यापूर्वी अधिक माहिती आवश्यक आहे
Your first recommendation is ready to be generated|आपकी पहली सिफारिश बनाई जा सकती है|तुमची पहिली शिफारस तयार करता येईल
ABSTAIN · View proof|सिफारिश रोकी गई · प्रमाण देखें|शिफारस रोखली · पुरावे पाहा
What we need next|आगे क्या चाहिए|पुढे काय आवश्यक आहे
Review soil report and crop details|मृदा रिपोर्ट और फसल जानकारी जाँचें|मातीचा अहवाल व पिकाची माहिती तपासा
What should I apply?|मुझे क्या देना चाहिए?|मी काय द्यावे?
How much?|कितना?|किती?
When? · Application window|कब? · उपयोग का समय|कधी? · वापराची वेळ
Why this plan?|यह योजना क्यों?|ही योजना का?
Based on what?|किस आधार पर?|कशाच्या आधारावर?
How sure are we?|कितना विश्वास है?|किती विश्वास आहे?
View calculation →|गणना देखें →|गणना पाहा →
Inspect the exact calculation|सटीक गणना देखें|अचूक गणना पाहा
Read source paragraphs|स्रोत के अनुच्छेद पढ़ें|स्रोत परिच्छेद वाचा
· View proof|· प्रमाण देखें|· पुरावे पाहा
Open the proof to inspect the recorded data-quality checks.|दर्ज डेटा गुणवत्ता जाँच देखने के लिए प्रमाण खोलें।|नोंदवलेल्या डेटा गुणवत्ता तपासण्या पाहण्यासाठी पुरावे उघडा.
Estimated plan cost|योजना की अनुमानित लागत|योजनेचा अंदाजित खर्च
per hectare|प्रति हेक्टेयर|प्रति हेक्टर
Compare in simulator →|सिम्युलेटर में तुलना करें →|सिम्युलेटरमध्ये तुलना करा →
Proof Trace|प्रमाण विवरण|पुराव्यांचा तपशील
· Evidence saved with this recommendation|· इस सिफारिश के साथ सहेजे प्रमाण|· या शिफारशीसोबत जतन केलेले पुरावे
Close Proof Trace|प्रमाण विवरण बंद करें|पुराव्यांचा तपशील बंद करा
No saved proof is available yet.|अभी सहेजा हुआ प्रमाण उपलब्ध नहीं है।|अद्याप जतन केलेला पुरावा उपलब्ध नाही.
Confirm your field and soil details, then generate a new recommendation to create its audit trail.|खेत और मृदा जानकारी की पुष्टि करके नई सिफारिश बनाएँ ताकि उसका प्रमाण विवरण बने।|शेत व मातीच्या माहितीची पुष्टी करून नवीन शिफारस तयार करा म्हणजे तिचे पुरावे नोंदवले जातील.
1. Exact soil-gap calculation|1. मृदा पोषक कमी की सटीक गणना|1. मातीतील पोषक कमतरतेची अचूक गणना
Nutrient|पोषक तत्व|पोषक घटक
Required|आवश्यक|आवश्यक
Soil|मृदा|माती
Credit|पूर्व उपयोग का श्रेय|पूर्व वापराचे श्रेय
Gap|कमी|कमतरता
Reported measurements:|रिपोर्ट के माप:|अहवालातील मोजमाप:
Conversion source:|रूपांतरण स्रोत:|रूपांतराचा स्रोत:
Prior fertilizer applications|पिछले उर्वरक उपयोग|आधीचे खत वापर
2. RDF citation and retrieved evidence|2. RDF संदर्भ और प्राप्त प्रमाण|2. RDF संदर्भ आणि मिळालेले पुरावे
3. Weather window reasoning|3. मौसम के अनुसार समय का आधार|3. हवामानानुसार वेळेचे कारण
Forecast rain over 7 days:|7 दिन की अनुमानित वर्षा:|7 दिवसांचा पावसाचा अंदाज:
Source:|स्रोत:|स्रोत:
· Status:|· स्थिति:|· स्थिती:
4. Confidence breakdown|4. विश्वसनीयता का विवरण|4. विश्वासार्हतेचा तपशील
Recorded confidence:|दर्ज विश्वसनीयता:|नोंदवलेली विश्वासार्हता:
This is a rule-based evidence and data-quality rating, not a probability of yield or a guarantee.|यह नियम आधारित प्रमाण और डेटा गुणवत्ता का आकलन है, उपज की संभावना या गारंटी नहीं।|हे नियमांवर आधारित पुरावे व डेटा गुणवत्तेचे मूल्यांकन आहे; उत्पादनाची शक्यता किंवा हमी नाही.
Recorded / passed|दर्ज / सफल|नोंदवले / उत्तीर्ण
Missing / needs review|अनुपलब्ध / जाँच आवश्यक|गहाळ / तपासणी आवश्यक
No confidence flags were saved.|विश्वसनीयता संबंधी संकेत सहेजे नहीं गए।|विश्वासार्हतेचे संकेत जतन केलेले नाहीत.
5. Source documents and field records|5. स्रोत दस्तावेज और खेत रिकॉर्ड|5. स्रोत दस्तऐवज आणि शेताच्या नोंदी
No source documents were recorded.|स्रोत दस्तावेज दर्ज नहीं हैं।|स्रोत दस्तऐवज नोंदवलेले नाहीत.
Selected-language voice is unavailable on this device.|इस उपकरण पर चुनी गई भाषा की आवाज़ उपलब्ध नहीं है।|या उपकरणावर निवडलेल्या भाषेचा आवाज उपलब्ध नाही.
No recommendation is available yet.|अभी कोई सिफारिश उपलब्ध नहीं है।|अद्याप शिफारस उपलब्ध नाही.
Check the crop and growth stage recorded for this field.|इस खेत की फसल और वृद्धि अवस्था जाँचें।|या शेताचे पीक आणि वाढीचा टप्पा तपासा.
Review your confirmed soil measurements and previous fertilizer applications.|पुष्ट मृदा माप और पहले दिए उर्वरकों की जाँच करें।|पुष्टी केलेले मातीचे मोजमाप आणि आधी दिलेली खते तपासा.
Generate a recommendation to check the evidence and application timing.|प्रमाण और उपयोग का समय जाँचने के लिए सिफारिश बनाएँ।|पुरावे व वापराची वेळ तपासण्यासाठी शिफारस तयार करा.
Review the reason above and correct any missing or uncertain field data.|ऊपर का कारण देखें और अधूरा या अनिश्चित खेत डेटा सुधारें।|वरील कारण पाहून अपूर्ण किंवा अनिश्चित शेत डेटा दुरुस्त करा.
Confirm soil measurements and the current crop stage before generating again.|फिर बनाने से पहले मृदा माप और वर्तमान फसल अवस्था की पुष्टि करें।|पुन्हा तयार करण्यापूर्वी मातीचे मोजमाप व सध्याच्या पीक टप्प्याची पुष्टी करा.
No application window recommended for this hypothetical mix.|इस काल्पनिक मिश्रण के लिए उपयोग का समय सुझाया नहीं गया है।|या काल्पनिक मिश्रणासाठी वापराची वेळ सुचवलेली नाही.
Field inputs changed since the saved plan. Generate a new recommendation.|सहेजी योजना के बाद खेत की जानकारी बदली है। नई सिफारिश बनाएँ।|जतन केलेल्या योजनेनंतर शेताची माहिती बदलली आहे. नवीन शिफारस तयार करा.
Confirm this field's soil report and crop stage.|इस खेत की मृदा रिपोर्ट और फसल अवस्था की पुष्टि करें।|या शेताच्या मातीच्या अहवालाची व पीक टप्प्याची पुष्टी करा.
Generate a new recommendation on the field dashboard, then return here.|खेत के डैशबोर्ड पर नई सिफारिश बनाएँ, फिर यहाँ लौटें।|शेताच्या डॅशबोर्डवर नवीन शिफारस तयार करा, मग येथे परत या.
Record previous fertilizer applications or review any incomplete application history.|पिछले उर्वरक उपयोग दर्ज करें या अधूरा इतिहास जाँचें।|आधीचे खत वापर नोंदवा किंवा अपूर्ण इतिहास तपासा.
Urea|यूरिया|युरिया
UREA|यूरिया|युरिया
No fertilizer application required|उर्वरक देने की आवश्यकता नहीं|खत देण्याची आवश्यकता नाही
Timing not weather-validated. Obtain a current field forecast before applying.|समय की मौसम से पुष्टि नहीं हुई है। उर्वरक देने से पहले खेत का वर्तमान मौसम पूर्वानुमान लें।|वेळेची हवामानानुसार पुष्टी झालेली नाही. खत देण्यापूर्वी शेताचा सध्याचा हवामान अंदाज घ्या.
Defer application during heavy rain. Recheck a current local forecast before choosing a date.|भारी वर्षा में उर्वरक देना टालें। तारीख चुनने से पहले स्थानीय पूर्वानुमान फिर जाँचें।|मुसळधार पावसात खत देणे टाळा. तारीख निवडण्यापूर्वी स्थानिक अंदाज पुन्हा तपासा.
The seven-day rainfall total does not establish a dry application date. Check the local forecast and soil conditions.|सात दिन की कुल वर्षा से सूखा दिन तय नहीं होता। स्थानीय पूर्वानुमान और मृदा की स्थिति जाँचें।|सात दिवसांच्या एकूण पावसावरून कोरडा दिवस ठरत नाही. स्थानिक अंदाज आणि मातीची स्थिती तपासा.
Set up your farm|अपना खेत दर्ज करें|तुमचे शेत नोंदवा
Start with your field|अपने खेत से शुरू करें|तुमच्या शेतापासून सुरुवात करा
Add your crop and farm details|फसल और खेत की जानकारी भरें|पीक व शेताची माहिती भरा
Your soil data|आपका मृदा डेटा|तुमचा मातीचा डेटा
Upload & review|अपलोड करें और जाँचें|अपलोड करा व तपासा
You confirm first|पहले आप पुष्टि करें|आधी तुम्ही पुष्टी करा
Recommendations follow your confirmed soil data.|सिफारिशें आपके पुष्ट मृदा डेटा पर आधारित हैं।|शिफारशी तुमच्या पुष्टी केलेल्या माती डेटावर आधारित आहेत.
Sustainable Fertilizer Support|टिकाऊ उर्वरक सहायता|शाश्वत खत सहाय्य
Field overview|खेत का अवलोकन|शेताचा आढावा
Weather agent|मौसम सेवा|हवामान सेवा
Rain (7d)|वर्षा (7 दिन)|पाऊस (7 दिवस)
No stage sequence available for this crop.|इस फसल की अवस्थाओं का क्रम उपलब्ध नहीं है।|या पिकासाठी टप्प्यांचा क्रम उपलब्ध नाही.
Agronomist Override|कृषि विशेषज्ञ द्वारा बदलाव|कृषितज्ज्ञाकडून बदल
Reason for override (required)|बदलाव का कारण (आवश्यक)|बदलाचे कारण (आवश्यक)
Submitting…|भेजा जा रहा है…|सादर होत आहे…
Submit Override|बदलाव दर्ज करें|बदल नोंदवा
Recommendation History & Oversight|सिफारिश इतिहास और समीक्षा|शिफारशींचा इतिहास व देखरेख
Override latest plan|नवीनतम योजना बदलें|नवीनतम योजना बदला
Loading history…|इतिहास लोड हो रहा है…|इतिहास लोड होत आहे…
No recommendations generated yet for this field.|इस खेत के लिए अभी सिफारिश नहीं बनी है।|या शेतासाठी अद्याप शिफारस तयार केलेली नाही.
Manually overridden by an agronomist|कृषि विशेषज्ञ ने स्वयं बदला|कृषितज्ज्ञाने स्वतः बदल केला
Show less|कम दिखाएँ|कमी दाखवा
Fleet overview — all registered fields|सभी दर्ज खेतों का अवलोकन|सर्व नोंदवलेल्या शेतांचा आढावा
Total fields|कुल खेत|एकूण शेते
Needs attention|ध्यान आवश्यक|लक्ष देणे आवश्यक
Active alerts|सक्रिय चेतावनियाँ|सक्रिय सूचना
Refresh fleet|खेत सूची ताज़ा करें|शेत यादी अद्ययावत करा
Loading fleet…|खेत सूची लोड हो रही है…|शेत यादी लोड होत आहे…
No fields registered yet.|अभी कोई खेत दर्ज नहीं है।|अद्याप कोणतेही शेत नोंदवलेले नाही.
Alert|चेतावनी|सूचना
Open →|खोलें →|उघडा →
Unreachable|संपर्क नहीं|संपर्क होत नाही
No soil test|मृदा परीक्षण नहीं|मातीची चाचणी नाही
Abstained|सिफारिश रोकी गई|शिफारस रोखली
No plan yet|अभी योजना नहीं|अद्याप योजना नाही
Plan active|योजना सक्रिय|योजना सक्रिय
Fleet-wide alerts & events|सभी खेतों की चेतावनियाँ और घटनाएँ|सर्व शेतांच्या सूचना व घटना
Loading alerts…|चेतावनियाँ लोड हो रही हैं…|सूचना लोड होत आहेत…
Resolved|समाधान हुआ|निराकरण झाले
ALL|सभी|सर्व
No|कोई नहीं|नाही
alerts recorded across any field yet.|अभी किसी खेत की चेतावनी दर्ज नहीं है।|अद्याप कोणत्याही शेताची सूचना नोंदवलेली नाही.
Pilot demo — sample data|पायलट डेमो — नमूना डेटा|पायलट नमुना — नमुना डेटा
These preloaded records demonstrate the app. They are not your farm or your uploaded soil results. This view is read-only.|ये पहले से दर्ज रिकॉर्ड ऐप का प्रदर्शन करते हैं। ये आपका खेत या आपकी रिपोर्ट नहीं हैं। यहाँ केवल देखा जा सकता है।|या आधीच्या नोंदी ॲपचे प्रात्यक्षिक आहेत. हे तुमचे शेत किंवा तुमचा अहवाल नाही. येथे फक्त पाहता येते.
Set up my own field|अपना खेत दर्ज करें|माझे शेत नोंदवा
Loading pilot examples...|पायलट नमूने लोड हो रहे हैं…|पायलट नमुने लोड होत आहेत…
No pilot examples available.|पायलट नमूने उपलब्ध नहीं।|पायलट नमुने उपलब्ध नाहीत.
Sample record|नमूना रिकॉर्ड|नमुना नोंद
Sample soil score:|नमूना मृदा स्कोर:|नमुना मातीचे गुण:
Data sources|डेटा स्रोत|डेटा स्रोत
Important|महत्वपूर्ण|महत्त्वाचे
Accessibility statement|सुलभता विवरण|सुलभतेचे निवेदन
Report an issue|समस्या बताएँ|समस्या कळवा
Helpline:|हेल्पलाइन:|मदत क्रमांक:
(Kisan Call Centre)|(किसान कॉल सेंटर)|(किसान कॉल सेंटर)
Last updated:|अंतिम अपडेट:|शेवटचे अद्यतन:
`.trim().split('\n').map(row => { const [en, hi, mr] = row.split('|'); return [en, [hi, mr]]; }));
