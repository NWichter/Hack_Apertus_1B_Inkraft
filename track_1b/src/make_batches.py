"""Build the Codex batch prompts (identical template, batch-specific parameters + article context)."""

import hashlib
import json
import sys
from pathlib import Path

from lib_src import MAN, arts, version

HERE = Path(__file__).parent
OUT = Path(sys.argv[1])
TEMPLATE = (HERE / "prompt_template.txt").read_text(encoding="utf-8")

BATCHES = [
    {
        "id": "b01_kvg",
        "act": "KVG",
        "n": 17,
        "quota": {"numeric": 7, "procedural": 5, "yes_no": 5, "temporal": 0},
        "domains": {
            "kvg_insured": [
                "art_4",
                "art_6",
                "art_8",
                "art_10",
                "art_25",
                "art_26",
                "art_32",
                "art_62",
                "art_85",
                "art_86",
            ],
            "kvg_billing": ["art_42_a", "art_44", "art_56", "art_57", "art_89"],
        },
        "changed": [],
    },
    {
        "id": "b02_kvv",
        "act": "KVV",
        "n": 14,
        "quota": {"numeric": 7, "procedural": 3, "yes_no": 4, "temporal": 0},
        "domains": {
            "kvg_insured": [
                "art_11",
                "art_91",
                "art_95",
                "art_96",
                "art_97",
                "art_98",
                "art_99",
                "art_100",
                "art_104_a",
                "art_105",
            ]
        },
        "changed": [],
    },
    {
        "id": "b03_ahvg",
        "act": "AHVG",
        "n": 20,
        "quota": {"numeric": 8, "procedural": 3, "yes_no": 4, "temporal": 5},
        "domains": {
            "ahv": [
                "art_1_a",
                "art_2",
                "art_3",
                "art_4",
                "art_5",
                "art_6",
                "art_14",
                "art_16",
                "art_22_ter",
                "art_23",
                "art_29_ter",
                "art_35",
                "art_35_ter",
                "art_39",
                "art_40",
                "art_46",
                "art_84",
            ]
        },
        "changed": ["art_2", "art_3", "art_4", "art_5", "art_39", "art_40"],
    },
    {
        "id": "b04_ivg",
        "act": "IVG",
        "n": 13,
        "quota": {"numeric": 5, "procedural": 4, "yes_no": 2, "temporal": 2},
        "domains": {
            "iv_el": [
                "art_3_a_bis",
                "art_3_b",
                "art_6",
                "art_7",
                "art_8",
                "art_10",
                "art_22",
                "art_24",
                "art_28_a",
                "art_35",
                "art_42_quater",
                "art_42_sexies",
                "art_47",
                "art_48",
                "art_54",
                "art_55",
                "art_69",
            ]
        },
        "changed": ["art_10", "art_47"],
    },
    {
        "id": "b05_elg",
        "act": "ELG",
        "n": 8,
        "quota": {"numeric": 3, "procedural": 2, "yes_no": 1, "temporal": 2},
        "domains": {
            "iv_el": [
                "art_6",
                "art_11",
                "art_13",
                "art_14",
                "art_15",
                "art_16_a",
                "art_16_b",
                "art_19",
                "art_21",
            ]
        },
        "changed": ["art_11"],
    },
    {
        "id": "b06_uvg",
        "act": "UVG",
        "n": 14,
        "quota": {"numeric": 7, "procedural": 4, "yes_no": 3, "temporal": 0},
        "domains": {
            "uvg_atsg": [
                "art_10",
                "art_15",
                "art_18",
                "art_19",
                "art_20",
                "art_24",
                "art_25",
                "art_26",
                "art_27",
                "art_28",
                "art_29",
                "art_30",
                "art_31",
                "art_36",
                "art_37",
                "art_58",
                "art_66",
                "art_91",
                "art_92",
            ]
        },
        "changed": [],
    },
    {
        "id": "b07_atsg",
        "act": "ATSG",
        "n": 14,
        "quota": {"numeric": 5, "procedural": 5, "yes_no": 4, "temporal": 0},
        "domains": {
            "uvg_atsg": [
                "art_3",
                "art_9",
                "art_13",
                "art_16",
                "art_19",
                "art_21",
                "art_26",
                "art_38",
                "art_39",
                "art_40",
                "art_41",
                "art_47",
                "art_49",
                "art_56",
                "art_58",
                "art_69",
            ]
        },
        "changed": [],
    },
    {
        "id": "b08_or",
        "act": "OR",
        "n": 5,
        "quota": {"numeric": 2, "procedural": 1, "yes_no": 2, "temporal": 0},
        "domains": {"or_illness": ["art_324_b", "art_336_c"]},
        "changed": [],
    },
]


def render_article(act, aid, changed):
    cur_v = version(act, "current")
    lines = []
    a_de = arts(act, "de")[aid]
    lines.append(
        f"### {act} {aid} | {a_de['heading']} | version {cur_v['version_date']}"
        + (" | CHANGED" if changed else "")
    )
    for lang in ("de", "fr", "it"):
        a = arts(act, lang).get(aid)
        if not a:
            continue
        lines.append(f"[{lang.upper()} current] {a['heading']}")
        for p in a["paragraphs"]:
            lines.append(f"  ({p['paragraph'] or '-'}) {p['text']}")
    if changed:
        prev_v = version(act, "previous")
        for lang in ("de", "fr", "it"):
            a = arts(act, lang, "previous").get(aid)
            if not a:
                continue
            lines.append(
                f"[{lang.upper()} PREVIOUS version {prev_v['version_date']}] {a['heading']}"
            )
            for p in a["paragraphs"]:
                lines.append(f"  ({p['paragraph'] or '-'}) {p['text']}")
    return "\n".join(lines)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    template_sha = hashlib.sha256(TEMPLATE.encode("utf-8")).hexdigest()
    index = []
    for b in BATCHES:
        art_ids = [a for ids in b["domains"].values() for a in ids]
        domain_lines = [f"  {d}: {', '.join(ids)}" for d, ids in b["domains"].items()]
        params = "\n".join(
            [
                f"ACT: {b['act']}",
                f"N_ITEMS: {b['n']}",
                "QUOTA: " + ", ".join(f"{k}={v}" for k, v in b["quota"].items()),
                "ARTICLES AND DOMAIN:",
                *domain_lines,
                "CHANGED ARTICLES (temporal allowed): "
                + (", ".join(b["changed"]) or "none"),
                "PARALLEL: yes",
            ]
        )
        articles = "\n\n".join(
            render_article(b["act"], a, a in b["changed"]) for a in art_ids
        )
        prompt = (
            TEMPLATE.replace("{N_ITEMS}", str(b["n"]))
            .replace("{MAX_PER_ARTICLE}", "3")
            .replace("{BATCH_PARAMETERS}", params)
            .replace("{ARTICLES}", articles)
        )
        (OUT / f"{b['id']}.prompt.txt").write_text(prompt, encoding="utf-8")
        index.append(
            {
                **b,
                "prompt_file": f"{b['id']}.prompt.txt",
                "prompt_chars": len(prompt),
                "template_sha256": template_sha,
            }
        )
        print(b["id"], len(prompt))
    (OUT / "batches.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
