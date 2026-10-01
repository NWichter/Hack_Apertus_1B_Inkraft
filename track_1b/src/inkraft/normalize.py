"""Text and number normalisation for German, French and Italian short answers."""

import re
import unicodedata

NUMBER_RE = re.compile(r"\d{1,3}(?:[ '’   ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?")

# Cardinals and ordinals. Indefinite articles (ein, un, una ...) are WEAK: they only count as 1
# when a unit follows ("ein Jahr", "un mois"), never in "eine Rente" or "une allocation".
NUM_WORDS = {
    "de": {
        "null": 0,
        "zwei": 2,
        "drei": 3,
        "vier": 4,
        "fünf": 5,
        "sechs": 6,
        "sieben": 7,
        "acht": 8,
        "neun": 9,
        "zehn": 10,
        "elf": 11,
        "zwölf": 12,
        "vierzehn": 14,
        "fünfzehn": 15,
        "sechzehn": 16,
        "zwanzig": 20,
        "dreissig": 30,
        "dreißig": 30,
        "vierzig": 40,
        "fünfzig": 50,
        "sechzig": 60,
        "neunzig": 90,
        "hundert": 100,
        "erste": 1,
        "ersten": 1,
        "zweite": 2,
        "zweiten": 2,
        "dritte": 3,
        "dritten": 3,
        "vierte": 4,
        "vierten": 4,
        "fünfte": 5,
        "fünften": 5,
        "sechste": 6,
        "sechsten": 6,
        "siebte": 7,
        "siebten": 7,
        "achte": 8,
        "achten": 8,
        "zehnte": 10,
        "zehnten": 10,
    },
    "fr": {
        "deux": 2,
        "trois": 3,
        "quatre": 4,
        "cinq": 5,
        "six": 6,
        "sept": 7,
        "huit": 8,
        "neuf": 9,
        "dix": 10,
        "onze": 11,
        "douze": 12,
        "quatorze": 14,
        "quinze": 15,
        "seize": 16,
        "vingt": 20,
        "trente": 30,
        "quarante": 40,
        "cinquante": 50,
        "soixante": 60,
        "cent": 100,
        "premier": 1,
        "première": 1,
        "deuxième": 2,
        "troisième": 3,
        "quatrième": 4,
        "cinquième": 5,
        "sixième": 6,
        "septième": 7,
        "dixième": 10,
        "treizième": 13,
    },
    "it": {
        "due": 2,
        "tre": 3,
        "quattro": 4,
        "cinque": 5,
        "sei": 6,
        "sette": 7,
        "otto": 8,
        "nove": 9,
        "dieci": 10,
        "undici": 11,
        "dodici": 12,
        "quattordici": 14,
        "quindici": 15,
        "sedici": 16,
        "venti": 20,
        "trenta": 30,
        "quaranta": 40,
        "cinquanta": 50,
        "sessanta": 60,
        "novanta": 90,
        "cento": 100,
        "primo": 1,
        "prima": 1,
        "secondo": 2,
        "terzo": 3,
        "terza": 3,
        "quarto": 4,
        "quinto": 5,
        "sesto": 6,
        "settimo": 7,
        "decimo": 10,
        "tredicesimo": 13,
        "tredicesima": 13,
        "ventitreesima": 23,
        "cinquantaseiesimo": 56,
    },
}
WEAK_ONE = {
    "de": {"ein", "eine", "einen", "einem", "einer", "eines"},
    "fr": {"un", "une"},
    "it": {"un", "uno", "una"},
}

# Unit words -> length in days (durations); used to compare "3 mois" with "3 semaines".
UNITS = {
    "de": {
        "tag": 1,
        "tage": 1,
        "tagen": 1,
        "tages": 1,
        "woche": 7,
        "wochen": 7,
        "monat": 30.44,
        "monate": 30.44,
        "monaten": 30.44,
        "monats": 30.44,
        "jahr": 365.25,
        "jahre": 365.25,
        "jahren": 365.25,
        "jahres": 365.25,
        "altersjahr": 365.25,
        "lebensjahr": 365.25,
        "stunde": 1 / 24,
        "stunden": 1 / 24,
    },
    "fr": {
        "jour": 1,
        "jours": 1,
        "semaine": 7,
        "semaines": 7,
        "mois": 30.44,
        "an": 365.25,
        "ans": 365.25,
        "année": 365.25,
        "années": 365.25,
        "heure": 1 / 24,
        "heures": 1 / 24,
    },
    "it": {
        "giorno": 1,
        "giorni": 1,
        "settimana": 7,
        "settimane": 7,
        "mese": 30.44,
        "mesi": 30.44,
        "anno": 365.25,
        "anni": 365.25,
        "ora": 1 / 24,
        "ore": 1 / 24,
    },
}
UNIT_DAYS = {
    "days": 1,
    "weeks": 7,
    "months": 30.44,
    "years": 365.25,
    "age": 365.25,
    "hours": 1 / 24,
}

# Article, paragraph and SR references carry numbers that are never the answer.
REFERENCE_RE = re.compile(
    r"\b(?:art(?:\.|icle|ikel|icolo)?|abs(?:\.|atz)?|al(?:\.|inéa)?|cpv\.?|capoverso|lit\.?|let\.?|"
    r"bst\.?|ziff\.?|ch\.?|n\.|sr|rs|ss\.?|ff\.?)\s*\d+[a-z]?(?:\s*(?:bis|ter|quater))?(?:[.,]\d+)*",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
MONTHS = (
    "januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember|"
    "janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre|"
    "gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre"
)
CALENDAR_DATE_RE = re.compile(
    rf"\b\d{{1,2}}(?:\.|er|°|º)?\s+(?:{MONTHS})\b(?:\s+(?:19|20)\d{{2}})?",
    re.IGNORECASE,
)
PERCENT_WORD_RE = re.compile(r"\b(?:per\s?cento|pour\s?cent|prozent)\b", re.IGNORECASE)
TOKEN_RE = re.compile(
    r"\d{1,3}(?:[ '’   ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?|[^\W\d_]+"
)


def lang2(lang):
    return (lang or "de")[:2]


def norm_space(s):
    s = unicodedata.normalize("NFC", s or "")
    s = s.replace(" ", " ").replace(" ", " ").replace(" ", " ").replace("‑", "-")
    return re.sub(r"\s+", " ", s).strip()


def norm_text(s):
    s = norm_space(s).casefold()
    for a, b in (
        ("’", "'"),
        ("‘", "'"),
        ("‐", "-"),
        ("–", "-"),
        ("ß", "ss"),
        ("*", ""),
    ):
        s = s.replace(a, b)
    return s


def _clean(text, drop_references, drop_years, drop_dates):
    t = norm_space(text).replace("**", "")
    t = PERCENT_WORD_RE.sub(" %", t)
    if drop_dates:
        t = CALENDAR_DATE_RE.sub(" ", t)
    if drop_references:
        t = REFERENCE_RE.sub(" ", t)
    if drop_years:
        t = YEAR_RE.sub(" ", t)
    return re.sub(r"\b[^\W\d_]{1,5}[’'](?=\w)", " ", t)


def _tokens(text, lang):
    """Yield (value or None, word or None) for every number/word token."""
    l2 = lang2(lang)
    words = NUM_WORDS.get(l2, {})
    for m in TOKEN_RE.finditer(text):
        tok = m.group(0)
        if tok[0].isdigit():
            raw = re.sub(r"[ '’   ]", "", tok).replace(",", ".")
            try:
                yield float(raw), None
            except ValueError:
                yield None, None
        else:
            w = tok.casefold()
            yield (float(words[w]) if w in words else None), w


def quantities(
    text, lang="de", drop_references=True, drop_years=False, drop_dates=True
):
    """List of (value, days_per_unit or None) for every number in the text."""
    l2 = lang2(lang)
    units = UNITS.get(l2, {})
    toks = list(_tokens(_clean(text, drop_references, drop_years, drop_dates), lang))
    out = []
    for i, (val, word) in enumerate(toks):
        nxt = toks[i + 1][1] if i + 1 < len(toks) else None
        unit = units.get(nxt) if nxt else None
        if val is None and word in WEAK_ONE.get(l2, ()) and unit is not None:
            val = 1.0
        if val is not None:
            out.append((val, unit))
    return out


def extract_numbers(
    text, lang="de", drop_references=True, drop_years=False, drop_dates=True
):
    """All numbers in the text (digits, number words, '<article> <unit>'), as floats."""
    return {
        v for v, _ in quantities(text, lang, drop_references, drop_years, drop_dates)
    }
