"""Numbers for the report beyond `inkraft score`: paired ablation on German rows (McNemar), exposure buckets
of the contamination check, STALE pairs per model, cost and judge agreement. Writes report/analysis.json.

Usage: python report/analysis.py [--judge-model qwen/qwen3-235b-a22b-2507]
"""

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
from inkraft import dataset, score  # noqa: E402
from inkraft.judge import judge_path  # noqa: E402

MODELS = ("apertus-v1.5-8b", "apertus-v1.5-70b")


def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 4), round(c + h, 4)]


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2**n
    return round(min(1.0, 2 * p), 4)


def share(rows, pred):
    n = len(rows)
    k = sum(1 for r in rows if pred(r))
    return {
        "k": k,
        "n": n,
        "rate": round(k / n, 4) if n else None,
        "wilson95": wilson(k, n),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge-model", default="qwen/qwen3-235b-a22b-2507")
    ap.add_argument(
        "--ablation-judge",
        default="qwen/qwen3-235b-a22b-2507",
        help="judge of the paired German ablation; it grades both sides (closed_dated and the ablation conditions)",
    )
    args = ap.parse_args()
    data = ROOT / "data"
    items = dataset.load(data)
    by_id = {it["id"]: it for it in items}
    contam = {r["id"]: r for r in dataset.read_jsonl(data / "contamination.jsonl")}
    out = {
        "judge_model": args.judge_model,
        "ablation_judge": args.ablation_judge,
        "models": {},
    }

    def rows_of(model, cond, judge=None):
        p = data / "responses" / f"{model}__{cond}.jsonl"
        return score.grade_rows(
            items,
            dataset.read_jsonl(p),
            dataset.read_jsonl(judge_path(data, judge or args.judge_model, model, cond)),
        )

    for m in MODELS:
        res = {}
        cd = {r["id"]: r for r in rows_of(m, "closed_dated")}
        ob = {r["id"]: r for r in rows_of(m, "open_book")}
        all_rows = list(cd.values())
        stale_pair = [r for r in all_rows if by_id[r["id"]].get("outdated_answers")]
        other = [r for r in all_rows if not by_id[r["id"]].get("outdated_answers")]
        is_c = lambda r: r["grade"] == "CORRECT"  # noqa: E731
        is_s = lambda r: r["grade"] == "INCORRECT" and r["subtype"] == "STALE"  # noqa: E731
        res["closed_dated"] = {
            "all": share(all_rows, is_c),
            "stale_pair_rows_correct": share(stale_pair, is_c),
            "stale_pair_rows_stale": share(stale_pair, is_s),
            "stale_pair_rows_not_attempted": share(
                stale_pair, lambda r: r["grade"] == "NOT_ATTEMPTED"
            ),
            "other_rows_correct": share(other, is_c),
            "changed_sentence_rows_correct": share([r for r in all_rows if r["temporal"] != "stable_pre2024"], is_c),
        }
        ob_sp = [ob[r["id"]] for r in stale_pair if r["id"] in ob]
        res["open_book"] = {
            "all": share(list(ob.values()), is_c),
            "stale_pair_rows_correct": share(ob_sp, is_c),
            "stale_pair_rows_stale": share(ob_sp, is_s),
        }
        # STALE pair cores: old answer in at least one language
        cores = Counter()
        stale_cores = set()
        for r in stale_pair:
            cores[r["core_id"]] += 1
            if is_s(r):
                stale_cores.add(r["core_id"])
        res["stale_pair_cores"] = {
            "n": len(cores),
            "with_stale_answer_in_any_language": len(stale_cores),
        }
        # exposure buckets (MultiLegalPile switzerland_lexfind)
        # data/contamination.jsonl stays local (it quotes the corpus): `inkraft contam --corpus <dir>` rebuilds it
        res["exposure"] = {} if contam else {"skipped": "no data/contamination.jsonl"}
        for b in ("current", "absent", "outdated") if contam else ():
            sel = [
                r for r in all_rows if (contam.get(r["id"]) or {}).get("bucket") == b
            ]
            res["exposure"][b] = {
                "correct": share(sel, is_c),
                "stale": share(sel, is_s),
            }
        # paired ablation on German rows
        cd_abl = {r["id"]: r for r in rows_of(m, "closed_dated", args.ablation_judge)}
        de_ids = sorted(i for i in cd_abl if i.endswith("-de"))
        abl = {"judge": args.ablation_judge}
        for cond in ("closed_swiss", "closed_plain"):
            other_c = {r["id"]: r for r in rows_of(m, cond, args.ablation_judge)}
            ids = [i for i in de_ids if i in other_c]
            b = sum(1 for i in ids if is_c(cd_abl[i]) and not is_c(other_c[i]))
            c = sum(1 for i in ids if not is_c(cd_abl[i]) and is_c(other_c[i]))
            abl[f"closed_dated_vs_{cond}"] = {
                "n": len(ids),
                "closed_dated_correct": round(
                    sum(is_c(cd_abl[i]) for i in ids) / len(ids), 4
                ),
                f"{cond}_correct": round(
                    sum(is_c(other_c[i]) for i in ids) / len(ids), 4
                ),
                "only_dated_correct": b,
                f"only_{cond}_correct": c,
                "mcnemar_exact_p": mcnemar_exact(b, c),
                "stale_dated": sum(is_s(cd_abl[i]) for i in ids),
                f"stale_{cond}": sum(is_s(other_c[i]) for i in ids),
            }
        res["ablation_de"] = abl
        res["by_lang_correct"] = {
            lang: share([r for r in all_rows if r["lang"] == lang], is_c)
            for lang in ("de-CH", "fr-CH", "it-CH")
        }
        res["language_consistency"] = score.language_consistency(all_rows)
        out["models"][m] = res
    # 70B vs 8B paired
    a = {r["id"]: r for r in rows_of(MODELS[1], "closed_dated")}
    b8 = {r["id"]: r for r in rows_of(MODELS[0], "closed_dated")}
    ids = sorted(set(a) & set(b8))
    only70 = sum(
        1 for i in ids if a[i]["grade"] == "CORRECT" and b8[i]["grade"] != "CORRECT"
    )
    only8 = sum(
        1 for i in ids if b8[i]["grade"] == "CORRECT" and a[i]["grade"] != "CORRECT"
    )
    out["70b_vs_8b_closed_dated"] = {
        "n": len(ids),
        "only_70b": only70,
        "only_8b": only8,
        "mcnemar_exact_p": mcnemar_exact(only70, only8),
    }
    costs = Counter()
    for p in (data / "judgements").glob("*.jsonl"):
        if p.name.startswith(("panel__", "apertus-")):
            continue
        for j in dataset.read_jsonl(p):
            costs[j.get("judge_model") or p.name.split("__")[0]] += j.get("cost_usd") or 0
    sc = dataset.read_jsonl(data / "review" / "second_check.jsonl")
    out["paid_usage_usd"] = {
        "judges": {k: round(v, 4) for k, v in sorted(costs.items())},
        "second_check_qwen": round(sum(r.get("cost_usd") or 0 for r in sc), 4),
        "note": "reported by OpenRouter per call; judge calibration (61 calls) and a 5-core test of the second check are not included",
    }
    (HERE / "analysis.json").write_text(
        json.dumps(out, indent=1) + "\n", encoding="utf-8"
    )
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
