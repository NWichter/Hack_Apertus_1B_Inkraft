import pytest

from inkraft.normalize import extract_numbers
from inkraft.pregrade import pregrade, provisional_grade

ITEM = {
    "lang": "de-CH",
    "answer": "1260 Franken",
    "answer_aliases": ["CHF 1'260"],
    "answer_type": "currency_chf",
    "answer_normalized": {"value": 1260, "unit": "CHF"},
    "outdated_answers": ["1225 Franken"],
    "near_miss_answers": ["2520 Franken"],
}


@pytest.mark.parametrize(
    "text,lang,expected",
    [
        ("CHF 1'260.– pro Monat", "de", {1260.0}),
        ("1 260 francs", "fr", {1260.0}),
        ("drei Monate", "de", {3.0}),
        ("tre mesi", "it", {3.0}),
        ("Gemäss Art. 34 Abs. 5 AHVG sind es 1260 Franken.", "de", {1260.0}),
        ("10,5 %", "de", {10.5}),
    ],
)
def test_extract_numbers(text, lang, expected):
    assert extract_numbers(text, lang) == expected


@pytest.mark.parametrize(
    "response,rule",
    [
        ("Der Mindestbetrag beträgt CHF 1'260 pro Monat.", "match"),
        ("Er beträgt 1225 Franken.", "stale"),
        ("2520 Franken.", "near_miss"),
        ("Der Mindestbetrag beträgt 2330 CHF pro Monat.", "conflict"),
        ("Das weiss ich leider nicht sicher.", "abstain"),
        ("Bitte wenden Sie sich an Ihre Ausgleichskasse.", "none"),
        ("", "none"),
    ],
)
def test_numeric(response, rule):
    assert pregrade(ITEM, response)["rule"] == rule


def test_year_is_not_a_number_answer():
    assert (
        pregrade(ITEM, "Seit 2025 gilt der Betrag von 1260 Franken.")["rule"] == "match"
    )
    assert pregrade(ITEM, "Im Jahr 2026 weiss ich es nicht.")["rule"] == "abstain"


def test_yes_no():
    it = {"lang": "fr-CH", "answer": "Non", "answer_type": "yes_no"}
    assert pregrade(it, "Non, ce n'est pas possible.")["rule"] == "match"
    assert pregrade(it, "Oui, en principe.")["rule"] == "conflict"


def test_text_answer():
    it = {
        "lang": "de-CH",
        "answer": "Tiers garant",
        "answer_aliases": [],
        "answer_type": "text",
    }
    assert pregrade(it, "Das ist das System des **Tiers garant**.")["rule"] == "match"
    assert pregrade(it, "Das nennt man Tiers payant.")["rule"] == "none"


def test_provisional():
    assert provisional_grade("match") == ("CORRECT", None)
    assert provisional_grade("stale") == ("INCORRECT", "STALE")
    assert provisional_grade("none") == (None, None)


def dur(lang, value, unit, answer="x"):
    return {"lang": lang, "answer": answer, "answer_type": "duration", "answer_normalized": {"value": value, "unit": unit}}


@pytest.mark.parametrize(
    "item,response,rule",
    [
        # articles and calendar dates are not numbers (pilot finding, 2026-10-01)
        (dur("fr-CH", 80, "percent"), "Je ne dispose pas d'informations précises en date du 1er octobre 2026.", "abstain"),
        (dur("it-CH", 6, "months"), "Non sono in grado di fornire una risposta, consulta un ufficio.", "abstain"),
        (dur("de-CH", 5, "years"), "Ich kann das nicht sicher sagen, es gibt eine Karenzfrist.", "abstain"),
        # units are compared in days
        (dur("fr-CH", 3, "weeks"), "720 heures de travail, soit généralement trois mois.", "conflict"),
        (dur("de-CH", 3, "months"), "Innert 90 Tagen nach der Wohnsitznahme.", "match"),
        (dur("fr-CH", 6, "months"), "au plus tôt à l'expiration d'un délai d'attente d'un an", "conflict"),
        (dur("de-CH", 1, "months"), "Innert eines Monats.", "match"),
        (dur("de-CH", 1, "months"), "Innert einem Monat.", "match"),
        # ordinals
        (dur("de-CH", 3, "days"), "Der Anspruch entsteht am dritten Tag nach dem Unfalltag.", "match"),
        (dur("fr-CH", 56, "days"), "Le délai prend fin le 42e jour après l'accouchement.", "conflict"),
    ],
)
def test_pilot_regressions(item, response, rule):
    assert pregrade(item, response)["rule"] == rule


def test_percent_words_and_text_fallback():
    pct = {"lang": "it-CH", "answer": "50 per cento", "answer_type": "percent", "answer_normalized": {"value": 50, "unit": "percent"}}
    assert extract_numbers("50 per cento", "it") == {50.0}
    assert pregrade(pct, "Il 60 per cento.")["rule"] == "conflict"
    month = {"lang": "fr-CH", "answer": "dans le mois qui suit l’information", "answer_aliases": [], "answer_type": "duration",
             "answer_normalized": {"value": 1, "unit": "months"}}
    assert pregrade(month, "Dans le mois qui suit l'information donnée par l'employeur.")["rule"] == "match"
