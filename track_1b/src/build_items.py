"""Expand compact draft items (Claude or Codex output) into full Stichtag draft records.

One compact line = one core item with optional fr/it versions. One output line = one language version.
Source metadata (SR number, version date, ELI URL, paragraph quote) is looked up in the fedlex
article files listed in manifest.json, never taken from the generator.
"""

import argparse
import json
import sys
from pathlib import Path

AS_OF = "2026-10-01"
LANG_TAG = {"de": "de-CH", "fr": "fr-CH", "it": "it-CH"}


class Fedlex:
    def __init__(self, root):
        self.root = Path(root)
        self.manifest = json.loads(
            (self.root / "manifest.json").read_text(encoding="utf-8")
        )
        self.acts = {a["abbr"]: a for a in self.manifest["acts"]}
        self._cache = {}

    def version(self, act, role):
        return next((v for v in self.acts[act]["versions"] if v["role"] == role), None)

    def doc(self, act, lang, role="current"):
        key = (act, lang, role)
        if key not in self._cache:
            v = self.version(act, role)
            if not v or lang not in v["files"]:
                self._cache[key] = None
            else:
                d = json.loads(
                    (self.root / v["files"][lang]["path"]).read_text(encoding="utf-8")
                )
                d["by_id"] = {a["article_id"]: a for a in d["articles"]}
                self._cache[key] = d
        return self._cache[key]

    def paragraph(self, act, article_id, paragraph, lang, role="current"):
        d = self.doc(act, lang, role)
        if not d:
            return None, None, None
        art = d["by_id"].get(article_id)
        if not art:
            return None, None, d
        para = next(
            (p for p in art["paragraphs"] if p["paragraph"] == (paragraph or "")), None
        )
        return art, para, d


def temporal_block(fx, act, article_id):
    entry = fx.acts[act]
    changed = article_id in entry.get("changed_since_previous", [])
    changed_on = entry.get("last_change_date", {}).get(article_id) if changed else None
    if not changed_on:
        bucket = "stable_pre2024"
    elif changed_on < "2026-01-01":
        bucket = "changed_2024_2025"
    else:
        bucket = "changed_2026"
    return {"bucket": bucket, "changed_on": changed_on, "bucket_level": "article"}


def future_changes(fx, act, article_id):
    out = []
    for date, ids in fx.acts[act].get("changes_after_as_of", {}).items():
        if article_id in ids:
            out.append(date)
    return sorted(out)


def build(compact, n, args, fx):
    core_id = f"{args.id_prefix}-{n:04d}"
    act = compact["act"]
    article_id = compact["article_id"]
    paragraph = compact.get("paragraph") or ""
    if paragraph.strip() in {"-", "–"}:
        paragraph = ""
    entry = fx.acts[act]
    cur_v = fx.version(act, "current")
    prev_v = fx.version(act, "previous")
    records = []
    for lang in ("de", "fr", "it"):
        lv = compact.get(lang)
        if not lv:
            continue
        art, para, _ = fx.paragraph(act, article_id, paragraph, lang)
        eli_url = f"{entry['eli']}/{cur_v['version_date'].replace('-', '')}/{lang}"
        temporal = temporal_block(fx, act, article_id)
        outdated = []
        if compact.get("question_type") == "temporal" and compact.get("temporal"):
            tl = compact["temporal"].get(lang) or {}
            prev_par = compact["temporal"].get("previous_paragraph") or ""
            p_art, p_para, _ = fx.paragraph(act, article_id, prev_par, lang, "previous")
            temporal.update(
                {
                    "previous_version_date": prev_v["version_date"] if prev_v else None,
                    "previous_eli_url": f"{entry['eli']}/{prev_v['version_date'].replace('-', '')}/{lang}#{article_id}"
                    if prev_v
                    else None,
                    "previous_paragraph": prev_par,
                    "previous_quote": p_para["text"] if p_para else None,
                    "previous_evidence": tl.get("evidence"),
                }
            )
            if tl.get("outdated_answer"):
                outdated.append(tl["outdated_answer"])
        rec = {
            "id": f"{core_id}-{lang}",
            "core_id": core_id,
            "lang": LANG_TAG[lang],
            "domain": compact.get("domain"),
            "question_type": compact.get("question_type"),
            "register": compact.get("register"),
            "difficulty_prior": compact.get("difficulty_prior"),
            "question": lv.get("question"),
            "answer": lv.get("answer"),
            "answer_aliases": lv.get("answer_aliases") or [],
            "answer_core": lv.get("answer_core"),
            "calc": compact.get("calc"),
            "calc_evidence": lv.get("calc_evidence"),
            "answer_type": compact.get("answer_type"),
            "answer_normalized": compact.get("answer_normalized"),
            "outdated_answers": outdated,
            "near_miss_answers": lv.get("near_miss_answers") or [],
            "as_of": AS_OF,
            "source": {
                "act": act,
                "sr": entry["sr"],
                "article": art["number"] if art else None,
                "article_id": article_id,
                "paragraph": paragraph,
                "version_date": cur_v["version_date"],
                "eli_url": eli_url,
                "article_url": f"{eli_url}#{article_id}",
                "quote": para["text"] if para else None,
                "evidence": lv.get("evidence"),
                "license": "public-domain-ch-urg-art5",
            },
            "temporal": temporal,
            "future_change": future_changes(fx, act, article_id),
            "status": "draft",
            "author": args.author,
            "needs_human_review": True,
            "generator": args.author,
            "generator_model": args.generator_model,
            "generated_at": args.generated_at,
            "prompt_version": args.prompt_version,
            "authoring": {
                "mode": "llm_drafted",
                "batch": compact.get("_batch"),
                "manual_correction": compact.get("_manual_correction"),
                "translation": None
                if lang == "de"
                else "question drafted by generator from the German core; answer and evidence taken from the authentic text in this language",
            },
            "license": "CDLA-Permissive-2.0",
        }
        records.append(rec)
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fedlex", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--author", required=True, choices=["claude", "codex", "human"])
    ap.add_argument("--id-prefix", required=True)
    ap.add_argument("--generator-model", required=True)
    ap.add_argument("--generated-at", required=True)
    ap.add_argument("--prompt-version", required=True)
    ap.add_argument("inputs", nargs="+")
    args = ap.parse_args()
    fx = Fedlex(args.fedlex)
    out = []
    n = 0
    parse_errors = 0
    for path in args.inputs:
        batch = Path(path).name.split(".")[0]
        for line_no, line in enumerate(
            Path(path).read_text(encoding="utf-8").splitlines(), 1
        ):
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            try:
                compact = json.loads(line)
            except json.JSONDecodeError as e:
                parse_errors += 1
                print(f"PARSE ERROR {path}:{line_no}: {e}", file=sys.stderr)
                continue
            compact.setdefault("_batch", batch)
            if compact.get("act") not in fx.acts:
                parse_errors += 1
                print(
                    f"UNKNOWN ACT {path}:{line_no}: {compact.get('act')}",
                    file=sys.stderr,
                )
                continue
            n += 1
            out.extend(build(compact, n, args, fx))
    Path(args.out).write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out), encoding="utf-8"
    )
    print(
        f"{n} core items, {len(out)} records, {parse_errors} parse errors -> {args.out}"
    )


if __name__ == "__main__":
    main()
