"""Import the export of the human check page (offline HTML page over data/human_labels/dataset_sample.jsonl and
sample_20pct.jsonl, written by src/draw_human_sample.py) and compute the numbers.

Writes data/human_labels/labels_<annotator>.jsonl (judge sample, format of inkraft agreement),
data/review/human_check_log.jsonl (dataset decisions, review-log format for auto_review.py --human-log)
and data/human_labels/summary.json (item error rate per stratum with Wilson interval, Cohen's kappa).

python src/import_human.py <export.json> --annotator niklas --name "Niklas Wichter" --judge-model <judge>
"""

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from inkraft import dataset, human  # noqa: E402


def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export")
    ap.add_argument("--data", default=str(ROOT / "data"))
    ap.add_argument("--annotator", default="niklas")
    ap.add_argument("--name", default="Niklas Wichter")
    ap.add_argument("--judge-model", required=True, help="judge the sample was drawn on (primary)")
    ap.add_argument("--also", nargs="*", default=["panel"], help="further judges to compare with (default: panel majority)")
    args = ap.parse_args()
    data = Path(args.data)
    ex = json.loads(Path(args.export).read_text(encoding="utf-8"))
    who = ex.get("annotator")
    who_text = json.dumps(who, ensure_ascii=False).lower()
    if any(w in who_text for w in ("claude", "gpt", "gemini", "qwen", "nemotron", "apertus", "ki,", "(ki", " ai ", "model")):
        sys.exit(f"export annotator {who!r} is not a person: a model's labels are not a human check")
    if isinstance(who, str) and who.strip():
        args.name = who.strip()
    strata = {
        r["core_id"]: r["stratum"]
        for r in dataset.read_jsonl(data / "human_labels" / "dataset_sample.jsonl")
    }

    log, per = [], {}
    for cid, a in sorted(ex.get("dataset", {}).items()):
        if not a.get("v") or cid not in strata:
            continue
        g = strata[cid]
        s = per.setdefault(g, {"n": 0, "drop": 0, "unsure": 0})
        if a["v"] == "unsure":
            s["unsure"] += (
                1  # unresolved: no human decision, not in the error-rate denominator
            )
            continue
        s["n"] += 1
        s["drop"] += a["v"] == "drop"
        log.append(
            {
                "core_id": cid,
                "decision": {"ok": "accept", "drop": "drop"}[a["v"]],
                "reviewer": args.name,
                "timestamp": a.get("at"),
                "duration_s": None,
                "agent_revealed_before_decision": False,
                "tool": "offline check page (blind)",
                "note": a.get("note") or "",
            }
        )
    dataset.write_jsonl(data / "review" / "human_check_log.jsonl", log)
    for g, s in per.items():
        s["error_rate"] = round(s["drop"] / s["n"], 4) if s["n"] else None
        s["error_rate_wilson95"] = wilson(s["drop"], s["n"])

    sample = {
        f"{r['id']}|{r['model']}|{r['condition']}": r
        for r in dataset.read_jsonl(data / "human_labels" / "sample_20pct.jsonl")
    }
    labels = []
    for key, b in sorted(ex.get("judge", {}).items()):
        if not b.get("g") or key not in sample:
            continue
        r = sample[key]
        g = b["g"]
        labels.append(
            {
                **r,
                "human_grade": "INCORRECT"
                if g in ("OTHER", "STALE", "NEAR_MISS")
                else g,
                "human_subtype": g if g in ("OTHER", "STALE", "NEAR_MISS") else None,
                "uncertain": bool(b.get("u")),
                "lang": r["id"].rsplit("-", 1)[1],
                "translation_aid": bool(b.get("translation_aid")),
                "annotator": args.annotator,
                "labelled_at": b.get("at"),
            }
        )
    dataset.write_jsonl(
        data / "human_labels" / f"labels_{args.annotator}.jsonl", labels
    )
    def judge_rows(name):
        snap = data / "human_labels" / f"sample_grades_{name.replace('/', '_').replace(':', '_')}.jsonl"
        if snap.exists():  # grades as they were when the sample was drawn
            return dataset.read_jsonl(snap)
        rows = []
        for p in sorted((data / "judgements").glob("*.jsonl")):
            rows += [j for j in dataset.read_jsonl(p) if j.get("judge_model") == name]
        return rows

    def full(judgements):
        if not labels:
            return {"n": 0}
        a = human.agreement(labels, judgements)
        a["by_language_group"] = {
            "de (original only)": human.agreement([x for x in labels if x["lang"] == "de"], judgements),
            "fr/it (human with machine translation)": human.agreement([x for x in labels if x["lang"] != "de"], judgements),
        }
        return a

    agree = full(judge_rows(args.judge_model))
    agree["judge_model"] = args.judge_model
    agree["translation_aid"] = ex.get("translation_aid")
    agree["uncertain_labels"] = sum(x["uncertain"] for x in labels)
    for other in args.also:
        rows = judge_rows(other)
        if rows:
            agree[f"vs_{other}"] = full(rows)
    summary = {
        "annotator": args.name,
        "exported_at": ex.get("exported_at"),
        "dataset_check": per,
        "judge_agreement": agree,
        "judge_sample_size": len(sample),
        "judge_labelled": len(labels),
    }
    (data / "human_labels" / "agreement.json").write_text(
        json.dumps(agree, indent=1) + "\n", encoding="utf-8"
    )
    (data / "human_labels" / "summary.json").write_text(
        json.dumps(summary, indent=1) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
