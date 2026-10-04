"""Review proposals for existing cores (review v3): yes/no -> open question, missing answer variants,
and drop proposals for paragraph clusters and near-duplicates.

Proposals only. Nothing is applied: the review tool shows them, Niklas decides, apply_review.py applies.
Nemotron (OpenRouter) drafts the rewrites and variants; cluster/duplicate drops are rule-based.

python src/gen_proposals.py --fedlex <fedlex-v2> --env <.env> --items data/merged.v1.jsonl
    --issues <validator issues.json> --out data/candidates/review-v3 [--workers 2]
"""

import argparse
import collections
import datetime as dt
import hashlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_items import Fedlex  # noqa: E402
from gen_nemotron import FALLBACK, MODEL, SETTINGS, call, env_value, parse  # noqa: E402

PROMPT_FILE = HERE / "prompts" / "nemotron_rewrite_v1.txt"
LANGS = ("de", "fr", "it")
ITEM_KEYS = (
    "question",
    "answer",
    "answer_aliases",
    "near_miss_answers",
    "outdated_answers",
)

TASK_REWRITE = (
    "The item is a yes/no question. Yes/no items are capped at 15 % of the benchmark because a guess is right "
    "half of the time. If the same paragraph allows an OPEN short-answer question that tests the same rule "
    "(e.g. 'Who ...', 'Within which period ...', 'What must ... pay ...'), write it in DE/FR/IT. If no open "
    'question with a short literal answer is possible, return {"rewrite": false, "reason": "..."}.'
)
OUT_REWRITE = (
    '{"rewrite": true, "question_type": "numeric|procedural", "answer_type": "currency_chf|number|percent|duration|age|date|text", '
    '"answer_normalized": {"value": <number>, "unit": "<CHF|percent|days|weeks|months|years|age|count>"} or null, '
    '"de": {"question": "...", "answer": "...", "answer_aliases": ["..."], "near_miss_answers": ["..."], "evidence": "..."}, '
    '"fr": {same keys}, "it": {same keys}}  or  {"rewrite": false, "reason": "..."}'
)
TASK_VARIANTS = (
    "The item has no answer variants in the languages {LANGS_MISSING}. Keep question and answer unchanged and propose "
    "answer_aliases (other correct spellings of exactly the same answer) for these languages only."
)
TASK_OUTDATED = (
    "The evidence sentence of this item changed: it is missing from the EARLIER versions below. If an earlier version "
    "answers the SAME question with a DIFFERENT answer of the same type, give that outdated answer per language with a "
    "verbatim evidence span copied from that earlier version (it must contain the outdated value or words). Keep the "
    "question and the current answer unchanged. If the earlier text does not answer the same question (the rule is new, "
    "or only the wording or a term changed), return {\"outdated\": false, \"reason\": \"...\"}.\n\n{EARLIER}"
)
OUT_OUTDATED = (
    '{"outdated": true, "version_date": "<date of the earlier version>", "paragraph": "<paragraph number there>", '
    '"de": {"outdated_answer": "...", "evidence": "..."}, "fr": {same keys}, "it": {same keys}}  or  {"outdated": false, "reason": "..."}'
)
OUT_VARIANTS = '{"<lang>": {"answer_aliases": ["...", "..."]}, ...}  with one key per language listed in the task'


def by_core(rows):
    out = collections.defaultdict(dict)
    for r in rows:
        out[r["core_id"]][r["lang"][:2]] = r
    return out


def fill(template, task, output, core, fx):
    p = core.get("de") or next(iter(core.values()))
    s = p["source"]
    item = {
        lang: {k: core[lang].get(k) for k in ITEM_KEYS}
        | {"evidence": core[lang]["source"]["evidence"]}
        for lang in LANGS
        if lang in core
    }
    vals = {
        "TASK": task,
        "OUTPUT": output,
        "ITEM": json.dumps(item, ensure_ascii=False, indent=1),
        "ACT": s["act"],
        "ARTICLE_ID": s["article_id"],
        "PARAGRAPH": s["paragraph"],
        "CUR_DATE": s["version_date"],
    }
    for lang in LANGS:
        _, para, _ = fx.paragraph(s["act"], s["article_id"], s["paragraph"], lang)
        vals[f"CUR_{lang.upper()}"] = para["text"] if para else "(missing)"
    out = template
    for k, v in vals.items():
        out = out.replace("{" + k + "}", v)
    return out


def rule_drops(cores, issues):
    """Clusters (> 2 cores on one paragraph) and validator near-duplicates: drop proposals, never applied."""
    props = {}
    para = collections.defaultdict(list)
    for cid, core in cores.items():
        s = core["de"]["source"]
        para[(s["act"], s["article_id"], s["paragraph"])].append(cid)

    def keep_rank(cid):
        r = cores[cid]["de"]
        return (
            r["question_type"] == "yes_no",
            not r.get("outdated_answers"),
            len(cores[cid]) < 3,
            cid,
        )

    for key, cids in para.items():
        if len(cids) <= 2:
            continue
        for cid in sorted(cids, key=keep_rank)[2:]:
            props[cid] = {
                "action": "drop",
                "kind": "cluster",
                "summary": f"Cluster: {len(cids)} cores on {key[0]} {key[1]} para. {key[2]} (target: at most 2 per paragraph). Keep: {', '.join(sorted(sorted(cids, key=keep_rank)[:2]))}",
            }
    for i in issues:
        if i["code"] not in (
            "dup.near_question",
            "dup.same_fact",
            "dup.exact_question",
        ):
            continue
        ids = sorted(
            {
                x
                for x in [i["id"]] + [w.strip(" ,;:()'\"") for w in i["msg"].split()]
                if x[:3] in ("cl-", "cx-", "ag-")
            }
        )
        cids = sorted(
            {x.rsplit("-", 1)[0] if x[-3:] in ("-de", "-fr", "-it") else x for x in ids}
            & set(cores)
        )
        if len(cids) < 2:
            continue
        drop = sorted(cids, key=keep_rank)[-1]
        if drop not in props:
            props[drop] = {
                "action": "drop",
                "kind": "duplicate",
                "summary": f"Near-duplicate ({i['code']}) of {', '.join(c for c in cids if c != drop)}; the core without yes/no or with an outdated answer is kept.",
            }
    return props


def put(proposals, cid, prop):
    """Merge several patch proposals of one core (e.g. outdated answer + variants)."""
    old = proposals.get(cid)
    if not old or old.get("action") != "patch" or prop.get("action") != "patch":
        if not old or old.get("action") != "patch":
            proposals[cid] = prop
        return
    merged = dict(old)
    for k in ("all", "de", "fr", "it"):
        if prop.get(k):
            merged[k] = {**(old.get(k) or {}), **prop[k]}
    merged["kind"] = f"{old['kind']}+{prop['kind']}"
    merged["summary"] = f"{old['summary']}; {prop['summary']}"
    proposals[cid] = merged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fedlex", required=True)
    ap.add_argument("--env", required=True)
    ap.add_argument("--items", default="data/merged.v1.jsonl")
    ap.add_argument(
        "--issues", required=True, help="validator --issues-json output for --items"
    )
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--max-tokens", type=int, default=9000)
    ap.add_argument("--reverse", action="store_true", help="work from the end (second process)")
    ap.add_argument("--buckets", help="data/temporal/sentence_buckets.json: adds outdated-answer proposals")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    fx = Fedlex(args.fedlex)
    rows = [
        json.loads(x)
        for x in Path(args.items).read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]
    cores = by_core(rows)
    issues = json.loads(Path(args.issues).read_text(encoding="utf-8"))
    template = PROMPT_FILE.read_text(encoding="utf-8")
    prompt_hash = hashlib.sha256(template.encode("utf-8")).hexdigest()[:12]
    out = Path(args.out)
    raw = out / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    key = env_value(args.env, "OPENROUTER_API_KEY")

    drops = rule_drops(cores, issues)
    jobs = []
    for cid, core in sorted(cores.items()):
        de = core["de"]
        if cid in drops:
            continue
        if de["question_type"] == "yes_no" or de["answer_type"] == "yes_no":
            jobs.append(
                (cid, "rewrite", fill(template, TASK_REWRITE, OUT_REWRITE, core, fx))
            )
        else:
            missing = [
                lang
                for lang in LANGS
                if lang in core and not core[lang].get("answer_aliases")
            ]
            if missing:
                task = TASK_VARIANTS.replace("{LANGS_MISSING}", ", ".join(missing))
                jobs.append(
                    (cid, "variants", fill(template, task, OUT_VARIANTS, core, fx))
                )

    if args.buckets:
        from find_changes import Fedlex as DiffFedlex

        dfx = DiffFedlex(args.fedlex)
        sb = json.loads(Path(args.buckets).read_text(encoding="utf-8"))
        for cid, v in sorted(sb.items()):
            if cid in drops or v["sentence_bucket"] == "stable_pre2024" or v["has_outdated_answers"] or cid not in cores:
                continue
            src_ = cores[cid]["de"]["source"]
            blocks, seen = [], set()
            for d in v["evidence_missing_in"][:3]:
                texts = {lang: dfx.article_text(src_["act"], src_["article_id"], lang=lang, date=d) for lang in LANGS}
                if texts["de"] in seen:
                    continue
                seen.add(texts["de"])
                blocks.append(f"EARLIER version {d} (whole article)\n" + "\n".join(f"{lang.upper()}: {texts[lang]}" for lang in LANGS))
            task = TASK_OUTDATED.replace("{EARLIER}", "\n\n".join(blocks))
            jobs.append((cid, "outdated", fill(template, task, OUT_OUTDATED, cores[cid], fx)))

    SETTINGS["max_tokens"] = args.max_tokens
    if args.reverse:
        jobs.reverse()

    def run(job):
        cid, kind, prompt = job
        path = raw / f"{cid}.{kind}.json"
        if path.exists():
            rec = json.loads(path.read_text(encoding="utf-8"))
            if parse(rec.get("content")) is not None:
                return job, rec
        data, err = call(key, args.model, prompt)
        if data is None:
            data, err = call(key, FALLBACK, prompt)
        if data is None:
            return job, {"error": err}
        msg = data["choices"][0]["message"]
        rec = {
            "model": data.get("model"),
            "content": msg.get("content") or "",
            "usage": data.get("usage") or {},
            "latency_s": data["_latency_s"],
            "generated_at": dt.date.today().isoformat(),
        }
        path.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        return job, rec

    t0 = time.time()
    results = {}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for f in as_completed([ex.submit(run, j) for j in jobs]):
            (cid, kind, _), rec = f.result()
            results[(cid, kind)] = rec
            print(
                cid,
                kind,
                "ok"
                if parse(rec.get("content")) is not None
                else f"FAIL {rec.get('error', 'unparseable')}",
                flush=True,
            )

    proposals = dict(drops)
    for (cid, kind), rec in sorted(results.items()):
        d = parse(rec.get("content"))
        if d is None:
            continue
        prov = {
            "generator": "nemotron",
            "generator_model": rec.get("model"),
            "generated_at": rec.get("generated_at"),
            "prompt_version": f"nemotron-rewrite-v1 sha256:{prompt_hash} (src/prompts/nemotron_rewrite_v1.txt)",
        }
        if kind == "outdated":
            if not d.get("outdated"):
                put(proposals, cid, {"action": "keep", "kind": "outdated_none", "summary": f"No outdated answer possible: {d.get('reason', '')}", "provenance": prov})
                continue
            prop = {
                "action": "patch",
                "kind": "outdated",
                "summary": f"Add outdated answer from the version of {d.get('version_date')} (STALE pair)",
                "all": {"temporal.previous_version_date": d.get("version_date"), "temporal.previous_paragraph": d.get("paragraph")},
                "provenance": prov,
            }
            for lang in LANGS:
                x = d.get(lang) or {}
                if x.get("outdated_answer") and lang in cores[cid]:
                    prop[lang] = {
                        "outdated_answers": [x["outdated_answer"]],
                        "temporal.previous_evidence": x.get("evidence"),
                    }
            put(proposals, cid, prop)
            continue
        if kind == "rewrite":
            if not d.get("rewrite"):
                put(proposals, cid, {
                    "action": "keep",
                    "kind": "yes_no_kept",
                    "summary": f"Ja/Nein bleibt: {d.get('reason', '')}",
                    "provenance": prov,
                })
                continue
            prop = {
                "action": "patch",
                "kind": "yes_no_rewrite",
                "summary": "Ja/Nein-Frage in offene Frage umbauen (Ja/Nein-Anteil ≤ 15 %)",
                "all": {
                    k: d.get(k)
                    for k in ("question_type", "answer_type", "answer_normalized")
                },
                "provenance": prov,
            }
            for lang in LANGS:
                if lang in d and lang in cores[cid]:
                    x = d[lang]
                    prop[lang] = {
                        "question": x.get("question"),
                        "answer": x.get("answer"),
                        "answer_aliases": x.get("answer_aliases") or [],
                        "near_miss_answers": x.get("near_miss_answers") or [],
                        "source.evidence": x.get("evidence"),
                    }
            put(proposals, cid, prop)
        else:
            prop = {
                "action": "patch",
                "kind": "variants",
                "summary": "Antwortvarianten ergänzen",
                "provenance": prov,
            }
            for lang in LANGS:
                if (
                    isinstance(d.get(lang), dict)
                    and d[lang].get("answer_aliases")
                    and lang in cores[cid]
                ):
                    prop[lang] = {"answer_aliases": d[lang]["answer_aliases"]}
            if any(lang in prop for lang in LANGS):
                put(proposals, cid, prop)
    (out / "proposals.json").write_text(
        json.dumps(proposals, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    kinds = collections.Counter(p["kind"] for p in proposals.values())
    print(f"{len(proposals)} proposals {dict(kinds)} in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
