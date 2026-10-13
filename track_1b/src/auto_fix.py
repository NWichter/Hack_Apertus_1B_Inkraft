"""Apply the correction notes of the candidate pre-assessment with an open model (Nemotron 3 Ultra).

Input: candidate cores whose pre-assessment verdict is accept_minor or revise. The note of the assessor is
the task; Nemotron returns the corrected item in DE/FR/IT. The result is a patch in the apply_review.py
format, never applied here. auto_review.py validates and decides.

python src/auto_fix.py --fedlex <fedlex-v2> --env <.env> --out data/candidates/auto-fix [--workers 3]
"""

import argparse
import datetime as dt
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
sys.path.insert(0, str(HERE))
from build_items import Fedlex  # noqa: E402
from gen_nemotron import MODEL, SETTINGS, call, env_value, parse  # noqa: E402
from gen_proposals import by_core, fill  # noqa: E402
from validate_items import ANSWER_TYPES, QUESTION_TYPES  # noqa: E402

PROMPT_FILE = HERE / "prompts" / "nemotron_rewrite_v1.txt"
PROMPT_NAME = "auto-fix-v1 (template nemotron-rewrite-v1)"
CANDIDATES = [
    DATA / "candidates" / "nemotron-v2" / "candidates.jsonl",
    DATA / "candidates" / "nemotron-pilot" / "candidates.ultra.jsonl",
]
ASSESSMENTS = [
    DATA / "candidates" / "nemotron-v2" / "assessment.json",
    DATA / "candidates" / "nemotron-pilot" / "assessment.ultra.json",
]

TASK = (
    'A reviewer checked this candidate item and asked for these corrections:\n"{NOTE}"\n'
    "Apply exactly these corrections in DE, FR and IT and nothing else. Keep the tested rule, the current answer "
    "and the outdated answers (the answer under the earlier version of the paragraph) unless the note says "
    "otherwise. If the corrections cannot be applied without breaking the rules below, return "
    '{"fixed": false, "reason": "..."}.'
)
OUTPUT = (
    '{"fixed": true, "question_type": "<unchanged unless the note asks>", "answer_type": "<unchanged unless the note asks>", '
    '"de": {"question": "...", "answer": "...", "answer_aliases": ["..."], "near_miss_answers": ["..."], '
    '"outdated_answers": ["..."], "evidence": "..."}, "fr": {same keys}, "it": {same keys}}  or  '
    '{"fixed": false, "reason": "..."}'
)


def read(path):
    return [
        json.loads(x)
        for x in Path(path).read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


def to_patch(core, d):
    de = core["de"]
    patch = {"action": "patch", "kind": "auto_fix", "all": {}}
    allowed = {"question_type": QUESTION_TYPES, "answer_type": ANSWER_TYPES}
    for k in ("question_type", "answer_type"):
        if d.get(k) in allowed[k] and d[k] != de.get(k):
            patch["all"][k] = d[k]
    for lang in ("de", "fr", "it"):
        x = d.get(lang) or {}
        p = {}
        for k in (
            "question",
            "answer",
            "answer_aliases",
            "near_miss_answers",
            "outdated_answers",
        ):
            if k in x and x[k] != core[lang].get(k):
                p[k] = x[k]
        if x.get("evidence") and x["evidence"] != core[lang]["source"]["evidence"]:
            p["source.evidence"] = x["evidence"]
        if p:
            patch[lang] = p
    return patch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fedlex", required=True)
    ap.add_argument("--env", required=True)
    ap.add_argument("--out", default=str(DATA / "candidates" / "auto-fix"))
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    key = env_value(args.env, "OPENROUTER_API_KEY")
    SETTINGS["max_tokens"] = 12000
    SETTINGS["reasoning_effort"] = "low"
    template = PROMPT_FILE.read_text(encoding="utf-8")
    prompt_sha = hashlib.sha256((template + TASK + OUTPUT).encode()).hexdigest()[:12]
    fx = Fedlex(args.fedlex)
    cores = by_core([r for p in CANDIDATES for r in read(p)])
    notes = {
        a["core_id"]: a
        for p in ASSESSMENTS
        for a in json.loads(p.read_text(encoding="utf-8"))
    }
    todo = sorted(
        c
        for c, a in notes.items()
        if a["verdict"] in ("accept_minor", "revise") and c in cores
    )
    out = Path(args.out)
    (out / "raw").mkdir(parents=True, exist_ok=True)

    def run(cid):
        raw = out / "raw" / f"{cid}.json"
        if raw.exists():
            cached = json.loads(raw.read_text(encoding="utf-8"))
            if parse(cached.get("content")):
                return cid, cached
        task = TASK.replace("{NOTE}", notes[cid]["reason"])
        prompt = fill(template, task, OUTPUT, cores[cid], fx)
        data, err = call(key, MODEL, prompt)
        rec = {
            "core_id": cid,
            "model": MODEL,
            "error": err,
            "content": data["choices"][0]["message"].get("content") if data else None,
            "usage": (data or {}).get("usage"),
            "latency_s": (data or {}).get("_latency_s"),
            "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        }
        raw.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        return cid, rec

    patches, log = {}, []
    with ThreadPoolExecutor(args.workers) as ex:
        for fut in as_completed([ex.submit(run, c) for c in todo]):
            cid, rec = fut.result()
            d = parse(rec.get("content"))
            status = "error" if not d else ("fixed" if d.get("fixed") else "not_fixed")
            log.append(
                {
                    "core_id": cid,
                    "status": status,
                    "reason": (d or {}).get("reason") or rec.get("error"),
                }
            )
            if status == "fixed":
                p = to_patch(cores[cid], d)
                p["summary"] = (
                    "auto fix of the pre-assessment note: " + notes[cid]["reason"][:300]
                )
                p["provenance"] = {
                    "generator": "nemotron",
                    "generator_model": MODEL,
                    "generated_at": dt.date.today().isoformat(),
                    "prompt_version": f"{PROMPT_NAME} sha256:{prompt_sha}",
                }
                patches[cid] = p
            print(cid, status, flush=True)
    (out / "patches.json").write_text(
        json.dumps(patches, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    (out / "log.json").write_text(
        json.dumps(
            sorted(log, key=lambda x: x["core_id"]), ensure_ascii=False, indent=1
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"{len(todo)} cores, {len(patches)} patches -> {out}")


if __name__ == "__main__":
    main()
