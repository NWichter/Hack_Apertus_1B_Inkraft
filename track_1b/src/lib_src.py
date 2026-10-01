"""Read access to the fedlex article files written by fetch_fedlex.py (folder from STICHTAG_FEDLEX_DIR)."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("STICHTAG_FEDLEX_DIR", "fedlex"))
MAN = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
_cache = {}


def version(act, role):
    a = next(x for x in MAN["acts"] if x["abbr"] == act)
    return next((v for v in a["versions"] if v["role"] == role), None)


def arts(act, lang="de", role="current"):
    key = (act, lang, role)
    if key not in _cache:
        v = version(act, role)
        d = json.loads((ROOT / v["files"][lang]["path"]).read_text(encoding="utf-8"))
        _cache[key] = {x["article_id"]: x for x in d["articles"]}
    return _cache[key]


def show(act, aid, lang="de", role="current"):
    a = arts(act, lang, role).get(aid)
    return f"[{act} {aid} {lang} {role}] {a['heading']}\n{a['text']}" if a else f"[{act} {aid} {lang} {role}] MISSING"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    act = sys.argv[1]
    lang = sys.argv[3] if len(sys.argv) > 3 else "de"
    for aid in sys.argv[2].split(","):
        print(show(act, aid, lang))
        print()
