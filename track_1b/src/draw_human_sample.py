"""Draw the two human-check samples of a frozen release (reproducible, fixed seed).

dataset_sample.jsonl: stratified random sample of cores (stratum "stale": cores with outdated answers; "other":
the rest) for the item error rate. sample_20pct.jsonl: stratified random 22 % of the judged responses of one model
and condition (inkraft.human.sample), for the human-judge agreement. sample_meta.json records seed, sizes and a
fingerprint of both samples. The annotation page itself is not part of this repository; any tool that shows
item, gold and response (and hides the judge grade) can be used, its export is read by src/import_human.py.

python src/draw_human_sample.py --judge-model qwen/qwen3-235b-a22b-2507 [--version 1.0.0-rc1]
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


def draw(
    data,
    judge_model,
    model="apertus-v1.5-70b",
    condition="closed_dated",
    n_stale=15,
    n_other=20,
    share=0.22,
    version=None,
):
    data = Path(data)
    version = (
        version
        or json.loads((data / "FREEZE.json").read_text(encoding="utf-8"))["version"]
    )
    rows = dataset.read_jsonl(data / f"merged.v{version}.jsonl")
    cores = collections.defaultdict(dict)
    for r in rows:
        cores[r["core_id"]][r["lang"][:2]] = r
    stale = sorted(c for c, x in cores.items() if x["de"].get("outdated_answers"))
    other = sorted(c for c in cores if c not in set(stale))
    rng = random.Random(SEED)
    pick = [(c, "stale") for c in sorted(rng.sample(stale, min(n_stale, len(stale))))]
    pick += [(c, "other") for c in sorted(rng.sample(other, min(n_other, len(other))))]
    rng.shuffle(pick)
    items = {it["id"]: it for it in dataset.load(data)}
    jsample = [
        r
        for r in human.sample(list(items.values()), data, judge_model, share=share)
        if r["model"] == model and r["condition"] == condition
    ]
    jsample.sort(key=lambda r: r["id"])
    random.Random(SEED).shuffle(jsample)
    keys = [f"{r['id']}|{r['model']}|{r['condition']}" for r in jsample]
    fp = hashlib.sha256(json.dumps([pick, keys]).encode()).hexdigest()[:10]
    return (
        pick,
        jsample,
        fp,
        {
            "version": version,
            "seed": SEED,
            "strata": {"stale": len(stale), "other": len(other)},
            "dataset_sample": dict(collections.Counter(g for _, g in pick)),
            "judge_sample": len(jsample),
            "model": model,
            "condition": condition,
            "judge_model": judge_model,
            "sample_fingerprint": fp,
        },
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "data"))
    ap.add_argument("--judge-model", required=True)
    ap.add_argument(
        "--version", help="release the sample is drawn from (default: FREEZE.json)"
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="only verify that the stored samples are reproduced",
    )
    args = ap.parse_args()
    data = Path(args.data)
    pick, jsample, fp, meta = draw(data, args.judge_model, version=args.version)
    out = data / "human_labels"
    if args.check:
        stored = json.loads((out / "sample_meta.json").read_text(encoding="utf-8"))
        ok = stored.get("sample_fingerprint") == fp
        print(
            f"stored {stored.get('sample_fingerprint')}, recomputed {fp}: {'OK' if ok else 'DIFFERENT'}"
        )
        sys.exit(0 if ok else 1)
    out.mkdir(exist_ok=True)
    dataset.write_jsonl(
        out / "dataset_sample.jsonl", [{"core_id": c, "stratum": g} for c, g in pick]
    )
    dataset.write_jsonl(out / "sample_20pct.jsonl", jsample)
    (out / "sample_meta.json").write_text(
        json.dumps(meta, indent=1) + "\n", encoding="utf-8"
    )
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
