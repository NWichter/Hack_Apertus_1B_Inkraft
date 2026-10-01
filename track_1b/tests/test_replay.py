import json
import shutil
from pathlib import Path

import pytest

from inkraft import dataset
from inkraft.cli import main
from inkraft.pregrade import pregrade, provisional_grade

FIXTURE = Path(__file__).parent / "fixtures" / "mini"


def test_replay_passes(capsys):
    main(["--data", str(FIXTURE), "replay"])
    assert "PASS" in capsys.readouterr().out


def test_replay_detects_a_changed_grade(tmp_path):
    data = tmp_path / "mini"
    shutil.copytree(FIXTURE, data)
    jpath = next((data / "judgements").glob("*.jsonl"))
    rows = dataset.read_jsonl(jpath)
    rows[0]["grade"] = "INCORRECT"
    dataset.write_jsonl(jpath, rows)
    with pytest.raises(SystemExit):
        main(["--data", str(data), "replay"])


def test_rules_agree_with_fixture_grades():
    items = {it["id"]: it for it in dataset.load(FIXTURE)}
    resp = {
        r["id"]: r
        for r in dataset.read_jsonl(next((FIXTURE / "responses").glob("*.jsonl")))
    }
    for j in dataset.read_jsonl(next((FIXTURE / "judgements").glob("*.jsonl"))):
        rule = pregrade(items[j["id"]], resp[j["id"]]["response"])["rule"]
        assert provisional_grade(rule) == (j["grade"], j["incorrect_subtype"]), j["id"]


def test_expected_results_are_committed():
    exp = json.loads((FIXTURE / "expected_results.json").read_text(encoding="utf-8"))
    assert exp["judge_model"] == "fixture-judge"
    assert set(exp["results"]) == {"fixture-model__closed_dated"}
