"""Apply review decisions (drop / patch per core and language) to a draft file and log every change.

Decision file: {"version": "...", "reviewer": "...", "decisions": [
  {"core_id": "cx-0016", "action": "drop", "reason": "..."},
  {"core_id": "cx-0035", "action": "patch", "reason": "...", "all": {...}, "de": {...}, "fr": {...}, "it": {...}}
]}
Patches set top-level fields; dotted keys ("temporal.bucket") set nested fields.
"""

import argparse
import json
from pathlib import Path


def set_path(d, key, value):
    parts = key.split(".")
    for p in parts[:-1]:
        d = d.setdefault(p, {})
    d[parts[-1]] = value


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("decisions")
    ap.add_argument("src")
    ap.add_argument("out")
    args = ap.parse_args()
    spec = json.loads(Path(args.decisions).read_text(encoding="utf-8"))
    by_core = {d["core_id"]: d for d in spec["decisions"]}
    rows = [
        json.loads(line)
        for line in Path(args.src).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    out, dropped, patched = [], set(), set()
    for r in rows:
        d = by_core.get(r["core_id"])
        if d and d["action"] == "drop":
            dropped.add(r["core_id"])
            continue
        if d and d["action"] == "patch":
            changes = {**d.get("all", {}), **d.get(r["lang"][:2], {})}
            before = {k: _get(r, k) for k in changes}
            for k, v in changes.items():
                set_path(r, k, v)
            log = r["authoring"].get("manual_correction") or []
            log = log if isinstance(log, list) else [log]
            log.append(
                {
                    "review": spec["version"],
                    "by": spec["reviewer"],
                    "reason": d["reason"],
                    "before": before,
                }
            )
            r["authoring"]["manual_correction"] = log
            patched.add(r["core_id"])
        if d and d["action"] == "keep":
            r.setdefault("review_notes", []).append(
                {"review": spec["version"], "note": d["reason"]}
            )
        out.append(r)
    Path(args.out).write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out), encoding="utf-8"
    )
    missing = set(by_core) - {r["core_id"] for r in rows}
    print(
        f"{len(rows)} -> {len(out)} rows; dropped cores {sorted(dropped)}; patched cores {sorted(patched)}"
    )
    if missing:
        print(f"WARNING: decisions for unknown cores {sorted(missing)}")


def _get(d, key):
    for p in key.split("."):
        if not isinstance(d, dict):
            return None
        d = d.get(p)
    return d


if __name__ == "__main__":
    main()
