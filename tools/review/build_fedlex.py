"""Bundle the local fedlex article files into fedlex_texte.js so index.html can check quotes offline (file://)."""

import argparse
import os
import json
from pathlib import Path

DEFAULT_SRC = os.environ.get("STICHTAG_FEDLEX_DIR")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--fedlex",
        default=DEFAULT_SRC,
        required=DEFAULT_SRC is None,
        help="output folder of track_1b/src/fetch_fedlex.py (default: $STICHTAG_FEDLEX_DIR)",
    )
    ap.add_argument("--out", default=str(Path(__file__).with_name("fedlex_texte.js")))
    ap.add_argument(
        "--roles",
        default="current,previous,intermediate",
        help="comma-separated version roles (current, previous, intermediate, future) or 'all'",
    )
    args = ap.parse_args()
    root = Path(args.fedlex)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    roles = None if args.roles == "all" else set(args.roles.split(","))
    out = {"as_of": manifest.get("as_of"), "source": str(root), "acts": {}}
    n_art = 0
    for act in manifest["acts"]:
        entry = {
            "sr": act["sr"],
            "eli": act["eli"],
            "title": act.get("title", {}),
            "versions": {},
        }
        for v in act["versions"]:
            if roles and v["role"] not in roles:
                continue
            ver = {"role": v["role"], "langs": {}}
            for lang, f in v["files"].items():
                doc = json.loads((root / f["path"]).read_text(encoding="utf-8"))
                arts = {}
                for a in doc["articles"]:
                    paras = [
                        [p["paragraph"], p["text"]] for p in a.get("paragraphs") or []
                    ]
                    arts[a["article_id"]] = {
                        "n": a.get("number"),
                        "h": a.get("heading"),
                        "p": paras,
                        "t": "" if paras else a.get("text", ""),
                    }
                    n_art += 1
                ver["langs"][lang] = arts
            entry["versions"][v["version_date"]] = ver
        out["acts"][act["abbr"]] = entry
    js = (
        "window.FEDLEX_DATA = "
        + json.dumps(out, ensure_ascii=False, separators=(",", ":"))
        + ";\n"
    )
    Path(args.out).write_text(js, encoding="utf-8")
    print(f"{n_art} articles, {len(js) / 1e6:.1f} MB -> {args.out}")


if __name__ == "__main__":
    main()
