"""Human check of the judge: stratified 20 % sample, blind labelling, Cohen's kappa."""

import datetime as dt
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from .dataset import read_jsonl
from .judge import judge_path
from .score import _pct

SEED = 20261016
LABELS = {"c": "CORRECT", "i": "INCORRECT", "n": "NOT_ATTEMPTED"}
CLASSES = ["CORRECT", "INCORRECT", "NOT_ATTEMPTED"]


def sample(items, data_dir, judge_model, share=0.2, seed=SEED):
    """20 % of every (model, condition), stratified by language x judge grade."""
    by_id = {it["id"]: it for it in items}
    rows = []
    for p in sorted((Path(data_dir) / "responses").glob("*.jsonl")):
        model, cond = p.stem.split("__", 1)
        grades = {
            j["id"]: j
            for j in read_jsonl(judge_path(data_dir, judge_model, model, cond))
            if j.get("grade")
        }
        strata = defaultdict(list)
        for r in read_jsonl(p):
            if r["id"] in grades and r["id"] in by_id:
                strata[(by_id[r["id"]]["lang"], grades[r["id"]]["grade"])].append(r)
        rng = random.Random(f"{seed}:{model}:{cond}")
        for key in sorted(strata):
            group = sorted(strata[key], key=lambda r: r["id"])
            k = max(1, round(share * len(group)))
            for r in rng.sample(group, k):
                rows.append(
                    {
                        "id": r["id"],
                        "model": model,
                        "condition": cond,
                        "response": r["response"],
                    }
                )
    rng = random.Random(seed)
    rng.shuffle(rows)
    return rows


def label(items, sample_rows, out_path, annotator, read=input, write=print):
    """Show item, gold, variants and response (never the judge grade); store one label per row."""
    by_id = {it["id"]: it for it in items}
    out_path = Path(out_path)
    done = {(r["id"], r["model"], r["condition"]) for r in read_jsonl(out_path)}
    todo = [r for r in sample_rows if (r["id"], r["model"], r["condition"]) not in done]
    write(
        f"{len(todo)} of {len(sample_rows)} left. Keys: c=correct i=incorrect n=not attempted, add '?' if unsure, q=quit"
    )
    for k, r in enumerate(todo, 1):
        it = by_id[r["id"]]
        write("\n" + "=" * 80)
        write(f"[{k}/{len(todo)}] {r['id']}  ({it['lang']}, as of {it['as_of']})")
        write(f"Q: {it['question']}")
        write(
            f"GOLD: {it['answer']}   variants: {'; '.join(it.get('answer_aliases') or []) or '-'}"
        )
        write(
            f"OUTDATED: {'; '.join(it.get('outdated_answers') or []) or '-'}   NEAR MISS: {'; '.join(it.get('near_miss_answers') or []) or '-'}"
        )
        write(f"RESPONSE:\n{r['response']}")
        while True:
            key = read("label> ").strip().lower()
            if key == "q":
                return
            if key[:1] in LABELS:
                break
        row = {
            **r,
            "human_grade": LABELS[key[0]],
            "uncertain": key.endswith("?"),
            "annotator": annotator,
            "labelled_at": dt.datetime.now(dt.timezone.utc).isoformat(
                timespec="seconds"
            ),
        }
        with out_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def cohen_kappa(a, b, classes=CLASSES):
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[c] * cb[c] for c in classes) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def agreement(human_rows, judge_rows, n_boot=1000, seed=SEED):
    jd = {
        (j["id"], j["examinee"], j["condition"]): j["grade"]
        for j in judge_rows
        if j.get("grade")
    }
    pairs = [
        (h["human_grade"], jd[(h["id"], h["model"], h["condition"])])
        for h in human_rows
        if (h["id"], h["model"], h["condition"]) in jd
    ]
    if not pairs:
        return {"n": 0}
    hum, jud = zip(*pairs)
    rng = random.Random(seed)
    boots = []
    for _ in range(n_boot):
        s = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        boots.append(cohen_kappa([x for x, _ in s], [y for _, y in s]))
    confusion = {
        h: {j: sum(1 for x, y in pairs if x == h and y == j) for j in CLASSES}
        for h in CLASSES
    }
    return {
        "n": len(pairs),
        "raw_agreement": round(sum(x == y for x, y in pairs) / len(pairs), 4),
        "kappa": round(cohen_kappa(hum, jud), 4),
        "kappa_ci95": [round(_pct(boots, 2.5), 4), round(_pct(boots, 97.5), 4)],
        "confusion_human_rows_judge_cols": confusion,
    }

