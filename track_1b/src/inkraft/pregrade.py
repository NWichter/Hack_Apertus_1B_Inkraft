"""Deterministic pre-grading: does the response contain the gold value, an outdated value, or refuse?

The result is a hint for the LLM judge and the basis for rule-vs-human agreement. It never
replaces the judge.
"""

import re

from .normalize import UNIT_DAYS, lang2, norm_text, quantities

NUMERIC_TYPES = {"duration", "percent", "currency_chf", "age", "number"}
REL_TOL = 0.03

ABSTAIN = {
    "de": [
        r"weiss (ich )?(es |das )?(leider )?nicht",
        r"nicht sicher",
        r"keine (genauen |aktuellen |verlässlichen |gesicherten )?(informationen|angaben|daten)",
        r"kann ich nicht (sicher |genau |verlässlich )?(sagen|beantworten|angeben)",
        r"ist mir nicht bekannt",
        r"habe ich keine",
        r"nicht beantworten",
    ],
    "fr": [
        r"je ne sais pas",
        r"pas s[uû]r",
        r"je ne suis pas (certain|en mesure)",
        r"pas d'informations?",
        r"je ne dispose pas",
        r"je ne peux pas (r[ée]pondre|confirmer|fournir)",
    ],
    "it": [
        r"non lo so",
        r"non so\b",
        r"non sono sicur",
        r"non ho informazioni",
        r"non dispongo",
        r"non posso (rispondere|confermare|fornire)",
        r"non sono in grado",
    ],
}
YES = {"de": ("ja",), "fr": ("oui",), "it": ("sì", "si")}
NO = {"de": ("nein",), "fr": ("non",), "it": ("no",)}


def is_abstention(response, lang):
    t = norm_text(response)
    return any(re.search(p, t) for p in ABSTAIN[lang2(lang)])


def _yes_no(response, lang):
    words = re.findall(r"[^\W\d_]+", norm_text(response))[:3]
    l2 = lang2(lang)
    if any(w in YES[l2] for w in words):
        return "yes"
    if any(w in NO[l2] for w in words):
        return "no"
    return None


def _same(q, t):
    """q, t = (value, days_per_unit or None). Same unit: exact. Different time units: compare in
    days with a small tolerance for month/year lengths ("90 Tage" = "3 Monate")."""
    (v, u), (tv, tu) = q, t
    if u is not None and tu is not None and u != tu:
        return abs(v * u - tv * tu) <= REL_TOL * tv * tu
    return v == tv


def _targets(answers, lang, default_unit):
    out = []
    for a in answers or []:
        out += [
            (v, u if u is not None else default_unit) for v, u in quantities(a, lang)
        ]
    return out


def pregrade(item, response):
    """Return {"rule": match|mixed|stale|near_miss|conflict|abstain|none, "detail": str}."""
    lang = item["lang"]
    if response is None or not response.strip():
        return {"rule": "none", "detail": "empty response"}
    abstain = is_abstention(response, lang)
    atype = item.get("answer_type")

    if atype == "yes_no":
        gold = _yes_no(item["answer"], lang)
        got = _yes_no(response, lang)
        if got is None:
            return {
                "rule": "abstain" if abstain else "none",
                "detail": "no yes/no found",
            }
        return {
            "rule": "match" if got == gold else "conflict",
            "detail": f"gold={gold} got={got}",
        }

    if atype in NUMERIC_TYPES and item.get("answer_normalized"):
        norm = item["answer_normalized"]
        gold_unit = UNIT_DAYS.get(norm.get("unit"))
        gold = (float(norm["value"]), gold_unit)
        drop_years = not (1900 <= gold[0] <= 2100)
        got = quantities(response, lang, drop_years=drop_years)
        if not got:
            return _text_rule(item, response, abstain)
        shown = sorted({v for v, _ in got})[:5]
        stale = [
            t
            for t in _targets(item.get("outdated_answers"), lang, gold_unit)
            if not _same(t, gold)
        ]
        near = [
            t
            for t in _targets(item.get("near_miss_answers"), lang, gold_unit)
            if not _same(t, gold)
        ]
        hit = lambda ts: any(_same(q, t) for q in got for t in ts)  # noqa: E731
        if hit([gold]):
            if hit(stale) or hit(near):
                return {
                    "rule": "mixed",
                    "detail": f"gold {gold[0]:g} and an outdated or near-miss value in {shown}",
                }
            return {"rule": "match", "detail": f"gold {gold[0]:g} found"}
        if hit(stale):
            return {"rule": "stale", "detail": f"outdated value found in {shown}"}
        if hit(near):
            return {"rule": "near_miss", "detail": f"near-miss value found in {shown}"}
        return {"rule": "conflict", "detail": f"numbers {shown} != gold {gold[0]:g}"}

    return _text_rule(item, response, abstain)


def _text_rule(item, response, abstain):
    resp = norm_text(response)
    for a in [
        item["answer"],
        *(item.get("answer_aliases") or []),
        item.get("answer_core") or "",
    ]:
        if a and norm_text(a) in resp:
            return {"rule": "match", "detail": f"answer text '{a}' found"}
    for a in item.get("outdated_answers") or []:
        if a and norm_text(a) in resp:
            return {"rule": "stale", "detail": f"outdated text '{a}' found"}
    return {
        "rule": "abstain" if abstain else "none",
        "detail": "no literal answer found, judge decides",
    }


PROVISIONAL = {
    "match": "CORRECT",
    "stale": "INCORRECT",
    "near_miss": "INCORRECT",
    "conflict": "INCORRECT",
    "abstain": "NOT_ATTEMPTED",
}
PROVISIONAL_SUBTYPE = {"stale": "STALE", "near_miss": "NEAR_MISS", "conflict": "OTHER"}


def provisional_grade(rule):
    """Rule-only (grade, subtype) for runs without a judge; grade None means 'needs the judge'."""
    return PROVISIONAL.get(rule), PROVISIONAL_SUBTYPE.get(rule)
