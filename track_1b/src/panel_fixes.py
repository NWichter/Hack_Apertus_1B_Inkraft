"""Use the panel's disagreements to find missing answer variants and unclear questions (before the freeze).

1. Rows where the panel judges disagree (closed_dated and open_book) are grouped per core and language.
2. For each, an open model (default Qwen3-235B) reads the cited paragraph, the gold answer, the variants and the
   disputed responses and proposes (a) answer variants that state the gold answer in another form, each with a
   verbatim evidence span from the paragraph, and (b) whether the question is ambiguous.
3. A variant is accepted only if it is checkable without any judge: its numbers equal the numbers of the gold answer
   (numeric answers) or all its content words occur in the cited paragraph (text answers), it contains no number of
   an outdated or near-miss answer, and the evidence span occurs verbatim in the paragraph.
4. Accepted variants become a decision file for src/apply_review.py (data/review/panel_fixes.json, reviewer
   "automatic (panel_fixes.py)"); ambiguous questions are only listed (data/review/panel_flags.json) for a human.

python src/panel_fixes.py --env <.env> [--src data/merged.v2.jsonl]
"""

import argparse
import collections
import datetime as dt
import json
import re
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
sys.path.insert(0, str(HERE))
from inkraft import dataset  # noqa: E402
from second_check import call, env_value  # noqa: E402

MODEL = "qwen/qwen3-235b-a22b-2507"
PROMPT = """A benchmark item about Swiss federal law (as of {as_of}) was graded differently by several judges. Decide only from the statute text below.

Question ({lang}): {question}
Gold answer: {answer}
Accepted variants: {aliases}
Outdated answers (wrong): {outdated}
Near-miss answers (wrong): {near}

Cited paragraph ({act} art. {article}):
{quote}

Model answers the judges disagreed on:
{responses}

Tasks:
1. "variants": other ways to state exactly the gold answer that a careful grader would accept (e.g. another unit spelling, a shorter or longer wording from the paragraph). Never a different value, never an equivalence the paragraph does not state. For each give "variant" (max 8 words, in {lang}) and "evidence" (a verbatim span copied from the paragraph that supports it). Empty list if none.
2. "ambiguous": true if the question, read alone, allows more than one defensible answer according to the paragraph; then "why" in one sentence.

Reply with JSON only: {{"variants": [{{"variant": "...", "evidence": "..."}}], "ambiguous": false, "why": ""}}"""

NUM = re.compile(r"\d{1,3}(?:['’  ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?")


def nums(text):
    return sorted(
        str(
            float(
                x.replace("'", "")
                .replace("’", "")
                .replace(" ", "")
                .replace(" ", "")
                .replace(",", ".")
            )
        )
        for x in NUM.findall(text or "")
    )


def norm(text):
    t = unicodedata.normalize("NFKC", text or "").lower().replace("’", "'")
    return re.sub(r"\s+", " ", t).strip()


def words(text):
    return [w for w in re.findall(r"[^\W\d_]{4,}", norm(text))]


def check_variant(row, v):
    quote = norm(row["source"]["quote"])
    var, ev = v.get("variant") or "", v.get("evidence") or ""
    if not var.strip() or norm(var) in {
        norm(x) for x in [row["answer"], *(row.get("answer_aliases") or [])]
    }:
        return "duplicate or empty"
    if not ev or norm(ev) not in quote:
        return "evidence not verbatim in the paragraph"
    gold_nums = nums(row["answer"])
    bad = set()
    for x in (row.get("outdated_answers") or []) + (row.get("near_miss_answers") or []):
        bad |= set(nums(x)) - set(gold_nums)
    if set(nums(var)) & bad:
        return "contains a number of an outdated or near-miss answer"
    if gold_nums:
        if nums(var) != gold_nums:
            return "numbers differ from the gold answer"
        return None
    if row["answer_type"] == "yes_no":
        return "yes/no answers get no new variants"
    missing = [w for w in words(var) if w not in quote]
    return f"words not in the paragraph: {missing[:3]}" if missing else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True)
    ap.add_argument("--src", default=str(DATA / "merged.v2.jsonl"))
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    key = env_value(args.env, "OPENROUTER_API_KEY")
    rows = {r["id"]: r for r in dataset.read_jsonl(args.src)}
    disputed = collections.defaultdict(list)
    for p in sorted((DATA / "judgements").glob("panel__*.jsonl")):
        resp = {
            r["id"]: r
            for r in dataset.read_jsonl(
                DATA / "responses" / p.name.replace("panel__", "", 1)
            )
        }
        for j in dataset.read_jsonl(p):
            if len({v["grade"] for v in j["votes"].values()}) > 1 and j["id"] in rows:
                disputed[j["id"]].append(resp[j["id"]]["response"])
    out_dir = DATA / "review"
    raw_path = out_dir / "panel_fixes_raw.jsonl"
    cache = (
        {r["id"]: r for r in dataset.read_jsonl(raw_path)} if raw_path.exists() else {}
    )

    def one(rid):
        r = rows[rid]
        prompt = PROMPT.format(
            as_of=r["as_of"],
            lang=r["lang"],
            question=r["question"],
            answer=r["answer"],
            aliases="; ".join(r.get("answer_aliases") or []) or "(none)",
            outdated="; ".join(r.get("outdated_answers") or []) or "(none)",
            near="; ".join(r.get("near_miss_answers") or []) or "(none)",
            act=r["source"]["act"],
            article=r["source"]["article"],
            quote=r["source"]["quote"],
            responses="\n".join(
                f"- {x.strip()[:600]}" for x in sorted(set(disputed[rid]))
            ),
        )
        d, err = call(key, args.model, prompt)
        text = d["choices"][0]["message"].get("content") if d else None
        try:
            res = json.loads(text[text.index("{") : text.rindex("}") + 1])
        except Exception:  # noqa: BLE001
            res = {"error": err or "unparsable", "raw": text}
        return {
            "id": rid,
            "model": args.model,
            "cost_usd": ((d or {}).get("usage") or {}).get("cost"),
            **res,
        }

    todo = sorted(r for r in disputed if r not in cache)
    with ThreadPoolExecutor(args.workers) as ex:
        for fut in as_completed([ex.submit(one, r) for r in todo]):
            x = fut.result()
            cache[x["id"]] = x
    dataset.write_jsonl(raw_path, [cache[k] for k in sorted(cache)])

    per_core = collections.defaultdict(dict)
    log, flags = [], []
    for rid, x in sorted(cache.items()):
        r = rows.get(rid)
        if not r:
            continue
        for v in x.get("variants") or []:
            why = check_variant(r, v)
            log.append(
                {
                    "id": rid,
                    "variant": v.get("variant"),
                    "evidence": v.get("evidence"),
                    "accepted": why is None,
                    "reason": why or "ok",
                }
            )
            if why is None:
                lang = r["lang"][:2]
                cur = per_core[r["core_id"]].setdefault(
                    lang, list(r.get("answer_aliases") or [])
                )
                if norm(v["variant"]) not in {norm(a) for a in cur}:
                    cur.append(v["variant"].strip())
        if x.get("ambiguous"):
            flags.append(
                {
                    "id": rid,
                    "question": r["question"],
                    "answer": r["answer"],
                    "why": x.get("why"),
                }
            )
    decisions = []
    for cid, langs in sorted(per_core.items()):
        ev = {
            e["id"]: e["evidence"]
            for e in log
            if e["accepted"] and e["id"].startswith(cid + "-")
        }
        decisions.append(
            {
                "core_id": cid,
                "action": "patch",
                "reason": "answer variants added after panel disagreement; each variant checked against the cited paragraph (evidence: "
                + " | ".join(f"{k}: {v[:80]}" for k, v in sorted(ev.items()))
                + ")",
                **{lang: {"answer_aliases": al} for lang, al in langs.items()},
            }
        )
    spec = {
        "version": "panel-fixes-v1",
        "reviewer": "automatic (panel_fixes.py)",
        "created": dt.date.today().isoformat(),
        "decisions": decisions,
    }
    (out_dir / "panel_fixes.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (out_dir / "panel_fixes_log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (out_dir / "panel_flags.json").write_text(
        json.dumps(flags, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "disputed_rows": len(disputed),
                "proposed_variants": len(log),
                "accepted_variants": sum(e["accepted"] for e in log),
                "patched_cores": len(decisions),
                "ambiguous_flags": len(flags),
                "cost_usd": round(
                    sum(x.get("cost_usd") or 0 for x in cache.values()), 4
                ),
                "rejected_by_reason": dict(
                    collections.Counter(
                        e["reason"].split(":")[0] for e in log if not e["accepted"]
                    )
                ),
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
