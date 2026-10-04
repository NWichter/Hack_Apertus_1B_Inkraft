"""Nemotron pilot: draft one candidate core per changed fedlex paragraph via OpenRouter.

Candidates only. Nothing here is merged into merged.v1.jsonl; every record keeps
status=draft and needs_human_review=true.

python gen_nemotron_pilot.py --fedlex <fedlex-v2> --env <path/.env> [--model ...] [--fallback ...]
"""

import argparse
import datetime as dt
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "src"))
from build_items import Fedlex, build  # noqa: E402

PROMPT_VERSION = "nemotron-pilot-v1"
URL = "https://openrouter.ai/api/v1/chat/completions"


def env_value(path, name):
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(rf"\s*{re.escape(name)}\s*=\s*(.*)$", line)
        if m:
            return m.group(1).strip().strip("'\"")
    raise SystemExit(f"{name} not set in {path}")


def para_text(fx, act, art, par, lang, role):
    _, p, _ = fx.paragraph(act, art, par, lang, role)
    return p["text"] if p else "(missing)"


def fill(template, t, fx):
    entry = fx.acts[t["act"]]
    vals = {
        "ACT": t["act"],
        "ARTICLE_ID": t["article_id"],
        "PARAGRAPH": t["paragraph"],
        "DOMAIN": t["domain"],
        "TITLE_DE": entry["title"]["de"],
        "CUR_DATE": fx.version(t["act"], "current")["version_date"],
        "PREV_DATE": fx.version(t["act"], "previous")["version_date"],
    }
    for role, tag in (("current", "CUR"), ("previous", "PREV")):
        for lang in ("de", "fr", "it"):
            vals[f"{tag}_{lang.upper()}"] = para_text(
                fx, t["act"], t["article_id"], t["paragraph"], lang, role
            )
    out = template
    for k, v in vals.items():
        out = out.replace("{" + k + "}", v)
    return out


def call(key, model, prompt, max_attempts=5):
    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 8000,
            "usage": {"include": True},
        }
    ).encode()
    delay = 10
    for attempt in range(1, max_attempts + 1):
        req = urllib.request.Request(
            URL,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
                "X-Title": "Inkraft dataset pilot",
            },
        )
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                data = json.loads(r.read())
            if "choices" not in data:
                raise RuntimeError(str(data.get("error"))[:300])
            data["_latency_s"] = round(time.time() - t0, 1)
            data["_attempts"] = attempt
            return data, None
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code}"
            if e.code not in (408, 429, 500, 502, 503, 504):
                return None, err
        except Exception as e:  # network or provider error payload
            err = type(e).__name__ + ": " + str(e)[:200]
        if attempt < max_attempts:
            time.sleep(delay)
            delay *= 2
    return None, f"gave up after {max_attempts} attempts ({err})"


def parse(content):
    text = re.sub(r"```(?:json)?", "", content or "").strip()
    start, depth = text.find("{"), 0
    if start < 0:
        return None
    for i in range(start, len(text)):
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        if depth == 0:
            try:
                return json.loads(text[start : i + 1])
            except json.JSONDecodeError:
                return None
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fedlex", required=True)
    ap.add_argument("--env", required=True)
    ap.add_argument("--model", default="nvidia/nemotron-3-ultra-550b-a55b:free")
    ap.add_argument("--fallback", default="nvidia/nemotron-3-super-120b-a12b:free")
    ap.add_argument("--targets", default=str(HERE / "targets.json"))
    ap.add_argument("--tag", default="ultra")
    args = ap.parse_args()

    key = env_value(args.env, "OPENROUTER_API_KEY")
    fx = Fedlex(args.fedlex)
    template = (HERE / "prompt_nemotron_pilot_v1.txt").read_text(encoding="utf-8")
    targets = json.loads(Path(args.targets).read_text(encoding="utf-8"))
    today = dt.date.today().isoformat()
    raw_dir = HERE / "raw" / args.tag
    raw_dir.mkdir(parents=True, exist_ok=True)

    compact, log = [], []
    for n, t in enumerate(targets, 1):
        prompt = fill(template, t, fx)
        used = args.model
        data, err = call(key, used, prompt)
        if data is None and args.fallback:
            used = args.fallback
            data, err = call(key, used, prompt)
        entry = {"n": n, **{k: t[k] for k in ("act", "article_id", "paragraph")}}
        if data is None:
            log.append({**entry, "ok": False, "error": err})
            print(n, t["act"], t["article_id"], "FAILED", err, flush=True)
            continue
        msg = data["choices"][0]["message"]
        content = msg.get("content") or ""
        usage = data.get("usage") or {}
        (raw_dir / f"{n:02d}_{t['act']}_{t['article_id']}.json").write_text(
            json.dumps(
                {
                    "model": data.get("model"),
                    "requested_model": used,
                    "provider": data.get("provider"),
                    "content": content,
                    "reasoning_chars": len(msg.get("reasoning") or ""),
                    "usage": usage,
                    "latency_s": data["_latency_s"],
                    "attempts": data["_attempts"],
                },
                ensure_ascii=False,
                indent=1,
            ),
            encoding="utf-8",
        )
        item = parse(content)
        ok = bool(item and item.get("de"))
        log.append(
            {
                **entry,
                "ok": ok,
                "model": data.get("model"),
                "requested_model": used,
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "cost_usd": usage.get("cost"),
                "latency_s": data["_latency_s"],
                "attempts": data["_attempts"],
                "error": None if ok else "unparseable output",
            }
        )
        print(
            n,
            t["act"],
            t["article_id"],
            "ok" if ok else "PARSE FAIL",
            data["_latency_s"],
            "s",
            flush=True,
        )
        if ok:
            item.update({k: t[k] for k in ("act", "article_id", "paragraph", "domain")})
            item["_batch"] = f"nemotron-pilot-{args.tag}"
            item["_change_kind"] = t["change_kind"]
            item["_model"] = used
            compact.append(item)

    (HERE / f"compact.{args.tag}.jsonl").write_text(
        "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in compact),
        encoding="utf-8",
    )
    (HERE / f"run_log.{args.tag}.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    records = []
    for n, c in enumerate(compact, 1):
        b = argparse.Namespace(
            id_prefix=f"nm{args.tag[0]}",
            author="nemotron",
            attested_by=None,
            generator_model=c["_model"],
            generated_at=today,
            prompt_version=f"{PROMPT_VERSION} (prompt_nemotron_pilot_v1.txt)",
        )
        for r in build(c, n, b, fx):
            r["candidate"] = {
                "pilot": PROMPT_VERSION,
                "change_kind": c["_change_kind"],
                "provider": "openrouter",
                "merged": False,
            }
            records.append(r)
    (HERE / f"candidates.{args.tag}.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
        encoding="utf-8",
    )
    print(f"{len(compact)}/{len(targets)} cores, {len(records)} rows")


if __name__ == "__main__":
    main()
