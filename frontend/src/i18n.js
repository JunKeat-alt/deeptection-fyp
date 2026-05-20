/**
 * Centralised translation dictionary + helpers for Deeptection.
 *
 *  - English ("en")  is the source of truth; every key MUST exist here.
 *  - Tamil   ("ta")  and Arabic ("ar") may omit keys; the `translate()`
 *    helper will fall back to English for anything missing.
 *  - Arabic is RTL; the `dir` property on LOCALE_META drives
 *    <html dir="..."> via I18nContext.
 *
 * Key namespaces
 *   nav.*            — navigation labels
 *   home.*           — landing page
 *   upload.*         — upload / analyze page
 *   loading.*        — loading screen
 *   result.*         — result card
 *   result.simple.*  — one-line verdict sentences (server returns these keys)
 *   reason.*         — detailed explanation reasons (server returns these keys)
 *   history.*        — history page
 *   about.*          — about page
 *   model.*          — model-source selector
 *   err.*            — error messages
 */

export const LOCALES = ["en", "ta", "ar"];

export const LOCALE_META = {
  en: { label: "English",  nativeLabel: "English",  dir: "ltr" },
  ta: { label: "Tamil",    nativeLabel: "தமிழ்",    dir: "ltr" },
  ar: { label: "Arabic",   nativeLabel: "العربية",   dir: "rtl" },
};

const dict = {
  /* ======================================================================= */
  /*                               ENGLISH                                   */
  /* ======================================================================= */
  en: {
    // ---- Nav ----
    "nav.home":    "Home",
    "nav.analyze": "Check a file",
    "nav.history": "History",
    "nav.about":   "About",

    // ---- Home ----
    "home.tagline":
      "A calm, trustworthy check for deepfake voice & video messages.",
    "home.title": "Is this really them?",
    "home.sub":
      "Deeptection analyses the voice and face in a suspicious message and tells you, in plain language, whether it is likely to be real, fake, or uncertain.",
    "home.cta":  "Check a file",
    "home.cta2": "How it works",
    "home.features.title": "Made for families, not engineers.",
    "home.f1.title": "Upload any voice or video",
    "home.f1.body":
      "MP4, MOV, AVI for video. WAV, MP3, M4A for audio. One file at a time.",
    "home.f2.title": "Two AI models, one clear answer",
    "home.f2.body":
      "The video model checks the face. The audio model checks the voice. We combine both into a single, easy-to-read verdict.",
    "home.f3.title": "Built to explain, not just to judge",
    "home.f3.body":
      "Every answer shows why — which signals were suspicious, or reassuring — so you can decide with confidence.",
    "home.edu.title": "Why this matters",
    "home.edu.body":
      "AI-generated voice and video is now being used to impersonate family members in phishing scams. If you receive a worrying message asking for money, urgent help, or private details, run it through Deeptection before replying.",

    // ---- Upload / Analyze ----
    "upload.title": "Upload a suspicious file",
    "upload.sub":
      "Drop a video or voice note below. We will analyse it on our servers and delete the file afterwards.",
    "upload.drop":    "Drop your file here",
    "upload.or":      "or",
    "upload.browse":  "Browse files",
    "upload.supported":
      "Supported: MP4, MOV, AVI, WAV, MP3, M4A. Video up to {vmb} MB / {vsec} s. Audio up to {amb} MB.",
    "upload.analyze":        "Analyse this file",
    "upload.remove":         "Remove",
    "upload.invalid_format": "That file type isn't supported.",
    "upload.too_large":      "That file is over the allowed size.",
    "upload.wait":           "Please wait — analysing your file…",

    // ---- Loading ----
    "loading.title": "Analysing your file",
    "loading.sub":   "Running the audio and video checks. This usually takes 10–20 seconds.",
    "loading.s1":    "Reading your file",
    "loading.s2":    "Finding faces and voice",
    "loading.s3":    "Checking for deepfake signs",
    "loading.s4":    "Combining the results",

    // ---- Result ----
    "result.verdict.real":      "Looks real",
    "result.verdict.fake":      "Likely a deepfake",
    "result.verdict.uncertain": "UNCERTAIN",

    "result.simple.real":
      "This message looks genuine. We did not find clear signs of manipulation.",
    "result.simple.fake":
      "This message shows strong signs of manipulation and is likely a deepfake.",
    "result.simple.uncertain":
      "We could not make a confident decision. Please verify through another channel.",

    "result.final":          "Final risk",
    "result.confidence":     "Confidence",
    "result.video_score":    "Video score",
    "result.audio_score":    "Audio score",
    "result.show_more":      "Show more",
    "result.show_less":      "Show less",
    "result.why":            "Why we decided this",
    "result.used":           "What we analysed",
    "result.retry":          "Check another file",
    "result.save":           "Saved to history",
    "result.unavailable":    "not available",
    "result.risk_low":       "Low risk",
    "result.risk_med":       "Medium risk",
    "result.risk_high":      "High risk",
    "result.modality.video": "Video",
    "result.modality.audio": "Audio",
    "result.modality.system":"System",

    // ---- Explanation reasons (keys returned by backend) ----
    "reason.video.strong_artefacts":
      "Facial texture and edges look inconsistent with a real recording.",
    "reason.video.minor_artefacts":
      "Some frames showed minor blending or boundary artefacts around the face.",
    "reason.video.low_face_confidence":
      "Face was hard to detect in several frames, which lowers reliability.",
    "reason.video.too_blurry":
      "The video is blurry or low-resolution, which can hide or mimic deepfake traces.",
    "reason.video.few_frames":
      "Only a few usable frames were available for analysis.",
    "reason.video.natural":
      "Facial movement and texture looked natural across sampled frames.",
    "reason.video.unavailable":
      "No usable video was found in this file.",

    "reason.audio.strong_synthetic":
      "The voice shows spectral patterns typical of AI-generated speech.",
    "reason.audio.atypical":
      "Some acoustic features are atypical for natural human speech.",
    "reason.audio.too_quiet":
      "Audio is very quiet or mostly silent, which reduces detection reliability.",
    "reason.audio.too_short":
      "The audio clip is very short — longer samples give more accurate results.",
    "reason.audio.noisy":
      "Background noise or heavy compression may be masking voice cues.",
    "reason.audio.natural":
      "Spectral features are consistent with natural human speech.",
    "reason.audio.unavailable":
      "No usable audio was found in this file.",

    "reason.system.conflict":
      "The audio and video signals disagree, which is often a sign that only one of them has been manipulated.",
    "reason.system.generic":
      "No specific cues stood out; the overall signal drove the decision.",
    
    "reason.system.low_quality":
      "The file is too low-quality or unclear for reliable deepfake analysis. Please try a clearer recording.",
    
    "reason.video.uncertain_signal":
      "The video signal is not strongly clear, so the system relied more on audio.",

    // ---- History ----
    "history.title":         "Your recent checks",
    "history.empty":         "No checks yet. When you analyse a file, it will appear here.",
    "history.clear":         "Clear history",
    "history.confirm_clear": "Clear all history? This cannot be undone.",

    // ---- About ----
    "about.title": "About Deeptection",
    "about.p1":
      "Deeptection is a proof-of-concept deepfake verification tool designed especially for non-technical users — parents, guardians, and elderly individuals — who are increasingly targeted by AI-generated scam calls and messages.",
    "about.p2":
      "Upload a voice note or short video, and two specialised AI models will analyse it independently: one for the face, one for the voice. Their outputs are combined into a single verdict of Real, Fake, or Uncertain, along with a short plain-language explanation.",
    "about.p3":
      "This project was developed as part of a BSc (Hons) Computer Science (Cybersecurity) Final Year Project at Asia Pacific University of Technology & Innovation, aligned with SDG 16 — Peace, Justice and Strong Institutions.",
    "about.tech":
      "Built with PyTorch, Flask, and React. CPU-only. Files are never stored long-term.",

    // ---- Model selector ----
    "model.label":        "AI model",
    "model.local":        "Our trained model",
    "model.local.hint":   "Recommended — the model we built for this project.",
    "model.hf":           "HuggingFace baseline",
    "model.hf.hint":      "A public pretrained model for comparison.",

    // ---- Errors ----
    "err.network": "We could not reach the Deeptection server.",
    "err.generic": "Something went wrong. Please try again.",
  },

  /* ======================================================================= */
  /*                                TAMIL                                    */
  /* ======================================================================= */
  ta: {
    "nav.home":    "முகப்பு",
    "nav.analyze": "கோப்பை சரிபார்க்கவும்",
    "nav.history": "வரலாறு",
    "nav.about":   "பற்றி",

    "home.tagline":
      "டீப்ஃபேக் குரல் மற்றும் வீடியோ செய்திகளுக்கான அமைதியான, நம்பகமான சோதனை.",
    "home.title": "இது உண்மையில் அவர்கள்தானா?",
    "home.sub":
      "சந்தேகத்திற்குரிய செய்தியின் குரலையும் முகத்தையும் டீப்டெக்ஷன் ஆய்வு செய்து, அது உண்மையானதா, போலியானதா அல்லது நிச்சயமில்லாததா என்பதை எளிய மொழியில் சொல்கிறது.",
    "home.cta":  "கோப்பை சரிபார்க்கவும்",
    "home.cta2": "இது எப்படி வேலை செய்கிறது",
    "home.features.title": "பொறியாளர்களுக்காக அல்ல, குடும்பங்களுக்காக வடிவமைக்கப்பட்டது.",
    "home.f1.title": "எந்த குரல் அல்லது வீடியோவையும் பதிவேற்றவும்",
    "home.f1.body":
      "வீடியோவிற்கு MP4, MOV, AVI. ஆடியோவிற்கு WAV, MP3, M4A. ஒரு நேரத்தில் ஒரு கோப்பு.",
    "home.f2.title": "இரண்டு AI மாதிரிகள், ஒரு தெளிவான பதில்",
    "home.f2.body":
      "வீடியோ மாதிரி முகத்தை சரிபார்க்கிறது. ஆடியோ மாதிரி குரலை சரிபார்க்கிறது. இரண்டையும் இணைத்து ஒரே தெளிவான முடிவை தருகிறோம்.",
    "home.f3.title": "தீர்ப்பு மட்டுமல்ல, விளக்கமும்",
    "home.f3.body":
      "எந்த அறிகுறிகள் சந்தேகமாக அல்லது உறுதியளிக்கும் வகையில் இருந்தன என்பதை ஒவ்வொரு பதிலும் காட்டுகிறது.",
    "home.edu.title": "இது ஏன் முக்கியமானது",
    "home.edu.body":
      "AI உருவாக்கிய குரல் மற்றும் வீடியோ இப்போது ஃபிஷிங் மோசடிகளில் குடும்ப உறுப்பினர்களைப் போலி செய்ய பயன்படுத்தப்படுகிறது. பணம், அவசர உதவி அல்லது தனிப்பட்ட விவரங்கள் கேட்கும் செய்தி வந்தால், பதிலளிக்கும் முன் இங்கே சரிபாருங்கள்.",

    "upload.title": "சந்தேகத்திற்குரிய கோப்பை பதிவேற்றவும்",
    "upload.sub":
      "கீழே வீடியோ அல்லது குரல் செய்தியை விடுங்கள். எங்கள் சேவையகத்தில் ஆய்வு செய்து பின் கோப்பை நீக்கிவிடுவோம்.",
    "upload.drop":    "உங்கள் கோப்பை இங்கே விடுங்கள்",
    "upload.or":      "அல்லது",
    "upload.browse":  "கோப்புகளை தேர்வு செய்யவும்",
    "upload.supported":
      "ஏற்கக்கூடியவை: MP4, MOV, AVI, WAV, MP3, M4A. வீடியோ அதிகபட்சம் {vmb} MB / {vsec} வினாடி. ஆடியோ அதிகபட்சம் {amb} MB.",
    "upload.analyze":        "இந்தக் கோப்பை ஆய்வு செய்யவும்",
    "upload.remove":         "நீக்கு",
    "upload.invalid_format": "அந்த கோப்பு வகை ஆதரிக்கப்படவில்லை.",
    "upload.too_large":      "அந்த கோப்பு அனுமதிக்கப்பட்ட அளவை விட பெரியது.",
    "upload.wait":           "காத்திருக்கவும் — உங்கள் கோப்பை ஆய்வு செய்கிறோம்…",

    "loading.title": "உங்கள் கோப்பை ஆய்வு செய்கிறோம்",
    "loading.sub":   "ஆடியோ மற்றும் வீடியோ சோதனைகள் நடைபெறுகின்றன. பொதுவாக 10–20 வினாடிகள் ஆகும்.",
    "loading.s1":    "கோப்பை படிக்கிறோம்",
    "loading.s2":    "முகங்கள் மற்றும் குரலை கண்டுபிடிக்கிறோம்",
    "loading.s3":    "டீப்ஃபேக் அறிகுறிகளை சரிபார்க்கிறோம்",
    "loading.s4":    "முடிவுகளை இணைக்கிறோம்",

    "result.verdict.real":      "உண்மையானது போல் தெரிகிறது",
    "result.verdict.fake":      "பெரும்பாலும் டீப்ஃபேக்",
    "result.verdict.uncertain": "உறுதியாக தெரியவில்லை",

    "result.simple.real":
      "இந்த செய்தி உண்மையானது போல் தெரிகிறது. கையாளப்பட்டதற்கான தெளிவான அறிகுறிகள் எதுவும் காணப்படவில்லை.",
    "result.simple.fake":
      "இந்த செய்தி கையாளப்பட்டதற்கான வலுவான அறிகுறிகளைக் காட்டுகிறது — இது ஒரு டீப்ஃபேக்காக இருக்கலாம்.",
    "result.simple.uncertain":
      "எங்களால் உறுதியாக முடிவெடுக்க முடியவில்லை. தயவுசெய்து வேறு வழியில் சரிபாருங்கள்.",

    "result.final":          "இறுதி ஆபத்து",
    "result.confidence":     "நம்பகத்தன்மை",
    "result.video_score":    "வீடியோ மதிப்பெண்",
    "result.audio_score":    "ஆடியோ மதிப்பெண்",
    "result.show_more":      "மேலும் காட்டு",
    "result.show_less":      "குறைவாக காட்டு",
    "result.why":            "ஏன் இந்த முடிவு",
    "result.used":           "நாங்கள் என்ன ஆய்வு செய்தோம்",
    "result.retry":          "மற்றொரு கோப்பை சரிபார்",
    "result.save":           "வரலாற்றில் சேர்க்கப்பட்டது",
    "result.unavailable":    "கிடைக்கவில்லை",
    "result.risk_low":       "குறைந்த ஆபத்து",
    "result.risk_med":       "நடுத்தர ஆபத்து",
    "result.risk_high":      "அதிக ஆபத்து",
    "result.modality.video": "வீடியோ",
    "result.modality.audio": "ஆடியோ",
    "result.modality.system":"கணினி",

    "reason.video.strong_artefacts":
      "முகத்தின் அமைப்பும் விளிம்புகளும் உண்மையான பதிவுடன் பொருந்தவில்லை.",
    "reason.video.minor_artefacts":
      "சில பிரேம்களில் முகத்தைச் சுற்றி சிறு குறைபாடுகள் காணப்பட்டன.",
    "reason.video.low_face_confidence":
      "பல பிரேம்களில் முகத்தை கண்டறிவது கடினமாக இருந்தது, நம்பகத்தன்மை குறைந்தது.",
    "reason.video.too_blurry":
      "வீடியோ மங்கலாக அல்லது குறைந்த தெளிவுத்திறனுடன் உள்ளது, இது டீப்ஃபேக் அறிகுறிகளை மறைக்கலாம்.",
    "reason.video.few_frames":
      "ஆய்வுக்கு சில பிரேம்கள் மட்டுமே கிடைத்தன.",
    "reason.video.natural":
      "எடுக்கப்பட்ட பிரேம்களில் முகச்சலனமும் அமைப்பும் இயற்கையாகத் தோன்றின.",
    "reason.video.unavailable":
      "இந்தக் கோப்பில் பயன்படுத்தக்கூடிய வீடியோ இல்லை.",

    "reason.audio.strong_synthetic":
      "குரல் AI-உருவாக்கிய பேச்சுக்குரிய வரம்பொழுங்கை காட்டுகிறது.",
    "reason.audio.atypical":
      "சில ஒலியியல் அம்சங்கள் இயற்கையான மனித பேச்சுக்கு பொருந்தவில்லை.",
    "reason.audio.too_quiet":
      "ஒலி மிகவும் மெதுவாக உள்ளது அல்லது மௌனமாக உள்ளது, நம்பகத்தன்மை குறைகிறது.",
    "reason.audio.too_short":
      "ஒலி மிகவும் குறுகியது — நீளமான மாதிரிகள் துல்லியமாக இருக்கும்.",
    "reason.audio.noisy":
      "பின்னணி சத்தம் அல்லது அழுத்தம் குரல் அறிகுறிகளை மறைக்கலாம்.",
    "reason.audio.natural":
      "ஒலியியல் அம்சங்கள் இயற்கையான மனித பேச்சுக்கு ஒத்தவை.",
    "reason.audio.unavailable":
      "இந்தக் கோப்பில் பயன்படுத்தக்கூடிய ஆடியோ இல்லை.",

    "reason.system.conflict":
      "ஒலியும் வீடியோவும் வேறுபடுகின்றன — இது ஒரே ஒன்று மட்டும் கையாளப்பட்டதற்கான அறிகுறியாக இருக்கலாம்.",
    "reason.system.generic":
      "குறிப்பிட்ட அறிகுறிகள் எதுவும் தெளிவாக இல்லை; ஒட்டுமொத்த சமிக்ஞை முடிவை தீர்மானித்தது.",
    "reason.system.low_quality":
      "இந்தக் கோப்பின் தரம் நம்பகமான டீப்ஃபேக் பகுப்பாய்வுக்குப் போதுமானதாக இல்லை. தெளிவான பதிவை முயற்சிக்கவும்.",

    "history.title":         "சமீபத்திய சோதனைகள்",
    "history.empty":         "இன்னும் எதுவும் இல்லை. ஒரு கோப்பை ஆய்வு செய்த பிறகு அது இங்கே காட்டப்படும்.",
    "history.clear":         "வரலாற்றை அழி",
    "history.confirm_clear": "எல்லா வரலாற்றையும் அழிக்கவா? இதை மீட்டெடுக்க முடியாது.",

    "about.title": "டீப்டெக்ஷன் பற்றி",
    "about.p1":
      "டீப்டெக்ஷன் என்பது தொழில்நுட்பம் அல்லாத பயனர்களுக்காக — பெற்றோர்கள், பாதுகாவலர்கள் மற்றும் முதியோருக்காக — வடிவமைக்கப்பட்ட ஒரு டீப்ஃபேக் சரிபார்ப்பு கருவி.",
    "about.p2":
      "ஒரு குரல் செய்தி அல்லது சிறிய வீடியோவை பதிவேற்றுங்கள்; இரண்டு சிறப்பு AI மாதிரிகள் அதை தனித்தனியாக ஆய்வு செய்யும் — ஒன்று முகத்திற்கு, மற்றொன்று குரலுக்கு. அவற்றின் முடிவுகள் ஒரே தீர்ப்பாக இணைக்கப்படுகின்றன: உண்மை, போலி அல்லது உறுதியற்றது.",
    "about.p3":
      "இது APU இல் BSc (Hons) கணினி அறிவியல் (சைபர் பாதுகாப்பு) இறுதி ஆண்டு திட்டத்தின் ஒரு பகுதியாக உருவாக்கப்பட்டது, UN SDG 16 உடன் இணைக்கப்பட்டுள்ளது.",
    "about.tech":
      "PyTorch, Flask, React உடன் கட்டமைக்கப்பட்டது. CPU மட்டும். கோப்புகள் நீண்ட காலமாக சேமிக்கப்படுவதில்லை.",

    "model.label":      "AI மாதிரி",
    "model.local":      "எங்கள் பயிற்சி பெற்ற மாதிரி",
    "model.local.hint": "பரிந்துரைக்கப்படுகிறது — இந்தத் திட்டத்திற்காக கட்டமைக்கப்பட்டது.",
    "model.hf":         "HuggingFace அடிப்படை மாதிரி",
    "model.hf.hint":    "ஒப்பிடுவதற்கான பொது முன் பயிற்சி பெற்ற மாதிரி.",

    "err.network": "டீப்டெக்ஷன் சேவையகத்தை அடைய முடியவில்லை.",
    "err.generic": "ஏதோ தவறு ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்.",
  },

  /* ======================================================================= */
  /*                                ARABIC                                   */
  /* ======================================================================= */
  ar: {
    "nav.home":    "الرئيسية",
    "nav.analyze": "تحقق من ملف",
    "nav.history": "السجل",
    "nav.about":   "حول",

    "home.tagline":
      "تحقق هادئ وموثوق لرسائل الصوت والفيديو المزيفة بالذكاء الاصطناعي.",
    "home.title": "هل هذا حقاً هم؟",
    "home.sub":
      "يُحلل Deeptection الصوت والوجه في الرسالة المشبوهة ويخبرك بلغة واضحة ما إذا كانت حقيقية أم مزيفة أم غير مؤكدة.",
    "home.cta":  "تحقق من ملف",
    "home.cta2": "كيف يعمل",
    "home.features.title": "مُصَمَّم للعائلات، لا للمهندسين.",
    "home.f1.title": "ارفع أي صوت أو فيديو",
    "home.f1.body":
      "MP4 و MOV و AVI للفيديو. WAV و MP3 و M4A للصوت. ملف واحد في كل مرة.",
    "home.f2.title": "نموذجان للذكاء الاصطناعي، وإجابة واحدة واضحة",
    "home.f2.body":
      "نموذج الفيديو يفحص الوجه. نموذج الصوت يفحص الصوت. ندمج النتيجتين في حكم واحد سهل القراءة.",
    "home.f3.title": "يشرح قراره، لا يصدر حكماً فقط",
    "home.f3.body":
      "تُظهر كل إجابة الأسباب — الإشارات المشبوهة أو المطمئنة — لتقرر بثقة.",
    "home.edu.title": "لماذا هذا مهم",
    "home.edu.body":
      "يُستخدم الصوت والفيديو المولَّدان بالذكاء الاصطناعي اليوم لانتحال شخصيات أفراد العائلة في عمليات الاحتيال. إذا تلقيت رسالة مقلقة تطلب مالاً أو مساعدة عاجلة أو تفاصيل خاصة، افحصها هنا قبل الرد.",

    "upload.title": "ارفع الملف المشبوه",
    "upload.sub":
      "اسحب فيديو أو مقطعاً صوتياً هنا. سنحلله على خوادمنا ثم نحذف الملف.",
    "upload.drop":    "اسحب ملفك هنا",
    "upload.or":      "أو",
    "upload.browse":  "تصفح الملفات",
    "upload.supported":
      "المدعوم: MP4 و MOV و AVI و WAV و MP3 و M4A. الفيديو حتى {vmb} ميغابايت / {vsec} ثانية. الصوت حتى {amb} ميغابايت.",
    "upload.analyze":        "حلل هذا الملف",
    "upload.remove":         "إزالة",
    "upload.invalid_format": "نوع الملف غير مدعوم.",
    "upload.too_large":      "حجم الملف يتجاوز المسموح به.",
    "upload.wait":           "يرجى الانتظار — نحلل ملفك…",

    "loading.title": "نحلل ملفك",
    "loading.sub":   "نُشغِّل فحوصات الصوت والفيديو. عادةً يستغرق ذلك 10–20 ثانية.",
    "loading.s1":    "قراءة الملف",
    "loading.s2":    "اكتشاف الوجوه والصوت",
    "loading.s3":    "البحث عن علامات التزييف",
    "loading.s4":    "دمج النتائج",

    "result.verdict.real":      "يبدو حقيقياً",
    "result.verdict.fake":      "يُرجَّح أنه تزييف عميق",
    "result.verdict.uncertain": "غير مؤكد",

    "result.simple.real":
      "تبدو هذه الرسالة أصلية. لم نعثر على علامات واضحة للتلاعب.",
    "result.simple.fake":
      "تُظهر هذه الرسالة علامات قوية على التلاعب ومن المُرجَّح أنها تزييف عميق.",
    "result.simple.uncertain":
      "لم نتمكن من اتخاذ قرار واثق. يُرجى التحقق عبر وسيلة أخرى.",

    "result.final":          "مستوى الخطر النهائي",
    "result.confidence":     "الثقة",
    "result.video_score":    "درجة الفيديو",
    "result.audio_score":    "درجة الصوت",
    "result.show_more":      "عرض المزيد",
    "result.show_less":      "عرض أقل",
    "result.why":            "لماذا هذا القرار",
    "result.used":           "ما الذي حللناه",
    "result.retry":          "تحقق من ملف آخر",
    "result.save":           "تم الحفظ في السجل",
    "result.unavailable":    "غير متوفر",
    "result.risk_low":       "خطر منخفض",
    "result.risk_med":       "خطر متوسط",
    "result.risk_high":      "خطر مرتفع",
    "result.modality.video": "الفيديو",
    "result.modality.audio": "الصوت",
    "result.modality.system":"النظام",

    "reason.video.strong_artefacts":
      "يبدو نسيج الوجه وحوافه غير متسقَين مع تسجيل حقيقي.",
    "reason.video.minor_artefacts":
      "أظهرت بعض اللقطات آثار دمج طفيفة حول الوجه.",
    "reason.video.low_face_confidence":
      "كان اكتشاف الوجه صعباً في عدة لقطات، مما يقلل الموثوقية.",
    "reason.video.too_blurry":
      "الفيديو ضبابي أو منخفض الدقة، وقد يُخفي ذلك آثار التزييف.",
    "reason.video.few_frames":
      "توفرت لقطات قليلة فقط للتحليل.",
    "reason.video.natural":
      "بدت حركة الوجه والنسيج طبيعيتين عبر اللقطات.",
    "reason.video.unavailable":
      "لم يتم العثور على فيديو قابل للاستخدام في الملف.",

    "reason.audio.strong_synthetic":
      "يُظهر الصوت أنماطاً طيفية نمطية للكلام المولَّد بالذكاء الاصطناعي.",
    "reason.audio.atypical":
      "بعض الخصائص الصوتية غير نمطية للكلام البشري الطبيعي.",
    "reason.audio.too_quiet":
      "الصوت خافت جداً أو صامت في معظمه، مما يقلل الموثوقية.",
    "reason.audio.too_short":
      "المقطع الصوتي قصير جداً — العينات الأطول أكثر دقة.",
    "reason.audio.noisy":
      "قد تحجب ضوضاء الخلفية أو الضغط إشارات الصوت.",
    "reason.audio.natural":
      "الخصائص الصوتية متسقة مع الكلام البشري الطبيعي.",
    "reason.audio.unavailable":
      "لم يتم العثور على صوت قابل للاستخدام في الملف.",

    "reason.system.conflict":
      "يتعارض الصوت والفيديو، وكثيراً ما يشير ذلك إلى أن أحدهما فقط تم التلاعب به.",
    "reason.system.generic":
      "لم تبرز مؤشرات محددة؛ اعتمد القرار على الإشارة الإجمالية.",
    "reason.system.low_quality":
      "جودة الملف منخفضة جداً بحيث لا يمكن إجراء تحليل موثوق للتزييف العميق. يُرجى تجربة تسجيل أوضح.",
      
    "history.title":         "عمليات الفحص الأخيرة",
    "history.empty":         "لا توجد عمليات فحص بعد. ستظهر هنا بعد تحليل أول ملف.",
    "history.clear":         "مسح السجل",
    "history.confirm_clear": "مسح كل السجل؟ لا يمكن التراجع عن هذا.",

    "about.title": "حول Deeptection",
    "about.p1":
      "Deeptection أداة مرجعية للتحقق من التزييف العميق، مصممة خصيصاً للمستخدمين غير التقنيين — الآباء والأمهات، والأوصياء، وكبار السن — الذين يتعرضون بشكل متزايد لعمليات احتيال تعتمد على الصوت والفيديو المولَّدين بالذكاء الاصطناعي.",
    "about.p2":
      "ارفع مقطعاً صوتياً أو فيديو قصيراً، وسيحلله نموذجان متخصصان للذكاء الاصطناعي بشكل مستقل: واحد للوجه وآخر للصوت. تُدمَج مخرجاتهما في حكم واحد: حقيقي، أو مزيف، أو غير مؤكد، مع شرح قصير بلغة بسيطة.",
    "about.p3":
      "طُوِّر هذا المشروع كجزء من مشروع التخرج لدرجة البكالوريوس (مرتبة الشرف) في علوم الحاسوب (الأمن السيبراني) في جامعة Asia Pacific، ويتوافق مع هدف التنمية المستدامة رقم 16 — السلام والعدالة والمؤسسات القوية.",
    "about.tech":
      "تم البناء باستخدام PyTorch و Flask و React. يعمل على المعالج فقط. لا تُخزَّن الملفات على المدى البعيد.",

    "model.label":      "نموذج الذكاء الاصطناعي",
    "model.local":      "نموذجنا المدرَّب",
    "model.local.hint": "مُوصى به — النموذج الذي بنيناه لهذا المشروع.",
    "model.hf":         "نموذج HuggingFace المرجعي",
    "model.hf.hint":    "نموذج عام مُدرَّب مسبقاً للمقارنة.",

    "err.network": "تعذَّر الوصول إلى خادم Deeptection.",
    "err.generic": "حدث خطأ ما. يُرجى المحاولة مرة أخرى.",
  },
};

/**
 * Resolve a translation key into the current locale's text.
 * Falls back to English if the key is missing in the target locale,
 * and to the key itself if it's missing in English too (dev aid).
 *
 *   translate("en", "nav.home")                → "Home"
 *   translate("ar", "nav.home")                → "الرئيسية"
 *   translate("ta", "upload.supported", {vmb: 50, vsec: 180, amb: 20})
 *     → "...அதிகபட்சம் 50 MB / 180 வினாடி. ஆடியோ அதிகபட்சம் 20 MB."
 */
export function translate(lang, key, vars) {
  const table = dict[lang] || dict.en;
  let s = table[key];
  if (s === undefined) s = dict.en[key];
  if (s === undefined) return key;
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      s = s.replace(new RegExp(`\\{${k}\\}`, "g"), String(v));
    }
  }
  return s;
}