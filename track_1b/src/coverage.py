"""Coverage matrix of the frozen dataset: domain x question type, plus changed and STALE-pair cores.
Prints a Markdown table (German cores); used in docs/DATA_CARD.md and by hf_release.py card.

python src/coverage.py [--data data]
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
QTYPES = (
    "numeric",
    "procedural",
    "yes_no",
    "temporal",
    "calc",
    "false_premise",
    "term",
)
DOMAINS = {
    "kvg_insured": "Health insurance (insured)",
    "kvg_billing": "Health insurance (billing)",
    "ahv": "AHV",
    "iv_el": "IV / EL",
    "uvg_atsg": "Accident insurance / ATSG",
    "eo_alv": "EO / ALV",
    "bvg_3a": "Occupational pensions / 3a",
    "or_illness": "Wage during illness (OR)",
    "famz": "Family allowances",
}


def matrix(data):
    freeze = json.loads((Path(data) / "FREEZE.json").read_text(encoding="utf-8"))
    rows = [
        json.loads(x)
        for x in (Path(data) / f"merged.v{freeze['version']}.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if x.strip()
    ]
    de = [r for r in rows if r["lang"] == "de-CH"]
    cell = defaultdict(Counter)
    changed, stale, acts = Counter(), Counter(), defaultdict(set)
    for r in de:
        d = r["domain"]
        cell[d][r["question_type"]] += 1
        changed[d] += r["temporal"]["bucket"] != "stable_pre2024"
        stale[d] += bool(r.get("outdated_answers"))
        acts[d].add(r["source"]["act"])
    head = ["Domain (acts)", *QTYPES, "changed since 2024", "STALE pairs", "total"]
    lines = [
        "| " + " | ".join(head) + " |",
        "| " + " | ".join(["---"] + ["---:"] * (len(head) - 1)) + " |",
    ]
    for d in sorted(cell, key=lambda d: -sum(cell[d].values())):
        name = f"{DOMAINS.get(d, d)} ({', '.join(sorted(acts[d]))})"
        lines.append(
            "| "
            + " | ".join(
                [
                    name,
                    *(str(cell[d][q]) for q in QTYPES),
                    str(changed[d]),
                    str(stale[d]),
                    str(sum(cell[d].values())),
                ]
            )
            + " |"
        )
    tot = Counter()
    for d in cell:
        tot.update(cell[d])
    lines.append(
        "| **Total** | "
        + " | ".join(
            [
                *(str(tot[q]) for q in QTYPES),
                str(sum(changed.values())),
                str(sum(stale.values())),
                str(len(de)),
            ]
        )
        + " |"
    )
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(HERE.parent / "data"))
    print(matrix(ap.parse_args().data))
