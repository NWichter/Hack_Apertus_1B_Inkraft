"""Draft temporal candidate cores from fedlex version diffs with Nemotron via OpenRouter.

Candidates only: every record keeps status=draft, needs_human_review=true and candidate.merged=false.
Nothing is written to merged/test/metadata. Raw outputs are cached per target, so a rerun resumes.

python src/gen_nemotron.py --fedlex <fedlex-v2> --env <path/.env> --targets <temporal_targets.json>
    --out data/candidates/nemotron-v2 [--workers 3] [--limit N]
"""

import argparse
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

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_items import Fedlex, build  # noqa: E402
from find_changes import Fedlex as DiffFedlex, bucket_of, norm  # noqa: E402

PROMPT_FILE = HERE / "prompts" / "nemotron_temporal_v2.txt"
PROMPT_NAME = "nemotron-temporal-v2"
URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
FALLBACK = "nvidia/nemotron-3-super-120b-a12b:free"
LANGS = ("de", "fr", "it")
MAX_EARLIER = 3
SETTINGS = {"max_tokens": 9000, "reasoning_effort": None}


def env_value(path, name):
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(rf"\s*{re.escape(name)}\s*=\s*(.*)$", line)
        if m:
            return m.group(1).strip().strip("'\"")
    raise SystemExit(f"{name} not set in {path}")


def earlier_versions(dfx, t):
    """Distinct earlier wordings of the paragraph, newest first, at most MAX_EARLIER."""
    act, aid = t["act"], t["article_id"]
    par = t.get("previous_paragraph") or t["paragraph"]
    cur = (dfx.paragraphs(act, "current") or {}).get((aid, t["paragraph"]))
    out, seen = [], {norm(cur)}
    for d in dfx.earlier_dates(act):
        texts = {
            lang: (dfx.paragraphs(act, None, lang, d) or {}).get((aid, par))
            for lang in LANGS
        }
        if not texts["de"] or norm(texts["de"]) in seen:
            continue
        seen.add(norm(texts["de"]))
        out.append({"version_date": d, "paragraph": par, "texts": texts})
        if len(out) >= MAX_EARLIER:
            break
    return out


def fill(template, t, fx, dfx):
    entry = fx.acts[t["act"]]
    art, _, _ = fx.paragraph(t["act"], t["article_id"], t["paragraph"], "de")
    vals = {
        "ACT": t["act"],
        "ARTICLE_ID": t["article_id"],
        "PARAGRAPH": t["paragraph"],
        "DOMAIN": t["domain"],
        "TITLE_DE": entry["title"]["de"],
        "HEADING_DE": (art or {}).get("heading", ""),
        "CUR_DATE": fx.version(t["act"], "current")["version_date"],
    }
    for lang in LANGS:
        _, p, _ = fx.paragraph(t["act"], t["article_id"], t["paragraph"], lang)
        vals[f"CUR_{lang.upper()}"] = p["text"] if p else "(missing)"
    blocks = []
    for v in earlier_versions(dfx, t):
        blocks.append(
            f'EARLIER version {v["version_date"]} (paragraph "{v["paragraph"]}")\n'
            + "\n".join(
                f"{lang.upper()}: {v['texts'][lang] or '(missing)'}" for lang in LANGS
            )
        )
    vals["EARLIER"] = (
        "\n\n".join(blocks) or "EARLIER versions: the paragraph did not exist before."
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
            "max_tokens": SETTINGS["max_tokens"],
            **(
                {"reasoning": {"effort": SETTINGS["reasoning_effort"]}}
                if SETTINGS["reasoning_effort"]
                else {}
            ),
            "usage": {"include": True},
        }
    ).encode()
    delay, err = 15, None
    for attempt in range(1, max_attempts + 1):
        req = urllib.request.Request(
            URL,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
                "X-Title": "Inkraft dataset candidates",
            },
        )
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=400) as r:
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
        except Exception as e:
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


def raw_name(n, t):
    return f"{n:03d}_{t['act']}_{t['article_id']}_{t['paragraph'] or 'x'}.json"


def generate_one(n, t, key, template, fx, dfx, raw_dir, model, fallback):
    path = raw_dir / raw_name(n, t)
    if path.exists():
        cached = json.loads(path.read_text(encoding="utf-8"))
        if parse(cached.get("content")):
            return cached, None
    prompt = fill(template, t, fx, dfx)
    used = model
    data, err = call(key, used, prompt)
    if data is None and fallback:
        used = fallback
        data, err = call(key, used, prompt)
    if data is None:
        return None, err
    msg = data["choices"][0]["message"]
    rec = {
        "model": data.get("model"),
        "requested_model": used,
        "provider": data.get("provider"),
        "content": msg.get("content") or "",
        "reasoning_chars": len(msg.get("reasoning") or ""),
        "usage": data.get("usage") or {},
        "latency_s": data["_latency_s"],
        "attempts": data["_attempts"],
        "generated_at": dt.date.today().isoformat(),
        "settings": dict(SETTINGS, temperature=0.3),
    }
    path.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec, None


def locate(dfx, act, aid, lang, evidence, hint_date):
    """Earlier version (date, paragraph, text) whose article contains the evidence; hint_date first."""
    dates = dfx.earlier_dates(act)
    order = ([hint_date] if hint_date in dates else []) + [
        d for d in dates if d != hint_date
    ]
    ev = norm(evidence)
    for d in order:
        paras = dfx.paragraphs(act, None, lang, d) or {}
        for (a, p), text in paras.items():
            if a == aid and ev and ev in norm(text):
                return d, p, text
    return None, None, None


def finish_temporal(rec, compact, fx, dfx, lang):
    """Outdated answers from every earlier version the model cited, located in the stored fedlex files."""
    act, aid = rec["source"]["act"], rec["source"]["article_id"]
    entry = fx.acts[act]
    vers = []
    for v in (compact.get("temporal") or {}).get("versions") or []:
        tl = v.get(lang) or {}
        if not tl.get("outdated_answer"):
            continue
        d, p, text = locate(
            dfx, act, aid, lang, tl.get("evidence"), v.get("version_date")
        )
        vers.append(
            {
                "version_date": d or v.get("version_date"),
                "paragraph": p if p is not None else v.get("paragraph"),
                "outdated_answer": tl["outdated_answer"],
                "evidence": tl.get("evidence"),
                "evidence_found": d is not None,
                "eli_url": f"{entry['eli']}/{(d or v.get('version_date') or '').replace('-', '')}/{lang}#{aid}",
                "quote": text,
            }
        )
    t = rec["temporal"]
    if compact.get("question_type") == "temporal" and vers:
        first = next((v for v in vers if v["evidence_found"]), vers[0])
        t.update(
            {
                "previous_version_date": first["version_date"],
                "previous_eli_url": first["eli_url"],
                "previous_paragraph": first["paragraph"],
                "previous_quote": first["quote"],
                "previous_evidence": first["evidence"],
                "outdated_versions": [
                    {
                        k: v[k]
                        for k in (
                            "version_date",
                            "paragraph",
                            "outdated_answer",
                            "evidence",
                            "evidence_found",
                        )
                    }
                    for v in vers
                ],
            }
        )
        seen = []
        for v in vers:
            if v["outdated_answer"] not in seen:
                seen.append(v["outdated_answer"])
        rec["outdated_answers"] = seen
    ev = norm(rec["source"]["evidence"])
    earlier = dfx.earlier_dates(act)
    missing = [
        d for d in earlier if ev not in dfx.article_text(act, aid, lang=lang, date=d)
    ]
    since = None
    if missing:
        since = min([dfx.current_date(act)] + [d for d in earlier if d > missing[0]])
    t["article_bucket"] = t["bucket"]
    t["bucket"] = bucket_of(since)
    t["bucket_level"] = "sentence"
    t["evidence_since"] = since


def clean_near_miss(rec, dfx):
    """Drop near misses that are outdated values (validator errors overlap / earlier_version); logged."""
    import validate_items as V

    lang = rec["lang"][:2]
    s = rec["source"]
    outdated = {V.norm_text(o) for o in rec.get("outdated_answers") or []}
    old_nums = set()
    for o in rec.get("outdated_answers") or []:
        old_nums |= V.extract_numbers(o, lang)
    cur_text = dfx.article_text(s["act"], s["article_id"], lang=lang)
    cur_nums = V.extract_numbers(cur_text, lang)
    earlier_nums = set()
    for d in dfx.earlier_dates(s["act"]):
        earlier_nums |= V.extract_numbers(dfx.article_text(s["act"], s["article_id"], lang=lang, date=d), lang)
    keep, dropped = [], []
    for m in rec.get("near_miss_answers") or []:
        nm = V.extract_numbers(m, lang)
        if V.norm_text(m) in outdated or (nm & old_nums) or (nm - cur_nums) & earlier_nums:
            dropped.append(m)
        else:
            keep.append(m)
    if dropped:
        rec["near_miss_answers"] = keep
        rec["authoring"]["manual_correction"] = [
            {
                "review": "auto-fix (src/gen_nemotron.py clean_near_miss)",
                "by": "rule",
                "reason": "near miss equals an outdated value of an earlier version; removed",
                "before": {"near_miss_answers": keep + dropped},
            }
        ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fedlex", required=True)
    ap.add_argument("--env", required=True)
    ap.add_argument("--targets", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--fallback", default=FALLBACK)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--id-prefix", default="nmv")
    ap.add_argument("--max-tokens", type=int, default=9000)
    ap.add_argument("--only", help="comma-separated target numbers to (re)generate; no files are rebuilt")
    ap.add_argument("--reasoning-effort", choices=["low", "medium", "high"])
    ap.add_argument(
        "--build-only",
        action="store_true",
        help="rebuild candidates from cached raw outputs",
    )
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    SETTINGS.update(max_tokens=args.max_tokens, reasoning_effort=args.reasoning_effort)
    only = {int(x) for x in args.only.split(",")} if args.only else set()

    fx, dfx = Fedlex(args.fedlex), DiffFedlex(args.fedlex)
    template = PROMPT_FILE.read_text(encoding="utf-8")
    prompt_hash = hashlib.sha256(template.encode("utf-8")).hexdigest()[:12]
    targets = json.loads(Path(args.targets).read_text(encoding="utf-8"))[: args.limit]
    out = Path(args.out)
    raw_dir = out / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    key = None if args.build_only else env_value(args.env, "OPENROUTER_API_KEY")

    results = {}
    t0 = time.time()
    if args.build_only:
        for n, t in enumerate(targets, 1):
            p = raw_dir / raw_name(n, t)
            results[n] = (
                (json.loads(p.read_text(encoding="utf-8")), None)
                if p.exists()
                else (None, "no raw output")
            )
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {
                ex.submit(
                    generate_one,
                    n,
                    t,
                    key,
                    template,
                    fx,
                    dfx,
                    raw_dir,
                    args.model,
                    args.fallback,
                ): n
                for n, t in enumerate(targets, 1)
                if not only or n in only
            }
            for f in as_completed(futs):
                n = futs[f]
                try:
                    results[n] = f.result()
                except Exception as e:
                    results[n] = (None, f"{type(e).__name__}: {e}")
                rec, err = results[n]
                t = targets[n - 1]
                status = (
                    "ok"
                    if rec and parse(rec["content"])
                    else f"FAIL {err or 'unparseable'}"
                )
                print(
                    f"{n:3d} {t['act']} {t['article_id']} {t['paragraph']} {status}",
                    flush=True,
                )

    if only:
        print(f"regenerated {sorted(only)}; rebuild with --build-only")
        return
    compact, log = [], []
    for n, t in enumerate(targets, 1):
        rec, err = results.get(n, (None, "not run"))
        item = parse(rec["content"]) if rec else None
        ok = bool(item and item.get("de"))
        usage = (rec or {}).get("usage") or {}
        log.append(
            {
                "n": n,
                **{k: t[k] for k in ("act", "article_id", "paragraph", "change_kind")},
                "ok": ok,
                "model": (rec or {}).get("model"),
                "requested_model": (rec or {}).get("requested_model"),
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "cost_usd": usage.get("cost"),
                "latency_s": (rec or {}).get("latency_s"),
                "attempts": (rec or {}).get("attempts"),
                "error": None if ok else (err or "unparseable output"),
            }
        )
        if ok:
            item.update({k: t[k] for k in ("act", "article_id", "paragraph", "domain")})
            item["_batch"] = PROMPT_NAME
            item["_target"] = t
            item["_model"] = rec["requested_model"]
            item["_model_returned"] = rec.get("model")
            item["_generated_at"] = (
                rec.get("generated_at") or dt.date.today().isoformat()
            )
            compact.append(item)

    (out / "compact.jsonl").write_text(
        "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in compact),
        encoding="utf-8",
    )
    (out / "run_log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    records = []
    for n, c in enumerate(compact, 1):
        temporal = c.get("temporal") or {}
        versions = temporal.get("versions") or []
        if c.get("question_type") == "temporal" and versions:
            c_build = {
                **c,
                "temporal": {
                    "previous_paragraph": versions[0].get("paragraph"),
                    **{lang: versions[0].get(lang) for lang in LANGS},
                },
            }
        else:
            c_build = {**c, "temporal": None}
        b = argparse.Namespace(
            id_prefix=args.id_prefix,
            author="nemotron",
            attested_by=None,
            generator_model=c["_model"],
            generated_at=c["_generated_at"],
            prompt_version=f"{PROMPT_NAME} sha256:{prompt_hash} (src/prompts/nemotron_temporal_v2.txt)",
        )
        for r in build(c_build, n, b, fx):
            finish_temporal(r, c, fx, dfx, r["lang"][:2])
            clean_near_miss(r, dfx)
            r["candidate"] = {
                "batch": PROMPT_NAME,
                "change_kind": c["_target"]["change_kind"],
                "target_score": c["_target"]["score"],
                "provider": "openrouter",
                "model_returned": c["_model_returned"],
                "merged": False,
            }
            records.append(r)
    (out / "candidates.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
        encoding="utf-8",
    )
    ok_n = sum(1 for x in log if x["ok"])
    print(
        f"{ok_n}/{len(targets)} parsed, {len(compact)} cores, {len(records)} rows, {time.time() - t0:.0f} s"
    )


if __name__ == "__main__":
    main()
