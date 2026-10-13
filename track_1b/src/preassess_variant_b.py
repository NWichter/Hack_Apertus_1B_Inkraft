"""What would change in the release if only the open-model pre-assessment counted (variant b)?

Applies the release rules of auto_review.py with the open verdicts instead of the original ones and lists, per
candidate core, the consequence. Nothing is applied.

python src/preassess_variant_b.py [--open data/candidates/preassess-open/assessment.jsonl]
"""

import argparse
import collections
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
CAND = DATA / "candidates"


def read(p):
    return [
        json.loads(x)
        for x in Path(p).read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--open", default=str(CAND / "preassess-open" / "assessment.jsonl"))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = Path(args.out or Path(args.open).with_name("variant_b.json"))
    freeze = json.loads((DATA / "FREEZE.json").read_text(encoding="utf-8"))
    rc = {r["core_id"] for r in read(DATA / f"merged.v{freeze['version']}.jsonl")}
    checks = json.loads((CAND / "checks" / "checks.json").read_text(encoding="utf-8"))
    log = {e["core_id"]: e for e in read(DATA / "review" / "auto" / "review_log.jsonl")}
    open_v = {r["core_id"]: r for r in read(args.open)}
    items = collections.defaultdict(list)
    for cid, o in sorted(open_v.items()):
        tier = checks[cid]["tier"]
        in_rc = cid in rc
        v = o["verdict"]
        now = log[cid]["decision"] if cid in log else None
        if tier.startswith(("C_duplicate", "D_errors")):
            continue  # dropped by the automatic checks under both variants
        if v == "reject":
            kind = "leaves" if in_rc else None
        elif v == "accept":
            kind = (
                "stays, but without the original fix"
                if in_rc and now == "correct"
                else (
                    "stays"
                    if in_rc
                    else "enters (needs validator, second check, Apertus answers)"
                )
            )
        else:
            kind = (
                "stays, needs a fix from the open model's note"
                if in_rc
                else "enters only after a fix from the open model's note"
            )
        if kind and kind != "stays":
            items[kind].append(
                {
                    "core_id": cid,
                    "open": v,
                    "now": now,
                    "stale_pair_candidate": checks[cid]["stale_pair"],
                    "open_reason": o["reason"],
                }
            )
    res = {
        "release": freeze["version"],
        "counts": {k: len(v) for k, v in items.items()},
        "stale_pair_candidates_entering_directly": sum(
            1
            for x in items.get(
                "enters (needs validator, second check, Apertus answers)", []
            )
            if x["stale_pair_candidate"]
        ),
        "items": items,
    }
    out.write_text(
        json.dumps(res, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {k: v for k, v in res.items() if k != "items"}, ensure_ascii=False, indent=1
        )
    )


if __name__ == "__main__":
    main()
