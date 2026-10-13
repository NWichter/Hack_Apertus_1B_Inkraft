"""Figure for the report: grade shares (correct / stale / near miss / other / not attempted) per model,
condition and item group, from data/responses and the judge's grades. Also writes report/figure_data.json.

Usage: python report/make_figures.py [--judge-model qwen/qwen3-235b-a22b-2507]
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
from inkraft import dataset, score  # noqa: E402
from inkraft.judge import judge_path  # noqa: E402

CATS = (
    ("CORRECT", "correct", "#2a78d6"),
    ("STALE", "stale (earlier law)", "#eb6834"),
    ("NEAR_MISS", "near miss", "#1baf7a"),
    ("OTHER", "other wrong", "#eda100"),
    ("NOT_ATTEMPTED", "not attempted", "#c3c2b7"),
)
RUNS = (
    ("apertus-v1.5-8b", "closed_dated", "8B closed"),
    ("apertus-v1.5-70b", "closed_dated", "70B closed"),
    ("apertus-v1.5-8b", "open_book", "8B open book"),
    ("apertus-v1.5-70b", "open_book", "70B open book"),
)
GROUPS = (
    ("stable", "unchanged since 2024"),
    ("changed", "changed, no stored earlier answer"),
    ("stale_pair", "changed, earlier answer stored (STALE pair)"),
)


def group_of(it):
    if it.get("outdated_answers"):
        return "stale_pair"
    return (
        "stable"
        if (it.get("temporal") or {}).get("bucket") == "stable_pre2024"
        else "changed"
    )


def cat_of(row):
    if row["grade"] == "INCORRECT":
        return row["subtype"] or "OTHER"
    return row["grade"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge-model", default="qwen/qwen3-235b-a22b-2507")
    args = ap.parse_args()
    data = ROOT / "data"
    items = dataset.load(data)
    by_id = {it["id"]: it for it in items}
    out = {}
    for model, cond, label in RUNS:
        p = data / "responses" / f"{model}__{cond}.jsonl"
        if not p.exists():
            continue
        rows = score.grade_rows(
            items,
            dataset.read_jsonl(p),
            dataset.read_jsonl(judge_path(data, args.judge_model, model, cond)),
        )
        for g, _ in GROUPS:
            sel = [r for r in rows if r["grade"] and group_of(by_id[r["id"]]) == g]
            c = Counter(cat_of(r) for r in sel)
            out[f"{label}|{g}"] = {
                "n": len(sel),
                **{k: c.get(k, 0) for k, _, _ in CATS},
            }
    (HERE / "figure_data.json").write_text(
        json.dumps(out, indent=1) + "\n", encoding="utf-8"
    )

    plt.rcParams.update({"font.size": 7, "font.family": "DejaVu Sans"})
    fig, axes = plt.subplots(len(GROUPS), 1, figsize=(6.6, 3.9), sharex=True)
    labels = [lab for _, _, lab in RUNS if any(k.startswith(lab + "|") for k in out)]
    for ax, (g, gtitle) in zip(axes, GROUPS):
        left = [0.0] * len(labels)
        for key, name, color in CATS:
            vals = []
            for lab in labels:
                d = out.get(f"{lab}|{g}") or {"n": 0}
                vals.append(100 * d.get(key, 0) / d["n"] if d["n"] else 0)
            ax.barh(
                labels,
                vals,
                left=left,
                color=color,
                edgecolor="#fcfcfb",
                linewidth=1.2,
                height=0.7,
                label=name,
            )
            for i, v in enumerate(vals):
                if v >= 7:
                    ax.text(
                        left[i] + v / 2,
                        i,
                        f"{v:.0f}",
                        ha="center",
                        va="center",
                        color="#0b0b0b",
                        fontsize=6,
                    )
            left = [a + b for a, b in zip(left, vals)]
        n = (out.get(f"{labels[0]}|{g}") or {}).get("n", 0)
        ax.set_title(
            f"{gtitle} (n = {n} rows per run)", loc="left", fontsize=7, color="#52514e"
        )
        ax.invert_yaxis()
        ax.set_xlim(0, 100)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="y", length=0)
    axes[-1].set_xlabel("share of graded answers (%)", color="#52514e")
    axes[0].legend(
        ncol=5, loc="lower left", bbox_to_anchor=(0, 1.25), frameon=False, fontsize=6.5
    )
    fig.tight_layout()
    fig.savefig(HERE / "fig_results.svg")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
