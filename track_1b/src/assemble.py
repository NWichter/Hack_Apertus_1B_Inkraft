import json
from pathlib import Path
def load(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip().startswith("{")]
out = []
b01 = load("b01_kvg.out.jsonl")
rejected = {2, 3, 4, 5, 6, 7}
for k, it in enumerate(b01, 1):
    it["_batch"] = "b01_kvg"
    if k in rejected:
        continue
    out.append(it)
for it in load("b01_kvg_r1.out.jsonl"):
    it["_batch"] = "b01_kvg_r1"
    out.append(it)
for b in ["b02_kvv", "b03_ahvg", "b04_ivg", "b05_elg", "b06_uvg", "b07_atsg", "b08_or"]:
    for it in load(f"{b}.out.jsonl"):
        it["_batch"] = b
        out.append(it)
corrections = []
for it in out:
    if it["_batch"] == "b02_kvv" and it["fr"] and it["fr"]["answer"] == "1 mois" and "dans le mois qui suit" in it["fr"]["evidence"]:
        it["fr"]["answer"], it["fr"]["answer_aliases"] = "dans le mois qui suit l’information", ["1 mois", "un mois"]
        it["it"]["answer"], it["it"]["answer_aliases"] = "nel mese che segue l’informazione", ["1 mese", "un mese"]
        it["_manual_correction"] = [
            {
                "review": "draft correction (2026-10-01)",
                "by": "drafting pipeline",
                "reason": "fr/it answer replaced by the literal phrase of the authentic text (was '1 mois'/'1 mese', not literal)",
            }
        ]
        corrections.append(it["de"]["question"])
Path("codex.compact.jsonl").write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in out), encoding="utf-8")
print(len(out), "items;", "corrections:", corrections)
