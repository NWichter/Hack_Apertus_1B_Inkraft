"""inkraft command line: build | generate | judge | calibrate | score | replay | expect |
sample-human | label | agreement | contam."""

import argparse
import json
import os
import random
import sys
from pathlib import Path

from . import contam, dataset, generate, human, judge, score
from .client import Endpoint
from .prompts import CONDITIONS

DEFAULT_DATA = Path(__file__).resolve().parents[2] / "data"


def _items(args):
    items = dataset.load(args.data)
    if args.lang:
        items = [it for it in items if it["lang"].startswith(args.lang)]
    if args.sample:
        cores = sorted({it["core_id"] for it in items})
        keep = set(random.Random(args.seed).sample(cores, min(args.sample, len(cores))))
        items = [it for it in items if it["core_id"] in keep]
    if args.limit:
        items = items[: args.limit]
    return items


def cmd_build(args):
    n = dataset.build(args.src, args.data)
    print(f"wrote {n} items to {args.data}/test.jsonl and metadata.jsonl")


def cmd_generate(args):
    ep = Endpoint.from_env("LLM", args.model)
    items = _items(args)
    for cond in args.condition:
        out = generate.response_path(args.data, ep.model, cond)
        n, err = generate.run(
            ep, items, cond, out, workers=args.workers, max_tokens=args.max_tokens
        )
        print(f"{ep.model} {cond}: {n} new responses, {err} errors -> {out}")


def cmd_judge(args):
    ep = Endpoint.from_env("JUDGE", args.judge_model)
    items = _items(args)
    for p in sorted((Path(args.data) / "responses").glob("*.jsonl")):
        model, cond = p.stem.split("__", 1)
        if args.examinee and model not in args.examinee:
            continue
        if args.condition and cond not in args.condition:
            continue
        out = judge.judge_path(args.data, ep.model, model, cond)
        n = judge.run(ep, items, dataset.read_jsonl(p), out, workers=args.workers)
        print(f"judged {n} responses of {model} {cond} -> {out}")


def cmd_score(args):
    res = score.score_all(dataset.load(args.data), args.data, args.judge_model)
    text = json.dumps(res, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    for key, r in res.items():
        o = r["overall"]
        print(
            f"{key:40s} n={o['n']:4d}/{o['n_total']:4d}  C={o['correct']:.3f}  I={o['incorrect']:.3f}  "
            f"NA={o['not_attempted']:.3f}  CGA={o['cga']:.3f}  F={o['f']:.3f}  src={o['grade_source']}"
        )


def cmd_replay(args):
    """Recompute every number from the stored responses and judgements and compare to expected."""
    expected_path = Path(args.data) / "expected_results.json"
    if not expected_path.exists():
        sys.exit(f"missing {expected_path}")
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    got = score.score_all(
        dataset.load(args.data), args.data, expected.get("judge_model")
    )
    exp = expected["results"]
    diffs = _diff(exp, json.loads(json.dumps(got)))
    for key, r in got.items():
        o = r["overall"]
        print(
            f"{key:40s} C={o['correct']:.3f}  I={o['incorrect']:.3f}  NA={o['not_attempted']:.3f}  F={o['f']:.3f}"
        )
    if diffs:
        print(f"FAIL: {len(diffs)} values differ from expected_results.json")
        for d in diffs[:20]:
            print("  ", d)
        sys.exit(1)
    print(f"PASS: all {len(got)} result blocks match expected_results.json")


def cmd_expect(args):
    """Freeze the current scores as expected_results.json (run once, at the dataset freeze)."""
    res = score.score_all(dataset.load(args.data), args.data, args.judge_model)
    out = {"judge_model": args.judge_model, "note": args.note, "results": res}
    path = Path(args.data) / "expected_results.json"
    path.write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(f"wrote {path} ({len(res)} result blocks)")


def cmd_sample_human(args):
    rows = human.sample(dataset.load(args.data), args.data, args.judge_model)
    out = Path(args.data) / "human_labels" / "sample_20pct.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    dataset.write_jsonl(out, rows)
    print(f"wrote {len(rows)} rows to {out}")


def cmd_label(args):
    base = Path(args.data) / "human_labels"
    rows = dataset.read_jsonl(base / "sample_20pct.jsonl")
    human.label(
        dataset.load(args.data),
        rows,
        base / f"labels_{args.annotator}.jsonl",
        args.annotator,
    )


def cmd_agreement(args):
    labels = dataset.read_jsonl(
        Path(args.data) / "human_labels" / f"labels_{args.annotator}.jsonl"
    )
    judgements = []
    for p in sorted((Path(args.data) / "judgements").glob("*.jsonl")):
        judgements += [
            j for j in dataset.read_jsonl(p) if j.get("judge_model") == args.judge_model
        ]
    res = human.agreement(labels, judgements)
    print(json.dumps(res, indent=1))
    if args.out:
        Path(args.out).write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")


def cmd_calibrate(args):
    ep = Endpoint.from_env("JUDGE", args.judge_model)
    rows = dataset.read_jsonl(args.calibration)
    res = judge.calibrate(ep, rows, workers=args.workers)
    out = Path(
        args.out
        or Path(args.data) / f"judge_calibration__{ep.model.replace('/', '_')}.json"
    )
    out.write_text(
        json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(
        f"{ep.model}: grade accuracy {res['grade_accuracy']}, with subtype {res['subtype_accuracy']} (n={res['n']}) -> {out}"
    )
    if res["grade_accuracy"] is None or res["grade_accuracy"] < 0.95:
        print(
            "below the 0.95 gate: adjust the judge prompt (bump JUDGE_PROMPT_VERSION) before grading Apertus"
        )


def cmd_contam(args):
    corpora = contam.load_corpora(args.corpus)
    if not corpora:
        sys.exit(f"no *_legislation_switzerland_lexfind.jsonl.xz in {args.corpus}")
    rows = contam.check(dataset.load(args.data), corpora)
    out = Path(args.out or Path(args.data) / "contamination.jsonl")
    dataset.write_jsonl(out, rows)
    summ = contam.summary(rows)
    out.with_suffix(".summary.json").write_text(
        json.dumps(summ, indent=1) + "\n", encoding="utf-8"
    )
    print(json.dumps(summ, indent=1))


def _diff(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(
                    f"{path}/{k}: only in {'expected' if k in a else 'recomputed'}"
                )
            else:
                out += _diff(a[k], b[k], f"{path}/{k}")
        return out
    return [] if a == b else [f"{path}: expected {a!r}, got {b!r}"]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="inkraft")
    ap.add_argument("--data", default=os.environ.get("INKRAFT_DATA", str(DEFAULT_DATA)))
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser(
        "build", help="split built items into test.jsonl + metadata.jsonl"
    )
    b.add_argument("src")
    b.set_defaults(fn=cmd_build)

    for name, fn in (("generate", cmd_generate), ("judge", cmd_judge)):
        p = sub.add_parser(name)
        p.add_argument(
            "--condition",
            nargs="+",
            choices=list(CONDITIONS),
            default=["closed_dated"] if name == "generate" else None,
        )
        p.add_argument("--lang", choices=["de", "fr", "it"])
        p.add_argument("--limit", type=int)
        p.add_argument(
            "--sample", type=int, help="random subset of N cores (all languages)"
        )
        p.add_argument("--seed", type=int, default=20261001)
        p.add_argument("--workers", type=int, default=3)
        if name == "generate":
            p.add_argument("--model", help="overrides LLM_NAME")
            p.add_argument("--max-tokens", type=int)
        else:
            p.add_argument("--judge-model", help="overrides JUDGE_NAME")
            p.add_argument("--examinee", nargs="+")
        p.set_defaults(fn=fn)

    s = sub.add_parser("score")
    s.add_argument("--judge-model", default=os.environ.get("JUDGE_NAME"))
    s.add_argument("--out")
    s.set_defaults(fn=cmd_score)

    r = sub.add_parser(
        "replay", help="recompute all results and compare with expected_results.json"
    )
    r.set_defaults(fn=cmd_replay)

    e = sub.add_parser(
        "expect", help="write expected_results.json from the current scores"
    )
    e.add_argument("--judge-model", default=os.environ.get("JUDGE_NAME"))
    e.add_argument("--note", default="")
    e.set_defaults(fn=cmd_expect)

    h = sub.add_parser(
        "sample-human",
        help="stratified 20 %% sample of judged responses for the human check",
    )
    h.add_argument("--judge-model", default=os.environ.get("JUDGE_NAME"))
    h.set_defaults(fn=cmd_sample_human)

    lb = sub.add_parser(
        "label", help="blind human labelling of the sample (judge grade hidden)"
    )
    lb.add_argument("--annotator", required=True)
    lb.set_defaults(fn=cmd_label)

    ag = sub.add_parser(
        "agreement", help="Cohen's kappa between human labels and the judge"
    )
    ag.add_argument("--annotator", required=True)
    ag.add_argument("--judge-model", default=os.environ.get("JUDGE_NAME"))
    ag.add_argument("--out")
    ag.set_defaults(fn=cmd_agreement)

    c = sub.add_parser(
        "calibrate",
        help="judge accuracy on the constructed calibration answers (gate: 0.95)",
    )
    c.add_argument("--judge-model", default=os.environ.get("JUDGE_NAME"))
    c.add_argument(
        "--calibration",
        default=str(
            Path(__file__).resolve().parents[2]
            / "tests"
            / "fixtures"
            / "judge_calibration.jsonl"
        ),
    )
    c.add_argument("--workers", type=int, default=3)
    c.add_argument("--out")
    c.set_defaults(fn=cmd_calibrate)

    ct = sub.add_parser(
        "contam", help="exposure/leak check against MultiLegalPile switzerland_lexfind"
    )
    ct.add_argument(
        "--corpus",
        required=True,
        help="folder with <lang>_legislation_switzerland_lexfind.jsonl.xz",
    )
    ct.add_argument("--out")
    ct.set_defaults(fn=cmd_contam)

    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
