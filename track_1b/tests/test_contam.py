from inkraft.contam import Corpus, check, summary

DOCS = [
    "832.10 Kantonales Gesetz. Jede Person muss sich innert drei Monaten nach der Wohnsitznahme versichern.",
    "Alte Fassung: b. Frauen, welche das 64. Altersjahr vollendet haben, erhalten eine Rente.",
    "Ein Erlass ohne Bezug. " + "wort " * 30,
]


def item(iid, ev, prev=None, q="Innert welcher Frist muss man sich versichern?"):
    return {
        "id": iid,
        "lang": "de-CH",
        "question_type": "temporal" if prev else "numeric",
        "question": q,
        "answer": "3 Monate",
        "source": {"evidence": ev},
        "temporal": {"previous_evidence": prev} if prev else {},
    }


def test_buckets_and_docs():
    c = Corpus(DOCS, [d[:20] for d in DOCS])
    rows = {
        r["id"]: r
        for r in check(
            [
                item("a", "innert drei Monaten nach der Wohnsitznahme"),
                item(
                    "b",
                    "Personen, die das 65. Altersjahr vollendet haben",
                    prev="b. Frauen, welche das 64. Altersjahr vollendet haben",
                ),
                item("c", "eine Formulierung, die es nirgends gibt"),
                item("d", "zu kurz"),
            ],
            {"de": c},
        )
    }
    assert rows["a"]["bucket"] == "current" and rows["a"]["current_docs"] == 1
    assert rows["b"]["bucket"] == "outdated"
    assert rows["c"]["bucket"] == "absent"
    assert rows["d"]["bucket"] == "evidence_too_short"
    assert summary(list(rows.values()))["bucket"]["current"] == 1


def test_question_leak():
    leaked_q = "Kantonales Gesetz: Jede Person muss sich innert drei Monaten nach der Wohnsitznahme versichern?"
    c = Corpus(DOCS, [d[:20] for d in DOCS])
    rows = check(
        [
            item("x", "innert drei Monaten nach der Wohnsitznahme", q=leaked_q),
            item("y", "innert drei Monaten nach der Wohnsitznahme"),
        ],
        {"de": c},
    )
    hits = {r["id"]: r["question_13gram_hits"] for r in rows}
    assert hits["x"] > 0 and hits["y"] == 0
