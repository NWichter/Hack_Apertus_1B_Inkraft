"""Freeze the judge grades of the human judge sample as they were when the sample was drawn.

Later changes to answer variants re-judge some rows; the human check must still be compared with the grades the
annotator was sampled against. Writes data/human_labels/sample_grades_<judge>.jsonl for each judge given.

python src/snapshot_sample_grades.py qwen/qwen3-235b-a22b-2507 panel
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
sys.path.insert(0, str(HERE))
from inkraft import dataset  # noqa: E402
from inkraft.judge import judge_path  # noqa: E402


def main():
    sample = dataset.read_jsonl(DATA / "human_labels" / "sample_20pct.jsonl")
    for judge in sys.argv[1:]:
        out, missing = [], 0
        cache = {}
        for r in sample:
            k = (r["model"], r["condition"])
            if k not in cache:
                cache[k] = {
                    j["id"]: j
                    for j in dataset.read_jsonl(judge_path(DATA, judge, *k))
                    if j.get("grade")
                }
            j = cache[k].get(r["id"])
            if not j:
                missing += 1
                continue
            out.append(
                {
                    k2: j.get(k2)
                    for k2 in (
                        "id",
                        "judge_model",
                        "examinee",
                        "condition",
                        "grade",
                        "incorrect_subtype",
                    )
                }
            )
        if missing:
            sys.exit(f"{judge}: {missing} sample rows without a grade")
        path = (
            DATA
            / "human_labels"
            / f"sample_grades_{judge.replace('/', '_').replace(':', '_')}.jsonl"
        )
        if path.exists():
            print(f"{path.name} exists, kept (snapshot is taken once)")
            continue
        dataset.write_jsonl(path, out)
        print(f"{path.name}: {len(out)} rows")


if __name__ == "__main__":
    main()
