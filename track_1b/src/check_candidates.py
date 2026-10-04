"""Automatic checks and pre-sorting of candidate cores (Nemotron) before the human review.

Per core: validator errors/warnings (same rules as for the dataset), duplicates against merged and between
candidates, quote and evidence verbatim in the current fedlex version, outdated evidence verbatim in an
earlier version, clean STALE pair, yes/no, provenance complete. Writes checks.json and checks.md.

python src/check_candidates.py --fedlex <fedlex-v2> --merged data/merged.v1.jsonl
    --candidates data/candidates/nemotron-v2/candidates.jsonl data/candidates/nemotron-pilot/candidates.ultra.jsonl
    --out data/candidates/checks
"""

import argparse
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate_items as V  # noqa: E402

V.AUTHORS.add("nemotron")
PROVENANCE = ("generator", "generator_model", "generated_at", "prompt_version")
CONTENT_WARN = {
    "question.contains_answer_number",
    "question.answer_overlap",
    "answer.threshold_word",
    "style.article_in_question",
    "style.long_answer",
    "answer.inflected",
    "answer.number_literal_only",
    "answer.no_variations",
    "temporal.evidence_unchanged",
    "lang.core_inconsistent",
    "lang.yes_no_inconsistent",
}


def core_of(rid):
    return rid.rsplit("-", 1)[0] if rid[-3:] in ("-de", "-fr", "-it") else rid


def load(paths):
    rows = []
    for p in paths:
        rows += [
            json.loads(x)
            for x in Path(p).read_text(encoding="utf-8").splitlines()
            if x.strip()
        ]
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fedlex", required=True)
    ap.add_argument("--merged", default="data/merged.v1.jsonl")
    ap.add_argument("--candidates", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    src = V.Sources(args.fedlex)
    merged = load([args.merged])
    cands = load(args.candidates)
    cand_ids = {r["core_id"] for r in cands}

    issues = V.Issues()
    seen = set()
    for r in cands:
        V.check_record(r, src, issues, seen)
    V.cross_checks(merged + cands, issues)
    per_core = collections.defaultdict(list)
    for i in issues.items:
        ids = {core_of(i["id"])} | {
            core_of(x)
            for x in re.findall(
                r"\b(?:cl|cx|ag|nm[a-z])-\d{4}(?:-(?:de|fr|it))?\b", i["msg"]
            )
        }
        if not ids & cand_ids:
            continue
        for c in ids & cand_ids:
            per_core[c].append(i)

    by_core = collections.defaultdict(dict)
    for r in cands:
        by_core[r["core_id"]][r["lang"][:2]] = r
    same_value = collections.defaultdict(set)
    for r in merged + cands:
        an = r.get("answer_normalized")
        if r["lang"] == "de-CH" and isinstance(an, dict) and an.get("value") is not None:
            same_value[(r["source"]["act"], r["source"]["article_id"], an.get("value"), an.get("unit"))].add(r["core_id"])

    out = {}
    for cid, langs in sorted(by_core.items()):
        de = langs.get("de") or next(iter(langs.values()))
        own = per_core.get(cid, [])
        errors = sorted({i["code"] for i in own if i["level"] == "ERROR"})
        warns = sorted({i["code"] for i in own if i["level"] == "WARN"})
        dups = sorted(
            {
                core_of(x)
                for i in own
                if i["code"].startswith("dup.")
                for x in re.findall(
                    r"\b(?:cl|cx|ag|nm[a-z])-\d{4}(?:-(?:de|fr|it))?\b",
                    i["id"] + " " + i["msg"],
                )
                if core_of(x) != cid
            }
        )
        an = de.get("answer_normalized")
        if isinstance(an, dict) and an.get("value") is not None:
            key = (de["source"]["act"], de["source"]["article_id"], an.get("value"), an.get("unit"))
            dups = sorted(set(dups) | (same_value[key] - {cid}))
        dups = [d for d in dups if d not in cand_ids or d < cid]
        temporal = de.get("question_type") == "temporal"
        outdated_ok = None
        if temporal:
            outdated_ok = all(
                bool(r.get("outdated_answers"))
                and all(
                    v.get("evidence_found", True)
                    for v in (r["temporal"].get("outdated_versions") or [])
                )
                and not any(
                    i["code"].startswith("temporal.")
                    and i["level"] == "ERROR"
                    and i["id"] == r["id"]
                    for i in own
                )
                for r in langs.values()
            )
        quote_ok = not any(
            c.startswith(("source.", "evidence."))
            and c != "source.discretion"
            and c != "source.future_change"
            for c in errors
        )
        stale_pair = bool(temporal and outdated_ok and not errors)
        yes_no = (
            de.get("question_type") == "yes_no" or de.get("answer_type") == "yes_no"
        )
        prov_ok = all(r.get(k) for r in langs.values() for k in PROVENANCE) and all(
            r.get("needs_human_review") is True for r in langs.values()
        )
        content_warns = [w for w in warns if w in CONTENT_WARN]
        if errors:
            tier = "D_errors"
        elif dups:
            tier = "C_duplicate"
        elif stale_pair:
            tier = "A_stale_pair" if not content_warns else "B_stale_pair_warn"
        else:
            tier = "B_no_stale_pair" if not content_warns else "C_no_stale_pair_warn"
        out[cid] = {
            "core_id": cid,
            "act": de["source"]["act"],
            "article_id": de["source"]["article_id"],
            "paragraph": de["source"]["paragraph"],
            "langs": sorted(langs),
            "question_type": de.get("question_type"),
            "change_kind": (de.get("candidate") or {}).get("change_kind"),
            "bucket": de["temporal"].get("bucket"),
            "errors": errors,
            "warnings": warns,
            "messages": [
                f"{i['level']} {i['code']} {i['id']}: {i['msg']}" for i in own
            ][:12],
            "duplicate_of": dups,
            "quote_ok": quote_ok,
            "outdated_in_earlier_version": outdated_ok,
            "stale_pair": stale_pair,
            "yes_no": yes_no,
            "provenance_ok": prov_ok,
            "tier": tier,
        }

    outp = Path(args.out)
    outp.mkdir(parents=True, exist_ok=True)
    (outp / "checks.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    n = len(out)
    tiers = collections.Counter(v["tier"] for v in out.values())
    by_prefix = collections.defaultdict(collections.Counter)
    for v in out.values():
        p = v["core_id"][:3]
        by_prefix[p]["cores"] += 1
        by_prefix[p]["no_errors"] += not v["errors"]
        by_prefix[p]["stale_pair"] += v["stale_pair"]
        by_prefix[p]["yes_no"] += v["yes_no"]
        by_prefix[p]["duplicate"] += bool(v["duplicate_of"])
        by_prefix[p]["provenance_ok"] += v["provenance_ok"]
    lines = [
        "# Candidate checks",
        "",
        f"{n} candidate cores from {', '.join(Path(p).as_posix() for p in args.candidates)}.",
        "",
        "| Prefix | Cores | No validator error | Clean STALE pair | Yes/no | Duplicate | Provenance complete |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for p, c in sorted(by_prefix.items()):
        lines.append(
            f"| `{p}` | {c['cores']} | {c['no_errors']} | {c['stale_pair']} | {c['yes_no']} | {c['duplicate']} | {c['provenance_ok']} |"
        )
    lines += ["", "| Tier | Cores |", "| --- | ---: |"] + [
        f"| {t} | {k} |" for t, k in sorted(tiers.items())
    ]
    lines += [
        "",
        "Error codes: "
        + ", ".join(
            f"{k} {v}"
            for k, v in collections.Counter(
                e for v in out.values() for e in v["errors"]
            ).most_common()
        ),
    ]
    (outp / "checks.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
