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
SUBTYPES = {"s": "STALE", "m": "NEAR_MISS", "o": "OTHER"}
CLASSES = ["CORRECT", "INCORRECT", "NOT_ATTEMPTED"]
EXTENDED_CLASSES = ["CORRECT", "STALE", "NEAR_MISS", "OTHER", "NOT_ATTEMPTED"]


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
        f"{len(todo)} of {len(sample_rows)} left. Keys: c=correct n=not attempted i=incorrect (or direct subtype: s=stale m=near-miss o=other), add '?' if unsure, q=quit"
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
            clean_k = key.rstrip("?")
            if clean_k in LABELS or clean_k in SUBTYPES or (clean_k.startswith("i") and len(clean_k) <= 2):
                break
        
        uncertain = key.endswith("?")
        clean_k = key.rstrip("?")
        if clean_k in SUBTYPES:
            human_grade = "INCORRECT"
            human_subtype = SUBTYPES[clean_k]
        elif clean_k.startswith("i") and len(clean_k) == 2 and clean_k[1] in SUBTYPES:
            human_grade = "INCORRECT"
            human_subtype = SUBTYPES[clean_k[1]]
        elif clean_k == "i":
            human_grade = "INCORRECT"
            human_subtype = "OTHER"
        else:
            human_grade = LABELS.get(clean_k, "NOT_ATTEMPTED")
            human_subtype = None

        row = {
            **r,
            "human_grade": human_grade,
            "human_subtype": human_subtype,
            "uncertain": uncertain,
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
    jd_grade = {}
    jd_sub = {}
    for j in judge_rows:
        if j.get("grade"):
            safe_m = j.get("examinee", "").replace("/", "_").replace(":", "_")
            key = (j["id"], safe_m, j["condition"])
            key_raw = (j["id"], j.get("examinee", ""), j["condition"])
            jd_grade[key] = j["grade"]
            jd_grade[key_raw] = j["grade"]
            jd_sub[key] = j.get("incorrect_subtype")
            jd_sub[key_raw] = j.get("incorrect_subtype")

    pairs = []
    pairs_ext = []
    has_subtypes = False
    for h in human_rows:
        safe_m = h["model"].replace("/", "_").replace(":", "_")
        k = (h["id"], safe_m, h["condition"])
        if k not in jd_grade:
            k = (h["id"], h["model"], h["condition"])
        if k in jd_grade:
            j_g = jd_grade[k]
            j_s = jd_sub.get(k)
            h_g = h["human_grade"]
            h_s = h.get("human_subtype")
            pairs.append((h_g, j_g))
            if h_s is not None or j_s is not None:
                has_subtypes = True
            h_ext = h_s if (h_g == "INCORRECT" and h_s in ("STALE", "NEAR_MISS", "OTHER")) else (h_g if h_g != "INCORRECT" else "OTHER")
            j_ext = j_s if (j_g == "INCORRECT" and j_s in ("STALE", "NEAR_MISS", "OTHER")) else (j_g if j_g != "INCORRECT" else "OTHER")
            pairs_ext.append((h_ext, j_ext))

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
    out = {
        "n": len(pairs),
        "raw_agreement": round(sum(x == y for x, y in pairs) / len(pairs), 4),
        "kappa": round(cohen_kappa(hum, jud), 4),
        "kappa_ci95": [round(_pct(boots, 2.5), 4), round(_pct(boots, 97.5), 4)],
        "confusion_human_rows_judge_cols": confusion,
    }
    if has_subtypes:
        hum_ext, jud_ext = zip(*pairs_ext)
        out["kappa_5class"] = round(cohen_kappa(hum_ext, jud_ext, classes=EXTENDED_CLASSES), 4)
        stale_h = sum(1 for h in hum_ext if h == "STALE")
        stale_j = sum(1 for j in jud_ext if j == "STALE")
        stale_both = sum(1 for h, j in pairs_ext if h == "STALE" and j == "STALE")
        out["stale_metrics"] = {
            "human_stale_count": stale_h,
            "judge_stale_count": stale_j,
            "both_stale_count": stale_both,
            "precision": round(stale_both / stale_j, 4) if stale_j else 0.0,
            "recall": round(stale_both / stale_h, 4) if stale_h else 0.0,
        }
    return out

