"""Build the human check file (one self-contained HTML page, works offline).

Part A: stratified random sample of frozen cores (stratum "stale": cores with outdated answers; stratum
"other": the rest), to estimate the item error rate per stratum. Part B: blind judge sample, a stratified
random share of the judged responses of one model and condition (judge grade hidden).

The sample definitions are written to data/human_labels/ so the analysis is reproducible.

python src/make_check_file.py --judge-model qwen/qwen3-235b-a22b-2507 --out <file.html>
"""

import argparse
import collections
import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from inkraft import dataset, human  # noqa: E402

SEED = 20261013


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "data"))
    ap.add_argument("--judge-model", required=True)
    ap.add_argument("--model", default="apertus-v1.5-70b")
    ap.add_argument("--condition", default="closed_dated")
    ap.add_argument("--n-stale", type=int, default=15)
    ap.add_argument("--n-other", type=int, default=20)
    ap.add_argument(
        "--share",
        type=float,
        default=0.22,
        help="judge sample share (20 %% plus a margin for later drops)",
    )
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    data = Path(args.data)
    freeze = json.loads((data / "FREEZE.json").read_text(encoding="utf-8"))
    rows = dataset.read_jsonl(next(data.glob(f"merged.v{freeze['version']}.jsonl")))
    cores = collections.defaultdict(dict)
    for r in rows:
        cores[r["core_id"]][r["lang"][:2]] = r
    stale = sorted(c for c, x in cores.items() if x["de"].get("outdated_answers"))
    other = sorted(c for c in cores if c not in set(stale))
    rng = random.Random(SEED)
    pick = [
        (c, "stale") for c in sorted(rng.sample(stale, min(args.n_stale, len(stale))))
    ]
    pick += [
        (c, "other") for c in sorted(rng.sample(other, min(args.n_other, len(other))))
    ]
    rng.shuffle(pick)

    def core_view(cid, group):
        x = cores[cid]
        de = x["de"]
        s, t = de["source"], de.get("temporal") or {}
        view = {
            "core_id": cid,
            "group": group,
            "question_type": de["question_type"],
            "generator": de["generator"],
            "act": s["act"],
            "article": s["article"],
            "paragraph": s.get("paragraph"),
            "version_date": s["version_date"],
            "previous_version_date": t.get("previous_version_date"),
            "rows": {},
        }
        for lang, r in x.items():
            tt = r.get("temporal") or {}
            view["rows"][lang] = {
                k: r.get(k)
                for k in (
                    "question",
                    "answer",
                    "answer_aliases",
                    "near_miss_answers",
                    "outdated_answers",
                )
            } | {
                "quote": r["source"]["quote"],
                "evidence": r["source"]["evidence"],
                "url": r["source"].get("article_url") or r["source"].get("eli_url"),
                "previous_evidence": tt.get("previous_evidence")
                or next(
                    (
                        v.get("evidence")
                        for v in tt.get("outdated_versions") or []
                        if v.get("evidence")
                    ),
                    None,
                )
                if r.get("outdated_answers")
                else None,
            }
        return view

    items = {it["id"]: it for it in dataset.load(data)}
    jsample = [
        r
        for r in human.sample(
            list(items.values()), data, args.judge_model, share=args.share
        )
        if r["model"] == args.model and r["condition"] == args.condition
    ]
    # order independent of the other response files (human.sample shuffles across all of them)
    jsample.sort(key=lambda r: r["id"])
    random.Random(SEED).shuffle(jsample)
    judge_view = []
    for r in jsample:
        it = items[r["id"]]
        judge_view.append(
            {
                "key": f"{r['id']}|{r['model']}|{r['condition']}",
                **{k: r[k] for k in ("id", "model", "condition", "response")},
                **{
                    k: it.get(k)
                    for k in (
                        "question",
                        "answer",
                        "answer_aliases",
                        "outdated_answers",
                        "near_miss_answers",
                    )
                },
            }
        )
    out_dir = data / "human_labels"
    out_dir.mkdir(exist_ok=True)
    dataset.write_jsonl(
        out_dir / "dataset_sample.jsonl",
        [{"core_id": c, "stratum": g} for c, g in pick],
    )
    dataset.write_jsonl(out_dir / "sample_20pct.jsonl", jsample)
    n_judged = sum(
        1
        for j in dataset.read_jsonl(
            data
            / "judgements"
            / f"{args.judge_model.replace('/', '_').replace(':', '_')}__{args.model}__{args.condition}.jsonl"
        )
        if j.get("grade")
    )
    meta = {
        "version": freeze["version"],
        "seed": SEED,
        "strata": {"stale": len(stale), "other": len(other)},
        "dataset_sample": collections.Counter(g for _, g in pick),
        "judge_sample": len(jsample),
        "judged_responses": n_judged,
        "judge_share": round(len(jsample) / max(1, n_judged), 4),
        "model": args.model,
        "condition": args.condition,
        "judge_model": args.judge_model,
    }
    (out_dir / "sample_meta.json").write_text(
        json.dumps(meta, indent=1) + "\n", encoding="utf-8"
    )
    fp = hashlib.sha256(
        json.dumps([pick, [v["key"] for v in judge_view]]).encode()
    ).hexdigest()[:10]
    meta["sample_fingerprint"] = fp
    (out_dir / "sample_meta.json").write_text(
        json.dumps(meta, indent=1) + "\n", encoding="utf-8"
    )
    payload = {
        "version": f"{freeze['version']}-{fp}",
        "cores": [core_view(c, g) for c, g in pick],
        "judge": judge_view,
    }
    tpl = (ROOT.parent / "tools" / "check" / "template.html").read_text(
        encoding="utf-8"
    )
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    Path(args.out).write_text(tpl.replace("__DATA__", blob), encoding="utf-8")
    print(json.dumps(meta, indent=1))
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
