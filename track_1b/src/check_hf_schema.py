"""Check that every Hugging Face configuration loads with one consistent column type per field.

`datasets`/pyarrow infer one type per column; a field that is a list in one row and a string in another makes
`load_dataset(..., "metadata")` fail. This check walks every row and reports such paths.

python src/check_hf_schema.py            # pure-Python check of all published JSONL files
python src/check_hf_schema.py --arrow    # additionally read every file with pyarrow.json (needs pyarrow)
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
CONFIGS = {
    "test": ["test.jsonl"],
    "metadata": ["metadata.jsonl"],
    "responses": ["responses/*.jsonl"],
    "judgements": ["judgements/panel__*.jsonl"],
}


def kind(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, (int, float)):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "list"
    if isinstance(v, dict):
        return "struct"
    return type(v).__name__


def walk(v, path, seen):
    k = kind(v)
    if k is None:
        return
    seen[path].add(k)
    if k == "list":
        for x in v:
            walk(x, path + "[]", seen)
    elif k == "struct":
        for key, x in v.items():
            walk(x, f"{path}.{key}", seen)


def conflicts(files):
    seen = defaultdict(set)
    for p in files:
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                walk(json.loads(line), "", seen)
    return {path or "<row>": sorted(k) for path, k in seen.items() if len(k) > 1}


def files_of(patterns, data=DATA):
    out = []
    for pat in patterns:
        out += sorted(data.glob(pat))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(DATA))
    ap.add_argument("--arrow", action="store_true")
    args = ap.parse_args()
    data, bad = Path(args.data), False
    for name, pats in CONFIGS.items():
        files = files_of(pats, data)
        c = conflicts(files)
        print(
            f"{name}: {len(files)} file(s), {'OK' if not c else 'mixed types ' + json.dumps(c)}"
        )
        bad |= bool(c)
        if args.arrow:
            import pyarrow.json as pj

            for f in files:
                pj.read_json(f, read_options=pj.ReadOptions(block_size=1 << 26))
            print(f"{name}: pyarrow reads all files")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
