"""Freeze the reviewed dataset as v1.0.0: mark rows reviewed, validate in frozen mode, write test.jsonl and
metadata.jsonl, the ablation subset and FREEZE.json. Needs --go (the freeze is Niklas' decision).

python src/freeze.py --fedlex <fedlex-v2> --go [--version 1.0.0] [--corpus <multilegalpile dir>]
Afterwards: report/fill_numbers.py, commit and `git tag dataset-v1.0.0` (printed at the end, not executed).
"""

import argparse
import datetime as dt
import hashlib
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
sys.path.insert(0, str(HERE))
from after_review import read, stats, write  # noqa: E402

STABLE_ABLATION = 60
SEED = 20261012


def sha(path):
    """SHA-256 over LF line endings, so the hash does not depend on the checkout platform."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fedlex", required=True)
    ap.add_argument(
        "--data", default=str(DATA), help="data folder (default track_1b/data)"
    )
    ap.add_argument("--src", help="reviewed rows (default <data>/merged.v2.jsonl)")
    ap.add_argument("--version", default="1.0.0")
    ap.add_argument(
        "--corpus", help="MultiLegalPile folder for the contamination check (optional)"
    )
    ap.add_argument(
        "--go", action="store_true", help="Niklas gave the go for the freeze"
    )
    ap.add_argument(
        "--rc",
        action="store_true",
        help="release candidate (version must contain '-rc'): evaluation runs, no release tag",
    )
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.rc and "-rc" not in args.version:
        sys.exit("--rc needs a version like 1.0.0-rc1")
    if not (args.go or args.rc):
        sys.exit("freeze needs --go: Niklas decides when the dataset is frozen")
    data = Path(args.data)
    args.src = args.src or str(data / "merged.v2.jsonl")

    rows = read(args.src)
    missing = sorted(
        {
            r["core_id"]
            for r in rows
            if (r.get("review") or {}).get("decision") not in ("keep", "patch")
        }
    )
    if missing:
        sys.exit(
            f"{len(missing)} cores without a keep/patch review decision, e.g. {missing[:5]}"
        )
    for r in rows:
        human = not str(r["review"].get("reviewer") or "").startswith("automatic")
        r["status"] = "reviewed" if human else "auto_verified"
        r["needs_human_review"] = not human
    frozen = data / f"merged.v{args.version}.jsonl"
    write(frozen, rows)

    report = data / f"validation_report.v{args.version}.md"
    issues = data / "review" / f"issues.v{args.version}.json"
    res = subprocess.run(
        [
            sys.executable,
            str(HERE / "validate_items.py"),
            "--fedlex",
            args.fedlex,
            "--frozen",
            "--report",
            str(report),
            "--issues-json",
            str(issues),
            str(frozen),
        ],
    )
    if res.returncode:
        sys.exit("validator reports errors in frozen mode; fix them before the freeze")

    env = {**__import__("os").environ, "PYTHONPATH": str(HERE)}
    subprocess.run(
        [sys.executable, "-m", "inkraft", "--data", str(data), "build", str(frozen)],
        check=True,
        env=env,
    )

    de = [r for r in rows if r["lang"] == "de-CH"]
    temporal = sorted(
        r["core_id"] for r in de if r["temporal"]["bucket"] != "stable_pre2024"
    )
    stable = sorted(
        r["core_id"] for r in de if r["temporal"]["bucket"] == "stable_pre2024"
    )
    ablation = temporal + sorted(
        random.Random(SEED).sample(stable, min(STABLE_ABLATION, len(stable)))
    )
    (data / "ablation_cores.txt").write_text(
        "\n".join(ablation) + "\n", encoding="utf-8", newline="\n"
    )

    if args.corpus:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "inkraft",
                "--data",
                str(data),
                "contam",
                "--corpus",
                args.corpus,
            ],
            check=True,
            env=env,
        )

    info = {
        "version": args.version,
        "frozen_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "as_of": "2026-10-01",
        "files": {
            p.name: sha(p)
            for p in (
                data / "test.jsonl",
                data / "metadata.jsonl",
                frozen,
                data / "ablation_cores.txt",
            )
        },
        "fedlex_manifest_sha256": sha(data / "sources" / "fedlex_manifest.v2.json"),
        "stats": stats(rows),
        "stats_note": "yes_no_cores counts answer_type yes_no; by_question_type.yes_no counts the question type (a core of another question type, e.g. temporal, can have a yes/no answer)",
        "ablation_cores": len(ablation),
        "release_candidate": bool(args.rc),
        "review_status_cores": {
            s: len({r["core_id"] for r in rows if r["status"] == s})
            for s in ("reviewed", "auto_verified")
        },
        "review_log_sha256": rows[0]["review"]["log_sha256"],
    }
    (data / "FREEZE.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(json.dumps(info["stats"], indent=1))
    print(
        "\nnext: scripts/run_after_freeze.sh (first freeze) or the rest of scripts/after_human_check.sh,\n"
        "then python report/fill_numbers.py, commit track_1b/data and tag dataset-v<version>"
    )


if __name__ == "__main__":
    main()
