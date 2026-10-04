"""Run the unchanged src/validate_items.py on the pilot candidates.

The only difference: "nemotron" is accepted as author/generator (the validator only knows
claude, codex, gemini, human). Second pass with merged.v1.jsonl finds duplicates against the draft.

python validate_candidates.py --fedlex <fedlex-v2> --tag ultra
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[2] / "src"
MERGED = HERE.parents[1] / "merged.v1.jsonl"
sys.path.insert(0, str(SRC))
import validate_items  # noqa: E402

validate_items.AUTHORS.add("nemotron")


def run(args_list):
    sys.argv = ["validate_items.py", *args_list]
    try:
        validate_items.main()
    except SystemExit as e:
        return e.code
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fedlex", required=True)
    ap.add_argument("--tag", default="ultra")
    a = ap.parse_args()
    cand = HERE / f"candidates.{a.tag}.jsonl"
    run(
        [
            "--fedlex",
            a.fedlex,
            "--report",
            str(HERE / f"validation.{a.tag}.md"),
            "--issues-json",
            str(HERE / f"issues.{a.tag}.json"),
            "--target-total",
            "19",
            "--min-parallel",
            "1",
            str(cand),
        ]
    )
    tmp = HERE / f"_issues_with_merged.{a.tag}.json"
    run(
        [
            "--fedlex",
            a.fedlex,
            "--report",
            str(HERE / "_tmp_report.md"),
            "--issues-json",
            str(tmp),
            str(MERGED),
            str(cand),
        ]
    )
    prefix = f"nm{a.tag[0]}-"
    cross = [
        i
        for i in json.loads(tmp.read_text(encoding="utf-8"))
        if i["code"].startswith("dup.") and prefix in (i["id"] + i["msg"])
    ]
    (HERE / f"duplicates_vs_merged.{a.tag}.json").write_text(
        json.dumps(cross, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    tmp.unlink()
    (HERE / "_tmp_report.md").unlink()
    print(f"{len(cross)} duplicate warnings against merged.v1.jsonl")
