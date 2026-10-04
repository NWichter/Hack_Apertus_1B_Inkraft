"""Compare the current fedlex consolidation of every act with its earlier versions, paragraph by paragraph.

Outputs in --out:
  sentence_stability.json  per DE core: is the evidence sentence still in the previous version?
  sentence_buckets.json    per core: temporal bucket from the evidence sentence over all stored earlier
                           versions (previous + intermediate); the bucket in merged.v1 is set per article
  diffpool.json            every changed, new or removed paragraph with its coverage by existing cores
  amount_candidates.json   uncovered paragraphs where an amount, rate or period with a unit changed
  temporal_targets.json    ranked uncovered paragraphs for temporal candidate generation (--targets N)

Usage:
  python src/find_changes.py --fedlex <fetch_fedlex.py --out dir> --items data/merged.v1.jsonl --out <dir>
      [--targets 130 --exclude data/candidates/nemotron-pilot/targets.json]
"""

import argparse
import collections
import difflib
import json
import re
import sys
from pathlib import Path

LANGS = ("de", "fr", "it")
NUM = re.compile(r"\d[\d'’ ]*(?:[.,]\d+)?")
UNIT = re.compile(
    r"(\d[\d'’    ]*(?:[.,]\d+)?)[\s  ]*"
    r"(Franken|Fr\.|CHF|Prozent|%|Promille|Tage|Tagen|Monate|Monaten|Jahre|Jahren|"
    r"Altersjahr|Lebensjahr|Wochen|Stunden|Rappen)"
)
REF = re.compile(
    r"(Art(?:ikel|\.)?|Abs(?:atz|\.)?|Bst\.|Buchstabe|Ziff(?:er|\.)?|SR|AS|BBl|Anhang|Kapitel)\s*\d+[a-z]*"
    r"(?:\s*(?:bis|ter|quater|quinquies|sexies|septies|octies))?"
)
DATE = re.compile(
    r"\d{1,2}\.\s*(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*\d{4}"
)
STOP = re.compile(
    r"(?i)(oder|und|der|die|das|des|dem|den|eine?[nmrs]?|innen|sowie|beziehungsweise)"
)
OR_RANGE = (319, 362)
ADMIN = re.compile(
    r"Datenaustausch|Datenformat|Statistik|Revisions|Aufsicht|Ausgleichsfonds|Bundesbeitrag|Informationssystem|"
    r"Register|Kommission|Zahlungsverkehr|codier|Gebühr|Verwaltungskosten|Durchführungsstelle|Rechnungsführung"
)
USER = re.compile(
    r"Rente|Beitr[aä]g|Anspruch|Frist|Franken|Prozent|Tage|Monat|Jahre|Referenzalter|Taggeld|Prämie|"
    r"Kostenbeteiligung|Franchise|Entschädigung|Vorbezug|Aufschub|Urlaub|versicherte Person|Arbeitnehmer"
)
DOMAIN = {
    "AHVG": "ahv",
    "AHVV": "ahv",
    "IVG": "iv_el",
    "IVV": "iv_el",
    "ELG": "iv_el",
    "ELV": "iv_el",
    "KVV": "kvg_billing",
    "UVG": "uvg_atsg",
    "ATSG": "uvg_atsg",
    "EOG": "eo_alv",
    "AVIG": "eo_alv",
    "AVIV": "eo_alv",
    "BVG": "bvg_3a",
    "BVV2": "bvg_3a",
    "BVV3": "bvg_3a",
    "OR": "or_illness",
}


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
        {(re.sub(r"['’    ]", "", a), u[:4]) for a, u in UNIT.findall(text or "")}
    )


RENAMES = [
    (r"(?:des )?ordentlichen? Rentenalters?(?: der AHV)?|ordentliches Rentenalter(?: der AHV)?|Rentenalter(?:s)?", "Referenzalter"),
    (r"Referenzalters", "Referenzalter"),
    (r"Vaterschaftsurlaub(?:s)?|Urlaub des anderen Elternteils", "Urlaub des andern Elternteils"),
    (r"Vaterschaftsentschädigung", "Entschädigung für den andern Elternteil"),
    (r"Bundesamt(?: für Sozialversicherungen)?", "BSV"),
    (r"Bundesamt(?: für Gesundheit)?", "BAG"),
    (r"(?:private |öffentliche )?Kasse", "Arbeitslosenkasse"),
    (r"des Gesetzes|dieses Gesetzes", "KVG"),
    (r"selbständig", "selbstständig"),
]


def strip_refs(text):
    """Drop references and dates and unify terms renamed without a change in the rule (AHV 21, EO)."""
    t = DATE.sub(" ", REF.sub(" ", text or ""))
    for pat, rep in RENAMES:
        t = re.sub(pat, rep, t)
    return t


def article_number(article_id):
    return int(re.sub(r"\D.*", "", article_id.split("art_")[-1]) or 0)


def domain_of(act, article_id):
    if act == "KVG":
        return (
            "kvg_billing" if 24 <= article_number(article_id) <= 59 else "kvg_insured"
        )
    return DOMAIN.get(act, "kvg_insured")


def bucket_of(date):
    if not date:
        return "stable_pre2024"
    return "changed_2024_2025" if date < "2026-01-01" else "changed_2026"


class Fedlex:
    def __init__(self, root):
        self.root = Path(root)
        self.manifest = json.loads(
            (self.root / "manifest.json").read_text(encoding="utf-8")
        )
        self._cache = {}

    def acts(self):
        return [a["abbr"] for a in self.manifest["acts"]]

    def entry(self, act):
        return next(x for x in self.manifest["acts"] if x["abbr"] == act)

    def current_date(self, act):
        return next(
            v["version_date"]
            for v in self.entry(act)["versions"]
            if v["role"] == "current"
        )

    def earlier_dates(self, act):
        """Dates of the stored versions before the current one, newest first."""
        cur = self.current_date(act)
        return sorted(
            (
                v["version_date"]
                for v in self.entry(act)["versions"]
                if v["role"] in ("previous", "intermediate") and v["version_date"] < cur
            ),
            reverse=True,
        )

    def paragraphs(self, act, role, lang="de", date=None):
        key = (act, role, lang, date)
        if key not in self._cache:
            versions = [
                v
                for v in self.entry(act)["versions"]
                if (v["version_date"] == date if date else v["role"] == role)
            ]
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

    def article_text(self, act, article_id, role="current", lang="de", date=None):
        paras = self.paragraphs(act, role, lang, date) or {}
        return norm(" ".join(t for (a, _), t in paras.items() if a == article_id))


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


def sentence_buckets(fx, de_rows):
    """Bucket per core from the evidence sentence: since when does it stand unchanged in the act?"""
    out = {}
    for r in de_rows:
        act, aid = r["source"]["act"], r["source"]["article_id"]
        ev = norm(r["source"]["evidence"])
        earlier = fx.earlier_dates(act)
        missing_in = [d for d in earlier if ev not in fx.article_text(act, aid, date=d)]
        since = None
        if missing_in:
            newer = [fx.current_date(act)] + [d for d in earlier if d > missing_in[0]]
            since = min(newer)
        out[r["core_id"]] = {
            "act": act,
            "article_bucket": r["temporal"]["bucket"],
            "sentence_bucket": bucket_of(since),
            "evidence_since": since,
            "evidence_missing_in": missing_in,
            "has_outdated_answers": bool(r.get("outdated_answers")),
            "question_type": r["question_type"],
        }
    return out


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


def match_previous(cur_text, prev_paras, article_id):
    """For a new paragraph: the most similar paragraph of the same article in the previous version."""
    best, best_r = None, 0.0
    for (a, p), t in prev_paras.items():
        if a != article_id:
            continue
        r = difflib.SequenceMatcher(None, norm(cur_text), norm(t)).ratio()
        if r > best_r:
            best, best_r = p, r
    return best, best_r


def score_target(cur, prev):
    """(change_kind, score) or None. Higher score = more likely a clean outdated/current answer pair."""
    if prev is None:
        return "rule_new", 2.0
    uc, up = unit_values(cur), unit_values(prev)
    if uc and uc != up and [x for x in up if x not in uc]:
        return "amount", 10.0
    nc, np_ = nums(strip_refs(cur)), nums(strip_refs(prev))
    if np_ and nc != np_:
        return "value", 6.0
    a, b = norm(strip_refs(prev)).split(), norm(strip_refs(cur)).split()
    sm = difflib.SequenceMatcher(None, a, b)
    changed = [
        w
        for tag, i1, i2, j1, j2 in sm.get_opcodes()
        if tag != "equal"
        for w in a[i1:i2] + b[j1:j2]
    ]
    content = [w for w in changed if len(w) > 3 and not STOP.fullmatch(w)]
    if len(content) < 2:
        return None
    score = 3.0 + min(len(content), 12) / 6
    if sm.ratio() < 0.3:
        score -= 1.5
    return "rule_changed", score


def rank_targets(
    fx, pool, exclude=(), n_targets=130, max_len=1500, per_article=2, per_act=22
):
    scored = []
    for p in pool:
        if p["covered"] or p["kind"] == "removed_paragraph":
            continue
        act, aid, par = p["act"], p["article_id"], p["paragraph"]
        if (act, aid, par) in exclude:
            continue
        if act == "OR" and not OR_RANGE[0] <= article_number(aid) <= OR_RANGE[1]:
            continue
        cur = (fx.paragraphs(act, "current") or {}).get((aid, par))
        if not cur or len(cur) > max_len or cur.lower().startswith("aufgehoben"):
            continue
        if any(
            (fx.paragraphs(act, "current", lang) or {}).get((aid, par)) is None
            for lang in ("fr", "it")
        ):
            continue
        prev_paras = fx.paragraphs(act, "previous") or {}
        prev_par = par
        prev = prev_paras.get((aid, par))
        if prev is None or difflib.SequenceMatcher(None, norm(cur), norm(prev)).ratio() < 0.45:
            prev_par, ratio = match_previous(cur, prev_paras, aid)
            prev = (
                prev_paras.get((aid, prev_par))
                if prev_par is not None and ratio >= 0.55
                else None
            )
        res = score_target(cur, prev)
        if not res:
            continue
        kind, score = res
        score -= max(0, len(cur) - 600) / 600
        score += 1.0 if USER.search(cur) else 0.0
        score -= 2.5 if ADMIN.search(cur) else 0.0
        scored.append(
            {
                "act": act,
                "article_id": aid,
                "paragraph": par,
                "previous_paragraph": prev_par if prev is not None else None,
                "domain": domain_of(act, aid),
                "change_kind": kind,
                "score": round(score, 2),
                "diff_kind": p["kind"],
            }
        )
    scored.sort(key=lambda t: (-t["score"], t["act"], t["article_id"], t["paragraph"]))
    picked, per_a, per_act_n = [], collections.Counter(), collections.Counter()
    for t in scored:
        if (
            per_a[(t["act"], t["article_id"])] >= per_article
            or per_act_n[t["act"]] >= per_act
        ):
            continue
        picked.append(t)
        per_a[(t["act"], t["article_id"])] += 1
        per_act_n[t["act"]] += 1
        if len(picked) >= n_targets:
            break
    return picked, scored


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--fedlex",
        required=True,
        help="output folder of fetch_fedlex.py (with manifest.json)",
    )
    ap.add_argument("--items", default="data/merged.v1.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--targets",
        type=int,
        default=0,
        help="write temporal_targets.json with N targets",
    )
    ap.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="targets.json files whose paragraphs are skipped",
    )
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
    print("sentence-level stability against the previous version (bucket, status):")
    for k, v in sorted(counts.items()):
        print(f"  {k[0]:<20} {k[1]:<22} {v}")
    print(
        f"cores whose evidence sentence changed: {len(changed)}"
        f" (with outdated answers: {sum(s['has_outdated_answers'] for s in changed)})"
    )

    sb = sentence_buckets(fx, de_rows)
    moves = collections.Counter(
        (v["article_bucket"], v["sentence_bucket"]) for v in sb.values()
    )
    print("article bucket -> sentence bucket (all earlier versions):")
    for k, v in sorted(moves.items()):
        print(f"  {k[0]:<20} -> {k[1]:<20} {v}")
    changed_sb = [c for c, v in sb.items() if v["sentence_bucket"] != "stable_pre2024"]
    print(
        f"cores with changed evidence sentence: {len(changed_sb)}"
        f" (with outdated answers: {sum(sb[c]['has_outdated_answers'] for c in changed_sb)})"
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

    outputs = [
        ("sentence_stability.json", stab),
        ("sentence_buckets.json", sb),
        ("diffpool.json", pool),
        ("amount_candidates.json", cands),
    ]
    if args.targets:
        exclude = set()
        for f in args.exclude:
            for t in json.loads(Path(f).read_text(encoding="utf-8")):
                exclude.add((t["act"], t["article_id"], t["paragraph"]))
        picked, scored = rank_targets(fx, pool, exclude, args.targets)
        print(f"temporal targets: {len(picked)} of {len(scored)} scored paragraphs")
        print("  by kind:", dict(collections.Counter(t["change_kind"] for t in picked)))
        print("  by act:", dict(collections.Counter(t["act"] for t in picked)))
        outputs.append(("temporal_targets.json", picked))

    for name, data in outputs:
        (out / name).write_text(
            json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
