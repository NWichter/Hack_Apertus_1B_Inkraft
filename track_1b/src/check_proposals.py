"""Validate the patch proposals of review v3: apply each proposal to a copy of its core and run the validator.

python src/check_proposals.py --fedlex <fedlex-v2> --items data/merged.v1.jsonl
    --proposals data/candidates/review-v3/proposals.json --out data/candidates/review-v3/proposal_checks.json
"""

import argparse
import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate_items as V  # noqa: E402
from apply_review import set_path  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fedlex", required=True)
    ap.add_argument("--items", default="data/merged.v1.jsonl")
    ap.add_argument("--proposals", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    src = V.Sources(args.fedlex)
    rows = [
        json.loads(x)
        for x in Path(args.items).read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]
    props = json.loads(Path(args.proposals).read_text(encoding="utf-8"))
    out = {}
    for cid, p in props.items():
        if p.get("action") != "patch":
            continue
        issues, seen, patched = V.Issues(), set(), []
        for r in rows:
            if r["core_id"] != cid:
                continue
            r = copy.deepcopy(r)
            for k, v in {
                **(p.get("all") or {}),
                **(p.get(r["lang"][:2]) or {}),
            }.items():
                if v is not None:
                    set_path(r, k, v)
            if r.get("question_type") != "temporal":
                r["outdated_answers"] = r.get("outdated_answers") or []
            t = r.get("temporal") or {}
            if p.get("kind") == "outdated" and r.get("outdated_answers"):
                art = src.article_at(r["source"]["act"], r["source"]["article_id"], r["lang"][:2], t.get("previous_version_date"))
                ev = V.norm_text(t.get("previous_evidence") or "")
                if not art or not ev or ev not in V.norm_text(art["text"]):
                    issues.add("ERROR", "temporal.prev_evidence", r["id"], "outdated-answer evidence not in the stated version")
                elif not (V.extract_numbers(r["outdated_answers"][0], r["lang"][:2]) <= V.extract_numbers(t["previous_evidence"], r["lang"][:2])):
                    issues.add("ERROR", "temporal.outdated_not_in_prev", r["id"], "number of the outdated answer not in the evidence")
                if V.norm_text(r["outdated_answers"][0]) == V.norm_text(r["answer"]):
                    issues.add("ERROR", "temporal.same_value", r["id"], "outdated answer equals gold")
            patched.append(r)
            V.check_record(r, src, issues, seen)
        V.cross_checks(patched, issues)
        out[cid] = {
            "errors": sorted(
                {
                    f"{i['code']} ({i['id'][-2:]})"
                    for i in issues.items
                    if i["level"] == "ERROR"
                }
            ),
            "warnings": sorted(
                {
                    i["code"]
                    for i in issues.items
                    if i["level"] == "WARN" and i["code"] != "source.future_change"
                }
            ),
        }
    Path(args.out).write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    ok = sum(1 for v in out.values() if not v["errors"])
    print(f"{len(out)} patch proposals, {ok} without validator errors")


if __name__ == "__main__":
    main()
