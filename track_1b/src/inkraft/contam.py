"""Exposure and leak check against a training corpus of Apertus 1.5 (MultiLegalPile switzerland_lexfind).

Per item: in how many corpus documents does the verbatim evidence of the current version occur, and
(for temporal items) the evidence of the previous version? Per question: 13-gram overlap with the
corpus (item leak). The corpus is read locally and never redistributed (CC BY-NC-SA).
"""

import bisect
import json
import lzma
import re
from collections import Counter
from pathlib import Path

from .normalize import norm_space

NGRAM = 13
MIN_EVIDENCE_CHARS = 25
WORD_RE = re.compile(r"[^\W_]+")


def _norm(text):
    t = norm_space(text).casefold()
    for a, b in (
        ("’", "'"),
        ("‘", "'"),
        ("«", '"'),
        ("»", '"'),
        ("„", '"'),
        ("“", '"'),
        ("–", "-"),
    ):
        t = t.replace(a, b)
    return t


class Corpus:
    def __init__(self, texts, heads):
        self.heads = heads
        parts, self.starts, pos = [], [], 0
        for t in texts:
            b = _norm(t).encode("utf-8")
            self.starts.append(pos)
            parts.append(b)
            pos += len(b) + 1
        self.blob = b"\x00".join(parts)

    @classmethod
    def from_xz(cls, path):
        texts, heads = [], []
        with lzma.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                t = json.loads(line)["text"]
                texts.append(t)
                heads.append(norm_space(t[:90]))
        return cls(texts, heads)

    def docs_containing(self, needle, limit=50):
        n = _norm(needle).encode("utf-8")
        docs, i = [], self.blob.find(n)
        while i != -1 and len(docs) < limit:
            d = bisect.bisect_right(self.starts, i) - 1
            if not docs or docs[-1] != d:
                docs.append(d)
            nxt = self.starts[d + 1] if d + 1 < len(self.starts) else len(self.blob)
            i = self.blob.find(n, nxt)
        return docs

    def ngram_hits(self, grams):
        """Which of the given word n-grams occur anywhere in the corpus (streamed, one pass)."""
        want = set(grams)
        first = {g[0] for g in want}
        hits = set()
        for part in self.blob.split(b"\x00"):
            words = WORD_RE.findall(part.decode("utf-8"))
            for k in range(len(words) - NGRAM + 1):
                if words[k] in first:
                    g = tuple(words[k : k + NGRAM])
                    if g in want:
                        hits.add(g)
        return hits


def ngrams(text):
    w = WORD_RE.findall(_norm(text))
    return [tuple(w[k : k + NGRAM]) for k in range(len(w) - NGRAM + 1)]


def check(items, corpora):
    """corpora: {"de": Corpus, ...}. Returns one row per item."""
    rows = []
    by_lang = {}
    for it in items:
        by_lang.setdefault(it["lang"][:2], []).append(it)
    for l2, its in by_lang.items():
        corpus = corpora.get(l2)
        if corpus is None:
            continue
        q_grams = {
            it["id"]: ngrams(it["question"])
            + ngrams(f"{it['question']} {it['answer']}")
            for it in its
        }
        leaked = corpus.ngram_hits([g for gs in q_grams.values() for g in gs])
        for it in its:
            src = it.get("source") or {}
            tmp = it.get("temporal") or {}
            ev, prev = src.get("evidence") or "", tmp.get("previous_evidence") or ""
            cur_docs = (
                corpus.docs_containing(ev) if len(ev) >= MIN_EVIDENCE_CHARS else None
            )
            prev_docs = (
                corpus.docs_containing(prev)
                if len(prev) >= MIN_EVIDENCE_CHARS
                else None
            )
            rows.append(
                {
                    "id": it["id"],
                    "lang": it["lang"],
                    "question_type": it["question_type"],
                    "evidence_chars": len(ev),
                    "current_docs": None if cur_docs is None else len(cur_docs),
                    "previous_docs": None if prev_docs is None else len(prev_docs),
                    "bucket": _bucket(cur_docs, prev_docs, bool(prev)),
                    "example_docs": [
                        corpus.heads[d] for d in (cur_docs or prev_docs or [])[:3]
                    ],
                    "question_13gram_hits": sum(g in leaked for g in q_grams[it["id"]]),
                }
            )
    return sorted(rows, key=lambda r: r["id"])


def _bucket(cur, prev, has_prev):
    if cur is None:
        return "evidence_too_short"
    if not has_prev:
        return "current" if cur else "absent"
    if prev is None:
        return "current" if cur else "absent"
    if cur and prev:
        return "both"
    return "current" if cur else ("outdated" if prev else "absent")


PUBLIC_FIELDS = (
    "id",
    "lang",
    "question_type",
    "bucket",
    "evidence_chars",
    "current_docs",
    "previous_docs",
    "question_13gram_hits",
)


def public_rows(rows):
    """Per-row result without corpus text (the corpus is CC BY-NC-SA and is not redistributed)."""
    return [{k: r.get(k) for k in PUBLIC_FIELDS} for r in rows]


def summary(rows):
    out = {"n": len(rows), "bucket": dict(Counter(r["bucket"] for r in rows))}
    out["bucket_by_lang"] = {
        l: dict(Counter(r["bucket"] for r in rows if r["lang"] == l))
        for l in sorted({r["lang"] for r in rows})
    }
    out["temporal_bucket"] = dict(
        Counter(r["bucket"] for r in rows if r["question_type"] == "temporal")
    )
    out["items_with_question_13gram_hit"] = sum(
        r["question_13gram_hits"] > 0 for r in rows
    )
    return out


def load_corpora(corpus_dir):
    out = {}
    for l2 in ("de", "fr", "it"):
        p = Path(corpus_dir) / f"{l2}_legislation_switzerland_lexfind.jsonl.xz"
        if p.exists():
            out[l2] = Corpus.from_xz(p)
    return out
