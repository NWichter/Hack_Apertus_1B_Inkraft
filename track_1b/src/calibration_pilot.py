"""Calibration pilot: a small Apertus sample per change group, closed_dated, rule pre-grade only.

Plausibility check for the dataset plan, not a result. Items are never selected or dropped on these
answers. Groups (DE, seed 42, 12 cores each): stable_pre2024, article changed but evidence sentence
stable, evidence sentence changed with outdated answers; optionally candidate files on top.

Usage (LLM_BASE_URL and LLM_API_KEY from the environment):
  python src/find_changes.py --fedlex <dir> --out <tmp>
  python src/calibration_pilot.py --stability <tmp>/sentence_stability.json --out <dir> \
      [--candidates data/candidates/nemotron-pilot/candidates.ultra.jsonl]
"""

import argparse
import collections
import json
import os
import random
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from inkraft.client import Endpoint  # noqa: E402
from inkraft.pregrade import pregrade, provisional_grade  # noqa: E402
from inkraft.prompts import extra_params, messages, split_reasoning  # noqa: E402

MODELS = ("apertus-v1.5-8b", "apertus-v1.5-70b")
CONDITION = "closed_dated"


def sample(de, changed, per_group, seed):
    rnd = random.Random(seed)
    g_stale = sorted(c for c, r in de.items() if c in changed and r["outdated_answers"])
    g_art = sorted(
        c
        for c, r in de.items()
        if r["temporal"]["bucket"] != "stable_pre2024" and c not in changed
    )
    g_stable = sorted(
        c for c, r in de.items() if r["temporal"]["bucket"] == "stable_pre2024"
    )
    return {
        "changed_with_outdated": rnd.sample(g_stale, min(per_group, len(g_stale))),
        "article_changed_sentence_stable": rnd.sample(
            g_art, min(per_group, len(g_art))
        ),
        "stable_pre2024": rnd.sample(g_stable, min(per_group, len(g_stable))),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--items", default="data/merged.v1.jsonl")
    ap.add_argument(
        "--stability",
        required=True,
        help="sentence_stability.json from find_changes.py",
    )
    ap.add_argument("--candidates", action="append", default=[])
    ap.add_argument("--out", required=True)
    ap.add_argument("--per-group", type=int, default=12)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--max-calls", type=int, default=300)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    rows = [json.loads(line) for line in open(args.items, encoding="utf-8")]
    de = {r["core_id"]: r for r in rows if r["lang"] == "de-CH"}
    stab = json.loads(Path(args.stability).read_text(encoding="utf-8"))
    changed = {
        s["core_id"]
        for s in stab
        if s["bucket"] != "stable_pre2024" and s["status"] == "evidence_changed"
    }
    pick = sample(de, changed, args.per_group, args.seed)
    items = [dict(de[c], _group=g) for g, cs in pick.items() for c in cs]
    for path in args.candidates:
        items += [
            dict(json.loads(line), _group="candidate")
            for line in open(path, encoding="utf-8")
        ]
    n_calls = len(MODELS) * len(items)
    print(f"{len(items)} items x {len(MODELS)} models = {n_calls} calls")
    if n_calls > args.max_calls:
        raise SystemExit(f"call budget exceeded ({n_calls} > {args.max_calls})")

    base, key = os.environ.get("LLM_BASE_URL"), os.environ.get("LLM_API_KEY")

    def run(job):
        model, it = job
        try:
            d = Endpoint(base, key, model).chat(
                messages(it, CONDITION),
                temperature=0.0,
                max_tokens=300,
                **extra_params(CONDITION),
            )
            resp, _ = split_reasoning(d["choices"][0]["message"].get("content"))
        except Exception as e:  # noqa: BLE001
            resp = None
            print("ERR", model, it["id"], str(e)[:120])
        rule = pregrade(it, resp)["rule"]
        grade, subtype = provisional_grade(rule)
        return {
            "id": it["id"],
            "core_id": it["core_id"],
            "lang": it["lang"],
            "group": it["_group"],
            "model": model,
            "bucket": it["temporal"]["bucket"],
            "question_type": it["question_type"],
            "response": resp,
            "rule": rule,
            "grade": grade,
            "subtype": subtype,
        }

    with ThreadPoolExecutor(3) as ex:
        res = list(ex.map(run, [(m, it) for m in MODELS for it in items]))

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "responses.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in res), encoding="utf-8"
    )
    (out / "sample.json").write_text(json.dumps(pick, indent=1), encoding="utf-8")
    summary = collections.defaultdict(collections.Counter)
    for r in res:
        summary[(r["model"], r["group"])][r["rule"]] += 1
    for k in sorted(summary):
        print(k, dict(summary[k]))


if __name__ == "__main__":
    main()
