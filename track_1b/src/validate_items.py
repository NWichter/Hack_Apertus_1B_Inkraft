"""Validate Stichtag draft items against the fedlex source texts.

Checks: format, answer-in-article (literal or normalised number), evidence verbatim in the cited
paragraph, outdated answer in the previous version, duplicates, language consistency, distribution.
Writes a Markdown report and, optionally, a review queue. Exit code 1 if any ERROR was found.
"""

import argparse
import ast
import datetime as dt
import difflib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

LANGS = {"de-CH": "de", "fr-CH": "fr", "it-CH": "it"}
QUESTION_TYPES = {
    "numeric",
    "procedural",
    "yes_no",
    "temporal",
    "term",
    "calc",
    "false_premise",
}
DOMAINS = {
    "kvg_insured",
    "kvg_billing",
    "ahv",
    "iv_el",
    "uvg_atsg",
    "eo_alv",
    "bvg_3a",
    "or_illness",
    "famz",
}
ANSWER_TYPES = {
    "currency_chf",
    "number",
    "percent",
    "duration",
    "age",
    "date",
    "text",
    "yes_no",
}
AUTHORS = {"claude", "codex", "gemini", "nemotron", "human"}
FROZEN = {"value": False}
THRESHOLD_WORDS = {
    "de": ["mehr als", "übersteig", "höchstens", "mindestens", "weniger als", "bis zu"],
    "fr": ["plus de", "dépass", "au plus", "au moins", "moins de", "jusqu"],
    "it": ["più di", "supera", "al massimo", "almeno", "meno di", "fino a"],
}
DISCRETION = re.compile(r"\b(Bundesrat|Departement|Reglement|Kantone? (?:kann|können|bestimm|regel))", re.I)
CONTENT_STOP = {
    "de": {"der", "die", "das", "des", "dem", "den", "ein", "eine", "einen", "einer", "und", "oder", "nach", "für", "von", "vom", "zur", "zum", "mit", "bei", "auf", "aus", "wird", "werden", "ist", "sind", "nicht", "sich", "wenn", "dass", "wie", "welche", "welcher", "welches", "wann", "was", "wer"},
    "fr": {"le", "la", "les", "des", "du", "de", "un", "une", "et", "ou", "pour", "par", "avec", "est", "sont", "qui", "que", "quel", "quelle", "quels", "quelles", "dans", "sur", "aux", "pas"},
    "it": {"il", "lo", "la", "le", "gli", "dei", "del", "della", "di", "un", "una", "e", "o", "per", "con", "è", "sono", "che", "quale", "quali", "nel", "nella", "su", "non"},
}
YES_NO = {"de": {"ja", "nein"}, "fr": {"oui", "non"}, "it": {"sì", "si", "no"}}
REQUIRED = [
    "id",
    "core_id",
    "lang",
    "domain",
    "question_type",
    "register",
    "difficulty_prior",
    "question",
    "answer",
    "answer_aliases",
    "answer_type",
    "answer_normalized",
    "outdated_answers",
    "near_miss_answers",
    "as_of",
    "source",
    "temporal",
    "status",
    "author",
    "needs_human_review",
    "generator",
    "generator_model",
    "generated_at",
    "prompt_version",
    "license",
]
SOURCE_REQUIRED = [
    "act",
    "sr",
    "article",
    "article_id",
    "paragraph",
    "version_date",
    "eli_url",
    "quote",
    "evidence",
    "license",
]

NUM_WORDS = {
    "de": {
        "null": 0,
        "ein": 1,
        "eine": 1,
        "einen": 1,
        "einem": 1,
        "einer": 1,
        "eines": 1,
        "zwei": 2,
        "drei": 3,
        "dreier": 3,
        "vier": 4,
        "fünf": 5,
        "sechs": 6,
        "sieben": 7,
        "acht": 8,
        "neun": 9,
        "zehn": 10,
        "elf": 11,
        "zwölf": 12,
        "fünfzehn": 15,
        "zwanzig": 20,
        "dreissig": 30,
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
        "zehnte": 10,
        "zehnten": 10,
        "siebte": 7,
        "siebten": 7,
        "siebente": 7,
        "siebenten": 7,
        "achte": 8,
        "fünftel": 5,
        "fünfteln": 5,
        "dreissigsten": 30,
        "einunddreissigsten": 31,
    },
    "fr": {
        "un": 1,
        "une": 1,
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
        "cinquièmes": 5,
        "sixième": 6,
        "dixième": 10,
        "treizième": 13,
    },
    "it": {
        "un": 1,
        "uno": 1,
        "una": 1,
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
        "seconda": 2,
        "terzo": 3,
        "terza": 3,
        "quarto": 4,
        "quinto": 5,
        "quinti": 5,
        "sesto": 6,
        "decimo": 10,
        "tredicesimo": 13,
        "tredicesima": 13,
        "biennale": 2,
        "biennali": 2,
    },
}
DE_COMPOUND_PREFIX = [
    "ein",
    "zwei",
    "drei",
    "vier",
    "fünf",
    "sechs",
    "acht",
    "zehn",
    "zwölf",
]
DE_COMPOUND_SUFFIX = ("monat", "jähr", "woch", "wöch", "tägig", "mal", "fach", "stünd")
LEADING_FUNCTION_WORDS = {
    "de": {
        "der",
        "die",
        "das",
        "dem",
        "den",
        "des",
        "ein",
        "eine",
        "einem",
        "einen",
        "einer",
        "bei",
        "beim",
        "am",
        "im",
        "ab",
        "auf",
        "zum",
        "zur",
        "von",
        "vom",
        "mit",
        "in",
        "seinem",
        "seiner",
        "seine",
        "ihr",
    },
    "fr": {
        "le",
        "la",
        "les",
        "l'",
        "du",
        "de",
        "des",
        "au",
        "aux",
        "un",
        "une",
        "à",
        "auprès",
        "pour",
        "son",
        "sa",
        "ses",
        "d'",
    },
    "it": {
        "il",
        "lo",
        "la",
        "i",
        "gli",
        "le",
        "l'",
        "al",
        "allo",
        "alla",
        "ai",
        "agli",
        "alle",
        "del",
        "dello",
        "della",
        "dei",
        "degli",
        "delle",
        "dal",
        "dalla",
        "un",
        "uno",
        "una",
        "per",
        "a",
        "da",
        "di",
        "dell'",
        "all'",
    },
}
STOPWORDS = {
    "de": {
        "der",
        "die",
        "das",
        "und",
        "ist",
        "wie",
        "welche",
        "welcher",
        "wird",
        "nach",
        "einer",
        "eine",
        "bei",
        "muss",
        "für",
        "dem",
        "den",
        "nicht",
        "werden",
        "hat",
        "wer",
        "wann",
        "zu",
        "im",
        "auf",
        "mit",
        "von",
        "welchen",
        "welches",
        "müssen",
        "viele",
        "jedem",
        "pro",
        "jahr",
        "einem",
        "einen",
        "oder",
        "wenn",
        "sich",
    },
    "fr": {
        "le",
        "la",
        "les",
        "des",
        "est",
        "une",
        "pour",
        "qui",
        "quel",
        "quelle",
        "dans",
        "du",
        "doit",
        "en",
        "au",
        "par",
        "sont",
        "ou",
        "pas",
        "il",
        "elle",
        "combien",
        "à",
        "de",
        "quels",
        "doit-il",
        "doit-elle",
        "lorsque",
        "après",
        "selon",
        "aux",
        "faut-il",
    },
    "it": {
        "il",
        "la",
        "che",
        "di",
        "per",
        "una",
        "sono",
        "è",
        "del",
        "della",
        "quale",
        "quanti",
        "deve",
        "gli",
        "al",
        "quanto",
        "quante",
        "delle",
        "degli",
        "alla",
        "dopo",
        "entro",
        "secondo",
        "ammonta",
        "anni",
        "giorni",
        "nel",
        "non",
        "chi",
        "da",
        "dei",
        "con",
        "un",
        "i",
        "le",
        "nella",
        "nelle",
        "nei",
        "in",
        "devono",
    },
}
PII_PATTERNS = {
    "ahv_number": re.compile(r"\b756[.\s]?\d{4}[.\s]?\d{4}[.\s]?\d{2}\b"),
    "iban": re.compile(r"\bCH\d{2}\s?(?:\d{4}\s?){4}\d\b"),
    "phone": re.compile(r"(?:\+41|\b0\d{2})\s?\d{3}\s?\d{2}\s?\d{2}\b"),
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"),
}
NUMBER_RE = re.compile(r"\d{1,3}(?:[ '’   ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?")


def norm_space(s):
    s = unicodedata.normalize("NFC", s or "")
    s = s.replace(" ", " ").replace(" ", " ").replace(" ", " ").replace("‑", "-")
    return re.sub(r"\s+", " ", s).strip()


def norm_text(s):
    s = (
        norm_space(s)
        .casefold()
        .replace("’", "'")
        .replace("‘", "'")
        .replace("‐", "-")
        .replace("–", "-")
    )
    return s


def strip_leading(s, lang):
    words = s.split(" ")
    while len(words) > 1:
        w = words[0]
        if w in LEADING_FUNCTION_WORDS[lang]:
            words = words[1:]
            continue
        m = re.match(r"^(l'|d'|dell'|all'|dall'|nell'|un')(.+)$", w)
        if m:
            words[0] = m.group(2)
            continue
        break
    return " ".join(words).strip(" .,;:")


def extract_numbers(text, lang):
    t = norm_space(text)
    t = re.sub(r"\b[^\W\d_]{1,5}[’'](?=\w)", " ", t)
    vals = set()
    for m in NUMBER_RE.finditer(t):
        raw = re.sub(r"[ '’   ]", "", m.group(0)).replace(",", ".")
        try:
            vals.add(float(raw))
        except ValueError:
            pass
    words = NUM_WORDS.get(lang, {})
    for tok in re.findall(r"[^\W\d_]+", t.casefold()):
        if tok in words:
            vals.add(float(words[tok]))
        elif lang == "de":
            for p in DE_COMPOUND_PREFIX:
                if tok.startswith(p) and tok[len(p) :].startswith(DE_COMPOUND_SUFFIX):
                    vals.add(float(words[p]))
    return vals


def detect_lang(text, expected=None):
    toks = re.findall(
        r"[^\W\d_]+", (text or "").casefold().replace("’", " ").replace("'", " ")
    )
    scores = {lang: sum(1 for t in toks if t in sw) for lang, sw in STOPWORDS.items()}
    top = max(scores.values())
    if top == 0:
        return None, scores
    best = [lang for lang, v in scores.items() if v == top]
    return (expected if expected in best else best[0]), scores


def stem_tokens_match(answer_core, evidence_norm):
    toks = [t for t in re.findall(r"[^\W_]+", answer_core) if len(t) >= 4]
    if not toks:
        return False
    ev_toks = re.findall(r"[^\W_]+", evidence_norm)
    return all(
        any(e.startswith(t[: max(4, len(t) - 3)]) for e in ev_toks) for t in toks
    )


def safe_eval(expr):
    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -ev(node.operand)
        if isinstance(node, ast.BinOp) and isinstance(
            node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)
        ):
            a, b = ev(node.left), ev(node.right)
            return {
                ast.Add: a + b,
                ast.Sub: a - b,
                ast.Mult: a * b,
                ast.Div: a / b if b else float("nan"),
            }[type(node.op)]
        raise ValueError("unsupported expression")

    return ev(ast.parse(expr, mode="eval"))


def check_calc(r, lang, src, issues):
    rid = r["id"]
    calc = r.get("calc") or {}
    formula = calc.get("formula")
    inputs = calc.get("inputs") or []
    evidences = r.get("calc_evidence") or []
    an = r.get("answer_normalized") or {}
    if (
        not formula
        or not inputs
        or len(evidences) != len(inputs)
        or not isinstance(an.get("value"), (int, float))
    ):
        issues.add(
            "ERROR",
            "calc.format",
            rid,
            "calc needs formula, inputs, calc_evidence (same length) and answer_normalized",
        )
        return
    try:
        result = safe_eval(formula)
    except (ValueError, SyntaxError):
        issues.add(
            "ERROR", "calc.formula", rid, f"Formula cannot be evaluated: {formula!r}"
        )
        return
    if abs(result - float(an["value"])) > 0.005:
        issues.add(
            "ERROR",
            "calc.result",
            rid,
            f"Formula yields {result}, answer_normalized is {an['value']}",
        )
    if float(an["value"]) not in extract_numbers(r.get("answer"), lang):
        issues.add(
            "ERROR",
            "answer.number_mismatch",
            rid,
            f"Result {an['value']} not in the answer",
        )
    allowed = {100.0} | extract_numbers(r.get("question"), lang)
    for inp, evid in zip(inputs, evidences):
        art = src.article(inp.get("act"), inp.get("article_id"), lang, "current")
        para = next(
            (
                p
                for p in (art or {}).get("paragraphs", [])
                if p["paragraph"] == (inp.get("paragraph") or "")
            ),
            None,
        )
        if not para or norm_text(evid) not in norm_text(para["text"]):
            issues.add(
                "ERROR",
                "calc.input_evidence",
                rid,
                f"Evidence for input value {inp.get('value')} is not in {inp.get('act')} {inp.get('article_id')} para. {inp.get('paragraph')}",
            )
        elif float(inp.get("value")) not in extract_numbers(evid, lang):
            issues.add(
                "ERROR",
                "calc.input_value",
                rid,
                f"Input value {inp.get('value')} not in its evidence",
            )
        allowed.add(float(inp.get("value")))
    for num in re.findall(r"\d+(?:\.\d+)?", formula):
        x = float(num)
        if x not in allowed and x * 100 not in allowed:
            issues.add(
                "ERROR",
                "calc.unanchored_number",
                rid,
                f"Number {num} of the formula is in neither the question nor the evidence",
            )


class Sources:
    def __init__(self, root):
        self.root = Path(root)
        self.manifest = json.loads(
            (self.root / "manifest.json").read_text(encoding="utf-8")
        )
        self.acts = {a["abbr"]: a for a in self.manifest["acts"]}
        self._cache = {}

    def article(self, act, article_id, lang, role):
        key = (act, lang, role)
        if key not in self._cache:
            a = self.acts.get(act)
            v = (
                next((v for v in a["versions"] if v["role"] == role), None)
                if a
                else None
            )
            if not v or lang not in v["files"]:
                self._cache[key] = {}
            else:
                d = json.loads(
                    (self.root / v["files"][lang]["path"]).read_text(encoding="utf-8")
                )
                self._cache[key] = {x["article_id"]: x for x in d["articles"]}
        return self._cache[key].get(article_id)

    def article_at(self, act, article_id, lang, version_date):
        """Article in the stored version with this date (any role); None if not stored."""
        a = self.acts.get(act)
        if not a or not version_date:
            return None
        v = next((v for v in a["versions"] if v["version_date"] == version_date), None)
        if not v or lang not in v["files"]:
            return None
        key = (act, lang, "v" + version_date)
        if key not in self._cache:
            d = json.loads((self.root / v["files"][lang]["path"]).read_text(encoding="utf-8"))
            self._cache[key] = {x["article_id"]: x for x in d["articles"]}
        return self._cache[key].get(article_id)

    def earlier_articles(self, act, article_id, lang):
        """(version_date, article) for every stored version older than the current one."""
        a = self.acts.get(act)
        if not a:
            return []
        cur = next((v for v in a["versions"] if v["role"] == "current"), None)
        out = []
        for v in a["versions"]:
            if v["role"] not in {"previous", "intermediate"} or lang not in v["files"]:
                continue
            if cur and v["version_date"] >= cur["version_date"]:
                continue
            key = (act, lang, "v" + v["version_date"])
            if key not in self._cache:
                d = json.loads(
                    (self.root / v["files"][lang]["path"]).read_text(encoding="utf-8")
                )
                self._cache[key] = {x["article_id"]: x for x in d["articles"]}
            art = self._cache[key].get(article_id)
            if art:
                out.append((v["version_date"], art))
        return out


class Issues:
    def __init__(self):
        self.items = []

    def add(self, level, code, rec_id, msg):
        self.items.append({"level": level, "code": code, "id": rec_id, "msg": msg})


def content_words(text, lang):
    return {
        w
        for w in re.findall(r"[^\W\d_]{4,}", norm_text(text))
        if w not in CONTENT_STOP.get(lang, set())
    }


def check_leaks(r, lang, q, a, issues):
    """Questions that give the answer away (number, words) and threshold words lost in the answer."""
    rid = r.get("id")
    qt, at = r.get("question_type"), r.get("answer_type")
    if qt in ("yes_no", "false_premise", "calc") or at == "yes_no":
        return
    an = r.get("answer_normalized")
    if isinstance(an, dict) and isinstance(an.get("value"), (int, float)):
        if float(an["value"]) in extract_numbers(q, lang) and an["value"] not in (0, 1):
            issues.add(
                "WARN",
                "question.contains_answer_number",
                rid,
                f"The number of the answer ({an['value']:g}) appears in the question",
            )
    aw = content_words(r.get("answer_core") or a, lang) if at == "text" else set()
    if aw and len(aw & content_words(q, lang)) / len(aw) >= 0.6:
        issues.add(
            "WARN",
            "question.answer_overlap",
            rid,
            f"Answer words appear in the question: {sorted(aw & content_words(q, lang))}",
        )
    ev = norm_text((r.get("source") or {}).get("evidence") or "")
    variants = [norm_text(x) for x in [a, *(r.get("answer_aliases") or [])]]
    for w in THRESHOLD_WORDS.get(lang, []):
        if w in ev and not any(w in v for v in variants) and w not in norm_text(q):
            issues.add(
                "WARN",
                "answer.threshold_word",
                rid,
                f"Evidence contains {w.strip()!r}, question and answer do not: check the threshold",
            )
            break


def check_record(r, src, issues, seen_ids):
    rid = r.get("id", "<no id>")
    for f in REQUIRED:
        if f not in r:
            issues.add("ERROR", "format.missing_field", rid, f"Missing field: {f}")
    if rid in seen_ids:
        issues.add("ERROR", "format.duplicate_id", rid, "Duplicate ID")
    seen_ids.add(rid)
    lang = LANGS.get(r.get("lang"))
    if not lang:
        issues.add("ERROR", "format.lang", rid, f"Unknown language: {r.get('lang')}")
        return
    if not rid.endswith("-" + lang) or not rid.startswith(str(r.get("core_id"))):
        issues.add(
            "ERROR", "format.id_pattern", rid, "ID does not match core_id/language"
        )
    for field, allowed in [
        ("question_type", QUESTION_TYPES),
        ("domain", DOMAINS),
        ("answer_type", ANSWER_TYPES),
        ("author", AUTHORS),
    ]:
        if r.get(field) not in allowed:
            issues.add(
                "ERROR",
                f"format.{field}",
                rid,
                f"Invalid value {field}={r.get(field)!r}",
            )
    if r.get("register") not in {"lay", "professional"}:
        issues.add(
            "ERROR",
            "format.register",
            rid,
            f"Invalid register={r.get('register')!r}",
        )
    if r.get("difficulty_prior") not in {1, 2, 3}:
        issues.add(
            "ERROR", "format.difficulty", rid, "difficulty_prior must be 1, 2 or 3"
        )
    if FROZEN["value"]:
        ok = (r.get("status"), r.get("needs_human_review")) in (
            ("reviewed", False),
            ("auto_verified", True),
        )
        if not ok:
            issues.add(
                "ERROR",
                "format.status",
                rid,
                "in the freeze: status reviewed + needs_human_review false (human) "
                "or auto_verified + needs_human_review true (automatically checked only)",
            )
    elif r.get("status") != "draft" or r.get("needs_human_review") is not True:
        issues.add(
            "ERROR",
            "format.status",
            rid,
            "status must be draft and needs_human_review true",
        )
    if r.get("author") == "human" and not (r.get("authoring") or {}).get("attested_by"):
        issues.add(
            "ERROR",
            "format.human_unattested",
            rid,
            "author human without authoring.attested_by (who wrote the item by hand?)",
        )
    if r.get("generator") != r.get("author"):
        issues.add("ERROR", "format.generator", rid, "generator and author differ")
    if r.get("as_of") != "2026-10-01":
        issues.add("ERROR", "format.as_of", rid, "as_of is not 2026-10-01")
    q = r.get("question") or ""
    a = r.get("answer") or ""
    if not q.strip().endswith("?"):
        issues.add("WARN", "style.question_mark", rid, "Question does not end with '?'")
    if len(a) > (220 if r.get("question_type") == "false_premise" else 120):
        issues.add("WARN", "style.long_answer", rid, f"Answer is long ({len(a)} characters)")
    if lang == "de" and ("ß" in q or "ß" in a):
        issues.add("ERROR", "style.eszett", rid, "de-CH item contains ß")
    if re.search(r"\b(Art\.|Artikel|article|articolo)\s*\d", q, re.I):
        issues.add(
            "WARN", "style.article_in_question", rid, "Question names an article number"
        )
    check_leaks(r, lang, q, a, issues)
    for name, pat in PII_PATTERNS.items():
        if pat.search(q) or pat.search(a):
            issues.add("ERROR", f"pii.{name}", rid, f"Possible personal data ({name})")

    detected, scores = detect_lang(q, lang)
    if detected and detected != lang:
        issues.add(
            "ERROR",
            "lang.question",
            rid,
            f"Question looks like '{detected}', expected '{lang}' {scores}",
        )

    s = r.get("source") or {}
    for f in SOURCE_REQUIRED:
        if f not in s:
            issues.add("ERROR", "format.source_field", rid, f"source.{f} missing")
    art = src.article(s.get("act"), s.get("article_id"), lang, "current")
    if not art:
        issues.add(
            "ERROR",
            "source.article_missing",
            rid,
            f"Article {s.get('act')} {s.get('article_id')} ({lang}) not found",
        )
        return
    if f"/{lang}" not in (s.get("eli_url") or ""):
        issues.add(
            "ERROR", "source.eli_lang", rid, "ELI URL is not in the item's language"
        )
    para = next(
        (p for p in art["paragraphs"] if p["paragraph"] == (s.get("paragraph") or "")),
        None,
    )
    ev = s.get("evidence") or ""
    ev_n = norm_text(ev)
    if not ev.strip():
        issues.add("ERROR", "evidence.missing", rid, "evidence missing")
    elif para and ev_n in norm_text(para["text"]):
        pass
    elif ev_n in norm_text(art["text"]):
        issues.add(
            "WARN",
            "evidence.other_paragraph",
            rid,
            f"Evidence is in the article, but not in para. {s.get('paragraph')!r}",
        )
    else:
        issues.add(
            "ERROR",
            "evidence.not_in_article",
            rid,
            "Evidence is not verbatim in the cited article",
        )
    if not para:
        issues.add(
            "ERROR",
            "source.paragraph_missing",
            rid,
            f"Paragraph {s.get('paragraph')!r} does not exist",
        )
    elif norm_space(s.get("quote")) != norm_space(para["text"]):
        issues.add(
            "ERROR",
            "source.quote_mismatch",
            rid,
            "source.quote does not match the paragraph text",
        )
    if "'" in ev and "’" in (para or {}).get("text", ""):
        issues.add(
            "WARN",
            "evidence.apostrophe",
            rid,
            "Evidence uses ' instead of ’ (found only after normalisation)",
        )

    qt = r.get("question_type")
    at = r.get("answer_type")
    an = r.get("answer_normalized")
    if qt == "calc":
        check_calc(r, lang, src, issues)
    elif qt == "false_premise" and not r.get("answer_core"):
        issues.add(
            "ERROR",
            "answer.false_premise_core",
            rid,
            "false_premise without answer_core (verbatim correction from the statute)",
        )
    elif r.get("answer_core"):
        if strip_leading(norm_text(r["answer_core"]), lang) not in ev_n:
            issues.add(
                "ERROR",
                "answer.not_in_evidence",
                rid,
                f"answer_core {r['answer_core']!r} is not verbatim in the evidence",
            )
        if norm_text(r["answer_core"]) not in norm_text(a):
            issues.add(
                "ERROR",
                "answer.core_not_in_answer",
                rid,
                "answer_core is not part of the answer",
            )
    elif at == "yes_no" or qt == "yes_no":
        if norm_text(a) not in YES_NO[lang]:
            issues.add(
                "ERROR",
                "answer.yes_no",
                rid,
                f"Yes/no answer expected, got {a!r}",
            )
    elif an is not None:
        v = an.get("value") if isinstance(an, dict) else None
        if not isinstance(v, (int, float)):
            issues.add(
                "ERROR",
                "answer.normalized_format",
                rid,
                "answer_normalized.value is not a number",
            )
        else:
            literal = strip_leading(norm_text(a), lang) in ev_n
            in_answer = float(v) in extract_numbers(a, lang)
            in_evidence = float(v) in extract_numbers(ev, lang)
            if in_answer and in_evidence:
                pass
            elif literal:
                issues.add(
                    "WARN",
                    "answer.number_literal_only",
                    rid,
                    f"Number {v} not recognised as digit/number word, but answer {a!r} is verbatim in the evidence",
                )
            elif not in_answer:
                issues.add(
                    "ERROR",
                    "answer.number_mismatch",
                    rid,
                    f"Number {v} not in the answer {a!r}",
                )
            else:
                issues.add(
                    "ERROR",
                    "answer.not_in_evidence",
                    rid,
                    f"Number {v} is not in the evidence",
                )
    else:
        if at in {"currency_chf", "percent", "age"}:
            issues.add(
                "WARN",
                "answer.normalized_missing",
                rid,
                f"answer_type={at} without answer_normalized",
            )
        core = strip_leading(norm_text(a), lang)
        if core and core in ev_n:
            pass
        elif any(
            strip_leading(norm_text(x), lang) in ev_n
            for x in r.get("answer_aliases") or []
            if x
        ):
            issues.add(
                "WARN",
                "answer.alias_only",
                rid,
                f"Answer {a!r} not verbatim, but an alias is",
            )
        elif stem_tokens_match(core, ev_n):
            issues.add(
                "WARN",
                "answer.inflected",
                rid,
                f"Answer {a!r} appears in the evidence only inflected/reordered",
            )
        else:
            issues.add(
                "ERROR",
                "answer.not_in_evidence",
                rid,
                f"Answer {a!r} is not verbatim in the evidence",
            )

    t = r.get("temporal") or {}
    if t.get("bucket") not in {"stable_pre2024", "changed_2024_2025", "changed_2026"}:
        issues.add("ERROR", "temporal.bucket", rid, "temporal.bucket missing/invalid")
    if qt == "temporal":
        if not r.get("outdated_answers"):
            issues.add(
                "ERROR",
                "temporal.no_outdated",
                rid,
                "temporal item without outdated answer",
            )
        if t.get("bucket") == "stable_pre2024":
            issues.add(
                "ERROR",
                "temporal.not_changed",
                rid,
                "Article unchanged since 2024, but type temporal",
            )
        prev_art = src.article_at(
            s.get("act"), s.get("article_id"), lang, t.get("previous_version_date")
        ) or src.article(s.get("act"), s.get("article_id"), lang, "previous")
        pev = t.get("previous_evidence") or ""
        for ov in t.get("outdated_versions") or []:
            ov_art = src.article_at(s.get("act"), s.get("article_id"), lang, ov.get("version_date"))
            if not ov_art or norm_text(ov.get("evidence") or "") not in norm_text(ov_art["text"]):
                issues.add(
                    "ERROR",
                    "temporal.version_evidence",
                    rid,
                    f"Evidence of the outdated answer {ov.get('outdated_answer')!r} is not in the version {ov.get('version_date')}",
                )
        if not prev_art:
            issues.add(
                "ERROR",
                "temporal.prev_missing",
                rid,
                "Previous version of the article not found",
            )
        elif not pev or norm_text(pev) not in norm_text(prev_art["text"]):
            issues.add(
                "ERROR",
                "temporal.prev_evidence",
                rid,
                "Evidence of the outdated answer is not in the previous version",
            )
        elif an and isinstance(an.get("value"), (int, float)):
            old_vals = set()
            for o in r.get("outdated_answers") or []:
                old_vals |= extract_numbers(o, lang)
            if float(an["value"]) in old_vals and len(old_vals) == 1:
                issues.add(
                    "ERROR",
                    "temporal.same_value",
                    rid,
                    "Outdated answer has the same value as the current one",
                )
            if old_vals and not (old_vals & extract_numbers(pev, lang)):
                issues.add(
                    "ERROR",
                    "temporal.outdated_not_in_prev",
                    rid,
                    "Number of the outdated answer not in the evidence of the previous version",
                )
    if r.get("outdated_answers") and art:
        ev_raw = norm_text(s.get("evidence") or "")
        earlier = src.earlier_articles(s.get("act"), s.get("article_id"), lang)
        if earlier and ev_raw and all(ev_raw in norm_text(a_old["text"]) for _, a_old in earlier):
            issues.add(
                "WARN",
                "temporal.evidence_unchanged",
                rid,
                "outdated answer given, but the evidence sentence is unchanged in all earlier versions",
            )
    quote = s.get("quote") or ""
    if DISCRETION.search(quote) and qt != "yes_no":
        issues.add(
            "WARN",
            "source.discretion",
            rid,
            "Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary",
        )
    outdated_norm = {norm_text(o) for o in (r.get("outdated_answers") or []) if o}
    near_miss_norm = {norm_text(m) for m in (r.get("near_miss_answers") or []) if m}
    overlap = outdated_norm & near_miss_norm
    if overlap:
        issues.add(
            "ERROR",
            "overlap.outdated_near_miss",
            rid,
            f"Outdated answer and near-miss overlap: {overlap}",
        )
    cur_nums = extract_numbers(art["text"], lang)
    if an and isinstance(an.get("value"), (int, float)):
        cur_nums.add(float(an["value"]))
    earlier = src.earlier_articles(s.get("act"), s.get("article_id"), lang)
    for m in r.get("near_miss_answers") or []:
        for n in sorted(extract_numbers(m, lang) - cur_nums):
            hits = [d for d, a_old in earlier if n in extract_numbers(a_old["text"], lang)]
            if hits:
                issues.add(
                    "ERROR",
                    "near_miss.earlier_version",
                    rid,
                    f"Near-miss {m!r}: value {n:g} is in the version of {hits[0]}, not in the current one; belongs in outdated_answers",
                )
    if qt != "yes_no" and at != "yes_no":
        aliases = r.get("answer_aliases") or []
        if not aliases and not near_miss_norm and not outdated_norm:
            issues.add(
                "WARN",
                "answer.no_variations",
                rid,
                "Neither answer_aliases nor near_miss/outdated given",
            )
    if r.get("future_change"):
        issues.add(
            "WARN",
            "source.future_change",
            rid,
            f"Article changes after the as-of date: {', '.join(r['future_change'])}",
        )


def cross_checks(records, issues):
    by_core = defaultdict(list)
    for r in records:
        by_core[r.get("core_id")].append(r)
    for core, rs in by_core.items():
        keys = {
            (
                r.get("question_type"),
                json.dumps(r.get("answer_normalized"), sort_keys=True),
                (r.get("source") or {}).get("article_id"),
                (r.get("source") or {}).get("paragraph"),
                r.get("author"),
            )
            for r in rs
        }
        if len(keys) > 1:
            issues.add(
                "ERROR",
                "lang.core_inconsistent",
                core,
                "Language versions of a core differ in type/value/source",
            )
        if not any(r.get("lang") == "de-CH" for r in rs):
            issues.add("ERROR", "lang.no_de", core, "Core without German version")
        yn = {
            LANGS.get(r.get("lang")): norm_text(r.get("answer"))
            for r in rs
            if r.get("question_type") == "yes_no"
        }
        if yn:
            polarity = {
                ("ja" if v in {"ja", "oui", "sì", "si"} else "nein")
                for v in yn.values()
            }
            if len(polarity) > 1:
                issues.add(
                    "ERROR",
                    "lang.yes_no_inconsistent",
                    core,
                    f"Yes/no differs between languages: {yn}",
                )

    de = [r for r in records if r.get("lang") == "de-CH"]
    seen_q = {}
    for r in de:
        nq = norm_text(r.get("question"))
        if nq in seen_q:
            issues.add(
                "ERROR",
                "dup.exact_question",
                r["id"],
                f"Same question as {seen_q[nq]}",
            )
        seen_q[nq] = r["id"]
    qs = [(r["id"], norm_text(r.get("question"))) for r in de]
    for i in range(len(qs)):
        for j in range(i + 1, len(qs)):
            ratio = difflib.SequenceMatcher(None, qs[i][1], qs[j][1]).ratio()
            if 0.85 <= ratio < 1:
                issues.add(
                    "WARN",
                    "dup.near_question",
                    qs[i][0],
                    f"Very similar to {qs[j][0]} (ratio {ratio:.2f})",
                )
    facts = defaultdict(list)
    for r in de:
        s = r.get("source") or {}
        an = r.get("answer_normalized")
        val = (
            an.get("value")
            if isinstance(an, dict)
            else strip_leading(norm_text(r.get("answer")), "de")
        )
        if r.get("question_type") == "yes_no":
            val = norm_text(s.get("evidence"))
        facts[(s.get("act"), s.get("article_id"), s.get("paragraph"), str(val))].append(
            r["id"]
        )
    for key, ids in facts.items():
        if len(ids) > 1:
            issues.add(
                "WARN",
                "dup.same_fact",
                ids[0],
                f"Same fact ({key[0]} {key[1]} para. {key[2]}, value {key[3]}) also in: {', '.join(ids[1:])}",
            )


def table(counter, total=None, header=("Value", "Count")):
    lines = [
        f"| {header[0]} | {header[1]} |" + (" Share |" if total else ""),
        "| --- | ---: |" + (" ---: |" if total else ""),
    ]
    for k, v in sorted(counter.items(), key=lambda x: (-x[1], str(x[0]))):
        lines.append(f"| {k} | {v} |" + (f" {v / total:.0%} |" if total else ""))
    return "\n".join(lines)


def cross_table(records, row_key, col_key, cols):
    c = defaultdict(Counter)
    for r in records:
        c[row_key(r)][col_key(r)] += 1
    lines = [
        "| | " + " | ".join(cols) + " | Total |",
        "| --- |" + " ---: |" * (len(cols) + 1),
    ]
    for row in sorted(c):
        lines.append(
            f"| {row} | "
            + " | ".join(str(c[row][x]) for x in cols)
            + f" | {sum(c[row].values())} |"
        )
    return "\n".join(lines)


WARN_LEGEND = {
    "source.future_change": "a later version of the paragraph is already published after 1 October 2026 (the as-of date)",
    "source.discretion": "the paragraph mentions Bundesrat/Departement/Reglement/Kanton, so the value may be discretionary; check it",
    "answer.threshold_word": "the evidence contains a threshold word (e.g. 'at least', 'more than') that is missing from question and answer; check the threshold",
    "answer.inflected": "the answer appears in the evidence only inflected or reordered, not verbatim",
    "answer.alias_only": "the answer is not verbatim in the evidence, but one of its aliases is",
    "answer.number_literal_only": "the number was not recognised as digit or number word, but the answer is verbatim in the evidence",
    "answer.normalized_missing": "answer_type is currency_chf/percent/age but answer_normalized is missing",
    "answer.no_variations": "neither answer_aliases nor near_miss/outdated answers are given",
    "evidence.apostrophe": "the evidence uses ' where the paragraph has the typographic apostrophe ’ (found only after normalisation)",
    "evidence.other_paragraph": "the evidence is in the cited article, but not in the cited paragraph",
    "question.answer_overlap": "most content words of the answer already appear in the question",
    "question.contains_answer_number": "the number of the answer already appears in the question",
    "style.long_answer": "the answer is longer than the length limit",
    "style.question_mark": "the question does not end with a question mark",
    "style.article_in_question": "the question names an article number",
    "temporal.evidence_unchanged": "an outdated answer is given, but the evidence sentence is unchanged in all earlier versions",
    "dup.near_question": "two DE questions are very similar (ratio 0.85 or higher)",
    "dup.same_fact": "several DE items cover the same fact (same paragraph and value)",
    "review.hint": "note from a manual spot check",
}


def write_report(
    path, records, issues, inputs, target_total, min_parallel, min_human_share
):
    de = [r for r in records if r.get("lang") == "de-CH"]
    cores = {r["core_id"] for r in records}
    by_core_langs = defaultdict(set)
    for r in records:
        by_core_langs[r["core_id"]].add(LANGS.get(r.get("lang")))
    parallel = sum(1 for langs in by_core_langs.values() if {"de", "fr", "it"} <= langs)
    errors = [i for i in issues.items if i["level"] == "ERROR"]
    warns = [i for i in issues.items if i["level"] == "WARN"]
    err_ids = {i["id"] for i in errors}
    authors = sorted({r.get("author") for r in records})
    out = []
    out.append("# Validation report\n")
    out.append(
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')} with `validate_items.py`  "
    )
    out.append("Inputs: " + ", ".join(f"`{Path(p).name}`" for p in inputs) + "\n")
    out.append("## Summary\n")
    out.append(
        f"- Core items (DE): **{len(de)}** of target {target_total}; rows in total (all languages): **{len(records)}**"
    )
    out.append(
        f"- Cores with DE+FR+IT: **{parallel}** (minimum {min_parallel}) → {'met' if parallel >= min_parallel else 'NOT met'}"
    )
    out.append(
        f"- Errors (ERROR): **{len(errors)}** in {len(err_ids)} rows/cores; warnings (WARN): **{len(warns)}**"
    )
    out.append(
        f"- Rows without errors: **{sum(1 for r in records if r['id'] not in err_ids and r['core_id'] not in err_ids)}** of {len(records)}\n"
    )
    out.append("## Checks\n")
    out.append("| Check | What exactly |\n| --- | --- |")
    out.append(
        "| Format | required fields, allowed values, ID pattern, `status`, `needs_human_review`, generator fields, `as_of` |"
    )
    out.append(
        "| Evidence | `source.evidence` appears verbatim (whitespace normalised) in the cited paragraph of the as-of-date version, in the item's language; `source.quote` = paragraph text |"
    )
    out.append(
        "| Answer in the article | Numbers: `answer_normalized.value` appears in answer and evidence (digits, thousands spaces, decimal comma, number words DE/FR/IT); text: answer (without leading articles/prepositions) appears verbatim in the evidence; yes/no: allowed form |"
    )
    out.append(
        "| Outdated (`temporal`) | article changed since 2024; outdated answer present; its evidence appears verbatim in the previous version; old value ≠ new value |"
    )
    out.append(
        "| Near-miss vs. earlier versions | a near-miss number appears in a stored earlier version of the article but not in the current one → error (belongs in `outdated_answers`) |"
    )
    out.append(
        "| Duplicates | identical DE question (error), similar DE questions from ratio 0.85 (warning), same fact = same paragraph + same value (warning) |"
    )
    out.append(
        "| Language consistency | language of the question (stop words), same type/value/paragraph per core, yes/no identical in all languages, ELI URL in the item's language |"
    )
    out.append(
        "| Style/PII | no ß in de-CH, no article number in the question, question mark, AHV number/IBAN/phone/email |"
    )
    out.append(
        "| As-of date | note if a version after 1 October 2026 is already published for the article |\n"
    )
    out.append("## Errors and warnings by check\n")
    out.append(
        table(
            Counter(f"{i['level']} {i['code']}" for i in issues.items),
            header=("Check", "Count"),
        )
        + "\n"
    )
    warn_codes = sorted({i["code"] for i in warns})
    if warn_codes:
        out.append("Warnings that occur:\n")
        for code in warn_codes:
            out.append(f"- `{code}`: {WARN_LEGEND.get(code, 'see the findings table below')}")
        out.append("")
    out.append("## Distribution (DE cores)\n")
    out.append("### Author × statute\n")
    acts = sorted({(r.get("source") or {}).get("act") for r in de})
    out.append(
        cross_table(
            de,
            lambda r: r.get("author"),
            lambda r: (r.get("source") or {}).get("act"),
            acts,
        )
        + "\n"
    )
    out.append("### Author × question type\n")
    qts = sorted({r.get("question_type") for r in de})
    out.append(
        cross_table(
            de, lambda r: r.get("author"), lambda r: r.get("question_type"), qts
        )
        + "\n"
    )
    out.append("### Domain (`domain`)\n")
    out.append(table(Counter(r.get("domain") for r in de), len(de)) + "\n")
    out.append("### Register and difficulty\n")
    out.append(
        table(
            Counter(
                f"{r.get('register')} / level {r.get('difficulty_prior')}" for r in de
            ),
            len(de),
        )
        + "\n"
    )
    out.append("### As-of-date group (article level)\n")
    out.append(
        table(Counter((r.get("temporal") or {}).get("bucket") for r in de), len(de))
        + "\n"
    )
    out.append("### Languages (all rows)\n")
    out.append(
        cross_table(
            records,
            lambda r: r.get("author"),
            lambda r: r.get("lang"),
            ["de-CH", "fr-CH", "it-CH"],
        )
        + "\n"
    )
    out.append("## All findings\n")
    if not issues.items:
        out.append("None.\n")
    else:
        out.append("| Level | Check | ID | Finding |\n| --- | --- | --- | --- |")
        for i in sorted(
            issues.items, key=lambda x: (x["level"] != "ERROR", x["code"], x["id"])
        ):
            out.append(
                f"| {i['level']} | {i['code']} | {i['id']} | {i['msg'].replace('|', '/')} |"
            )
    Path(path).write_text("\n".join(out) + "\n", encoding="utf-8")


def write_review_queue(path, records, issues):
    by_id = defaultdict(list)
    for i in issues.items:
        by_id[i["id"]].append(i)

    def prio(r):
        own = by_id.get(r["id"], []) + by_id.get(r["core_id"], [])
        if any(i["level"] == "ERROR" or i["code"] == "review.hint" for i in own):
            return 0
        if r.get("question_type") == "temporal" or r.get("future_change"):
            return 1
        if own:
            return 2
        return 3

    labels = {
        0: "A – check error or concrete note from the visual review; edit or discard first",
        1: "B – outdated items and articles with an already published future version",
        2: "C – warnings (suspected duplicate, style)",
        3: "D – no findings, normal visual review",
    }
    out = [
        "# Review queue, cut-off date (drafts)\n",
        "Each row is a draft with `needs_human_review: true`. Decide per item: **accept**, **edit** or **discard**, and record the result in `review_decision`.\n",
        "Questions per item: (1) Is the answer really stated in the linked paragraph? (2) Is there exactly one defensible short answer? (3) Is the question understandable and practical without the article? (4) Do FR/IT match DE in content? (5) For `temporal`: is the outdated answer the rule before 2024/2025?\n",
    ]
    groups = defaultdict(list)
    for r in records:
        if r.get("lang") != "de-CH":
            continue
        groups[prio(r)].append(r)
    for p in sorted(groups):
        out.append(f"## {labels[p]} ({len(groups[p])})\n")
        out.append(
            "| ID | Author | Act | Type | Question | Answer | Source | Findings |\n| --- | --- | --- | --- | --- | --- | --- | --- |"
        )
        for r in sorted(groups[p], key=lambda x: x["id"]):
            s = r.get("source") or {}
            own = by_id.get(r["id"], []) + by_id.get(r["core_id"], [])
            for lang in ("fr", "it"):
                own += by_id.get(f"{r['core_id']}-{lang}", [])
            notes = (
                "; ".join(
                    sorted(
                        {
                            f"{i['level']} {i['code']}"
                            + (f": {i['msg']}" if i["code"] == "review.hint" else "")
                            for i in own
                        }
                    )
                )
                or "–"
            )
            if r.get("question_type") == "temporal":
                notes += f"; veraltet: {', '.join(r.get('outdated_answers') or [])}"
            out.append(
                f"| {r['id']} | {r.get('author')} | {s.get('act')} Art. {s.get('article')} Abs. {s.get('paragraph') or '–'} | {r.get('question_type')} | {r.get('question', '').replace('|', '/')} | {r.get('answer', '').replace('|', '/')} | [Link]({s.get('article_url')}) | {notes.replace('|', '/')} |"
            )
        out.append("")
    Path(path).write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--fedlex",
        required=True,
        help="folder with manifest.json and article JSON files",
    )
    ap.add_argument("--report", required=True)
    ap.add_argument("--review-queue")
    ap.add_argument("--issues-json")
    ap.add_argument(
        "--hints",
        help="JSON {item id: note} from a manual spot check; reported as WARN review.hint",
    )
    ap.add_argument("--target-total", type=int, default=300)
    ap.add_argument("--min-parallel", type=int, default=150)
    ap.add_argument("--min-human-share", type=float, default=0.30)
    ap.add_argument(
        "--frozen",
        action="store_true",
        help="frozen release: rows must be status reviewed and needs_human_review false",
    )
    ap.add_argument("inputs", nargs="+")
    args = ap.parse_args()
    FROZEN["value"] = args.frozen
    src = Sources(args.fedlex)
    records = []
    issues = Issues()
    for p in args.inputs:
        for n, line in enumerate(Path(p).read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                issues.add("ERROR", "format.json", f"{Path(p).name}:{n}", str(e))
    seen = set()
    for r in records:
        check_record(r, src, issues, seen)
    cross_checks(records, issues)
    if args.hints:
        for rid, note in json.loads(
            Path(args.hints).read_text(encoding="utf-8")
        ).items():
            issues.add("WARN", "review.hint", rid, note)
    write_report(
        args.report,
        records,
        issues,
        args.inputs,
        args.target_total,
        args.min_parallel,
        args.min_human_share,
    )
    if args.review_queue:
        write_review_queue(args.review_queue, records, issues)
    if args.issues_json:
        Path(args.issues_json).write_text(
            json.dumps(issues.items, ensure_ascii=False, indent=1), encoding="utf-8"
        )
    n_err = sum(1 for i in issues.items if i["level"] == "ERROR")
    n_warn = len(issues.items) - n_err
    print(f"{len(records)} records, {n_err} errors, {n_warn} warnings")
    sys.exit(1 if n_err else 0)


if __name__ == "__main__":
    main()
