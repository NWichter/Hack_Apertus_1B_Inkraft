import json
import re
from pathlib import Path

FEDLEX_ROOT = Path(r"C:\Users\nikla\OneDrive - NeoTube GmbH\Hackathon-Daten\Hack_Apertus\1B_Swiss_Voices\quellen\fedlex-v2")
manifest = json.loads((FEDLEX_ROOT / "manifest.json").read_text(encoding="utf-8"))
acts = {a["abbr"]: a for a in manifest["acts"]}

cache = {}
def get_doc(act, lang="de"):
    key = (act, lang)
    if key not in cache:
        a = acts[act]
        curr = next(v for v in a["versions"] if v["role"] == "current")
        doc = json.loads((FEDLEX_ROOT / curr["files"][lang]["path"]).read_text(encoding="utf-8"))
        cache[key] = {art["article_id"]: art for art in doc["articles"]}
    return cache[key]

def get_para_text(act, art_id, para_id, lang):
    doc = get_doc(act, lang)
    art = doc.get(art_id)
    if not art:
        raise ValueError(f"Article {art_id} not found in {act} ({lang})")
    para = next((p for p in art["paragraphs"] if p["paragraph"] == (para_id or "")), None)
    if not para:
        raise ValueError(f"Paragraph {para_id!r} not found in {act} {art_id} ({lang})")
    return para["text"]

def norm_ws(s):
    return " ".join(s.replace("\u00a0", " ").replace("’", "'").split()).lower()

def verify_single_item(item, index=None):
    errors = []
    act = item["act"]
    art_id = item["article_id"]
    p_id = item.get("paragraph") or ""
    qt = item["question_type"]
    at = item["answer_type"]
    an = item.get("answer_normalized")

    for lang in ["de", "fr", "it"]:
        if lang not in item:
            errors.append(f"Missing {lang}")
            continue
        data = item[lang]
        q = data.get("question", "")
        a = data.get("answer", "")
        ev = data.get("evidence", "")

        if not q.endswith("?"):
            errors.append(f"[{lang}] Question does not end with '?': {q}")
        if len(a) > 120:
            errors.append(f"[{lang}] Answer too long ({len(a)} chars): {a}")
        if lang == "de":
            if "ß" in q or "ß" in a or "ß" in ev:
                errors.append(f"[{lang}] Contains ß!")

        # Verify evidence against Fedlex authentic paragraph
        try:
            para_text = get_para_text(act, art_id, p_id, lang)
            if norm_ws(ev) not in norm_ws(para_text):
                errors.append(f"[{lang}] Evidence not found in {act} {art_id} p={p_id!r}:\n  EV: {ev}\n  PARA: {para_text[:120]}")
        except Exception as e:
            errors.append(f"[{lang}] Fedlex lookup error: {e}")

        # Check numeric types
        if qt == "numeric":
            if an is None:
                errors.append(f"[{lang}] numeric question requires answer_normalized")
            else:
                val = an.get("value")
                val_str = str(val)
                # Check that val is in answer
                if val_str not in a and (not isinstance(val, float) or f"{val:.1f}" not in a):
                    # check word representation?
                    pass
        elif qt == "yes_no":
            expected = {"de": {"ja", "nein"}, "fr": {"oui", "non"}, "it": {"sì", "si", "no"}}
            if norm_ws(a) not in expected[lang]:
                errors.append(f"[{lang}] yes_no answer {a!r} not in {expected[lang]}")

    return errors

print("Verifier harness ready")
