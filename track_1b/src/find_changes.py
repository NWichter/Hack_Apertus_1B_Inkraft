"""Compare the current and previous fedlex consolidation of every act, paragraph by paragraph.

Three outputs in --out:
  sentence_stability.json  per DE core: is the evidence sentence still in the previous version?
                           (the temporal bucket in merged.v1 is set per article, this checks the sentence)
  diffpool.json            every changed, new or removed paragraph with its coverage by existing cores
  amount_candidates.json   uncovered paragraphs where an amount, rate or period with a unit changed
                           (input for temporal candidate generation)

Usage:
  python src/find_changes.py --fedlex <fetch_fedlex.py --out dir> --items data/merged.v1.jsonl --out <dir>
"""

import argparse
import collections
import json
import re
import sys
from pathlib import Path

LANGS = ("de", "fr", "it")
NUM = re.compile(r"\d[\d'’ ]*(?:[.,]\d+)?")
UNIT = re.compile(
    r"(\d[\d'’    ]*(?:[.,]\d+)?)[\s  ]*"
    r"(Franken|Fr\.|CHF|Prozent|%|Promille|Tage|Tagen|Monate|Monaten|Jahre|Jahren|"
    r"Altersjahr|Lebensjahr|Wochen|Stunden|Rappen)"
)


def norm(s):
    return re.sub(r"\s+", " ", s or "").strip()


def nums(text):
    return sorted(
        {
            re.sub(r"['’ ]", "", x).replace(",", ".").rstrip(".")
            for x in NUM.findall(text or "")
        }
    )


def unit_values(text):
    return sorted(
        {(re.sub(r"['’    ]", "", a), u[:4]) for a, u in UNIT.findall(text or "")}
    )


class Fedlex:
    def __init__(self, root):
        self.root = Path(root)
        self.manifest = json.loads(
            (self.root / "manifest.json").read_text(encoding="utf-8")
        )
        self._cache = {}

    def acts(self):
        return [a["abbr"] for a in self.manifest["acts"]]

    def paragraphs(self, act, role, lang="de"):
        key = (act, role, lang)
        if key not in self._cache:
            entry = next(x for x in self.manifest["acts"] if x["abbr"] == act)
            versions = [v for v in entry["versions"] if v["role"] == role]
            if not versions or lang not in versions[0]["files"]:
                self._cache[key] = None
            else:
                path = self.root / versions[0]["files"][lang]["path"]
                doc = json.loads(path.read_text(encoding="utf-8"))
                self._cache[key] = {
                    (art["article_id"], p["paragraph"]): p["text"]
                    for art in doc["articles"]
                    for p in art["paragraphs"]
                }
        return self._cache[key]


def sentence_stability(fx, de_rows):
    out, counts = [], collections.Counter()
    for r in de_rows:
        act, bucket = r["source"]["act"], r["temporal"]["bucket"]
        prev = fx.paragraphs(act, "previous")
        if prev is None:
            status = "no_previous_version"
        else:
            article_text = norm(
                " ".join(
                    t for (a, _), t in prev.items() if a == r["source"]["article_id"]
                )
            )
            ev = norm(r["source"]["evidence"])
            status = (
                "evidence_in_previous"
                if ev and ev in article_text
                else "evidence_changed"
            )
        counts[(bucket, status)] += 1
        out.append(
            {
                "core_id": r["core_id"],
                "act": act,
                "bucket": bucket,
                "status": status,
                "has_outdated_answers": bool(r.get("outdated_answers")),
            }
        )
    return out, counts


def diff_pool(fx, de_rows):
    covered = collections.Counter(
        (r["source"]["act"], r["source"]["article_id"], r["source"]["paragraph"])
        for r in de_rows
    )
    pool = []
    for act in fx.acts():
        cur, prev = fx.paragraphs(act, "current"), fx.paragraphs(act, "previous")
        if not cur or not prev:
            continue
        for k, text in cur.items():
            old = prev.get(k)
            if old is None:
                kind = "new_paragraph"
            elif norm(old) == norm(text):
                continue
            else:
                kind = "value_change" if nums(old) != nums(text) else "text_change"
            pool.append(
                {
                    "act": act,
                    "article_id": k[0],
                    "paragraph": k[1],
                    "kind": kind,
                    "covered": covered.get((act, *k), 0),
                    "old_nums": nums(old),
                    "new_nums": nums(text),
                    "len": len(text),
                }
            )
        for k, text in prev.items():
            if k not in cur:
                pool.append(
                    {
                        "act": act,
                        "article_id": k[0],
                        "paragraph": k[1],
                        "kind": "removed_paragraph",
                        "covered": 0,
                        "len": len(text),
                    }
                )
    return pool


def amount_candidates(fx, pool, max_len=1500):
    cands = []
    for p in pool:
        if p["kind"] != "value_change" or p["covered"]:
            continue
        act, k = p["act"], (p["article_id"], p["paragraph"])
        texts = {
            (role, lang): (fx.paragraphs(act, role, lang) or {}).get(k)
            for role in ("current", "previous")
            for lang in LANGS
        }
        if any(v is None for v in texts.values()):
            continue
        cur, prev = texts[("current", "de")], texts[("previous", "de")]
        uc, up = unit_values(cur), unit_values(prev)
        old = [x for x in up if x not in uc]
        if not uc or uc == up or not old:
            continue
        if len(cur) > max_len or "aufgehoben" in cur[:40]:
            continue
        cands.append(
            {
                "act": act,
                "article_id": k[0],
                "paragraph": k[1],
                "new": [x for x in uc if x not in up],
                "old": old,
                "current": cur,
                "previous": prev,
            }
        )
    return cands


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--fedlex",
        required=True,
        help="output folder of fetch_fedlex.py (with manifest.json)",
    )
    ap.add_argument("--items", default="data/merged.v1.jsonl")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    fx = Fedlex(args.fedlex)
    rows = [json.loads(line) for line in open(args.items, encoding="utf-8")]
    de_rows = [r for r in rows if r["lang"] == "de-CH"]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    stab, counts = sentence_stability(fx, de_rows)
    changed = [
        s
        for s in stab
        if s["bucket"] != "stable_pre2024" and s["status"] == "evidence_changed"
    ]
    print("sentence-level stability (bucket, status):")
    for k, v in sorted(counts.items()):
        print(f"  {k[0]:<20} {k[1]:<22} {v}")
    print(
        f"cores whose evidence sentence changed: {len(changed)}"
        f" (with outdated answers: {sum(s['has_outdated_answers'] for s in changed)})"
    )

    pool = diff_pool(fx, de_rows)
    kinds = collections.Counter(p["kind"] for p in pool)
    uncovered = collections.Counter(p["kind"] for p in pool if not p["covered"])
    print("diff pool (kind: paragraphs / uncovered):")
    for k in sorted(kinds):
        print(f"  {k:<18} {kinds[k]:>4} / {uncovered[k]:>4}")

    cands = amount_candidates(fx, pool)
    print(f"uncovered amount/rate/period changes: {len(cands)}")
    for c in cands:
        print(
            f"  {c['act']} {c['article_id']} {c['paragraph']}  old {c['old']}  new {c['new']}"
        )

    for name, data in (
        ("sentence_stability.json", stab),
        ("diffpool.json", pool),
        ("amount_candidates.json", cands),
    ):
        (out / name).write_text(
            json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
