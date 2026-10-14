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


def test_closed_swiss_prompt():
    from inkraft.prompts import extra_params, messages

    item = {"lang": "de-CH", "question": "Gilt Art. 12?"}
    msgs = messages(item, "closed_swiss")
    assert len(msgs) == 2
    assert "Schweizer Bundesrecht" in msgs[0]["content"]
    assert "Oktober" not in msgs[0]["content"]
    assert msgs[1]["content"] == "Gilt Art. 12?"
    assert extra_params("closed_swiss") == {
        "chat_template_kwargs": {"enable_thinking": False}
    }
    assert extra_params("closed_dated") == {
        "chat_template_kwargs": {"enable_thinking": False}
    }
    assert extra_params("closed_plain") == {
        "chat_template_kwargs": {"enable_thinking": False}
    }
    assert extra_params("open_book") == {
        "chat_template_kwargs": {"enable_thinking": False}
    }
    assert extra_params("thinking") == {
        "chat_template_kwargs": {"enable_thinking": True},
        "max_tokens": 3000,
    }


def test_path_sanitization():
    from inkraft.generate import response_path
    from inkraft.judge import judge_path

    p_resp = response_path("data", "meta-llama/Llama-3.1-8B-Instruct", "closed_dated")
    assert "/" not in p_resp.name and "meta-llama_Llama-3.1-8B-Instruct" in p_resp.name

    p_jd = judge_path(
        "data",
        "Qwen/Qwen2.5-72B-Instruct",
        "swiss-ai/apertus-v1.5-8b",
        "closed_swiss",
    )
    assert "/" not in p_jd.name
    assert "Qwen_Qwen2.5-72B-Instruct" in p_jd.name
    assert "swiss-ai_apertus-v1.5-8b" in p_jd.name


def test_cluster_bootstrap():
    rows = [
        row("CORRECT", core="c1"),
        row("CORRECT", core="c1"),
        row("INCORRECT", core="c2"),
        row("INCORRECT", core="c2"),
    ]
    res = summarise(rows, cluster_by_core=True)
    assert "ci95" in res
    assert res["ci95"]["correct"] == res["ci95"]["correct"]


def test_compute_deltas():
    from inkraft.score import compute_deltas

    mock_res = {
        "modelA__closed_dated": {
            "overall": {"correct": 0.60, "f": 0.60, "stale_share_of_errors": 0.20},
            "lang:de-CH": {"correct": 0.50, "f": 0.50, "stale_share_of_errors": 0.40},
        },
        "modelA__closed_swiss": {
            "overall": {"correct": 0.45, "f": 0.45, "stale_share_of_errors": 0.10}
        },
        "modelA__closed_plain": {"overall": {"correct": 0.30, "f": 0.30}},
        "modelA__open_book": {"overall": {"correct": 0.85, "f": 0.85}},
    }
    deltas = compute_deltas(mock_res)
    assert "modelA" in deltas
    m_d = deltas["modelA"]
    assert m_d["open_book_gain"]["delta_correct"] == 0.25
    # date effect only on the German rows, which closed_swiss covers
    assert m_d["date_effect_de"]["delta_correct"] == 0.05
    assert m_d["date_effect_de"]["delta_stale_share"] == 0.30
    assert m_d["swiss_context_effect"]["delta_correct"] == 0.15
