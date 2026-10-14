"""Hugging Face release: build the dataset card from the frozen numbers and upload the dataset.

  python src/hf_release.py card --repo <owner/name>       # hf/README.md from hf/README.template.md
  python src/hf_release.py upload --repo <owner/name>     # dry run: list what would be uploaded
  python src/hf_release.py upload --repo <owner/name> --go [--public]

The card step fails if a value is missing (no placeholders are ever uploaded). Upload creates the dataset
repo private unless --public is given (the submission needs it public; Niklas decides when).
Token: HF_TOKEN from the environment or from --env <file> (read with a parser, never printed).
"""

import argparse
import collections
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HF = ROOT / "hf"
sys.path.insert(0, str(ROOT / "src"))
import coverage  # noqa: E402


def load_json(path, required=True):
    p = Path(path)
    if not p.exists():
        if required:
            sys.exit(
                f"missing {p.relative_to(ROOT)}: run the step that writes it first"
            )
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def table(header, rows):
    out = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    return "\n".join(out)


def card(args):
    freeze = load_json(DATA / "FREEZE.json")
    summary = load_json(DATA / "review" / "after_review_summary.json")
    agreement = load_json(DATA / "human_labels" / "agreement.json")
    calib = load_json(DATA / "judge_calibration.json")
    panel = load_json(DATA / "judge_panel.json")
    calibs = {
        j: load_json(DATA / f"judge_calibration__{j.replace('/', '_')}.json", False)
        or (calib if j == calib.get("judge_model") else None)
        for j in panel["judges"]
    }
    human = load_json(DATA / "human_labels" / "summary.json")
    human_dataset = "; ".join(
        f"{g}: {s['drop']} of {s['n']} rejected (Wilson 95 % {s['error_rate_wilson95']}), {s['unsure']} unsure"
        for g, s in sorted(human["dataset_check"].items())
    )
    st = freeze["stats"]
    vp = agreement.get("vs_panel") or {}
    agreement_text = (
        f"{agreement['n']} grades; Cohen's kappa human vs first judge {agreement['kappa']:.2f} "
        f"(95 % CI {agreement['kappa_ci95'][0]:.2f}–{agreement['kappa_ci95'][1]:.2f})"
        + (
            f", human vs panel majority {vp['kappa']:.2f} (95 % CI {vp['kappa_ci95'][0]:.2f}–{vp['kappa_ci95'][1]:.2f})"
            if vp
            else ""
        )
    )
    sample = DATA / "human_labels" / "sample_20pct.jsonl"
    n_sample = (
        sum(1 for x in sample.read_text(encoding="utf-8").splitlines() if x.strip())
        if sample.exists()
        else None
    )
    models = sorted(
        {p.stem.split("__")[0] for p in (DATA / "responses").glob("*.jsonl")}
    )
    comp = table(
        ["Axis (DE cores)", "Distribution"],
        [
            [
                k.replace("by_", ""),
                ", ".join(
                    f"{a} {b}" for a, b in sorted(st[k].items(), key=lambda x: -x[1])
                ),
            ]
            for k in (
                "by_act",
                "by_domain",
                "by_question_type",
                "by_generator",
                "by_bucket",
            )
        ],
    )
    qc = table(
        ["Check", "Result"],
        [
            [
                "Validator (`src/validate_items.py`, frozen mode): schema, evidence verbatim in the cited paragraph, answer in evidence, outdated answer verbatim in an earlier version, near miss never an earlier value, duplicates, language consistency, leaks of the answer into the question, threshold words",
                "0 errors",
            ],
            [
                "Release rules and independent second check (Qwen3-235B) of every core",
                f"{st['cores']} cores kept, {summary['decisions'].get('drop', 0)} dropped, {summary['decisions'].get('patch', 0)} corrected",
            ],
            ["Human spot check (stratified random sample)", human_dataset],
            [
                "Judge calibration on 61 constructed answers (gate 0.95 per judge)",
                "; ".join(
                    f"{j}: grade {c['grade_accuracy']:.3f}, with subtype {c['subtype_accuracy']:.3f}"
                    for j, c in calibs.items()
                    if c
                ),
            ],
            [
                "Agreement within the judge panel (all main rows)",
                f"Fleiss' kappa {panel['fleiss_kappa_3class']:.2f} (3 grades), {panel['fleiss_kappa_5class']:.2f} (5 grades with subtypes); "
                + "; ".join(f"{j} agrees with the majority on {100 * v:.1f} %" for j, v in panel["agreement_with_majority"].items()),
            ],
            [
                f"Human check of a stratified random {100 * n_sample / st['rows']:.0f} % of judge grades",
                agreement_text,
            ],
        ],
    )
    rej = table(
        ["Generator", "Decided", "Dropped", "Drop rate"],
        [
            [g, v["decided"], v["dropped"], f"{100 * v['rate']:.0f} %"]
            for g, v in sorted(summary["reject_rate_by_generator"].items())
        ],
    )
    vals = {
        "VERSION": freeze["version"],
        "FROZEN_AT": freeze["frozen_at"][:10],
        "MODELS": ", ".join(models) if models else None,
        "PANEL": ", ".join(panel["judges"]),
        "CORES": st["cores"],
        "ROWS": st["rows"],
        "TRILINGUAL": st["trilingual_cores"],
        "TEMPORAL_CHANGED": st["temporal_changed_cores"],
        "STALE_PAIRS": st["stale_pair_cores"],
        "YES_NO_SHARE": f"{100 * st['yes_no_share']:.0f} %",
        "COMPOSITION_TABLE": comp,
        "COVERAGE_TABLE": coverage.matrix(DATA),
        "QC_TABLE": qc,
        "REJECT_TABLE": rej,
        "HUMAN_DATASET": human_dataset,
        "SAMPLE_N": n_sample,
        "AGREEMENT": agreement_text,
        "HF_REPO": args.repo,
    }
    missing = [k for k, v in vals.items() if v in (None, "", [])]
    if missing:
        sys.exit(f"values missing for the card: {missing}")
    text = (HF / "README.template.md").read_text(encoding="utf-8")
    for k, v in vals.items():
        text = text.replace("{{" + k + "}}", str(v))
    left = re.findall(r"\{\{[A-Z_]+\}\}", text) + (
        ["[More Information Needed]"] if "[More Information Needed]" in text else []
    )
    if left:
        sys.exit(f"placeholders left in the card: {left}")
    (HF / "README.md").write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {HF / 'README.md'}")


def files_to_upload():
    out = {
        "README.md": HF / "README.md",
        "LICENSE": DATA / "LICENSE",
        "FREEZE.json": DATA / "FREEZE.json",
    }
    for name in ("test.jsonl", "metadata.jsonl"):
        out[f"data/{name}"] = DATA / name
    for p in (
        DATA / "results.json",
        DATA / "expected_results.json",
        ROOT / "report" / "analysis.json",
        DATA / "judge_panel.json",
        DATA / "judge_calibration.json",
        DATA / "judge_calibration__apertus-v1.5-70b.json",
        *[
            DATA / f"judge_calibration__{j.replace('/', '_')}.json"
            for j in (load_json(DATA / "judge_panel.json", False) or {}).get("judges", [])
            if (DATA / f"judge_calibration__{j.replace('/', '_')}.json").exists()
        ],
        DATA / "judge_agreement_qwen_vs_apertus70b.json",
        DATA / "contamination.summary.json",
        DATA / "sources" / "fedlex_manifest.v2.json",
    ):
        out[f"results/{p.name}"] = p
    for sub in ("responses", "judgements", "human_labels"):
        for p in sorted((DATA / sub).glob("*.jsonl")) + sorted(
            (DATA / sub).glob("*.json")
        ):
            out[f"{sub}/{p.name}"] = p
    return out


def token(env_file):
    if os.environ.get("HF_TOKEN"):
        return os.environ["HF_TOKEN"]
    if env_file:
        for line in Path(env_file).read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*HF_TOKEN\s*=\s*(.*)$", line)
            if m:
                return m.group(1).strip().strip("'\"")
    sys.exit("HF_TOKEN not set")


def upload(args):
    files = files_to_upload()
    missing = [k for k, p in files.items() if not p.exists()]
    sizes = collections.OrderedDict(
        (k, p.stat().st_size) for k, p in files.items() if p.exists()
    )
    for k, s in sizes.items():
        print(f"  {k:<55} {s / 1e6:8.2f} MB")
    if missing:
        print("missing:", missing)
    if "README.md" in missing:
        sys.exit("build the card first: hf_release.py card")
    if not args.go:
        print(
            f"dry run: {len(sizes)} files for https://huggingface.co/datasets/{args.repo} (private={not args.public}); add --go to upload"
        )
        return
    from huggingface_hub import CommitOperationAdd, HfApi

    api = HfApi(token=token(args.env))
    api.create_repo(
        args.repo, repo_type="dataset", private=not args.public, exist_ok=True
    )
    ops = [
        CommitOperationAdd(path_in_repo=k, path_or_fileobj=str(p))
        for k, p in files.items()
        if p.exists()
    ]
    version = load_json(DATA / "FREEZE.json")["version"]
    info = api.create_commit(
        args.repo,
        ops,
        repo_type="dataset",
        commit_message=f"Inkraft dataset v{version}",
    )
    api.create_tag(
        args.repo,
        tag=f"v{version}",
        repo_type="dataset",
        revision=info.oid,
        exist_ok=True,
    )
    print(f"uploaded {len(ops)} files to {args.repo} @ {info.oid}, tag v{version}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("card")
    c.add_argument("--repo", required=True)
    c.set_defaults(fn=card)
    u = sub.add_parser("upload")
    u.add_argument("--repo", required=True)
    u.add_argument(
        "--go", action="store_true", help="Niklas gave the go for the upload"
    )
    u.add_argument("--public", action="store_true")
    u.add_argument("--env", help=".env file with HF_TOKEN (read with a parser)")
    u.set_defaults(fn=upload)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    args.fn(args)


if __name__ == "__main__":
    main()
