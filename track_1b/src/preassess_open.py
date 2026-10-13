"""Repeat the candidate pre-assessment with an open model (default Qwen3-235B-A22B-2507 via OpenRouter).

Same candidates and the same criteria and verdict scale as the original pre-assessment of 2026-10-04
(claude-opus-5-5 agents; prompt text recovered from the agent transcripts and stored in
src/prompts/preassess_v1.txt). Input per core: current paragraph, earlier versions with outdated answer and
evidence, question/answer/variants/near misses/outdated answers per language, automatic check results.
Writes data/candidates/preassess-open/assessment.jsonl and compares with the original verdicts
(agreement, Cohen's kappa, list of disagreements). Changes nothing in the dataset.

python src/preassess_open.py --env <.env> [--model qwen/qwen3-235b-a22b-2507] [--max-usd 0.40]
"""

import argparse
import collections
import datetime as dt
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
CAND = DATA / "candidates"
sys.path.insert(0, str(HERE))
from inkraft.human import cohen_kappa  # noqa: E402
from second_check import call, env_value, read  # noqa: E402

PROMPT_FILE = HERE / "prompts" / "preassess_v1.txt"
VERDICTS = ["accept", "accept_minor", "revise", "reject"]
FILES = [
    (
        CAND / "nemotron-v2" / "candidates.jsonl",
        CAND / "nemotron-v2" / "assessment.json",
    ),
    (
        CAND / "nemotron-pilot" / "candidates.ultra.jsonl",
        CAND / "nemotron-pilot" / "assessment.ultra.json",
    ),
]
ITEM_KEYS = (
    "question",
    "answer",
    "answer_aliases",
    "near_miss_answers",
    "outdated_answers",
)


def core_input(core, checks):
    de = core.get("de") or next(iter(core.values()))
    s, t = de["source"], de.get("temporal") or {}
    out = {
        "core_id": de["core_id"],
        "question_type": de["question_type"],
        "answer_type": de["answer_type"],
        "act": s["act"],
        "article": s["article"],
        "paragraph": s.get("paragraph"),
        "current_version": s["version_date"],
        "current_paragraph": {
            lang: r["source"]["quote"] for lang, r in sorted(core.items())
        },
        "earlier_versions": {
            lang: [
                {
                    k: v.get(k)
                    for k in (
                        "version_date",
                        "paragraph",
                        "outdated_answer",
                        "evidence",
                    )
                }
                for v in (r.get("temporal") or {}).get("outdated_versions") or []
            ]
            or (
                [
                    {
                        "version_date": t.get("previous_version_date"),
                        "evidence": (r.get("temporal") or {}).get("previous_evidence"),
                    }
                ]
                if (r.get("temporal") or {}).get("previous_evidence")
                else []
            )
            for lang, r in sorted(core.items())
        },
        "item": {
            lang: {k: r.get(k) for k in ITEM_KEYS} for lang, r in sorted(core.items())
        },
        "automatic_checks": {
            k: checks.get(k)
            for k in (
                "errors",
                "warnings",
                "quote_ok",
                "outdated_in_earlier_version",
                "stale_pair",
                "duplicate_of",
                "change_kind",
            )
        },
    }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True)
    ap.add_argument("--model", default="qwen/qwen3-235b-a22b-2507")
    ap.add_argument("--out", default=str(CAND / "preassess-open"))
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--max-usd", type=float, default=0.40)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    key = env_value(args.env, "OPENROUTER_API_KEY")
    template = PROMPT_FILE.read_text(encoding="utf-8")
    sha = hashlib.sha256(template.encode()).hexdigest()[:12]
    checks = json.loads((CAND / "checks" / "checks.json").read_text(encoding="utf-8"))
    cores, original = {}, {}
    for cand, assess in FILES:
        by = collections.defaultdict(dict)
        for r in read(cand):
            by[r["core_id"]][r["lang"][:2]] = r
        cores.update(by)
        original.update(
            {a["core_id"]: a for a in json.loads(assess.read_text(encoding="utf-8"))}
        )
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    res_path = out / "assessment.jsonl"
    done = {r["core_id"]: r for r in read(res_path)} if res_path.exists() else {}
    todo = sorted(
        c
        for c in cores
        if c in original and (done.get(c) or {}).get("verdict") not in VERDICTS
    )
    cost = [sum(r.get("cost_usd") or 0 for r in done.values())]

    def one(cid):
        if cost[0] > args.max_usd:
            return {"core_id": cid, "error": "budget stop"}
        prompt = template.replace(
            "{CORE}",
            json.dumps(
                core_input(cores[cid], checks.get(cid, {})),
                ensure_ascii=False,
                indent=1,
            ),
        )
        d, err = call(key, args.model, prompt, extra={"reasoning": {"enabled": False}} if "nemotron" in args.model else None)
        usage = (d or {}).get("usage") or {}
        cost[0] += usage.get("cost") or 0
        text = d["choices"][0]["message"].get("content") if d else None
        verdict, reason = None, None
        try:
            j = json.loads(text[text.index("{") : text.rindex("}") + 1])
            verdict, reason = j.get("verdict"), j.get("reason")
        except Exception:  # noqa: BLE001
            pass
        return {
            "core_id": cid,
            "verdict": verdict if verdict in VERDICTS else None,
            "reason": reason,
            "raw": None if verdict in VERDICTS else text,
            "error": err,
            "assessor": f"{args.model} (open-model pre-assessment, not a human review)",
            "prompt_version": f"preassess-v1 sha256:{sha}",
            "cost_usd": usage.get("cost"),
            "date": dt.date.today().isoformat(),
        }

    with ThreadPoolExecutor(args.workers) as ex:
        for fut in as_completed([ex.submit(one, c) for c in todo]):
            r = fut.result()
            done[r["core_id"]] = r
            print(r["core_id"], r["verdict"], flush=True)
    rows = [done[c] for c in sorted(done)]
    res_path.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8",
        newline="\n",
    )

    pairs = [
        (original[r["core_id"]]["verdict"], r["verdict"]) for r in rows if r["verdict"]
    ]
    a, b = zip(*pairs)
    usable = lambda v: v in ("accept", "accept_minor", "revise")  # noqa: E731  (release rule: reject drops)
    two = [(usable(x), usable(y)) for x, y in pairs]
    summary = {
        "original": "claude-opus-5-5 (agents, 2026-10-04)",
        "open_model": args.model,
        "n": len(pairs),
        "four_class": {
            "raw_agreement": round(sum(x == y for x, y in pairs) / len(pairs), 4),
            "kappa": round(cohen_kappa(a, b, classes=VERDICTS), 4),
            "confusion_original_rows_open_cols": {
                x: {y: sum(1 for p, q in pairs if p == x and q == y) for y in VERDICTS}
                for x in VERDICTS
            },
        },
        "keep_vs_reject": {
            "raw_agreement": round(sum(x == y for x, y in two) / len(two), 4),
            "kappa": round(
                cohen_kappa(
                    [x for x, _ in two], [y for _, y in two], classes=[True, False]
                ),
                4,
            ),
        },
        "verdicts_original": dict(collections.Counter(a)),
        "verdicts_open": dict(collections.Counter(b)),
        "failed": [r["core_id"] for r in rows if not r["verdict"]],
        "cost_usd": round(sum(r.get("cost_usd") or 0 for r in rows), 4),
        "disagreements": [
            {
                "core_id": r["core_id"],
                "original": original[r["core_id"]]["verdict"],
                "open": r["verdict"],
                "original_reason": original[r["core_id"]]["reason"],
                "open_reason": r["reason"],
            }
            for r in rows
            if r["verdict"] and r["verdict"] != original[r["core_id"]]["verdict"]
        ],
    }
    (out / "comparison.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps({k: v for k, v in summary.items() if k != "disagreements"}, indent=1)
    )


if __name__ == "__main__":
    main()
