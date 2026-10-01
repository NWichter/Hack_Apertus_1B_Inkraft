"""Build the judge calibration set: constructed answers with a known grade, from dataset items.

Every row is synthetic (templates below) and carries its expected grade by construction.
The judge prompt is frozen only after it reaches >= 95 % on this set.
"""

import argparse
import json
import random
from pathlib import Path

TEMPLATES = {
    "correct_short": ("CORRECT", None, {"de": "{a}.", "fr": "{a}.", "it": "{a}."}),
    "correct_verbose": (
        "CORRECT",
        None,
        {
            "de": "Nach dem geltenden Bundesrecht gilt: {a}. Im Einzelfall gibt die zuständige Stelle Auskunft.",
            "fr": "Selon le droit fédéral en vigueur: {a}. Dans un cas concret, l’organe compétent renseigne.",
            "it": "Secondo il diritto federale vigente: {a}. Nel caso concreto informa l’organo competente.",
        },
    ),
    "hedged_correct": (
        "CORRECT",
        None,
        {
            "de": "Ich bin nicht ganz sicher, aber vermutlich: {a}.",
            "fr": "Je n’en suis pas tout à fait certain, mais probablement: {a}.",
            "it": "Non ne sono del tutto certo, ma probabilmente: {a}.",
        },
    ),
    "wrong_language": (
        "CORRECT",
        None,
        {
            "de": "La réponse est: {a}.",
            "fr": "Die Antwort lautet: {a}.",
            "it": "The answer is: {a}.",
        },
    ),
    "stale": ("INCORRECT", "STALE", {"de": "{o}.", "fr": "{o}.", "it": "{o}."}),
    "near_miss": (
        "INCORRECT",
        "NEAR_MISS",
        {
            "de": "Soweit ich weiss: {n}.",
            "fr": "À ma connaissance: {n}.",
            "it": "Per quanto ne so: {n}.",
        },
    ),
    "conflicting": (
        "INCORRECT",
        "OTHER",
        {
            "de": "Das hängt vom Fall ab: entweder {a} oder {n}.",
            "fr": "Cela dépend du cas: soit {a}, soit {n}.",
            "it": "Dipende dal caso: o {a} o {n}.",
        },
    ),
    "abstain": (
        "NOT_ATTEMPTED",
        None,
        {
            "de": "Das weiss ich nicht sicher. Bitte wenden Sie sich an die zuständige Ausgleichskasse oder Krankenkasse.",
            "fr": "Je ne sais pas avec certitude. Veuillez vous adresser à la caisse compétente.",
            "it": "Non lo so con certezza. Si rivolga alla cassa competente.",
        },
    ),
}
ITEM_FIELDS = [
    "id",
    "core_id",
    "lang",
    "question",
    "answer",
    "answer_aliases",
    "answer_core",
    "answer_type",
    "answer_normalized",
    "outdated_answers",
    "near_miss_answers",
    "as_of",
    "question_type",
]


def build(items, n_items, seed):
    rng = random.Random(seed)
    temporal = [it for it in items if it.get("outdated_answers")]
    others = [
        it
        for it in items
        if not it.get("outdated_answers") and it.get("near_miss_answers")
    ]
    picked = rng.sample(temporal, min(len(temporal), n_items // 2))
    picked += rng.sample(others, n_items - len(picked))
    rows = []
    for k, it in enumerate(picked):
        l2 = it["lang"][:2]
        if it.get("outdated_answers"):
            kinds = [
                "stale",
                ["hedged_correct", "correct_verbose", "conflicting", "abstain"][k % 4],
            ]
        else:
            kinds = [
                ["correct_short", "abstain", "near_miss", "conflicting"][k % 4],
                [
                    "correct_verbose",
                    "wrong_language",
                    "hedged_correct",
                    "correct_verbose",
                ][k % 4],
            ]
        for kind in kinds:
            grade, sub, tpl = TEMPLATES[kind]
            near = (it.get("near_miss_answers") or [None])[0]
            if "{n}" in tpl[l2] and not near:
                continue
            text = tpl[l2].format(
                a=it["answer"], o=(it.get("outdated_answers") or [""])[0], n=near
            )
            rows.append(
                {
                    "cal_id": f"cal-{len(rows) + 1:03d}",
                    "kind": kind,
                    "expected_grade": grade,
                    "expected_subtype": sub,
                    "response": text,
                    "item": {f: it.get(f) for f in ITEM_FIELDS},
                    "generator": "template (make_calibration.py)",
                }
            )
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("items", help="draft or frozen items (jsonl)")
    ap.add_argument("out")
    ap.add_argument("--n-items", type=int, default=32)
    ap.add_argument("--seed", type=int, default=20261001)
    args = ap.parse_args()
    items = [
        json.loads(line)
        for line in Path(args.items).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows = build(items, args.n_items, args.seed)
    Path(args.out).write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8",
    )
    kinds = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print(f"{len(rows)} calibration rows: {kinds}")


if __name__ == "__main__":
    main()
