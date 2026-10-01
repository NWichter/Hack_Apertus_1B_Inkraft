from inkraft.judge import parse
from inkraft.score import _point, language_consistency, summarise


def row(grade, sub=None, core="c1", lang="de-CH"):
    return {
        "grade": grade,
        "subtype": sub,
        "core_id": core,
        "lang": lang,
        "grade_source": "judge",
    }


def test_simpleqa_metrics():
    rows = (
        [row("CORRECT")] * 6
        + [row("INCORRECT", "STALE")] * 2
        + [row("NOT_ATTEMPTED")] * 2
    )
    m = _point(rows)
    assert m["correct"] == 0.6
    assert m["cga"] == 0.75
    assert abs(m["f"] - 2 * 0.6 * 0.75 / 1.35) < 1e-12
    assert m["hallucination_rate"] == 0.25
    assert m["stale_share_of_errors"] == 1.0
    assert abs(m["score_l3"] - 0.0) < 1e-12


def test_bootstrap_is_deterministic():
    rows = [row("CORRECT")] * 5 + [row("INCORRECT")] * 5
    assert summarise(rows)["ci95"] == summarise(rows)["ci95"]


def test_language_consistency():
    rows = [row("CORRECT", lang=l) for l in ("de-CH", "fr-CH", "it-CH")]
    rows += [
        row("CORRECT", core="c2", lang="de-CH"),
        row("INCORRECT", core="c2", lang="fr-CH"),
        row("CORRECT", core="c2", lang="it-CH"),
    ]
    lc = language_consistency(rows)
    assert lc["n_cores"] == 2 and lc["same_grade_all_three"] == 0.5
    assert lc["correct_on_parallel_cores"]["fr"] == 0.5


def test_judge_parse():
    assert (
        parse('{"grade": "INCORRECT", "incorrect_subtype": "STALE", "reason": "old"}')[
            "incorrect_subtype"
        ]
        == "STALE"
    )
    assert (
        parse('Sure: {"grade": "correct", "incorrect_subtype": null}')["grade"]
        == "CORRECT"
    )
    assert parse('{"grade": "INCORRECT"}')["incorrect_subtype"] == "OTHER"
    assert parse("no json") is None


def test_redact_key_identifier():
    from inkraft.client import redact

    assert redact(b"Rate limit exceeded for api_key: 0a1b2c3d. Limit") == "Rate limit exceeded for api_key: [redacted]. Limit"
