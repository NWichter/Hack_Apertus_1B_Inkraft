"""German machine translation of the FR/IT rows of the human judge sample (reading aid for the annotator).

Translates question, gold answer, variants, outdated and near-miss answers and the model response of every
FR/IT row in data/human_labels/sample_20pct.jsonl with Apertus 70B (temperature 0, reasoning off).
Cache: data/human_labels/translations_de.json, one entry per text keyed by sha256(model | prompt | text).
The translations are only shown next to the original on the check page; they are not part of the dataset.

python src/translate_sample.py --env <.env with LLM_BASE_URL, LLM_API_KEY> [--model apertus-v1.5-70b]
"""

import argparse
import hashlib
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
sys.path.insert(0, str(HERE))
from inkraft.client import Endpoint  # noqa: E402
from second_check import env_value, read  # noqa: E402

PROMPT_VERSION = "translate-de-v1"
SYSTEM = (
    "Translate the user's text from {lang} into German. Translate literally, sentence by sentence. "
    "Keep every number, date, amount, percentage, unit and article reference exactly as written. "
    "Do not answer, explain, correct or shorten the text. Output only the German translation."
)
LANGS = {"fr": "French", "it": "Italian"}
FIELDS = (
    "question",
    "answer",
    "answer_aliases",
    "outdated_answers",
    "near_miss_answers",
)


def key_of(model, lang, text):
    return hashlib.sha256(
        f"{model}|{PROMPT_VERSION}|{lang}|{text}".encode()
    ).hexdigest()


def texts_of(row, item):
    out = [item["question"], item["answer"], row["response"]]
    for f in FIELDS[2:]:
        out += item.get(f) or []
    return [t for t in out if t and t.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True)
    ap.add_argument("--model", default="apertus-v1.5-70b")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    ep = Endpoint(
        env_value(args.env, "LLM_BASE_URL"),
        env_value(args.env, "LLM_API_KEY"),
        args.model,
    )
    items = {r["id"]: r for r in read(DATA / "test.jsonl")}
    sample = read(DATA / "human_labels" / "sample_20pct.jsonl")
    path = DATA / "human_labels" / "translations_de.json"
    cache = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    jobs = {}
    for r in sample:
        lang = r["id"].rsplit("-", 1)[1]
        if lang not in LANGS:
            continue
        for t in texts_of(r, items[r["id"]]):
            k = key_of(ep.model, lang, t)
            if k not in cache:
                jobs[k] = (lang, t)
    lock = threading.Lock()

    def one(k, lang, text):
        d = ep.chat(
            [
                {"role": "system", "content": SYSTEM.format(lang=LANGS[lang])},
                {"role": "user", "content": text},
            ],
            temperature=0.0,
            max_tokens=600,
            chat_template_kwargs={"enable_thinking": False},
        )
        de = (d["choices"][0]["message"].get("content") or "").strip()
        return k, {
            "lang": lang,
            "source": text,
            "de": de,
            "model": ep.model,
            "prompt_version": PROMPT_VERSION,
        }

    with ThreadPoolExecutor(args.workers) as ex:
        for fut in as_completed([ex.submit(one, k, *v) for k, v in jobs.items()]):
            k, v = fut.result()
            with lock:
                cache[k] = v
    path.write_text(
        json.dumps(cache, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"{len(jobs)} new translations, {len(cache)} in {path}")


if __name__ == "__main__":
    main()
