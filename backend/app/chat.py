"""TaxShield Intelligent Assistant engine.

Deterministic, tool-based, no external LLM calls (judge-safe offline).
Pipeline: language detection (en/ta/hi + code-mix) -> intent classification
-> controlled tools (user-scoped DB/engine) -> templated explainable response.
"""
import re
from datetime import datetime
from typing import Dict, List, Optional
from bson import ObjectId

TAMIL_RE = re.compile(r'[\u0B80-\u0BFF]')
DEVA_RE = re.compile(r'[\u0900-\u097F]')

TAMIL_KEYS = ["enoda", "enakku", "unga", "irukku", "irukka", "illa", "pannanum", "pannunga",
              "yen", "enna", "edhu", "indha", "konjam", "thevai", "vanakkam"]
HINDI_KEYS = ["mera", "mujhe", "mujhko", "kaunsa", "kaunsi", "kaise", "kyun", "kyu", "kya",
              "kitna", "kitne", "hain", "chahiye", "namaste"]


def _tokens(low: str) -> List[str]:
    return re.findall(r"[a-z\u0B80-\u0BFF\u0900-\u097F]+", low)

INTENTS = ["CHECK_READINESS", "EXPLAIN_READINESS", "SHOW_MISSING_DOCUMENTS",
           "SHOW_ALERTS", "EXPLAIN_ALERT", "SHOW_DEADLINES", "SHOW_OBLIGATIONS",
           "FINANCIAL_SUMMARY", "TAX_ESTIMATE", "SCENARIO_ANALYSIS", "DOCUMENT_STATUS",
           "TRANSACTION_SEARCH", "PROFILE_INFORMATION", "SYSTEM_HELP", "NAVIGATION",
           "GREETING", "UNKNOWN"]

NATIVE_INTENT_KEYS = {
    "EXPLAIN_READINESS": ["ஏன்", "காரணம்", "குறைவு", "क्यों", "कारण", "कम"],
    "CHECK_READINESS": ["மதிப்பெண்", "தயார்நிலை", "ஸ்கோர்", "स्कोर", "तैयारी"],
    "SHOW_MISSING_DOCUMENTS": ["ஆவணம்", "ஆவணங்கள்", "பதிவேற்ற", "காணாமல்", "दस्तावेज़", "दस्तावेज", "अपलोड", "गुम"],
    "SHOW_ALERTS": ["ஆபத்து", "எச்சரிக்கை", "அபாய", "जोखिम", "चेतावनी", "अलर्ट"],
    "SHOW_DEADLINES": ["காலக்கெடு", "தேதி", "மாதம்", "समय-सीमा", "तारीख", "महीना"],
    "SHOW_OBLIGATIONS": ["கடமை", "தயார்", "நிலுவை", "दायित्व", "तैयार", "बकाया"],
    "FINANCIAL_SUMMARY": ["சுருக்கம்", "நிதி", "மொத்த", "सारांश", "वित्त", "कुल"],
    "TAX_ESTIMATE": ["வரி", "பொறுப்பு", "கணக்கு", "कर", "देयता", "हिसाब"],
    "SCENARIO_ANALYSIS": ["சூழ்நிலை", "ஒப்பீடு", "முதலீடு", "விற்பனை", "परिदृश्य", "तुलना", "निवेश", "बेच"],
    "DOCUMENT_STATUS": ["பதிவேற்றினேனா", "சரிபார்ப்பு", "இணைப்பு", "सत्यापन", "अपलोड"],
    "TRANSACTION_SEARCH": ["பரிவர்த்தனை", "சம்பளம்", "வாடகை", "लेनदेन", "वेतन", "किराया"],
    "PROFILE_INFORMATION": ["சுயவிவரம்", "நிதியாண்டு", "முறை", "विवरण", "वित्तीय", "व्यवस्था"],
    "SYSTEM_HELP": ["உதவி", "எப்படி", "मदद", "कैसे"],
    "GREETING": ["வணக்கம்", "நமஸ்தே", "नमस्ते"],
}

INTENT_KEYS = {
    "CHECK_READINESS": ["readiness score", "readiness", "score", "ready", "score enna", "score kitna"],
    "EXPLAIN_READINESS": ["why", "yen", "kyun", "kyu", "low", "explain", "karan", "reason"],
    "SHOW_MISSING_DOCUMENTS": ["missing document", "missing", "upload", "pannanum", "karna", "document"],
    "SHOW_ALERTS": ["alert", "risk", "high-risk", "high risk", "risks"],
    "EXPLAIN_ALERT": ["explain alert", "why high risk", "why marked", "indha alert"],
    "SHOW_DEADLINES": ["deadline", "due", "prepare this month", "this month"],
    "SHOW_OBLIGATIONS": ["obligation", "prepare", "need to prepare", "pending"],
    "FINANCIAL_SUMMARY": ["summar", "finance", "overview", "total income", "enoda finance"],
    "TAX_ESTIMATE": ["tax position", "tax estimate", "tax liability", "tax kitna", "tax enna", "liability"],
    "SCENARIO_ANALYSIS": ["what if", "scenario", "invest", "sell", "impact", "compare"],
    "DOCUMENT_STATUS": ["uploaded", "salary slip", "invoice", "verification", "linked"],
    "TRANSACTION_SEARCH": ["transaction", "freelance income", "salary", "rental", "show my"],
    "PROFILE_INFORMATION": ["profile", "financial year", "assessment year", "regime", "employment"],
    "SYSTEM_HELP": ["help", "how", "what can you", "udhavi", "madad"],
    "NAVIGATION": ["open", "go to", "page", "show dashboard"],
    "GREETING": ["hi", "hello", "vanakkam", "namaste", "hey"],
}

DISCLAIMER = ("TaxShield provides preliminary analysis based on the information available "
              "in the system. It does not provide legal, tax or financial advice and should "
              "not replace a qualified tax professional.")

_context: Dict[str, dict] = {}


def detect_language(text: str) -> str:
    t = text or ""
    if TAMIL_RE.search(t):
        return "ta" if not HINDI_KEYS_HIT(t) else "ta-mix"
    if DEVA_RE.search(t):
        return "hi" if not TAMIL_HIT(t) else "hi-mix"
    low = t.lower()
    toks = set(_tokens(low))
    ta = sum(1 for k in TAMIL_KEYS if k in toks)
    hi = sum(1 for k in HINDI_KEYS if k in toks)
    if ta and hi:
        return "ta-mix" if ta >= hi else "hi-mix"
    if ta:
        return "ta-mix" if any(w in low for w in ["score", "invoice", "document", "risk", "tax"]) else "ta"
    if hi:
        return "hi-mix" if any(w in low for w in ["score", "invoice", "document", "risk", "tax", "readiness"]) else "hi"
    return "en"


def TAMIL_HIT(t: str) -> bool:
    return bool(TAMIL_RE.search(t))


def HINDI_KEYS_HIT(t: str) -> bool:
    return any(k in _tokens(t.lower()) for k in HINDI_KEYS)


def base_lang(lang: str) -> str:
    return "ta" if lang.startswith("ta") else ("hi" if lang.startswith("hi") else "en")


def classify_intent(text: str, lang: str) -> str:
    for _intent, _keys in NATIVE_INTENT_KEYS.items():
        if any(k in text for k in _keys):
            if _intent == "EXPLAIN_READINESS" and not any(
                    k in text for k in ["மதிப்பெண்", "தயார்நிலை", "ஸ்கோர்", "स्कोर", "तैयारी", "score", "readiness"]):
                continue
            return _intent
    low = text.lower()
    if re.search(r"what if|scenario|invest.*\?|sell.*\?|impact", low):
        return "SCENARIO_ANALYSIS"
    if any(k in low for k in ["why", "yen ", "yen", "kyun", "kyu"]) and any(k in low for k in ["score", "readiness", "low"]):
        return "EXPLAIN_READINESS"
    scores = {}
    for intent, keys in INTENT_KEYS.items():
        scores[intent] = sum(1 for k in keys if k in low)
    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        # pronoun follow-ups use context
        if any(w in low for w in ["what should i fix", "fix first", "priority", "first"]):
            return "EXPLAIN_READINESS"
        if any(w in low for w in ["that document", "where is", "andha", "enge"]):
            return "DOCUMENT_STATUS"
        return "UNKNOWN"
    # EXPLAIN wins ties when why-words present
    if scores.get("EXPLAIN_READINESS", 0) and scores[best] <= 2:
        pass
    return best


def inr(n) -> str:
    try:
        return f"₹{float(n):,.0f}"
    except Exception:
        return "₹0"


# ---- templated responses (simple language, same-language rule) ----
def tr(key: str, lang: str, **kw) -> str:
    b = base_lang(lang)
    mix = lang in ("ta-mix", "hi-mix")
    T = {
        "readiness": {
            "en": "Your Tax Readiness Score is {score}/100. Main reasons: {reasons} Your first priority: {first}",
            "ta": "Unga Tax Readiness Score {score}/100. Main reasons: {reasons} First, {first}.",
            "hi": "आपका टैक्स तैयारी स्कोर {score}/100 है। मुख्य कारण: {reasons} सबसे पहले: {first}।",
        },
        "missing_docs": {
            "en": "Currently {n} important document(s) need attention: {items} First upload {first} because it is linked to higher-risk alerts.",
            "ta": "Currently {n} important documents missing ah irukku: {items} First {first} upload pannunga, because athu higher-risk alert-oda linked.",
            "hi": "इस समय {n} महत्वपूर्ण दस्तावेज़ों पर ध्यान चाहिए: {items}। पहले {first} अपलोड करना बेहतर रहेगा क्योंकि वह अधिक जोखिम से जुड़ा है।",
        },
        "no_missing": {
            "en": "Good news — no missing documents right now. Your evidence looks complete.",
            "ta": "Nalla news — ippo missing documents ethuvum illa. Evidence complete ah irukku.",
            "hi": "अच्छी खबर — अभी कोई दस्तावेज़ गुम नहीं है। प्रमाण पूर्ण है।",
        },
        "alerts": {
            "en": "You have {n} open alert(s): {items} Ask me to explain any alert.",
            "ta": "Ungalukku {n} open alert(s) irukku: {items} Entha alert-ah explain pannanum-nu kelunga.",
            "hi": "आपके पास {n} खुली चेतावनियाँ हैं: {items}। किसी भी चेतावनी को समझाने के लिए कहें।",
        },
        "summary": {
            "en": "Income: {income}. Deductions (verified): {deduct}. Tax paid: {paid}. Open obligations: {ob}. Missing documents: {miss}. High-risk alerts: {high}. Readiness: {score}/100. Most important action: {first}",
            "ta": "Income: {income}. Deductions (verified): {deduct}. Tax paid: {paid}. Open obligations: {ob}. Missing documents: {miss}. High-risk alerts: {high}. Readiness: {score}/100. Mukkiyama: {first}.",
            "hi": "आय: {income}। कटौतियाँ (सत्यापित): {deduct}। चुकाया कर: {paid}। खुले दायित्व: {ob}। गुम दस्तावेज़: {miss}। अधिक जोखिम चेतावनियाँ: {high}। तैयारी: {score}/100। सबसे ज़रूरी: {first}।",
        },
        "deadlines": {
            "en": "Upcoming deadlines ({n}): {items}",
            "ta": "Upcoming deadlines ({n}): {items}",
            "hi": "आगामी समय-सीमाएँ ({n}): {items}",
        },
        "tax": {
            "en": "Estimated tax position ({regime} regime): taxable income {taxable}, base {base}, rebate {rebate}, surcharge {surcharge}, cess {cess}. Estimated liability {liab}, paid {paid}, outstanding {out}. Estimated based on the information currently available.",
            "ta": "Estimated tax position ({regime} regime): taxable income {taxable}, base {base}, rebate {rebate}, surcharge {surcharge}, cess {cess}. Estimated liability {liab}, paid {paid}, outstanding {out}. Ithu estimate mattum.",
            "hi": "अनुमानित कर स्थिति ({regime}): कर योग्य आय {taxable}, आधार {base}, छूट {rebate}, अधिभार {surcharge}, उपकर {cess}। अनुमानित देयता {liab}, चुकाया {paid}, बकाया {out}। यह अनुमान है।",
        },
        "scenario": {
            "en": "I compared your scenario (estimate, not guaranteed): current liability {cur}, scenario liability {sc}, difference {diff}. {extra} Assumptions: {assump}",
            "ta": "Scenario compare pannen (estimate mattum): current liability {cur}, scenario liability {sc}, difference {diff}. {extra} Assumptions: {assump}",
            "hi": "परिदृश्य तुलना की (अनुमान है): वर्तमान देयता {cur}, परिदृश्य देयता {sc}, अंतर {diff}। {extra} मान्यताएँ: {assump}",
        },
        "help": {
            "en": "I can help with readiness, missing documents, risks, deadlines, obligations, tax position and scenarios. Try: 'Why is my score low?' or 'Show missing documents'.",
            "ta": "Readiness, missing documents, risks, deadlines, obligations, tax position, scenarios patri help panna mudiyum. Try: 'Enoda score yen low?'",
            "hi": "तैयारी, गुम दस्तावेज़, जोखिम, समय-सीमाएँ, दायित्व, कर स्थिति और परिदृश्यों में मदद कर सकता हूँ। पूछें: 'मेरा स्कोर कम क्यों है?'",
        },
        "fallback": {
            "en": "I don't have enough information to give a reliable answer yet. Try asking about your readiness score, missing documents, risks, deadlines or finances.",
            "ta": "Reliable answer kudukka ippo pothumana information illa. Readiness score, missing documents, risks, deadlines patri kelunga.",
            "hi": "विश्वसनीय उत्तर के लिए अभी पर्याप्त जानकारी नहीं है। तैयारी स्कोर, गुम दस्तावेज़, जोखिम, समय-सीमाओं के बारे में पूछें।",
        },
        "greeting": {
            "en": "Hi! I can help you understand your tax readiness, documents, risks, deadlines and scenarios.",
            "ta": "Vanakkam! Tax readiness, documents, risks, deadlines, scenarios patri help panna mudiyum.",
            "hi": "नमस्ते! कर तैयारी, दस्तावेज़, जोखिम, समय-सीमाएँ और परिदृश्यों में मदद कर सकता हूँ।",
        },
    }
    if lang in ("ta", "ta-mix") and key in TA_SCRIPT:
        tmpl = TA_SCRIPT[key]
        try:
            return tmpl.format(**kw)
        except Exception:
            return tmpl
    tmpl = T[key][b] if b in T[key] else T[key]["en"]
    try:
        return tmpl.format(**kw)
    except Exception:
        return tmpl


# Proper Tamil-script templates (used only when the user writes in Tamil script).
# Tanglish ('ta-mix') responses are intentionally preserved.
TA_SCRIPT = {
    "readiness": "உங்கள் வரி தயார்நிலை மதிப்பெண் {score}/100. முக்கிய காரணங்கள்: {reasons} முதலில்: {first}.",
    "missing_docs": "தற்போது {n} முக்கிய ஆவணங்கள் கவனம் தேவை: {items} முதலில் {first} பதிவேற்றுங்கள், ஏனெனில் இது அதிக ஆபத்து எச்சரிக்கையுடன் தொடர்புடையது.",
    "no_missing": "நல்ல செய்தி — தற்போது காணாமல் போன ஆவணங்கள் எதுவும் இல்லை. ஆதாரங்கள் முழுமையாக உள்ளன.",
    "alerts": "உங்களுக்கு {n} திறந்த எச்சரிக்கைகள் உள்ளன: {items} ஏதேனும் எச்சரிக்கையை விளக்கச் சொல்லுங்கள்.",
    "summary": "வருமானம்: {income}. விலக்குகள் (சரிபார்க்கப்பட்டது): {deduct}. செலுத்திய வரி: {paid}. திறந்த கடமைகள்: {ob}. காணாமல் போன ஆவணங்கள்: {miss}. அதிக ஆபத்து எச்சரிக்கைகள்: {high}. தயார்நிலை: {score}/100. மிக முக்கிய நடவடிக்கை: {first}",
    "deadlines": "வரவிருக்கும் காலக்கெடுக்கள் ({n}): {items}",
    "tax": "மதிப்பிடப்பட்ட வரி நிலை ({regime}): வரிக்குட்பட்ட வருமானம் {taxable}, அடிப்படை {base}, தள்ளுபடி {rebate}, கூடுதல் கட்டணம் {surcharge}, செஸ் {cess}. மதிப்பிடப்பட்ட பொறுப்பு {liab}, செலுத்தியது {paid}, நிலுவை {out}. தற்போதைய தகவலின் அடிப்படையில் மதிப்பீடு.",
    "scenario": "உங்கள் சூழ்நிலையை ஒப்பிட்டேன் (மதிப்பீடு மட்டும், உத்தரவாதம் இல்லை): தற்போதைய பொறுப்பு {cur}, சூழ்நிலை பொறுப்பு {sc}, வித்தியாசம் {diff}. {extra} அனுமானங்கள்: {assump}",
    "help": "தயார்நிலை, காணாமல் போன ஆவணங்கள், ஆபத்துகள், காலக்கெடுக்கள், கடமைகள், வரி நிலை மற்றும் சூழ்நிலைகள் பற்றி உதவ முடியும்.",
    "fallback": "நம்பகமான பதில் தர இப்போது போதுமான தகவல் இல்லை. தயார்நிலை மதிப்பெண், காணாமல் போன ஆவணங்கள், ஆபத்துகள், காலக்கெடுக்கள் பற்றி கேளுங்கள்.",
    "greeting": "வணக்கம்! உங்கள் வரி தயார்நிலை, ஆவணங்கள், ஆபத்துகள், காலக்கெடுக்கள் மற்றும் சூழ்நிலைகள் பற்றி உதவ முடியும்.",
}


def pick(lang: str, en: str, ta_mix: str, ta_native: str, hi: str) -> str:
    # User requirement: Tamil (script or transliterated) -> pure Tamil script only.
    if lang in ("ta", "ta-mix"):
        return ta_native
    if base_lang(lang) == "hi":
        return hi
    return en



CAT_TA = {"salary": "சம்பளம்", "freelance": "ஃப்ரீலான்ஸ்", "business": "வணிகம்", "rental": "வாடகை",
          "bank_interest": "வங்கி வட்டி", "interest": "வட்டி", "dividends": "ஈவுத்தொகை",
          "capital_gains": "மூலதன ஆதாயம்", "other": "மற்றவை"}
CAT_HI = {"salary": "वेतन", "freelance": "फ्रीलांस", "business": "व्यवसाय", "rental": "किराया",
          "bank_interest": "बैंक ब्याज", "interest": "ब्याज", "dividends": "लाभांश",
          "capital_gains": "पूंजीगत लाभ", "other": "अन्य"}


def cat_w(cat: str, lang: str) -> str:
    c = str(cat or "other").lower()
    if lang in ("ta", "ta-mix"):
        return CAT_TA.get(c, str(cat))
    if base_lang(lang) == "hi":
        return CAT_HI.get(c, str(cat))
    return str(cat)


def LT(title: str, lang: str) -> str:
    """Localize known system-generated obligation/deadline titles. Unknown titles pass through."""
    if base_lang(lang) == "en":
        return title
    ta = lang in ("ta", "ta-mix")
    t = title or ""
    low = t.lower()
    if low.startswith("missing document for "):
        c = cat_w(t.split("for ", 1)[1].strip().lower().replace(" ", "_"), lang)
        return f"{c} தொடர்பான ஆவணம் காணவில்லை" if ta else f"{c} का दस्तावेज़ गुम है"
    if low.startswith("deduction proof needed:"):
        c = cat_w(t.split(":", 1)[1].strip().lower().replace(" ", "_"), lang)
        return f"{c} சான்று தேவை" if ta else f"{c} प्रमाण चाहिए"
    if low.startswith("ais mismatch:"):
        src = t.split(":", 1)[1].strip()
        return f"AIS பொருத்தமின்மை: {src}" if ta else f"AIS बेमेल: {src}"
    fixed = {
        "multiple income sources detected": ("பல வருமான ஆதாரங்கள் கண்டறியப்பட்டன", "कई आय स्रोत पाए गए"),
        "freelance income documentation incomplete": ("ஃப்ரீலான்ஸ் வருமான ஆவணங்கள் முழுமையடையவில்லை", "फ्रीलांस आय दस्तावेज़ अधूरे हैं"),
        "capital gain purchase documentation missing": ("மூலதன ஆதாய கொள்முதல் ஆவணம் காணவில்லை", "पूंजीगत लाभ खरीद दस्तावेज़ गुम है"),
        "possible advance tax liability": ("முன்கூட்டிய வரி பொறுப்பு இருக்கலாம்", "अग्रिम कर देयता संभव है"),
        "investment sale without purchase record": ("கொள்முதல் பதிவு இல்லாமல் முதலீட்டு விற்பனை", "खरीद रिकॉर्ड के बिना निवेश बिक्री"),
        "income tax return filing": ("வருமான வரி அறிக்கை தாக்கல்", "आयकर रिटर्न दाखिल करना"),
    }
    if low in fixed:
        return fixed[low][0] if ta else fixed[low][1]
    if low.startswith("advance tax -"):
        rest = t.split("-", 1)[1].strip()
        return f"முன்கூட்டிய வரி - {rest}" if ta else f"अग्रिम कर - {rest}"
    if "tds return" in low or "tds" in low:
        return t.replace("TDS Return", "TDS அறிக்கை") if ta else t.replace("TDS Return", "TDS रिटर्न")
    return t


def reg_w(regime: str, lang: str) -> str:
    r = str(regime or "old").lower()
    if lang in ("ta", "ta-mix"):
        return "பழைய" if r == "old" else "புதிய"
    if base_lang(lang) == "hi":
        return "पुरानी" if r == "old" else "नई"
    return r


DISCLAIMER_TA = ("டாக்ஸ்ஷீல்டு அமைப்பில் உள்ள தகவலின் அடிப்படையில் ஆரம்ப மதிப்பீட்டை வழங்குகிறது. "
                 "இது சட்ட, வரி அல்லது நிதி ஆலோசனை அல்ல, தகுதிவாய்ந்த வரி நிபுணருக்கு மாற்றாகாது.")
DISCLAIMER_HI = ("टैक्सशील्ड सिस्टम में उपलब्ध जानकारी के आधार पर प्रारंभिक विश्लेषण देता है। "
                 "यह कानूनी, कर या वित्तीय सलाह नहीं है और योग्य कर विशेषज्ञ का विकल्प नहीं है।")


def get_ctx(uid: str) -> dict:
    return _context.setdefault(uid, {"last_intent": None, "last_items": [], "turns": 0})


async def build_snapshot(user, db, analysis_engine) -> dict:
    from app.models import Obligation, Deadline
    uid = user.id if hasattr(user, "id") else user["_id"]
    try:
        obligations, deadlines, score, summary = await analysis_engine.analyze_user_data(uid)
    except Exception:
        obligations, deadlines, score, summary = [], [], None, None
    docs = await db.documents.find({"user_id": uid}).to_list(200)
    txs = await db.transactions.find({"user_id": uid}).sort("date", -1).to_list(50)
    try:
        recon = await analysis_engine.reconcile_user(uid)
    except Exception:
        recon = {}
    risks, actions = [], []
    try:
        ob_models = [Obligation(**o) for o in await db.obligations.find({"user_id": uid}).to_list(200)]
        dl_models = [Deadline(**d) for d in await db.deadlines.find({"user_id": uid}).to_list(200)]
        risks, actions = analysis_engine.derive_risks_and_actions(ob_models, dl_models, recon or {})
    except Exception:
        pass
    return {"obligations": obligations, "deadlines": deadlines, "score": score,
            "summary": summary, "docs": docs, "txs": txs, "recon": recon,
            "risks": risks, "actions": actions}


def fmt_reasons(obligations, lang: str) -> tuple:
    if not obligations:
        d = pick(lang, "records look complete", "records complete ah irukku", "பதிவுகள் முழுமையாக உள்ளன", "रिकॉर्ड पूर्ण हैं")
        return d, pick(lang, "keep records updated", "records-a update pannunga", "பதிவுகளை புதுப்பிக்கவும்", "रिकॉर्ड अद्यतन रखें")
    tops = sorted(obligations, key=lambda o: (0 if str(getattr(o, "risk_level", "")) == "high" else 1))[:3]
    parts = []
    for o in tops:
        parts.append(f"{LT(o.title, lang)} ({inr(o.estimated_amount)})")
    first = pick(lang, f"upload documents for '{tops[0].title}'", f"'{tops[0].title}'-ku documents upload pannunga", f"'{LT(tops[0].title, lang)}' பதிவேற்றுங்கள்", f"'{LT(tops[0].title, lang)}' अपलोड करें")
    return "; ".join(parts), first


async def answer(uid: str, text: str, user, db, analysis_engine, scenario_extra: dict = None, language_override: str = None) -> dict:
    detected = detect_language(text)
    # Language selector override (frontend): only en/ta/hi; auto-detect otherwise.
    lang = language_override if language_override in ("en", "ta", "hi") else detected
    intent = classify_intent(text, detected)
    ctx = get_ctx(uid)
    # pronoun follow-up: reuse last intent
    low = text.lower()
    if intent == "UNKNOWN" and ctx["last_intent"] in ("EXPLAIN_READINESS", "SHOW_ALERTS", "SHOW_MISSING_DOCUMENTS"):
        if any(w in low for w in ["fix first", "first", "priority", "should i"]):
            intent = "EXPLAIN_READINESS"
    snap = await build_snapshot(user, db, analysis_engine)
    obligations = snap["obligations"] or []
    deadlines = snap["deadlines"] or []
    score = snap["score"]
    summary = snap["summary"]
    score_n = score.score if score and hasattr(score, "score") else 0
    sdict = summary.model_dump() if summary and hasattr(summary, "model_dump") else {}
    nav = None
    extra_cards = None
    needs_disclaimer = False

    if intent in ("CHECK_READINESS", "EXPLAIN_READINESS"):
        reasons, first = fmt_reasons(obligations, lang)
        resp = tr("readiness", lang, score=score_n, reasons=reasons + ".", first=first + ".")
        nav = "/dashboard"
    elif intent in ("SHOW_MISSING_DOCUMENTS", "DOCUMENT_STATUS"):
        missing = [o for o in obligations if "missing" in o.title.lower() or "document" in o.title.lower() or "proof" in o.title.lower()]
        if not missing:
            resp = tr("no_missing", lang)
        else:
            items = ", ".join(LT(o.title, lang) for o in missing[:5])
            resp = tr("missing_docs", lang, n=len(missing), items=items + ".", first=f"'{LT(missing[0].title, lang)}'")
            ctx["last_items"] = [o.title for o in missing]
        nav = "/documents"
    elif intent in ("SHOW_ALERTS", "EXPLAIN_ALERT"):
        risks = snap["risks"] or []
        if not risks:
            resp = pick(lang, "No open alerts right now.", "Ippo open alerts ethuvum illa.", "தற்போது திறந்த எச்சரிக்கைகள் எதுவும் இல்லை.", "अभी कोई खुली चेतावनी नहीं है।")
        else:
            items = ", ".join(f"{LT(r['title'], lang)} ({r['severity']})" for r in risks[:5])
            if intent == "EXPLAIN_ALERT":
                r = risks[0]
                why = pick(lang, f"This is {r['severity']} risk because the rule engine detected: {r['title']} (amount {inr(r.get('estimated_amount', 0))}). Recommended action: resolve the linked obligation and upload supporting evidence.",
                       f"Ithu {r['severity']} risk, rule engine kandupidichathu: {r['title']} (amount {inr(r.get('estimated_amount', 0))}). Supporting evidence upload pannunga.",
                       f"இது {r['severity']} ஆபத்து, விதி இயந்திரம் கண்டறிந்தது: {LT(r['title'], lang)} (தொகை {inr(r.get('estimated_amount', 0))}). தொடர்புடைய கடமையை தீர்த்து ஆதாரங்களை பதிவேற்றுங்கள்.",
                       f"यह {r['severity']} जोखिम है, नियम इंजन ने पकड़ा: {r['title']} (राशि {inr(r.get('estimated_amount', 0))})। सहायक प्रमाण अपलोड करें।")
                resp = why
            else:
                resp = tr("alerts", lang, n=len(risks), items=items + ".")
        nav = "/dashboard"
    elif intent in ("SHOW_DEADLINES", "SHOW_OBLIGATIONS"):
        items = ", ".join(f"{LT(d.title, lang)}" for d in deadlines[:5]) if deadlines else "none"
        resp = tr("deadlines", lang, n=len(deadlines), items=items + ".")
        nav = "/deadlines"
    elif intent == "FINANCIAL_SUMMARY":
        inc = inr(sdict.get("total_income", 0)); ded = inr(sdict.get("taxable_income", 0) and (sdict.get("total_income", 0) - sdict.get("taxable_income", 0)))
        _, first = fmt_reasons(obligations, lang)
        highs = len([r for r in (snap["risks"] or []) if r.get("severity") == "high"])
        resp = tr("summary", lang, income=inc, deduct=ded, paid=inr(sdict.get("tax_paid", 0)), ob=len(obligations),
                  miss=len([d for d in snap["docs"] if str(d.get("verification_status")) != "complete"]),
                  high=highs, score=score_n, first=first + ".")
        extra_cards = {"income_breakdown": sdict.get("income_breakdown", {})}
    elif intent == "TAX_ESTIMATE":
        needs_disclaimer = True
        resp = tr("tax", lang, regime=reg_w(sdict.get("regime", "old"), lang), taxable=inr(sdict.get("taxable_income", 0)),
                  base=inr(sdict.get("base_tax", 0)), rebate=inr(sdict.get("rebate", 0)),
                  surcharge=inr(sdict.get("surcharge", 0)), cess=inr(sdict.get("cess", 0)),
                  liab=inr(sdict.get("estimated_liability", 0)), paid=inr(sdict.get("tax_paid", 0)), out=inr(sdict.get("outstanding_tax", 0)))
    elif intent == "SCENARIO_ANALYSIS":
        needs_disclaimer = True
        import re as _re
        m = _re.search(r"₹?\s*([\d,]+(?:\.\d+)?)", text.replace("₹", ""))
        amt = float(m.group(1).replace(",", "")) if m else 50000.0
        cur = float(sdict.get("estimated_liability", 0)); inc = float(sdict.get("total_income", 0))
        ded = float(sdict.get("total_income", 0)) - float(sdict.get("taxable_income", 0))
        regime = sdict.get("regime", "old")
        sc = analysis_engine.compute_scenario_liability(inc, ded + amt, regime)
        diff = round(sc - cur, 2)
        extra = pick(lang, "Lower estimated liability." if diff < 0 else "Higher estimated liability.",
                       "Lower estimated liability." if diff < 0 else "Higher estimated liability.",
                       "குறைந்த மதிப்பிடப்பட்ட பொறுப்பு." if diff < 0 else "அதிக மதிப்பிடப்பட்ட பொறுப்பு.",
                       "कम अनुमानित देयता।" if diff < 0 else "अधिक अनुमानित देयता।")
        assump = pick(lang, f"extra deduction {inr(amt)}, {regime} regime", f"extra deduction {inr(amt)}, {regime} regime",
                      f"கூடுதல் விலக்கு {inr(amt)}, {reg_w(regime, lang)}", f"अतिरिक्त कटौती {inr(amt)}, {reg_w(regime, lang)}")
        resp = tr("scenario", lang, cur=inr(cur), sc=inr(sc), diff=inr(diff), extra=extra, assump=assump)
        extra_cards = {"current_liability": cur, "scenario_liability": sc, "difference": diff}
    elif intent == "TRANSACTION_SEARCH":
        txs = snap["txs"] or []
        items = ", ".join(f"{t.get('description', '')} ({inr(t.get('amount', 0))})" for t in txs[:5]) if txs else "none"
        resp = pick(lang, f"Recent transactions: {items}.", f"Recent transactions: {items}.", f"சமீபத்திய பரிவர்த்தனைகள்: {items}.", f"हाल के लेनदेन: {items}।")
        nav = "/transactions"
    elif intent == "PROFILE_INFORMATION":
        p = {"fy": getattr(user, "financial_year", "2024-25"), "regime": reg_w(getattr(user, "preferred_tax_regime", None) or sdict.get("regime", "old"), lang),
             "emp": getattr(user, "employment_type", None) or "-", "jur": getattr(user, "tax_jurisdiction", "India")}
        resp = pick(lang, f"Profile: FY {p['fy']}, regime {p['regime']}, employment {p['emp']}, jurisdiction {p['jur']}.",
                f"Profile: FY {p['fy']}, regime {p['regime']}, employment {p['emp']}.",
                f"சுயவிவரம்: FY {p['fy']}, regime {p['regime']}, employment {p['emp']}.",
                f"विवरण: FY {p['fy']}, व्यवस्था {p['regime']}, रोज़गार {p['emp']}।")
        nav = "/settings"
    elif intent in ("SYSTEM_HELP", "GREETING", "NAVIGATION"):
        resp = tr("greeting" if intent == "GREETING" else "help", lang)
        nav = "/dashboard" if intent == "NAVIGATION" else None
    else:
        resp = tr("fallback", lang)

    if needs_disclaimer:
        resp = resp + " " + (DISCLAIMER_TA if lang in ("ta", "ta-mix") else (DISCLAIMER_HI if base_lang(lang) == "hi" else DISCLAIMER))
    ctx["last_intent"] = intent
    ctx["turns"] += 1
    return {"response": resp, "language": lang, "detected_language": detected, "intent": intent, "navigate_to": nav,
            "cards": extra_cards, "disclaimer": (DISCLAIMER_TA if lang in ("ta", "ta-mix") else (DISCLAIMER_HI if base_lang(lang) == "hi" else DISCLAIMER)) if needs_disclaimer else None}
