"""After the human review: apply the exported decisions to the dataset and the candidates, recompute the
temporal buckets per evidence sentence and write merged.v2.jsonl with a summary. Does not freeze.

Inputs are the exports of the review tool (tools/review): review_decisions.json and review_log.jsonl.

python src/after_review.py --fedlex <fedlex-v2> --decisions data/review/review_decisions.json
    --log data/review/review_log.jsonl [--allow-open]
"""

import argparse
import collections
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
sys.path.insert(0, str(HERE))
from find_changes import Fedlex, bucket_of, norm  # noqa: E402

CANDIDATE_FILES = [
    DATA / "candidates" / "nemotron-v2" / "candidates.jsonl",
    DATA / "candidates" / "nemotron-pilot" / "candidates.ultra.jsonl",
]
CANDIDATE_PREFIXES = ("nmu-", "nmv-", "nms-")


def read(path):
    return [
        json.loads(x)
        for x in Path(path).read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


def write(path, rows):
    Path(path).write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8",
        newline="\n",
    )


def apply(decisions_spec, src, out):
    tmp = Path(out).with_suffix(".decisions.json")
    tmp.write_text(
        json.dumps(decisions_spec, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    subprocess.run(
        [sys.executable, str(HERE / "apply_review.py"), str(tmp), str(src), str(out)],
        check=True,
    )
    tmp.unlink()
    return read(out)


def sentence_bucket(fx, r):
    act, aid = r["source"]["act"], r["source"]["article_id"]
    lang = r["lang"][:2]
    ev = norm(r["source"]["evidence"])
    earlier = fx.earlier_dates(act)
    missing = [
        d for d in earlier if ev not in fx.article_text(act, aid, lang=lang, date=d)
    ]
    since = (
        min([fx.current_date(act)] + [d for d in earlier if d > missing[0]])
        if missing
        else None
    )
    return bucket_of(since), since


def stats(rows):
    de = [r for r in rows if r["lang"] == "de-CH"]
    temporal_changed = [r for r in de if r["temporal"]["bucket"] != "stable_pre2024"]
    stale = [r for r in temporal_changed if r.get("outdated_answers")]
    yes_no = [
        r for r in de if r["question_type"] == "yes_no" or r["answer_type"] == "yes_no"
    ]
    langs = collections.Counter(r["core_id"] for r in rows)
    no_var = [
        r for r in rows if r["answer_type"] != "yes_no" and not r.get("answer_aliases")
    ]
    return {
        "cores": len(de),
        "rows": len(rows),
        "trilingual_cores": sum(1 for v in langs.values() if v == 3),
        "temporal_changed_cores": len(temporal_changed),
        "stale_pair_cores": len(stale),
        "yes_no_cores": len(yes_no),
        "yes_no_share": round(len(yes_no) / max(1, len(de)), 3),
        "rows_without_variants": len(no_var),
        "by_generator": dict(collections.Counter(r["generator"] for r in de)),
        "by_act": dict(collections.Counter(r["source"]["act"] for r in de)),
        "by_domain": dict(collections.Counter(r["domain"] for r in de)),
        "by_question_type": dict(collections.Counter(r["question_type"] for r in de)),
        "by_bucket": dict(collections.Counter(r["temporal"]["bucket"] for r in de)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fedlex", required=True)
    ap.add_argument("--decisions", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--merged", default=str(DATA / "merged.v1.jsonl"))
    ap.add_argument("--out", default=str(DATA / "merged.v2.jsonl"))
    ap.add_argument(
        "--allow-open",
        action="store_true",
        help="continue although cores have no final decision",
    )
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    spec = json.loads(Path(args.decisions).read_text(encoding="utf-8"))
    log = read(args.log)
    log_sha = hashlib.sha256(Path(args.log).read_bytes()).hexdigest()
    final = {}
    for e in log:
        if e["decision"] == "reset":
            final.pop(e["core_id"], None)
        else:
            final[e["core_id"]] = e
    decided = {d["core_id"]: d for d in spec["decisions"]}

    merged = read(args.merged)
    cands = [r for p in CANDIDATE_FILES if p.exists() for r in read(p)]
    existing_ids = {r["core_id"] for r in merged}
    open_existing = sorted(existing_ids - set(decided))
    print(
        f"existing cores: {len(existing_ids)}, decided {len(existing_ids & set(decided))}, open {len(open_existing)}"
    )
    if open_existing and not args.allow_open:
        sys.exit(
            f"{len(open_existing)} existing cores without a final decision (first: {open_existing[:5]}); finish the review or pass --allow-open"
        )

    work = Path(args.out).parent / "review"
    work.mkdir(parents=True, exist_ok=True)
    spec_existing = {
        **spec,
        "decisions": [d for d in spec["decisions"] if d["core_id"] in existing_ids],
    }
    spec_cands = {
        **spec,
        "decisions": [
            d for d in spec["decisions"] if d["core_id"].startswith(CANDIDATE_PREFIXES)
        ],
    }
    rows = apply(spec_existing, args.merged, work / "_existing.jsonl")

    cand_keep = {
        d["core_id"]
        for d in spec_cands["decisions"]
        if d["action"] in ("keep", "patch")
    }
    cand_src = work / "_candidates.in.jsonl"
    write(cand_src, [r for r in cands if r["core_id"] in cand_keep])
    accepted = (
        apply(spec_cands, cand_src, work / "_candidates.jsonl") if cand_keep else []
    )
    for r in accepted:
        c = r.pop("candidate", {}) or {}
        r["authoring"]["candidate_batch"] = c.get("batch") or c.get("pilot")
        r["authoring"]["candidate_change_kind"] = c.get("change_kind")
        if r["core_id"].startswith("nmu-"):
            r["authoring"]["exposure_note"] = (
                "pilot candidate, answered once by Apertus 1.5 in the calibration pilot of 2026-10-04 before the review; kept on review only"
            )
    rows += accepted
    for f in work.glob("_*.jsonl"):
        f.unlink()

    fx = Fedlex(args.fedlex)
    moved = collections.Counter()
    per_core = {r["core_id"]: sentence_bucket(fx, r) for r in rows if r["lang"] == "de-CH"}
    for r in rows:
        t = r["temporal"]
        new, since = per_core.get(r["core_id"]) or sentence_bucket(fx, r)
        if t.get("bucket_level") != "sentence":
            t["article_bucket"] = t["bucket"]
        moved[(t.get("article_bucket", t["bucket"]), new)] += 1
        t["bucket"], t["bucket_level"], t["evidence_since"] = new, "sentence", since
        e = final.get(r["core_id"])
        r["review"] = {
            "decision": {"accept": "keep", "correct": "patch"}.get(
                e["decision"], e["decision"]
            )
            if e
            else None,
            "reviewer": e.get("reviewer") if e else None,
            "reviewed_at": e.get("timestamp") if e else None,
            "duration_s": e.get("duration_s") if e else None,
            "agent_revealed_before_decision": e.get("agent_revealed_before_decision")
            if e
            else None,
            "tool": e.get("tool") if e else None,
            "log_sha256": log_sha,
        }
    rows.sort(key=lambda r: (r["core_id"], r["lang"]))
    write(args.out, rows)

    st = stats(rows)
    st["decisions"] = dict(collections.Counter(d["action"] for d in spec["decisions"]))
    st["candidates_decided"] = len(spec_cands["decisions"])
    st["candidates_accepted"] = len({r["core_id"] for r in accepted})
    st["reject_rate_by_generator"] = {}
    gen_of = {r["core_id"]: r["generator"] for r in merged + cands}
    per_gen = collections.defaultdict(collections.Counter)
    for d in spec["decisions"]:
        per_gen[gen_of.get(d["core_id"], "?")][d["action"]] += 1
    for g, c in per_gen.items():
        st["reject_rate_by_generator"][g] = {
            "decided": sum(c.values()),
            "dropped": c["drop"],
            "rate": round(c["drop"] / max(1, sum(c.values())), 3),
        }
    times = [e.get("duration_s") or 0 for e in final.values()]
    st["review_time_h"] = round(sum(times) / 3600, 2)
    st["median_review_s"] = sorted(times)[len(times) // 2] if times else None
    st["bucket_moves"] = {f"{a}->{b}": n for (a, b), n in sorted(moved.items())}
    st["log_sha256"] = log_sha
    (work / "after_review_summary.json").write_text(
        json.dumps(st, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                k: st[k]
                for k in (
                    "cores",
                    "rows",
                    "trilingual_cores",
                    "temporal_changed_cores",
                    "stale_pair_cores",
                    "yes_no_share",
                    "rows_without_variants",
                    "candidates_accepted",
                )
            },
            indent=1,
        )
    )
    print(
        f"-> {args.out}; next: validate_items.py on it, then src/freeze.py (only after Niklas' go)"
    )


if __name__ == "__main__":
    main()
