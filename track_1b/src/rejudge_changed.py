"""Re-judge only the rows whose grading reference changed between the release candidate and the release.

Compares question, gold answer, variants, outdated and near-miss answers of every row in
merged.v<release>.jsonl with merged.v<candidate>.jsonl. For changed rows the stored grades of the given judges
are removed and the judges are run again (main conditions: all judges; other conditions: the first judge only).
Answers and grades of rows that are not in the release (cores removed after the human check) are deleted from
data/responses and data/judgements; all other Apertus answers are not touched. Judges that need extra request fields read them from JUDGE_EXTRA_<n>.

python src/rejudge_changed.py --env <.env> --judges <primary> <judge2> ... [--candidate 1.0.0-rc1]
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
sys.path.insert(0, str(HERE))
from inkraft import dataset  # noqa: E402
from inkraft.judge import judge_path  # noqa: E402
from second_check import env_value  # noqa: E402

FIELDS = (
    "question",
    "answer",
    "answer_aliases",
    "outdated_answers",
    "near_miss_answers",
)
MAIN = ("closed_dated", "open_book")
EXTRA = {"z-ai/glm-5.3": str(DATA / "judge_extra_reasoning_low.json")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True)
    ap.add_argument("--judges", nargs="+", required=True)
    ap.add_argument("--candidate", default="1.0.0-rc1")
    args = ap.parse_args()
    freeze = json.loads((DATA / "FREEZE.json").read_text(encoding="utf-8"))
    new = {
        r["id"]: r
        for r in dataset.read_jsonl(DATA / f"merged.v{freeze['version']}.jsonl")
    }
    old = {
        r["id"]: r for r in dataset.read_jsonl(DATA / f"merged.v{args.candidate}.jsonl")
    }
    changed = sorted(
        i
        for i, r in new.items()
        if i in old and any(r.get(f) != old[i].get(f) for f in FIELDS)
    )
    (DATA / "review" / "rejudged_rows.json").write_text(
        json.dumps(changed, indent=1) + "\n", encoding="utf-8"
    )
    print(f"{len(changed)} rows with a changed grading reference")
    removed = set(old) - set(new)
    if removed:
        for p in sorted((DATA / "responses").glob("*.jsonl")) + sorted(
            (DATA / "judgements").glob("*.jsonl")
        ):
            rows = dataset.read_jsonl(p)
            keep = [r for r in rows if r["id"] not in removed]
            if len(keep) != len(rows):
                dataset.write_jsonl(p, keep)
        print(f"{len(removed)} rows not in the release: answers and grades removed")
    if not changed:
        return
    ch = set(changed)
    for p in sorted((DATA / "responses").glob("*.jsonl")):
        model, cond = p.stem.split("__", 1)
        judges = args.judges if cond in MAIN else args.judges[:1]
        for j in judges:
            jp = judge_path(DATA, j, model, cond)
            rows = dataset.read_jsonl(jp)
            if rows:
                dataset.write_jsonl(jp, [r for r in rows if r["id"] not in ch])
    env = {
        **os.environ,
        "PYTHONPATH": str(HERE),
        "JUDGE_BASE_URL": "https://openrouter.ai/api/v1",
        "JUDGE_API_KEY": env_value(args.env, "OPENROUTER_API_KEY"),
    }
    for k, j in enumerate(args.judges):
        conds = list(MAIN) + ([] if k else ["closed_swiss", "closed_plain"])
        cmd = [
            sys.executable,
            "-m",
            "inkraft",
            "--data",
            str(DATA),
            "judge",
            "--judge-model",
            j,
            "--workers",
            "6",
            "--condition",
            *conds,
        ]
        if j in EXTRA:
            cmd += ["--judge-extra", EXTRA[j]]
        subprocess.run(cmd, check=True, env=env)


if __name__ == "__main__":
    main()
