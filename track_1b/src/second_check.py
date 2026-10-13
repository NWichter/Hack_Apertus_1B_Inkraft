"""Independent second check of every core by an open model of another family (default Qwen3-235B).

The checker sees the item in DE/FR/IT, the current paragraph (source.quote, verified verbatim against
Fedlex by validate_items.py) and, for STALE pairs, the earlier evidence. It answers fixed yes/no
questions and a verdict ok | minor | problem. It never edits items; auto_review.py uses the verdict.

python src/second_check.py --env <.env> --items <rows.jsonl> --out data/review/second_check.jsonl
"""

import argparse
import collections
import datetime as dt
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "qwen/qwen3-235b-a22b-2507"
PROMPT_VERSION = "second-check-v1"

PROMPT = """You check ONE item of a closed-book short-answer benchmark about Swiss federal social and health insurance law (reference date {as_of}). The statute text below is the only ground truth. Do not use your own knowledge of the law.

ITEM (the same question in German, French and Italian):
{item}

CURRENT paragraph of {act} {article} (version {version}):
DE: {quote_de}
FR: {quote_fr}
IT: {quote_it}
{earlier}
Answer each check with true or false:
- "answer_supported": the gold answer is exactly what the current paragraph says for this question (in every language).
- "unambiguous": a careful expert who reads only the question would know which rule is meant and give one short answer; the question names the insurance branch and the conditions needed (not answerable with a different value from the same paragraph or a neighbouring rule).
- "no_leak": the question does not give away the answer.
- "langs_equivalent": the three questions ask the same thing and the three gold answers mean the same.
- "aliases_ok": every accepted variant means exactly the gold answer (true if there are none).
- "near_miss_ok": no near-miss answer is actually correct (true if there are none).
- "outdated_ok": only if outdated answers are listed: the earlier text gives the outdated answer to the SAME question, and it differs in substance from the current answer (not only a renamed term or a renumbered reference). null if no outdated answers are listed.

Then "verdict": "ok" if all checks pass; "minor" if only aliases_ok or near_miss_ok fail or a wording issue does not change the answer; "problem" if answer_supported, unambiguous, no_leak, langs_equivalent or outdated_ok fail.
Reply with JSON only, one line: {{"answer_supported": true, "unambiguous": true, "no_leak": true, "langs_equivalent": true, "aliases_ok": true, "near_miss_ok": true, "outdated_ok": null, "verdict": "ok|minor|problem", "issue": "<one short sentence, empty if ok>"}}"""

ITEM_KEYS = (
    "question",
    "answer",
    "answer_aliases",
    "near_miss_answers",
    "outdated_answers",
)


def read(path):
    return [
        json.loads(x)
        for x in Path(path).read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


def env_value(path, name):
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(rf"\s*{re.escape(name)}\s*=\s*(.*)$", line)
        if m:
            return m.group(1).strip().strip("'\"")
    raise SystemExit(f"{name} not set in {path}")


def build_prompt(core):
    de = core.get("de") or next(iter(core.values()))
    s = de["source"]
    item = {lang: {k: r.get(k) for k in ITEM_KEYS} for lang, r in sorted(core.items())}
    earlier = ""
    if any(r.get("outdated_answers") for r in core.values()):
        lines = []
        for lang, r in sorted(core.items()):
            t = r.get("temporal") or {}
            ev = t.get("previous_evidence") or next(
                (
                    v.get("evidence")
                    for v in t.get("outdated_versions") or []
                    if v.get("evidence")
                ),
                None,
            )
            lines.append(f"{lang.upper()}: {ev or '(not stored)'}")
        when = (de.get("temporal") or {}).get(
            "previous_version_date"
        ) or "earlier version"
        earlier = (
            f"\nEARLIER text (version {when}) that gives the outdated answer:\n"
            + "\n".join(lines)
            + "\n"
        )
    quote = {
        lang: core[lang]["source"]["quote"] if lang in core else "(missing)"
        for lang in ("de", "fr", "it")
    }
    para = f" para. {s['paragraph']}" if s.get("paragraph") else ""
    return PROMPT.format(
        as_of=de["as_of"],
        item=json.dumps(item, ensure_ascii=False, indent=1),
        act=s["act"],
        article=f"art. {s['article']}{para}",
        version=s["version_date"],
        quote_de=quote["de"],
        quote_fr=quote["fr"],
        quote_it=quote["it"],
        earlier=earlier,
    )


def call(key, model, prompt, attempts=6):
    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 400,
            "usage": {"include": True},
        }
    ).encode()
    delay, err = 5, None
    for _ in range(attempts):
        req = urllib.request.Request(
            URL,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.loads(r.read())
            if "choices" in d:
                return d, None
            err = str(d.get("error"))[:200]
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code}"
            if e.code not in (408, 429, 500, 502, 503, 504):
                break
        except Exception as e:  # noqa: BLE001
            err = type(e).__name__
        time.sleep(delay)
        delay = min(delay * 2, 60)
    return None, err


def parse(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return d if d.get("verdict") in ("ok", "minor", "problem") else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True)
    ap.add_argument("--items", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument(
        "--max-usd",
        type=float,
        default=0.25,
        help="stop when the reported cost exceeds this",
    )
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    key = env_value(args.env, "OPENROUTER_API_KEY")
    cores = collections.defaultdict(dict)
    for r in read(args.items):
        cores[r["core_id"]][r["lang"][:2]] = r
    out = Path(args.out)
    done = (
        {r["core_id"] for r in read(out) if r.get("verdict")} if out.exists() else set()
    )
    todo = sorted(c for c in cores if c not in done)
    sha = hashlib.sha256(PROMPT.encode()).hexdigest()[:12]
    cost = [0.0]

    def one(cid):
        if cost[0] > args.max_usd:
            return {"core_id": cid, "error": "budget stop"}
        d, err = call(key, args.model, build_prompt(cores[cid]))
        content = d["choices"][0]["message"].get("content") if d else None
        usage = (d or {}).get("usage") or {}
        cost[0] += usage.get("cost") or 0.0
        res = parse(content) or {}
        return {
            "core_id": cid,
            **res,
            "raw": None if res else content,
            "error": err if not res else None,
            "checker_model": args.model,
            "prompt_version": f"{PROMPT_VERSION} sha256:{sha}",
            "cost_usd": usage.get("cost"),
            "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        }

    with ThreadPoolExecutor(args.workers) as ex, out.open("a", encoding="utf-8") as f:
        for fut in as_completed([ex.submit(one, c) for c in todo]):
            row = fut.result()
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
    rows = {}
    for r in read(out):
        if r.get("verdict") or r["core_id"] not in rows:
            rows[r["core_id"]] = r
    out.write_text(
        "".join(
            json.dumps(r, ensure_ascii=False) + "\n"
            for r in sorted(rows.values(), key=lambda r: r["core_id"])
        ),
        encoding="utf-8",
    )
    c = collections.Counter(r.get("verdict") or "error" for r in rows.values())
    print(dict(c), f"cost this run {cost[0]:.4f} USD")


if __name__ == "__main__":
    main()
