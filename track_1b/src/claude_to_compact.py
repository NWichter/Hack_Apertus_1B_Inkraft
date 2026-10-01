import json
import sys
from claude_items_frit import P
items = json.load(open("claude_items_de.json", encoding="utf-8"))
out = []
for n, i in enumerate(items):
    c = {"act": i["k"], "article_id": i["a"], "paragraph": i["p"], "domain": i["d"], "question_type": i["t"],
         "register": i["r"], "difficulty_prior": i["dp"], "answer_type": i["at"],
         "answer_normalized": {"value": i["n"][0], "unit": i["n"][1]} if i["n"] else None,
         "de": {"question": i["q"], "answer": i["ans"], "answer_aliases": i["al"], "near_miss_answers": i["nm"], "evidence": i["ev"]},
         "fr": None, "it": None, "temporal": None, "_batch": "claude_direct"}
    tmp = None
    if i["t"] == "temporal":
        tmp = {"previous_paragraph": i["pp"], "de": {"outdated_answer": i["oans"], "evidence": i["oev"]}, "fr": None, "it": None}
    if n in P:
        for lang in ("fr", "it"):
            v = P[n][lang]
            c[lang] = {"question": v[0], "answer": v[1], "answer_aliases": v[2], "near_miss_answers": [], "evidence": v[3]}
            if tmp is not None and len(v) > 4:
                tmp[lang] = {"outdated_answer": v[4], "evidence": v[5]}
    c["temporal"] = tmp
    out.append(c)
open(sys.argv[1] if len(sys.argv) > 1 else "claude.compact.jsonl", "w", encoding="utf-8").write("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in out))
print(len(out), sum(1 for c in out if c["fr"]))
