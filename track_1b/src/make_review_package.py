"""Build the review package for tools/review: existing cores plus candidates, each with a review_hint
(block, rank, priority, estimated minutes, reasons, automatic checks, proposal, hidden agent assessment).

python src/make_review_package.py --merged data/merged.v1.jsonl --issues data/candidates/review-v3/issues.merged.json
    --buckets data/temporal/sentence_buckets.json --proposals data/candidates/review-v3/proposals.json
    --candidates data/candidates/nemotron-v2/candidates.jsonl data/candidates/nemotron-pilot/candidates.ultra.jsonl
    --checks data/candidates/checks/checks.json
    --assessments data/candidates/nemotron-v2/assessment.json data/candidates/nemotron-pilot/assessment.ultra.json
    --out data/review/review_package.v1.jsonl
"""

import argparse
import collections
import json
import sys
from pathlib import Path

PACKAGE = "review-package-v1"
BLOCKS = [
    (
        "A1",
        "Bestand: Vorschläge (Ja/Nein-Umbau, Klumpen, Duplikate, Varianten)",
        "hoch",
        2.5,
    ),
    ("A2", "Bestand: Temporal, Belegsatz geändert", "hoch", 3.0),
    ("A3", "Bestand: inhaltliche Warnungen", "hoch", 2.5),
    ("B1", "Kandidaten Nemotron: STALE-Paar (Altantwort belegt)", "hoch", 3.0),
    ("B3", "Pilot-Kandidaten (hatten Apertus-Kontakt)", "mittel", 3.0),
    ("C", "Bestand: Rechnen und falsche Prämisse", "mittel", 2.0),
    ("D", "Bestand: Rest ohne Warnungen", "niedrig", 1.0),
    ("B2", "Kandidaten Nemotron: ohne STALE-Paar (nur bei Zeit)", "niedrig", 3.0),
    ("X", "Kandidaten vorab aussortiert (Fehler oder Duplikat)", "niedrig", 0.5),
]
NOT_CONTENT = {"source.future_change", "evidence.apostrophe"}
CODE_DE = {
    "question.answer_overlap": "Antwortwörter stehen schon in der Frage",
    "question.contains_answer_number": "Zahl der Antwort steht in der Frage",
    "answer.threshold_word": "Schwellenwort (mehr als, höchstens …) der Evidenz fehlt in Frage/Antwort",
    "source.discretion": "Absatz nennt Bundesrat/Reglement/Kanton: Ermessen?",
    "answer.no_variations": "keine Antwortvarianten",
    "answer.inflected": "Antwort nur flektiert belegt",
    "answer.number_literal_only": "Zahl nur als Ziffer/Wort belegt",
    "dup.near_question": "fast gleiche Frage wie ein anderer Kern",
    "dup.same_fact": "gleicher Fakt wie ein anderer Kern",
    "style.article_in_question": "Frage nennt eine Artikelnummer",
    "style.long_answer": "Antwort lang",
    "temporal.evidence_unchanged": "Altantwort angegeben, Belegsatz aber unverändert",
    "source.future_change": "spätere Fassung schon publiziert",
}


def read(path):
    return [
        json.loads(x)
        for x in Path(path).read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


def core_of(rid):
    return rid.rsplit("-", 1)[0] if rid[-3:] in ("-de", "-fr", "-it") else rid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--merged", required=True)
    ap.add_argument("--issues", required=True)
    ap.add_argument("--buckets", required=True)
    ap.add_argument("--proposals", required=True)
    ap.add_argument("--proposal-checks")
    ap.add_argument("--candidates", nargs="*", default=[])
    ap.add_argument("--checks")
    ap.add_argument("--assessments", nargs="*", default=[])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    merged = read(args.merged)
    cands = [r for p in args.candidates if Path(p).exists() for r in read(p)]
    issues = json.loads(Path(args.issues).read_text(encoding="utf-8"))
    buckets = json.loads(Path(args.buckets).read_text(encoding="utf-8"))
    proposals = json.loads(Path(args.proposals).read_text(encoding="utf-8"))
    checks = (
        json.loads(Path(args.checks).read_text(encoding="utf-8")) if args.checks else {}
    )
    pchecks = (
        json.loads(Path(args.proposal_checks).read_text(encoding="utf-8"))
        if args.proposal_checks
        else {}
    )
    assess = {}
    for p in args.assessments:
        if Path(p).exists():
            d = json.loads(Path(p).read_text(encoding="utf-8"))
            items = d.get("items", d) if isinstance(d, dict) else d
            if isinstance(items, dict):
                items = [{"core_id": k, **v} for k, v in items.items()]
            for a in items:
                assess[a["core_id"]] = a

    own = collections.defaultdict(list)
    for i in issues:
        own[core_of(i["id"])].append(i)

    def first_de(rows):
        by = collections.defaultdict(dict)
        for r in rows:
            by[r["core_id"]][r["lang"][:2]] = r
        return by

    existing, candidates = first_de(merged), first_de(cands)
    hints = {}
    for cid, langs in existing.items():
        de = langs.get("de") or next(iter(langs.values()))
        content = sorted({i["code"] for i in own[cid] if i["code"] not in NOT_CONTENT})
        b = buckets.get(cid, {})
        reasons = [f"{CODE_DE.get(c, c)} ({c})" for c in content]
        if b.get("sentence_bucket") and b["sentence_bucket"] != b.get("article_bucket"):
            reasons.append(
                f"Bucket je Belegsatz: {b['sentence_bucket']} statt {b.get('article_bucket')} (Artikel)"
            )
        if b.get("sentence_bucket", "stable_pre2024") != "stable_pre2024":
            reasons.append(
                f"Belegsatz fehlt in den Fassungen {', '.join(b.get('evidence_missing_in', []))}: bestätigen, dass sich das Recht geändert hat (nicht nur der Wortlaut)"
            )
        if any(i["code"] == "source.future_change" for i in own[cid]):
            reasons.append(
                "Hinweis: spätere Fassung schon publiziert (Antwort gilt am Stichtag 01.10.2026)"
            )
        prop = proposals.get(cid)
        if prop and prop.get("action") == "keep":
            reasons.append(f"Ja/Nein-Prüfung durch Nemotron: {prop['summary']}")
            prop = None
        qt = de["question_type"]
        if prop:
            block = "A1"
        elif b.get("sentence_bucket", "stable_pre2024") != "stable_pre2024":
            block = "A2"
        elif content:
            block = "A3"
        elif qt in ("calc", "false_premise"):
            block = "C"
        else:
            block = "D"
        if prop and prop.get("action") == "patch" and cid in pchecks:
            pc = pchecks[cid]
            reasons.append(
                "Vorschlag geprüft: "
                + ("keine Validator-Fehler" if not pc["errors"] else "FEHLER " + ", ".join(pc["errors"]))
                + (f"; Warnungen {', '.join(pc['warnings'])}" if pc["warnings"] else "")
            )
        if prop and prop.get("provenance"):
            pv = prop["provenance"]
            reasons.append(f"Vorschlag von {pv['generator']} ({pv['generator_model']}), {pv['generated_at']}")
        hints[cid] = {
            "block": block,
            "reasons": reasons,
            "auto_checks": {
                "validator_ohne_fehler": not any(
                    i["level"] == "ERROR" for i in own[cid]
                ),
                "belegsatz_geaendert": b.get("sentence_bucket", "stable_pre2024")
                != "stable_pre2024",
                "altantwort_vorhanden": bool(de.get("outdated_answers")),
            },
            "proposal": {k: v for k, v in prop.items() if k != "kind"}
            | {"kind": prop.get("kind")}
            if prop
            else None,
            "sort": (de["source"]["act"], de["source"]["article_id"], cid),
        }

    for cid, langs in candidates.items():
        de = langs.get("de") or next(iter(langs.values()))
        c = checks.get(cid, {})
        tier = c.get("tier", "B_no_stale_pair")
        pilot = cid.startswith("nmu-")
        a = assess.get(cid)
        verdict = (a or {}).get("verdict") or (a or {}).get("decision")
        if tier in ("D_errors", "C_duplicate") or verdict == "reject":
            block = "X"
        elif pilot:
            block = "B3"
        elif tier in ("A_stale_pair", "B_stale_pair_warn"):
            block = "B1"
        else:
            block = "B2"
        reasons = [f"Prüfstufe {tier}"]
        reasons += [
            f"{CODE_DE.get(w, w)} ({w})"
            for w in c.get("warnings", [])
            if w not in NOT_CONTENT
        ]
        reasons += [f"Fehler: {e}" for e in c.get("errors", [])]
        if c.get("duplicate_of"):
            reasons.append(f"Duplikat-Verdacht: {', '.join(c['duplicate_of'])}")
        t = de.get("temporal") or {}
        for v in t.get("outdated_versions") or []:
            reasons.append(
                f"Altantwort „{v['outdated_answer']}“ aus Fassung {v['version_date']}{'' if v.get('evidence_found', True) else ' (Evidenz NICHT gefunden)'}"
            )
        if pilot:
            reasons.append(
                "Pilot-Kandidat: wurde am 04.10. einmal von Apertus beantwortet; nur nach Leitfaden entscheiden, nie nach Antworten"
            )
        reasons.append(
            f"Generator nemotron ({de.get('generator_model')}), Prompt {str(de.get('prompt_version')).split(' ')[0]}, {de.get('generated_at')}"
        )
        hints[cid] = {
            "block": block,
            "reasons": reasons,
            "auto_checks": {
                "validator_ohne_fehler": not c.get("errors"),
                "zitat_wörtlich_im_gesetz": c.get("quote_ok", True),
                "altantwort_in_früherer_fassung": c.get("outdated_in_earlier_version"),
                "kein_duplikat": not c.get("duplicate_of"),
                "provenienz_vollständig": c.get("provenance_ok", True),
            },
            "agent_assessment": {
                "verdict": verdict,
                "note": a.get("note") or a.get("reason") or "",
            }
            if a
            else None,
            "proposal": None,
            "sort": (tier, de["source"]["act"], de["source"]["article_id"], cid),
        }

    order = {b[0]: i for i, b in enumerate(BLOCKS)}
    meta = {b[0]: b for b in BLOCKS}
    ranked = sorted(hints, key=lambda c: (order[hints[c]["block"]], hints[c]["sort"]))
    rows_out = []
    all_rows = {
        **{c: v for c, v in existing.items()},
        **{c: v for c, v in candidates.items()},
    }
    for rank, cid in enumerate(ranked, 1):
        h = hints[cid]
        _, label, prio, minutes = meta[h["block"]]
        hint = {
            "package": PACKAGE,
            "rank": rank,
            "block": h["block"],
            "block_label": label,
            "priority": prio,
            "est_minutes": minutes,
            "reasons": h["reasons"],
            "auto_checks": {k: v for k, v in h["auto_checks"].items() if v is not None},
        }
        if h.get("proposal"):
            hint["proposal"] = h["proposal"]
        if h.get("agent_assessment"):
            hint["agent_assessment"] = h["agent_assessment"]
        for lang in ("de", "fr", "it"):
            r = all_rows[cid].get(lang)
            if r:
                rows_out.append({**r, "review_hint": hint})
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows_out),
        encoding="utf-8",
        newline="\n",
    )

    per = collections.Counter(hints[c]["block"] for c in hints)
    lines = [
        "# Review package v1",
        "",
        f"{len(hints)} cores ({len(existing)} existing, {len(candidates)} candidates), {len(rows_out)} rows. Order = rank in the review tool.",
        "",
        "| Block | Label | Priority | Cores | Min/core | Hours |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    total = 0.0
    for code, label, prio, minutes in BLOCKS:
        h = per[code] * minutes / 60
        total += h
        lines.append(
            f"| {code} | {label} | {prio} | {per[code]} | {minutes:g} | {h:.1f} |"
        )
    lines += [
        "",
        f"Total estimate: {total:.1f} h (review only; without hand-written cores and the 20 % judge sample).",
    ]
    props = collections.Counter(p.get("kind") for p in proposals.values())
    lines += [
        "",
        "Proposals: " + ", ".join(f"{k} {v}" for k, v in sorted(props.items())),
    ]
    out.with_suffix(".md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
    )
    print("\n".join(lines))


if __name__ == "__main__":
    main()
