import json
from pathlib import Path

from inkraft.pregrade import pregrade, provisional_grade

CAL = Path(__file__).parent / "fixtures" / "judge_calibration.jsonl"


def rows():
    return [
        json.loads(line)
        for line in CAL.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_calibration_set_shape():
    r = rows()
    assert len(r) >= 60
    assert len({x["cal_id"] for x in r}) == len(r)
    assert len({(x["item"]["id"], x["response"]) for x in r}) == len(r)
    assert {x["expected_grade"] for x in r} == {"CORRECT", "INCORRECT", "NOT_ATTEMPTED"}


def test_rule_pregrade_never_contradicts_a_known_grade():
    """When the rules commit to a grade, it must be the constructed one; otherwise the judge decides."""
    committed = 0
    for x in rows():
        grade, sub = provisional_grade(pregrade(x["item"], x["response"])["rule"])
        if grade is None:
            continue
        committed += 1
        assert (grade, sub) == (x["expected_grade"], x["expected_subtype"]), x["cal_id"]
    assert committed >= 0.6 * len(rows())


class FakeJudge:
    """Answers with the constructed grade, except for one row: checks the accounting, not a model."""

    model = "fake-judge"

    def __init__(self, rows):
        self.by_key = {(x["item"]["question"], x["response"]): x for x in rows}

    def chat(self, messages, **_):
        prompt = messages[0]["content"]
        resp = prompt.split("<<<\n", 1)[1].split("\n>>>", 1)[0]
        question = prompt.split("\nQuestion: ", 1)[1].split("\n", 1)[0]
        x = self.by_key[(question, resp)]
        grade = (
            "CORRECT"
            if x["cal_id"] == "cal-001" and x["expected_grade"] != "CORRECT"
            else x["expected_grade"]
        )
        content = json.dumps(
            {
                "grade": grade,
                "incorrect_subtype": x["expected_subtype"],
                "reason": "fake",
            }
        )
        return {"choices": [{"message": {"content": content}}]}


def test_calibrate_accounting():
    from inkraft.judge import calibrate

    r = rows()
    res = calibrate(FakeJudge(r), r, workers=2)
    wrong = 1 if r[0]["expected_grade"] != "CORRECT" else 0
    assert res["n"] == len(r)
    assert res["grade_accuracy"] == round((len(r) - wrong) / len(r), 4)
