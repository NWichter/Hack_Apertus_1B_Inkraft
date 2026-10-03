import pytest

from inkraft import dataset
from inkraft.human import agreement, cohen_kappa, label, sample
from tests.test_replay import FIXTURE


def test_kappa_known_values():
    assert cohen_kappa(["CORRECT", "INCORRECT"] * 5, ["CORRECT", "INCORRECT"] * 5) == 1.0
    # 3x3 example: po = 0.7, pe = (4*4 + 4*5 + 2*1) / 100 = 0.38
    a = ["CORRECT"] * 4 + ["INCORRECT"] * 4 + ["NOT_ATTEMPTED"] * 2
    b = ["CORRECT"] * 3 + ["INCORRECT"] + ["INCORRECT"] * 3 + ["CORRECT"] + ["NOT_ATTEMPTED"] * 1 + ["INCORRECT"]
    assert cohen_kappa(a, b) == pytest.approx((0.7 - 0.38) / 0.62, abs=1e-9)


def test_sample_is_deterministic_and_stratified():
    items = dataset.load(FIXTURE)
    s1 = sample(items, FIXTURE, "fixture-judge")
    s2 = sample(items, FIXTURE, "fixture-judge")
    assert s1 == s2
    assert len(s1) == 5  # five (lang, grade) strata, at least one row each


def test_label_hides_judge_and_writes(tmp_path):
    items = dataset.load(FIXTURE)
    rows = sample(items, FIXTURE, "fixture-judge")[:2]
    shown = []
    answers = iter(["x", "c", "i?"])
    out = tmp_path / "labels.jsonl"
    label(items, rows, out, "tester", read=lambda _: next(answers), write=shown.append)
    labels = dataset.read_jsonl(out)
    assert [r["human_grade"] for r in labels] == ["CORRECT", "INCORRECT"]
    assert labels[1]["uncertain"] is True
    assert not any("fixture-judge" in s or "STALE" in s for s in shown)


def test_agreement_on_fixture():
    judg = dataset.read_jsonl(next((FIXTURE / "judgements").glob("*.jsonl")))
    human = [{"id": j["id"], "model": j["examinee"], "condition": j["condition"], "human_grade": j["grade"]} for j in judg]
    res = agreement(human, judg)
    assert res["n"] == 6 and res["kappa"] == 1.0 and res["raw_agreement"] == 1.0


def test_subtype_labeling_and_agreement(tmp_path):
    items = dataset.load(FIXTURE)
    rows = sample(items, FIXTURE, "fixture-judge")[:3]
    answers = iter(["s", "m", "c?"])
    out = tmp_path / "subtypes.jsonl"
    label(items, rows, out, "tester", read=lambda _: next(answers), write=lambda _: None)
    labels = dataset.read_jsonl(out)
    assert labels[0]["human_grade"] == "INCORRECT" and labels[0]["human_subtype"] == "STALE"
    assert labels[1]["human_grade"] == "INCORRECT" and labels[1]["human_subtype"] == "NEAR_MISS"
    assert labels[2]["human_grade"] == "CORRECT" and labels[2]["uncertain"] is True

    # test 5-class agreement calculation
    judg = [
        {"id": labels[0]["id"], "examinee": labels[0]["model"], "condition": labels[0]["condition"], "grade": "INCORRECT", "incorrect_subtype": "STALE"},
        {"id": labels[1]["id"], "examinee": labels[1]["model"], "condition": labels[1]["condition"], "grade": "INCORRECT", "incorrect_subtype": "NEAR_MISS"},
        {"id": labels[2]["id"], "examinee": labels[2]["model"], "condition": labels[2]["condition"], "grade": "CORRECT", "incorrect_subtype": None},
    ]
    agr = agreement(labels, judg)
    assert agr["kappa"] == 1.0
    assert agr["kappa_5class"] == 1.0
    assert agr["stale_metrics"]["both_stale_count"] == 1
    assert agr["stale_metrics"]["precision"] == 1.0
