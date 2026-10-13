"""Agreement between two judges on the same responses (Cohen's kappa, 3 and 5 classes), plus agreement of
each judge with the deterministic pre-grade where the rules decide. Diagnostic only; it does not replace
the human check.

python src/judge_agreement.py --a qwen/qwen3-235b-a22b-2507 --b apertus-v1.5-70b [--condition closed_dated]
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from inkraft import dataset  # noqa: E402
from inkraft.human import CLASSES, EXTENDED_CLASSES, cohen_kappa  # noqa: E402
from inkraft.judge import judge_path  # noqa: E402
from inkraft.pregrade import provisional_grade  # noqa: E402


def ext(j):
    if j["grade"] == "INCORRECT":
        return j.get("incorrect_subtype") or "OTHER"
    return j["grade"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(HERE.parent / "data"))
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--condition", default="closed_dated")
    ap.add_argument("--out")
    args = ap.parse_args()
    data = Path(args.data)
    out = {}
    for p in sorted((data / "responses").glob(f"*__{args.condition}.jsonl")):
        model = p.stem.split("__")[0]
        ja = {
            j["id"]: j
            for j in dataset.read_jsonl(judge_path(data, args.a, model, args.condition))
            if j.get("grade")
        }
        jb = {
            j["id"]: j
            for j in dataset.read_jsonl(judge_path(data, args.b, model, args.condition))
            if j.get("grade")
        }
        ids = sorted(set(ja) & set(jb))
        if not ids:
            continue
        a3 = [ja[i]["grade"] for i in ids]
        b3 = [jb[i]["grade"] for i in ids]
        a5 = [ext(ja[i]) for i in ids]
        b5 = [ext(jb[i]) for i in ids]
        rule = {}
        for i in ids:
            g, _ = provisional_grade(ja[i]["rule_pregrade"])
            if g:
                rule[i] = g
        out[model] = {
            "n": len(ids),
            "raw_agreement": round(sum(x == y for x, y in zip(a3, b3)) / len(ids), 4),
            "kappa": round(cohen_kappa(a3, b3), 4),
            "kappa_5class": round(cohen_kappa(a5, b5, classes=EXTENDED_CLASSES), 4),
            "grades_a": dict(Counter(a3)),
            "grades_b": dict(Counter(b3)),
            "rule_decided": len(rule),
            "rule_agreement_a": round(
                sum(rule[i] == ja[i]["grade"] for i in rule) / max(1, len(rule)), 4
            ),
            "rule_agreement_b": round(
                sum(rule[i] == jb[i]["grade"] for i in rule) / max(1, len(rule)), 4
            ),
        }
    res = {
        "judge_a": args.a,
        "judge_b": args.b,
        "condition": args.condition,
        "classes": CLASSES,
        "by_model": out,
    }
    text = json.dumps(res, indent=1)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
