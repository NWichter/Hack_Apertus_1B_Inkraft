"""Automatic review decisions for the release candidate (no human involved).

Writes a decision file and a review log in the format of the review tool, so that after_review.py and
freeze.py treat them like any review. Every log entry has reviewer "automatic (...)"; freeze.py then marks
the rows auto_verified (never reviewed). A later human log overrides single cores (--human-log).

Rules, in this order:
- existing cores: drop paragraph clusters and near-duplicates (review-v3 proposals); patch additive
  proposals (answer variants, outdated answers) when check_proposals found no error; keep the rest.
- candidates: drop pre-assessment "reject", validator errors and duplicates; keep "accept"; patch
  "accept_minor"/"revise" only with an auto-fix patch (auto_fix.py), else drop; keep unassessed ones
  without validator errors.
- --validator-issues: drop cores whose rows still have validator errors after patching.
- --second-check: drop cores with verdict "problem" from the independent check (second_check.py).

python src/auto_review.py --out data/review/auto [--validator-issues f.json] [--second-check f.jsonl]
    [--human-log data/review/review_log.jsonl]
"""

import argparse
import collections
import datetime as dt
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
REVIEWER = "automatic (auto_review.py v1)"
CAND = DATA / "candidates"


def read(path):
    return [
        json.loads(x)
        for x in Path(path).read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DATA / "review" / "auto"))
    ap.add_argument("--validator-issues")
    ap.add_argument("--second-check")
    ap.add_argument(
        "--human-log", help="review_log.jsonl of a human check; its decisions win"
    )
    args = ap.parse_args()

    merged = read(DATA / "merged.v1.jsonl")
    existing = sorted({r["core_id"] for r in merged})
    proposals = load_json(CAND / "review-v3" / "proposals.json")
    pchecks = load_json(CAND / "review-v3" / "proposal_checks.json")
    checks = load_json(CAND / "checks" / "checks.json")
    verdicts = {
        a["core_id"]: a
        for p in ("nemotron-v2/assessment.json", "nemotron-pilot/assessment.ultra.json")
        for a in load_json(CAND / p)
    }
    fix_file = CAND / "auto-fix" / "patches.json"
    fixes = load_json(fix_file) if fix_file.exists() else {}

    decisions, why = [], collections.Counter()

    def decide(cid, action, reason, patch=None):
        d = {"core_id": cid, "action": action, "reason": reason}
        if patch:
            for k in ("all", "de", "fr", "it"):
                if patch.get(k):
                    d[k] = patch[k]
        decisions.append(d)
        why[reason.split(":")[0]] += 1

    for cid in existing:
        p = proposals.get(cid)
        if p and p["kind"] in ("cluster", "duplicate"):
            decide(cid, "drop", f"{p['kind']}: {p['summary']}")
        elif (
            p
            and p["kind"] in ("variants", "outdated", "outdated+variants")
            and not pchecks.get(cid, {}).get("errors")
        ):
            decide(
                cid,
                "patch",
                f"proposal {p['kind']}: {p['summary']} ({p['provenance']['generator_model']})",
                p,
            )
        else:
            decide(cid, "keep", "existing core, no applicable proposal")

    for cid, c in sorted(checks.items()):
        v = (verdicts.get(cid) or {}).get("verdict")
        if c["tier"].startswith(("C_duplicate", "D_errors")):
            decide(cid, "drop", f"candidate check: {c['tier']}")
        elif v == "reject":
            decide(
                cid, "drop", "pre-assessment reject: " + verdicts[cid]["reason"][:200]
            )
        elif v == "accept":
            decide(cid, "keep", "pre-assessment accept")
        elif v in ("accept_minor", "revise"):
            if cid in fixes:
                decide(
                    cid,
                    "patch",
                    f"auto fix ({v}): " + fixes[cid]["summary"][:250],
                    fixes[cid],
                )
            else:
                decide(cid, "drop", f"pre-assessment {v} without a usable auto fix")
        else:
            decide(cid, "keep", "candidate without pre-assessment, no validator error")

    v3 = CAND / "nemotron-v3" / "candidates.jsonl"
    if v3.exists():
        for cid in sorted({r["core_id"] for r in read(v3)}):
            decide(
                cid,
                "keep",
                "new-act candidate (nemotron-v3), checked by validator and second check only",
            )

    by_core = {d["core_id"]: d for d in decisions}
    if args.validator_issues:
        bad = collections.defaultdict(set)
        for i in load_json(args.validator_issues):
            if i["level"] == "ERROR":
                bad[i["id"].rsplit("-", 1)[0]].add(i["code"])
        for cid, codes in bad.items():
            if cid in by_core and by_core[cid]["action"] != "drop":
                by_core[cid].update(
                    action="drop",
                    reason="validator error after patch: " + ", ".join(sorted(codes)),
                )
                for k in ("all", "de", "fr", "it"):
                    by_core[cid].pop(k, None)
                why["validator error after patch"] += 1
    if args.second_check:
        # calc items: the checker sees no calc_evidence; the validator recomputes them (calc.*)
        calc = {r["core_id"] for r in merged if r["question_type"] == "calc"}
        for r in read(args.second_check):
            d = by_core.get(r["core_id"])
            if r.get("verdict") == "problem" and r["core_id"] in calc:
                why[
                    "second check problem on calc item (kept, validator recomputes)"
                ] += 1
                continue
            if d and d["action"] != "drop" and r.get("verdict") == "problem":
                d.update(
                    action="drop",
                    reason="second check problem: " + (r.get("issue") or "")[:200],
                )
                for k in ("all", "de", "fr", "it"):
                    d.pop(k, None)
                why["second check problem"] += 1

    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    act = {"keep": "accept", "patch": "correct", "drop": "drop"}
    log = [
        {
            "core_id": d["core_id"],
            "decision": act[d["action"]],
            "reviewer": REVIEWER,
            "timestamp": now,
            "duration_s": None,
            "agent_revealed_before_decision": None,
            "tool": "src/auto_review.py",
            "reason": d["reason"],
        }
        for d in decisions
    ]
    if args.human_log:
        human = {}
        for e in read(args.human_log):
            human[e["core_id"]] = e
        for e in human.values():
            log.append(e)
            if e["decision"] == "drop":
                by_core[e["core_id"]].update(
                    action="drop", reason="human: " + str(e.get("note") or "")
                )
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    spec = {"version": "auto-review-v1", "reviewer": REVIEWER, "decisions": decisions}
    (out / "review_decisions.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    (out / "review_log.jsonl").write_text(
        "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in log), encoding="utf-8"
    )
    acts = collections.Counter(d["action"] for d in decisions)
    print(dict(acts))
    for k, n in why.most_common():
        print(f"  {n:4d}  {k}")


if __name__ == "__main__":
    main()
