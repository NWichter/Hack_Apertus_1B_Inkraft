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
AUTHORS = {"claude", "codex", "gemini", "human"}
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
            "calc braucht formula, inputs, calc_evidence (gleiche Länge) und answer_normalized",
        )
        return
    try:
        result = safe_eval(formula)
    except (ValueError, SyntaxError):
        issues.add(
            "ERROR", "calc.formula", rid, f"Formel nicht auswertbar: {formula!r}"
        )
        return
    if abs(result - float(an["value"])) > 0.005:
        issues.add(
            "ERROR",
            "calc.result",
            rid,
            f"Formel ergibt {result}, answer_normalized ist {an['value']}",
        )
    if float(an["value"]) not in extract_numbers(r.get("answer"), lang):
        issues.add(
            "ERROR",
            "answer.number_mismatch",
            rid,
            f"Ergebnis {an['value']} nicht in der Antwort",
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
                f"Evidenz für Eingangswert {inp.get('value')} steht nicht in {inp.get('act')} {inp.get('article_id')} Abs. {inp.get('paragraph')}",
            )
        elif float(inp.get("value")) not in extract_numbers(evid, lang):
            issues.add(
                "ERROR",
                "calc.input_value",
                rid,
                f"Eingangswert {inp.get('value')} nicht in seiner Evidenz",
            )
        allowed.add(float(inp.get("value")))
    for num in re.findall(r"\d+(?:\.\d+)?", formula):
        x = float(num)
        if x not in allowed and x * 100 not in allowed:
            issues.add(
                "ERROR",
                "calc.unanchored_number",
                rid,
                f"Zahl {num} der Formel steht weder in Frage noch in Evidenz",
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


def check_record(r, src, issues, seen_ids):
    rid = r.get("id", "<no id>")
    for f in REQUIRED:
        if f not in r:
            issues.add("ERROR", "format.missing_field", rid, f"Feld fehlt: {f}")
    if rid in seen_ids:
        issues.add("ERROR", "format.duplicate_id", rid, "ID doppelt")
    seen_ids.add(rid)
    lang = LANGS.get(r.get("lang"))
    if not lang:
        issues.add("ERROR", "format.lang", rid, f"Unbekannte Sprache: {r.get('lang')}")
        return
    if not rid.endswith("-" + lang) or not rid.startswith(str(r.get("core_id"))):
        issues.add(
            "ERROR", "format.id_pattern", rid, "ID passt nicht zu core_id/Sprache"
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
                f"Ungültiger Wert {field}={r.get(field)!r}",
            )
    if r.get("register") not in {"lay", "professional"}:
        issues.add(
            "ERROR",
            "format.register",
            rid,
            f"Ungültiges register={r.get('register')!r}",
        )
    if r.get("difficulty_prior") not in {1, 2, 3}:
        issues.add(
            "ERROR", "format.difficulty", rid, "difficulty_prior muss 1, 2 oder 3 sein"
        )
    if r.get("status") != "draft" or r.get("needs_human_review") is not True:
        issues.add(
            "ERROR",
            "format.status",
            rid,
            "status muss draft und needs_human_review true sein",
        )
    if r.get("author") == "human" and not (r.get("authoring") or {}).get("attested_by"):
        issues.add(
            "ERROR",
            "format.human_unattested",
            rid,
            "author human ohne authoring.attested_by (wer hat das Item von Hand geschrieben?)",
        )
    if r.get("generator") != r.get("author"):
        issues.add("ERROR", "format.generator", rid, "generator und author weichen ab")
    if r.get("as_of") != "2026-10-01":
        issues.add("ERROR", "format.as_of", rid, "as_of ist nicht 2026-10-01")
    q = r.get("question") or ""
    a = r.get("answer") or ""
    if not q.strip().endswith("?"):
        issues.add("WARN", "style.question_mark", rid, "Frage endet nicht mit '?'")
    if len(a) > (220 if r.get("question_type") == "false_premise" else 120):
        issues.add("WARN", "style.long_answer", rid, f"Antwort lang ({len(a)} Zeichen)")
    if lang == "de" and ("ß" in q or "ß" in a):
        issues.add("ERROR", "style.eszett", rid, "de-CH-Item enthält ß")
    if re.search(r"\b(Art\.|Artikel|article|articolo)\s*\d", q, re.I):
        issues.add(
            "WARN", "style.article_in_question", rid, "Frage nennt eine Artikelnummer"
        )
    for name, pat in PII_PATTERNS.items():
        if pat.search(q) or pat.search(a):
            issues.add("ERROR", f"pii.{name}", rid, f"Mögliche Personendaten ({name})")

    detected, scores = detect_lang(q, lang)
    if detected and detected != lang:
        issues.add(
            "ERROR",
            "lang.question",
            rid,
            f"Frage wirkt wie '{detected}', erwartet '{lang}' {scores}",
        )

    s = r.get("source") or {}
    for f in SOURCE_REQUIRED:
        if f not in s:
            issues.add("ERROR", "format.source_field", rid, f"source.{f} fehlt")
    art = src.article(s.get("act"), s.get("article_id"), lang, "current")
    if not art:
        issues.add(
            "ERROR",
            "source.article_missing",
            rid,
            f"Artikel {s.get('act')} {s.get('article_id')} ({lang}) nicht gefunden",
        )
        return
    if f"/{lang}" not in (s.get("eli_url") or ""):
        issues.add(
            "ERROR", "source.eli_lang", rid, "ELI-URL nicht in der Sprache des Items"
        )
    para = next(
        (p for p in art["paragraphs"] if p["paragraph"] == (s.get("paragraph") or "")),
        None,
    )
    ev = s.get("evidence") or ""
    ev_n = norm_text(ev)
    if not ev.strip():
        issues.add("ERROR", "evidence.missing", rid, "evidence fehlt")
    elif para and ev_n in norm_text(para["text"]):
        pass
    elif ev_n in norm_text(art["text"]):
        issues.add(
            "WARN",
            "evidence.other_paragraph",
            rid,
            f"Evidenz steht im Artikel, aber nicht in Abs. {s.get('paragraph')!r}",
        )
    else:
        issues.add(
            "ERROR",
            "evidence.not_in_article",
            rid,
            "Evidenz steht nicht wörtlich im zitierten Artikel",
        )
    if not para:
        issues.add(
            "ERROR",
            "source.paragraph_missing",
            rid,
            f"Absatz {s.get('paragraph')!r} existiert nicht",
        )
    elif norm_space(s.get("quote")) != norm_space(para["text"]):
        issues.add(
            "ERROR",
            "source.quote_mismatch",
            rid,
            "source.quote entspricht nicht dem Absatztext",
        )
    if "'" in ev and "’" in (para or {}).get("text", ""):
        issues.add(
            "WARN",
            "evidence.apostrophe",
            rid,
            "Evidenz nutzt ' statt ’ (nur normalisiert gefunden)",
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
            "false_premise ohne answer_core (wörtliche Korrektur aus dem Gesetz)",
        )
    elif r.get("answer_core"):
        if strip_leading(norm_text(r["answer_core"]), lang) not in ev_n:
            issues.add(
                "ERROR",
                "answer.not_in_evidence",
                rid,
                f"answer_core {r['answer_core']!r} steht nicht wörtlich in der Evidenz",
            )
        if norm_text(r["answer_core"]) not in norm_text(a):
            issues.add(
                "ERROR",
                "answer.core_not_in_answer",
                rid,
                "answer_core ist nicht Teil der Antwort",
            )
    elif at == "yes_no" or qt == "yes_no":
        if norm_text(a) not in YES_NO[lang]:
            issues.add(
                "ERROR",
                "answer.yes_no",
                rid,
                f"Ja/Nein-Antwort erwartet, erhalten {a!r}",
            )
    elif an is not None:
        v = an.get("value") if isinstance(an, dict) else None
        if not isinstance(v, (int, float)):
            issues.add(
                "ERROR",
                "answer.normalized_format",
                rid,
                "answer_normalized.value ist keine Zahl",
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
                    f"Zahl {v} nicht als Ziffer/Zahlwort erkannt, Antwort {a!r} steht aber wörtlich in der Evidenz",
                )
            elif not in_answer:
                issues.add(
                    "ERROR",
                    "answer.number_mismatch",
                    rid,
                    f"Zahl {v} nicht in der Antwort {a!r}",
                )
            else:
                issues.add(
                    "ERROR",
                    "answer.not_in_evidence",
                    rid,
                    f"Zahl {v} steht nicht in der Evidenz",
                )
    else:
        if at in {"currency_chf", "percent", "age"}:
            issues.add(
                "WARN",
                "answer.normalized_missing",
                rid,
                f"answer_type={at} ohne answer_normalized",
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
                f"Antwort {a!r} nicht wörtlich, aber ein Alias",
            )
        elif stem_tokens_match(core, ev_n):
            issues.add(
                "WARN",
                "answer.inflected",
                rid,
                f"Antwort {a!r} nur flektiert/umgestellt in der Evidenz",
            )
        else:
            issues.add(
                "ERROR",
                "answer.not_in_evidence",
                rid,
                f"Antwort {a!r} steht nicht wörtlich in der Evidenz",
            )

    t = r.get("temporal") or {}
    if t.get("bucket") not in {"stable_pre2024", "changed_2024_2025", "changed_2026"}:
        issues.add("ERROR", "temporal.bucket", rid, "temporal.bucket fehlt/ungültig")
    if qt == "temporal":
        if not r.get("outdated_answers"):
            issues.add(
                "ERROR",
                "temporal.no_outdated",
                rid,
                "temporal-Item ohne veraltete Antwort",
            )
        if t.get("bucket") == "stable_pre2024":
            issues.add(
                "ERROR",
                "temporal.not_changed",
                rid,
                "Artikel seit 2024 unverändert, aber Typ temporal",
            )
        prev_art = src.article(s.get("act"), s.get("article_id"), lang, "previous")
        pev = t.get("previous_evidence") or ""
        if not prev_art:
            issues.add(
                "ERROR",
                "temporal.prev_missing",
                rid,
                "Vorfassung des Artikels nicht gefunden",
            )
        elif not pev or norm_text(pev) not in norm_text(prev_art["text"]):
            issues.add(
                "ERROR",
                "temporal.prev_evidence",
                rid,
                "Evidenz der veralteten Antwort steht nicht in der Vorfassung",
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
                    "Veraltete Antwort hat denselben Wert wie die aktuelle",
                )
            if old_vals and not (old_vals & extract_numbers(pev, lang)):
                issues.add(
                    "ERROR",
                    "temporal.outdated_not_in_prev",
                    rid,
                    "Zahl der veralteten Antwort nicht in der Evidenz der Vorfassung",
                )
    outdated_norm = {norm_text(o) for o in (r.get("outdated_answers") or []) if o}
    near_miss_norm = {norm_text(m) for m in (r.get("near_miss_answers") or []) if m}
    overlap = outdated_norm & near_miss_norm
    if overlap:
        issues.add(
            "ERROR",
            "overlap.outdated_near_miss",
            rid,
            f"Veraltete Antwort und Near-Miss überlappen: {overlap}",
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
                    f"Near-Miss {m!r}: Wert {n:g} steht in der Fassung vom {hits[0]}, nicht in der geltenden; gehört nach outdated_answers",
                )
    if qt != "yes_no" and at != "yes_no":
        aliases = r.get("answer_aliases") or []
        if not aliases and not near_miss_norm and not outdated_norm:
            issues.add(
                "WARN",
                "answer.no_variations",
                rid,
                "Weder answer_aliases noch near_miss/outdated angegeben",
            )
    if r.get("future_change"):
        issues.add(
            "WARN",
            "source.future_change",
            rid,
            f"Artikel ändert sich nach dem Stichtag: {', '.join(r['future_change'])}",
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
                "Sprachfassungen eines Kerns weichen in Typ/Wert/Quelle ab",
            )
        if not any(r.get("lang") == "de-CH" for r in rs):
            issues.add("ERROR", "lang.no_de", core, "Kern ohne deutsche Fassung")
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
                    f"Ja/Nein weicht zwischen Sprachen ab: {yn}",
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
                f"Gleiche Frage wie {seen_q[nq]}",
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
                    f"Sehr ähnlich zu {qs[j][0]} (Ratio {ratio:.2f})",
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
                f"Gleicher Fakt ({key[0]} {key[1]} Abs. {key[2]}, Wert {key[3]}) auch in: {', '.join(ids[1:])}",
            )


def table(counter, total=None, header=("Wert", "Anzahl")):
    lines = [
        f"| {header[0]} | {header[1]} |" + (" Anteil |" if total else ""),
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
        "| | " + " | ".join(cols) + " | Summe |",
        "| --- |" + " ---: |" * (len(cols) + 1),
    ]
    for row in sorted(c):
        lines.append(
            f"| {row} | "
            + " | ".join(str(c[row][x]) for x in cols)
            + f" | {sum(c[row].values())} |"
        )
    return "\n".join(lines)


def write_report(
    path, records, issues, inputs, target_total, min_parallel, min_human_share
):
    de = [r for r in records if r.get("lang") == "de-CH"]
    cores = {r["core_id"] for r in records}
    by_core_langs = defaultdict(set)
    for r in records:
        by_core_langs[r["core_id"]].add(LANGS.get(r.get("lang")))
    parallel = sum(1 for langs in by_core_langs.values() if {"de", "fr", "it"} <= langs)
    human = sum(
        1
        for r in de
        if r.get("author") == "human"
        and (r.get("authoring") or {}).get("mode") == "human_written"
    )
    errors = [i for i in issues.items if i["level"] == "ERROR"]
    warns = [i for i in issues.items if i["level"] == "WARN"]
    err_ids = {i["id"] for i in errors}
    authors = sorted({r.get("author") for r in records})
    out = []
    out.append("# Validierungsbericht Stichtag (Entwürfe)\n")
    out.append(
        f"Erzeugt: {dt.datetime.now().isoformat(timespec='seconds')} mit `validate_items.py`  "
    )
    out.append("Eingaben: " + ", ".join(f"`{Path(p).name}`" for p in inputs) + "\n")
    out.append("## Zusammenfassung\n")
    out.append(
        f"- Kern-Items (DE): **{len(de)}** von Ziel {target_total}; Zeilen gesamt (alle Sprachen): **{len(records)}**"
    )
    out.append(
        f"- Kerne mit DE+FR+IT: **{parallel}** (Minimum {min_parallel}) → {'erfüllt' if parallel >= min_parallel else 'NICHT erfüllt'}"
    )
    share = human / max(len(de), 1)
    out.append(
        f"- Handgeschriebener Anteil: **{human}/{len(de)} = {share:.0%}** (Ziel {min_human_share:.0%} des fertigen Datensatzes; zählt nur `author: human` mit `authoring.mode: human_written`)"
    )
    out.append(
        f"- Fehler (ERROR): **{len(errors)}** in {len(err_ids)} Zeilen/Kernen; Warnungen (WARN): **{len(warns)}**"
    )
    out.append(
        f"- Zeilen ohne Fehler: **{sum(1 for r in records if r['id'] not in err_ids and r['core_id'] not in err_ids)}** von {len(records)}\n"
    )
    out.append("## Prüfungen\n")
    out.append("| Prüfung | Was genau |\n| --- | --- |")
    out.append(
        "| Format | Pflichtfelder, erlaubte Werte, ID-Muster, `status: draft`, `needs_human_review: true`, Generator-Felder, `as_of` |"
    )
    out.append(
        "| Evidenz | `source.evidence` steht wörtlich (Leerraum normalisiert) im zitierten Absatz der Fassung vom Stichtag in der Sprache des Items; `source.quote` = Absatztext |"
    )
    out.append(
        "| Antwort im Artikel | Zahlen: `answer_normalized.value` steht in Antwort und Evidenz (Ziffern, Tausender-Leerzeichen, Dezimalkomma, Zahlwörter DE/FR/IT); Text: Antwort (ohne führende Artikel/Präpositionen) steht wörtlich in der Evidenz; Ja/Nein: erlaubte Form |"
    )
    out.append(
        "| Veraltet (`temporal`) | Artikel seit 2024 geändert; veraltete Antwort vorhanden; deren Evidenz steht wörtlich in der Vorfassung; alter Wert ≠ neuer Wert |"
    )
    out.append(
        "| Near-Miss vs. frühere Fassungen | Zahl eines Near-Miss steht in einer gespeicherten früheren Fassung des Artikels, aber nicht in der geltenden → Fehler (gehört nach `outdated_answers`) |"
    )
    out.append(
        "| Duplikate | gleiche DE-Frage (Fehler), ähnliche DE-Fragen ab Ratio 0,85 (Warnung), gleicher Fakt = gleicher Absatz + gleicher Wert (Warnung) |"
    )
    out.append(
        "| Sprachkonsistenz | Sprache der Frage (Stoppwörter), gleicher Typ/Wert/Absatz je Kern, Ja/Nein gleich in allen Sprachen, ELI-URL in Item-Sprache |"
    )
    out.append(
        "| Stil/PII | kein ß in de-CH, keine Artikelnummer in der Frage, Fragezeichen, AHV-Nr./IBAN/Telefon/E-Mail |"
    )
    out.append(
        "| Stichtag | Hinweis, wenn für den Artikel bereits eine Fassung nach dem 01.10.2026 publiziert ist |\n"
    )
    out.append("## Fehler und Warnungen nach Prüfung\n")
    out.append(
        table(
            Counter(f"{i['level']} {i['code']}" for i in issues.items),
            header=("Prüfung", "Anzahl"),
        )
        + "\n"
    )
    out.append("## Verteilung (DE-Kerne)\n")
    out.append("### Autor × Gesetz\n")
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
    out.append("### Autor × Fragetyp\n")
    qts = sorted({r.get("question_type") for r in de})
    out.append(
        cross_table(
            de, lambda r: r.get("author"), lambda r: r.get("question_type"), qts
        )
        + "\n"
    )
    out.append("### Bereich (`domain`)\n")
    out.append(table(Counter(r.get("domain") for r in de), len(de)) + "\n")
    out.append("### Register und Schwierigkeit\n")
    out.append(
        table(
            Counter(
                f"{r.get('register')} / Stufe {r.get('difficulty_prior')}" for r in de
            ),
            len(de),
        )
        + "\n"
    )
    out.append("### Stichtag-Gruppe (Artikelebene)\n")
    out.append(
        table(Counter((r.get("temporal") or {}).get("bucket") for r in de), len(de))
        + "\n"
    )
    out.append("### Sprachen (alle Zeilen)\n")
    out.append(
        cross_table(
            records,
            lambda r: r.get("author"),
            lambda r: r.get("lang"),
            ["de-CH", "fr-CH", "it-CH"],
        )
        + "\n"
    )
    out.append("## Alle Befunde\n")
    if not issues.items:
        out.append("Keine.\n")
    else:
        out.append("| Stufe | Prüfung | ID | Befund |\n| --- | --- | --- | --- |")
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
    ap.add_argument("inputs", nargs="+")
    args = ap.parse_args()
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
