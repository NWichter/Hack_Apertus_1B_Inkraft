"""Figure for the preliminary results: correct share per group, Apertus 8B vs 70B, closed_dated, Wilson 95 % CI.

Input: preliminary_summary.json (aggregates of the run on the unreviewed draft, rule-based grading only).
Usage: python report/make_figures.py
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).parent
S = json.loads((HERE / "preliminary_summary.json").read_text(encoding="utf-8"))
MODELS = (
    ("apertus-v1.5-8b__closed_dated", "Apertus 1.5 8B", "#9bb3cf"),
    ("apertus-v1.5-70b__closed_dated", "Apertus 1.5 70B", "#1a4f8b"),
)
GROUPS = (
    ("All rows", lambda r: r["overall"]),
    ("Stable before 2024", lambda r: r["by_temporal"]["stable_pre2024"]),
    ("Changed since 2024", lambda r: r["temporal_qtype"]),
    ("Current wording in corpus", lambda r: r["by_contam"]["current"]),
    ("No wording found", lambda r: r["by_contam"]["absent"]),
    ("Only previous wording", lambda r: r["by_contam"]["outdated"]),
)


def main():
    plt.rcParams.update({"font.size": 7, "font.family": "DejaVu Sans"})
    fig, ax = plt.subplots(figsize=(3.4, 3.2))
    h = 0.38
    for i, (key, label, color) in enumerate(MODELS):
        run = S["runs"][key]
        ys, xs, lo, hi = [], [], [], []
        for g, (_, get) in enumerate(GROUPS):
            d = get(run)
            share = d["correct"] / d["n"]
            ys.append(g + (i - 0.5) * h)
            xs.append(share * 100)
            lo.append((share - d["correct_ci95"][0]) * 100)
            hi.append((d["correct_ci95"][1] - share) * 100)
        ax.barh(ys, xs, height=h, color=color, label=label)
        ax.errorbar(
            xs,
            ys,
            xerr=[lo, hi],
            fmt="none",
            ecolor="#333333",
            elinewidth=0.7,
            capsize=1.5,
        )
        for y, x, e in zip(ys, xs, hi):
            ax.text(x + e + 1, y, f"{x:.0f}", va="center", fontsize=6)
    first = S["runs"][MODELS[0][0]]
    labels = [name + "\n(n = " + str(get(first)["n"]) + ")" for name, get in GROUPS]
    ax.set_yticks(range(len(GROUPS)), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 80)
    ax.set_xlabel("Correct, % of rows (95 % Wilson CI)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper right", frameon=False, fontsize=6)
    fig.tight_layout()
    fig.savefig(HERE / "fig_preliminary.svg")


if __name__ == "__main__":
    main()
