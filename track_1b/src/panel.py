"""Judge panel: majority vote of several open-weight judges over every response.

For every responses/<model>__<condition>.jsonl the judgement files of the panel judges are combined into
judgements/panel__<model>__<condition>.jsonl (judge_model "panel"), which `inkraft score --judge-model panel`
then uses. Majority on the three-way grade; for INCORRECT the subtype is the majority among the judges that said
INCORRECT. Without a majority (all judges differ) the grade of the first (primary) judge is used and the row is
flagged. Writes data/judge_panel.json: Fleiss' kappa among the judges (3 classes and 5 classes), each judge's
agreement with the majority, and the number of rows without majority.

python src/panel.py --judges qwen/qwen3-235b-a22b-2507 z-ai/glm-5.3 deepseek/deepseek-v3.2
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from inkraft import dataset  # noqa: E402
from inkraft.judge import judge_path  # noqa: E402

PANEL = "panel"
CLASSES3 = ["CORRECT", "INCORRECT", "NOT_ATTEMPTED"]
CLASSES5 = ["CORRECT", "STALE", "NEAR_MISS", "OTHER", "NOT_ATTEMPTED"]


def ext(j):
    return (
        (j.get("incorrect_subtype") or "OTHER")
        if j["grade"] == "INCORRECT"
        else j["grade"]
    )


def fleiss(ratings, classes):
    """ratings: list of per-item label lists (same number of raters per item)."""
    n_items = len(ratings)
    if not n_items:
        return None
    m = len(ratings[0])
    counts = [Counter(r) for r in ratings]
    p_j = {c: sum(cn[c] for cn in counts) / (n_items * m) for c in classes}
    p_i = [(sum(v * v for v in cn.values()) - m) / (m * (m - 1)) for cn in counts]
    p_bar = sum(p_i) / n_items
    p_e = sum(v * v for v in p_j.values())
    return round((p_bar - p_e) / (1 - p_e), 4) if p_e < 1 else 1.0


def combine(js):
    grades = Counter(j["grade"] for j in js)
    top, n = grades.most_common(1)[0]
    majority = n > len(js) / 2
    grade = top if majority else js[0]["grade"]
    sub = None
    if grade == "INCORRECT":
        subs = Counter(
            j.get("incorrect_subtype") or "OTHER"
            for j in js
            if j["grade"] == "INCORRECT"
        )
        best = subs.most_common()
        sub = (
            best[0][0]
            if len(best) == 1 or best[0][1] > best[1][1]
            else (
                js[0].get("incorrect_subtype")
                if js[0]["grade"] == "INCORRECT"
                else best[0][0]
            )
        )
    return grade, sub, majority


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(HERE.parent / "data"))
    ap.add_argument(
        "--judges", nargs="+", required=True, help="first judge = primary (tie-break)"
    )
    args = ap.parse_args()
    data = Path(args.data)
    stats = {
        "judges": args.judges,
        "rule": "majority of the three-way grade; no majority -> first judge",
        "runs": {},
    }
    all3, all5, agree = [], [], {j: [0, 0] for j in args.judges}
    agree5 = {j: [0, 0] for j in args.judges}
    no_major = 0
    for p in sorted((data / "responses").glob("*.jsonl")):
        model, cond = p.stem.split("__", 1)
        by = []
        for j in args.judges:
            by.append(
                {
                    r["id"]: r
                    for r in dataset.read_jsonl(judge_path(data, j, model, cond))
                    if r.get("grade")
                }
            )
        names = [jn for jn, b in zip(args.judges, by) if b]
        by = [b for b in by if b]
        if not by:
            continue
        single = len(by) == 1  # run judged by one judge only (e.g. the ablation): panel = that judge
        ids = sorted(set.intersection(*(set(b) for b in by)))
        rows, nm = [], 0
        for i in ids:
            js = [b[i] for b in by]
            grade, sub, major = combine(js)
            nm += not major
            rows.append(
                {
                    "id": i,
                    "judge_model": PANEL,
                    "examinee": js[0]["examinee"],
                    "condition": cond,
                    "grade": grade,
                    "incorrect_subtype": sub,
                    "majority": major,
                    "votes": {
                        jn: {
                            "grade": j["grade"],
                            "incorrect_subtype": j.get("incorrect_subtype"),
                        }
                        for jn, j in zip(names, js)
                    },
                    "single_judge": single,
                    "rule_pregrade": js[0].get("rule_pregrade"),
                    "rule_detail": js[0].get("rule_detail"),
                }
            )
            if single:
                continue
            all3.append([j["grade"] for j in js])
            all5.append([ext(j) for j in js])
            ext_major = ext({"grade": grade, "incorrect_subtype": sub})
            for jn, j in zip(names, js):
                agree[jn][0] += j["grade"] == grade
                agree[jn][1] += 1
                agree5[jn][0] += ext(j) == ext_major
                agree5[jn][1] += 1
        no_major += nm
        missing = max(len(b) for b in by) - len(ids)
        dataset.write_jsonl(judge_path(data, PANEL, model, cond), rows)
        stats["runs"][f"{model}__{cond}"] = {
            "n": len(ids),
            "no_majority": nm,
            "missing_votes": missing,
            "judges": names,
        }
    stats["fleiss_kappa_3class"] = fleiss(all3, CLASSES3)
    stats["fleiss_kappa_5class"] = fleiss(all5, CLASSES5)
    stats["unanimous_share_3class"] = round(
        sum(len(set(r)) == 1 for r in all3) / len(all3), 4
    )
    stats["no_majority_rows"] = no_major
    stats["agreement_with_majority"] = {
        j: round(a / n, 4) for j, (a, n) in agree.items()
    }
    stats["agreement_with_majority_5class"] = {
        j: round(a / n, 4) for j, (a, n) in agree5.items()
    }
    stats["n_rows"] = len(all3)
    cost = {}
    for j in args.judges:
        cost[j] = round(
            sum(
                r.get("cost_usd") or 0
                for p in (data / "judgements").glob(
                    f"{j.replace('/', '_').replace(':', '_')}__*.jsonl"
                )
                for r in dataset.read_jsonl(p)
            ),
            4,
        )
    stats["judging_cost_usd"] = cost
    (data / "judge_panel.json").write_text(
        json.dumps(stats, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
