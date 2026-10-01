"""Metrics over graded responses: SimpleQA counts, CGA, F, hallucination and stale rates, penalised
score, language consistency, all with percentile bootstrap intervals (fixed seed)."""

import random
from collections import defaultdict
from pathlib import Path

from .dataset import read_jsonl
from .pregrade import pregrade, provisional_grade

SEED = 20261016
N_BOOT = 1000


def grade_rows(items, responses, judgements=None):
    """One row per response: grade from the judge if present, else the provisional rule grade."""
    by_id = {it["id"]: it for it in items}
    jd = {j["id"]: j for j in (judgements or []) if j.get("grade")}
    rows = []
    for r in responses:
        it = by_id.get(r["id"])
        if it is None:
            continue
        rule = pregrade(it, r.get("response"))
        if r["id"] in jd:
            grade, sub, source = (
                jd[r["id"]]["grade"],
                jd[r["id"]].get("incorrect_subtype"),
                "judge",
            )
        elif r.get("response") is None:
            grade, sub, source = None, None, "error"
        else:
            grade, sub = provisional_grade(rule["rule"])
            source = "rule" if grade else "ungraded"
        rows.append(
            {
                "id": r["id"],
                "core_id": it["core_id"],
                "lang": it["lang"],
                "domain": it["domain"],
                "question_type": it["question_type"],
                "register": it.get("register"),
                "temporal": (it.get("temporal") or {}).get("bucket"),
                "authoring": (it.get("authoring") or {}).get("mode"),
                "model": r["model"],
                "condition": r["condition"],
                "grade": grade,
                "subtype": sub,
                "grade_source": source,
                "rule": rule["rule"],
                "tokens_out": r.get("tokens_out"),
                "latency_ms": r.get("latency_ms"),
            }
        )
    return rows


def _point(rows):
    g = [r for r in rows if r["grade"]]
    n = len(g)
    c = sum(r["grade"] == "CORRECT" for r in g)
    i = sum(r["grade"] == "INCORRECT" for r in g)
    na = n - c - i
    stale = sum(r["grade"] == "INCORRECT" and r["subtype"] == "STALE" for r in g)
    att = c + i
    cr = c / n if n else 0.0
    cga = c / att if att else 0.0
    return {
        "n": n,
        "correct": cr,
        "incorrect": i / n if n else 0.0,
        "not_attempted": na / n if n else 0.0,
        "cga": cga,
        "f": 2 * cr * cga / (cr + cga) if cr + cga else 0.0,
        "hallucination_rate": i / att if att else 0.0,
        "stale_share_of_errors": stale / i if i else 0.0,
        "score_l1": (c - i) / n if n else 0.0,
        "score_l3": (c - 3 * i) / n if n else 0.0,
    }


def summarise(rows, boot=True, seed=SEED, n_boot=N_BOOT):
    graded = [r for r in rows if r["grade"]]
    out = {
        k: round(v, 4) if isinstance(v, float) else v for k, v in _point(graded).items()
    }
    out["n_total"] = len(rows)
    out["n_ungraded"] = len(rows) - len(graded)
    out["grade_source"] = dict(sorted(_count(r["grade_source"] for r in rows).items()))
    if boot and graded:
        rng = random.Random(seed)
        samples = defaultdict(list)
        for _ in range(n_boot):
            s = [graded[rng.randrange(len(graded))] for _ in graded]
            for k, v in _point(s).items():
                if k != "n":
                    samples[k].append(v)
        out["ci95"] = {
            k: [round(_pct(v, 2.5), 4), round(_pct(v, 97.5), 4)]
            for k, v in samples.items()
        }
    return out


def _count(xs):
    d = defaultdict(int)
    for x in xs:
        d[x] += 1
    return d


def _pct(vals, q):
    v = sorted(vals)
    k = (len(v) - 1) * q / 100
    lo, hi = int(k), min(int(k) + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def language_consistency(rows):
    """Share of cores (graded in de, fr and it) with the same grade in all three languages."""
    by_core = defaultdict(dict)
    for r in rows:
        if r["grade"]:
            by_core[r["core_id"]][r["lang"][:2]] = r["grade"]
    full = [g for g in by_core.values() if {"de", "fr", "it"} <= g.keys()]
    same = sum(len({g["de"], g["fr"], g["it"]}) == 1 for g in full)
    acc = {
        l: sum(g[l] == "CORRECT" for g in full) / len(full) if full else 0.0
        for l in ("de", "fr", "it")
    }
    return {
        "n_cores": len(full),
        "same_grade_all_three": round(same / len(full), 4) if full else 0.0,
        "correct_on_parallel_cores": {k: round(v, 4) for k, v in acc.items()},
    }


def breakdown(rows, key):
    groups = defaultdict(list)
    for r in rows:
        groups[r[key]].append(r)
    return {
        str(k): summarise(v, boot=False)
        for k, v in sorted(groups.items(), key=lambda kv: str(kv[0]))
    }


def score_all(items, data_dir, judge_model=None):
    """Score every response file in data/responses; use judgements of judge_model if present."""
    from .judge import judge_path

    data_dir = Path(data_dir)
    results = {}
    for p in sorted((data_dir / "responses").glob("*.jsonl")):
        model, condition = p.stem.split("__", 1)
        responses = read_jsonl(p)
        judgements = (
            read_jsonl(judge_path(data_dir, judge_model, model, condition))
            if judge_model
            else []
        )
        rows = grade_rows(items, responses, judgements)
        key = f"{model}__{condition}"
        res = {"overall": summarise(rows)}
        for lang in sorted({r["lang"] for r in rows}):
            res[f"lang:{lang}"] = summarise([r for r in rows if r["lang"] == lang])
        temporal = [r for r in rows if r["question_type"] == "temporal"]
        if temporal:
            res["temporal_items"] = summarise(temporal, boot=False)
        res["language_consistency"] = language_consistency(rows)
        res["by_domain"] = breakdown(rows, "domain")
        res["by_question_type"] = breakdown(rows, "question_type")
        res["by_rule"] = dict(sorted(_count(r["rule"] for r in rows).items()))
        outs = [r["tokens_out"] for r in rows if r["tokens_out"] is not None]
        res["mean_tokens_out"] = round(sum(outs) / len(outs), 1) if outs else None
        results[key] = res
    return results
