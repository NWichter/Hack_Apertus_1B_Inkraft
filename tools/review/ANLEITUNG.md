# Inkraft-Prüfung – Anleitung

Lokales Prüfwerkzeug für den Inkraft-Datensatz (Hack Apertus 2026, Projekt 1B). Jeder Kern – eine Frage in
DE + FR + IT (Deutsch, Französisch, Italienisch), verbunden über `core_id` – wird mit dem Gesetzestext abgehakt,
korrigiert oder verworfen; dabei entsteht automatisch ein Prüfprotokoll.

Das Werkzeug liegt im Repo unter `Hack_Apertus_1B_Inkraft/tools/review/` (bis 03.10.2026 lag es außerhalb des
Repos unter `werkzeuge/inkraft-pruefung/`; jener Ordner wird nicht mehr gepflegt). Es ist reines HTML/JS
(kein Server, läuft über `file://`).

## Start

1. Einmalig (und nach jedem neuen Fedlex-Abruf oder neuen Verordnungen) die Gesetzestexte bündeln:
   `python build_fedlex.py` im Ordner `tools/review/` – liest den lokalen Fedlex-Abruf `quellen/fedlex-v2`
   (Standardpfad im Skript, andere Quelle mit `--fedlex <ordner>`) und schreibt `fedlex_texte.js` neben das Skript.
   Gebündelt werden standardmäßig die aktuelle Fassung, die Vorfassung und die Zwischenfassungen
   (`--roles current,previous,intermediate`), weil veraltete Antworten auch aus einer Zwischenfassung stammen
   können; alle Fassungen inklusive künftiger: `--roles all`. Die Datei ist groß (über 13 MB) und wird nicht
   committet – sie steht in `tools/review/.gitignore`.
2. `index.html` per Doppelklick öffnen (Edge oder Chrome, kein Server nötig).
3. Datensatz hineinziehen oder über **Dateien laden** wählen, aus `track_1b/data/`: `merged.v1.jsonl` allein
   **oder** `test.jsonl` + `metadata.jsonl` zusammen **oder** ein Review-Paket (siehe unten). Alle Dateien sind
   JSONL (JSON Lines: ein JSON-Objekt pro Zeile). Das Werkzeug liest die Dateien nur, es schreibt nichts ins Repo.
   Neue Stände einfach erneut laden – Zeilen werden über `id` zusammengeführt.

Ohne `fedlex_texte.js` läuft alles weiter, nur ohne Zitatabgleich und ohne Artikelanzeige.

## Prüfen

Pro Kern siehst du oben den Kopf (Erlass, Artikel, Absatz, Fassung, Fragetyp, Generator, Status), darunter
DE, FR und IT nebeneinander: Frage, Antwort, Varianten, Near-Miss, veraltete Antworten, Evidenz und den
Gesetzesabsatz aus der lokalen Fedlex-Fassung. Das **Zitat** ist gelb, die **Evidenz** orange markiert. Der Link
„Fedlex …“ öffnet die Fassung im neuen Tab. Bei `temporal`-Items lässt sich die Vorfassung aufklappen.

Automatische Vorprüfungen (grün = in Ordnung, gelb = ansehen, rot = Fehler):

- Zitat steht wörtlich im angegebenen Absatz der Fassung; Evidenz steht wörtlich im Zitat
- Zahl der Antwort steht in der Evidenz (Zahlwörter wie „drei“ werden erkannt)
- Fassung = am Stichtag geltende Fassung; Absatz existiert
- veraltete Antwort ≠ Gold, Near-Miss ≠ Gold/Variante/veraltete Antwort
- Vorfassung: Zitat und Evidenz der Vorfassung gefunden
- Rechenfragen: Formel ergibt den Goldwert, Rechen-Evidenz steht im Gesetz
- Sprachen: DE/FR/IT vorhanden, gleicher Artikel/Absatz/Typ, gleiche Zahl, gleiches Ja/Nein
- Hinweise: Artikelnummer in der Frage, bereits publizierte Änderung nach dem Stichtag

Die Vorprüfungen sind Hilfen, kein Urteil. Entschieden wird nach der Checkliste in
`track_1b/docs/annotation_guidelines.md`.

## Tastenkürzel

| Taste | Wirkung |
| --- | --- |
| `A` | ✓ korrekt |
| `K` | ✎ korrigieren – alle Felder werden editierbar, Änderungen erscheinen als Diff |
| `Strg`+`Enter` | Korrektur bzw. Verwerfen bestätigen (Begründung ist Pflicht) |
| `V` | ✗ verwerfen, dann `1`–`9` für den Grund, optional Freitext |
| `S` | ? später |
| `P` | Vorschlag aus dem Review-Paket übernehmen (siehe unten) |
| `Esc` | abbrechen (bei Korrektur: Änderungen verwerfen) |
| `→` / `←` | nächster / vorheriger Kern |
| `N` | nächster offener Kern |
| `T` | ganzen Artikel ein-/ausblenden |
| `/` | Suche, `G` Sprung zu ID |
| `Strg`+`Z` | Entscheidung des aktuellen Kerns zurücknehmen (bleibt im Protokoll) |
| `H` | Hilfe |
| `Alt`+`1`/`2`/`3` | Modus Prüfen / Handschrift / Blind-Stichprobe |

Nach einer Entscheidung springt das Werkzeug zum nächsten offenen Kern („danach weiter“ abschaltbar).
Filter links: Gesetz, Sprache, Generator, Fragetyp, Status, Entscheidung, nur offene, nur mit Warnungen; bei einem
Review-Paket zusätzlich Block und Priorität.

Die Zeit pro Kern wird nur gezählt, solange das Fenster sichtbar ist und du in den letzten 2 Minuten aktiv warst.

## Review-Paket

Ein Review-Paket ist eine normale JSONL-Datei im Format von `merged.v1.jsonl` (eine Zeile je Sprachfassung), in der
jede Zeile zusätzlich ein Feld `review_hint` tragen kann – auf allen Sprachzeilen eines Kerns gleich. Es wird wie ein
Datensatz geladen. Zeilen ohne `review_hint` verhalten sich wie bisher.

```json
"review_hint": {
  "package": "review-package-v1", "rank": 17, "block": "B", "block_label": "Temporal-Kandidaten (Nemotron)",
  "priority": "hoch", "est_minutes": 3,
  "reasons": ["Validator: answer.no_variations"],
  "auto_checks": {"quote_in_law": true, "outdated_in_earlier_version": true, "duplicate_of": null},
  "proposal": {"action": "patch", "summary": "…", "all": {"question_type": "procedural"}, "de": {"answer": "…"}},
  "agent_assessment": {"verdict": "accept|minor_fix|revise|reject", "note": "…"}
}
```

Pflicht sind nur `rank`, `block` und `block_label`.

- **Reihenfolge:** Kerne mit `rank` kommen nach Rang, danach die übrigen nach ID. `N` („nächster offener Kern“) und
  das automatische Weiterspringen folgen dieser Reihenfolge.
- **Blöcke:** In der Kernliste steht vor der ID das Block-Kürzel. Über der Liste stehen je Block geprüft / gesamt und
  die geschätzte Restzeit (Summe `est_minutes` der offenen Kerne); die Restzeit steht auch in der Fortschrittsanzeige.
  Filter „Block“ und „Priorität“ (hoch / mittel / niedrig) grenzen die Liste ein.
- **Hinweis-Karte** über den Sprachkarten: Block, Priorität, geschätzte Minuten, Gründe (`reasons`) und automatische
  Prüfungen (`auto_checks`: grün = erfüllt, rot = nicht erfüllt bzw. Duplikat gefunden).
- **Vorschlag** (`proposal`, vom Agenten erzeugt, nicht geprüft): Die Karte zeigt je Sprache und Feld den Diff
  alt → neu, bei `drop` die Begründung. Die Schlüssel sind Datensatzpfade wie bei `apply_review.py` (`question`,
  `answer`, `answer_aliases`, `near_miss_answers`, `outdated_answers`, `source.evidence`,
  `temporal.previous_evidence`, `question_type` …); `all` gilt für alle Sprachen, `de`/`fr`/`it` für eine.
  `P` (oder der Knopf auf der Karte) öffnet den Korrekturmodus wie `K` und trägt die vorgeschlagenen Werte ein; die
  Begründung ist mit `summary` vorbelegt. Danach weiter bearbeiten und wie immer mit `Strg`+`Enter` speichern.
  Felder, die oben nicht editierbar sind (z. B. `question_type`), stehen im Korrekturfeld unter „Zusätzlich
  geändert“; `Esc` verwirft alles. Bei `action: drop` öffnet `P` das Verwerfen-Panel mit Grund „Anderer Grund“ und
  `summary` als Freitext.
- **Agenten-Einschätzung** (`agent_assessment`): standardmäßig verborgen, damit das eigene Urteil nicht vom Agenten
  geprägt wird (Anchoring, also Verankerung am zuerst gesehenen Urteil). Sie erscheint erst, wenn für den Kern eine
  Entscheidung vorliegt (auch „später“), oder nach Klick auf „Agenten-Einschätzung aufdecken“. Jeder Protokolleintrag
  hat das Feld `agent_revealed_before_decision` (`true`, wenn die Einschätzung vor dieser Entscheidung sichtbar war).
- **Kandidaten:** Kerne mit ID-Präfix `nmu-`, `nmv-` oder `nms-` tragen in der Kopfzeile das Tag „Kandidat“.
- **Export:** `review_decisions.json` bleibt im Format von `apply_review.py` und bekommt je Entscheidung zusätzlich
  `block` (das Skript ignoriert den Schlüssel). `review_hint` bleibt in `metadata.reviewed.jsonl` erhalten.
  `pruefung_zusammenfassung.md` nennt je Block Anzahl Entscheidungen, Verwerfquote und mittlere Prüfzeit.

Beispiel einer exportierten Korrektur nach `P`:

```json
{"core_id": "cl-0003", "action": "patch", "reason": "Ja/Nein-Frage in offene Frage umbauen", "block": "B",
 "de": {"question_type": "procedural", "answer": "einen Prämienzuschlag", "source.evidence": "…"},
 "fr": {"question_type": "procedural", "answer": "un supplément de prime"},
 "it": {"question_type": "procedural", "answer": "un supplemento di premio"}}
```

## Handschrift

Modus **Handschrift**: neuen Kern selbst schreiben (Regeln aus `HANDGESCHRIEBEN-VORLAGE.md`). Gesetz, Artikel und
Absatz wählen – der Absatz erscheint unter dem Formular, die Evidenz wird live darin gesucht. FR/IT optional.
Gespeichert wird im Kompaktformat für `build_items.py`, gekennzeichnet mit `author: human`,
`generator_model: none`, `_written_by`, `_written_at`, `_duration_s`. Das ID-Präfix (Standard `hw`) ist
einstellbar; die endgültige ID vergibt `build_items.py --id-prefix`.

## Blind-Stichprobe (Mensch vs. Judge)

1. Im Repo die Stichprobe ziehen: `inkraft sample-human` → `data/human_labels/sample_20pct.jsonl`.
2. `test.jsonl` und `sample_20pct.jsonl` laden (Antwortdateien aus `responses/` gehen auch).
   Judge-Dateien werden absichtlich nicht geladen; Judge-Felder in Antwortdateien werden entfernt.
   Der Modellname wird nicht angezeigt.
3. Bewerten: `C` CORRECT, `S`/`M`/`I` INCORRECT mit Untertyp STALE / NEAR_MISS / OTHER, `N` NOT_ATTEMPTED,
   `?` vorher für „unsicher“. Annotator-Kürzel oben einstellbar (Standard `niklas`).
4. Export `labels_<annotator>.jsonl` – gleiches Format wie `inkraft label`
   (`id, model, condition, response, human_grade, human_subtype, uncertain, annotator, labelled_at`).

## Speichern und Export

Alles wird automatisch im Browser gespeichert (localStorage). Das ist **kein Archiv**: regelmäßig über
**Export → Alles exportieren** sichern. Exportdateien:

| Datei | Inhalt |
| --- | --- |
| `review_log.jsonl` | eine Zeile je Entscheidung: `item_id`/`core_id`, `decision` (accept, correct, reject, later, reset), Grund, Änderungen `old`→`new` je Feld, Prüfer, Zeitstempel nach ISO 8601, `duration_s`, Fingerabdruck (Erlass, Artikel, DE-Frage), `agent_revealed_before_decision`, bei Review-Paketen `block` |
| `review_decisions.json` | Entscheidungen im Format von `track_1b/src/apply_review.py` (keep / patch / drop), bei Review-Paketen mit `block` |
| `metadata.reviewed.jsonl` | geladene Zeilen mit angewendeten Entscheidungen – identisch mit dem Ergebnis von `apply_review.py` (verworfene Kerne entfernt, Korrekturen mit `authoring.manual_correction`, geprüfte mit `review_notes`) |
| `handwritten.jsonl` | neue Kerne im Kompaktformat |
| `labels_<annotator>.jsonl` | Blind-Labels |
| `pruefung_zusammenfassung.md` | Anzahl je Entscheidung, nach Gesetz und Generator, bei Review-Paketen je Block (Entscheidungen, Verwerfquote, mittlere Prüfzeit), Verwerfungsgründe, Zeit |

`status` und `needs_human_review` bleiben unverändert, weil `validate_items.py` für Entwürfe `draft`/`true` verlangt.
Die Prüfung ist über `review_log.jsonl` und `review_notes`/`manual_correction` nachvollziehbar.

**Weitermachen** auf einem anderen Rechner oder nach dem Löschen des Browser-Speichers: Datensatz laden und
`review_log.jsonl` (sowie ggf. `handwritten.jsonl`, `labels_*.jsonl`) hineinziehen. Haben sich Kern-IDs
inzwischen geändert, ordnet das Werkzeug Einträge über den Fingerabdruck (Artikel + DE-Frage) neu zu.

## Wohin die Dateien danach gehören

Im Repo `Hack_Apertus_1B_Inkraft/track_1b/`:

- `review_log.jsonl`, `review_decisions.json`, `pruefung_zusammenfassung.md`, `metadata.reviewed.jsonl` → `data/review/`
  (Prüfprotokoll, Beleg für die 100-%-Prüfung).
- Danach läuft alles Weitere per Skript (siehe „Nach der Prüfung“ unten). Für Teilstände reicht
  `python src/after_review.py --fedlex <fedlex-v2> --decisions data/review/review_decisions.json --log data/review/review_log.jsonl --allow-open`.
- `handwritten.jsonl` → `data/handwritten.compact.jsonl`, dann `build_items.py --author human --attested-by "Niklas Wichter"
  --generator-model none …` und `validate_items.py`.
- `labels_<annotator>.jsonl` → `data/human_labels/`, dann `inkraft agreement --annotator niklas --out data/human_labels/agreement.json`.

---

# Prüfauftrag 1B (Stand 04.10.2026)

## Was laden

1. `python build_fedlex.py --fedlex <OneDrive>/1B_Swiss_Voices/quellen/fedlex-v2` (einmalig, ≈ 1 min, 48 MB; enthält jetzt
   auch AHVV, IVV, ELV, AVIV und alle Zwischenfassungen).
2. `index.html` öffnen, **nur** `track_1b/data/review/review_package.v1.jsonl` laden (enthält Bestand und Kandidaten).
   Kein `merged.v1.jsonl` zusätzlich laden. Bisheriger Fortschritt im Browser bleibt erhalten.
3. Filter „nur offene“ an; dann mit `N` von Kern zu Kern. Die Reihenfolge ist die Priorität.

## Blöcke und Zeit

Die aktuelle Tabelle steht in `track_1b/data/review/review_package.v1.md`. Kurzfassung:

| Block | Inhalt | Was tun | Pflicht? |
| --- | --- | --- | --- |
| A1 | Bestand mit Vorschlag: Ja/Nein → offene Frage, Altantwort ergänzen (STALE-Paar), Varianten ergänzen, Klumpen/Duplikat streichen | Vorschlag ansehen, `P` übernimmt ihn als Korrektur, anpassen, `Strg`+`Enter`; oder `A` (Original behalten) / `V` | ja |
| A2 | Bestand, Belegsatz hat sich seit 2024 geändert | bestätigen, dass sich das **Recht** geändert hat (nicht nur der Wortlaut); Altantwort prüfen | ja |
| A3 | Bestand mit inhaltlicher Warnung (Antwort in der Frage, Schwellenwort, Ermessen) | Warnung prüfen, ggf. korrigieren | ja |
| B1 | Nemotron-Kandidaten mit belegter Altantwort | **erst selbst urteilen**, dann ggf. Agenten-Einschätzung aufdecken; nur aufnehmen, was echte Rechtsänderung testet | ja (Kernaussage STALE) |
| B3 | Pilot-Kandidaten (hatten Apertus-Kontakt) | wie B1, nie nach Apertus-Antworten entscheiden | ja |
| C | Bestand: Rechnen, falsche Prämisse | Rechnung und Prämisse nachvollziehen | ja |
| D | Bestand ohne Warnung | Schnellprüfung: Zitat gelb, Evidenz orange, Antwort stimmt → `A` | ja |
| B2 | Nemotron-Kandidaten ohne Altantwort | nur bei Zeit; sonst gar nicht anfassen (bleiben draußen) | nein |
| X | vorab aussortierte Kandidaten (Fehler, Duplikat) | nicht nötig; bleiben draußen | nein |

Typische Verwerfgründe bei Kandidaten (aus der Vorprüfung): reine Umbenennung (ordentliches Rentenalter → Referenzalter,
Vaterschaftsurlaub → Urlaub des andern Elternteils, Kasse → Arbeitslosenkasse), Antwort ist nur ein Artikelverweis,
Frage nach dem „letzten Eintrag einer Liste“, reine Verwaltungsdetails.

Pflicht für die 100-%-Prüfung sind alle Bestandskerne (A1–A3, C, D) und jeder Kandidat, der aufgenommen werden soll.
Nicht entschiedene Kandidaten bleiben automatisch draußen. Arbeite in Blöcken à 60–90 min; nach dem ersten Block die
gemessene Zeit pro Kern mit der Schätzung vergleichen (Zusammenfassung → „Nach Block“).

**Ausstiegspunkt 09.10. abends:** Ist bis dahin weniger als die Hälfte von A–D geschafft, B1/B3 nur noch bis zum Ende
des laufenden Blocks, dann Bestand fertig prüfen (Option A).

## Nach der Prüfung (läuft automatisch, nach deinem Go)

1. Export → **Alles exportieren**, Dateien nach `track_1b/data/review/`.
2. `python src/after_review.py --fedlex <fedlex-v2> --decisions data/review/review_decisions.json --log data/review/review_log.jsonl`
   → `data/merged.v2.jsonl` + `data/review/after_review_summary.json` (Zahlen: Kerne, STALE-Paare, Ja/Nein-Anteil, Verwerfquote je Generator).
3. **Freeze** (dein Go): `python src/freeze.py --fedlex <fedlex-v2> --go --corpus <multilegalpile>` → v1.0.0, `test.jsonl`,
   `metadata.jsonl`, `ablation_cores.txt`, `FREEZE.json`; dann Commit + Tag `dataset-v1.0.0`.
4. **Läufe** (dein Go): `sh scripts/run_after_freeze.sh` → Judge-Kalibrierung (Schranke 0,95), Apertus 8B/70B `closed_dated`,
   Ablation DE 8B, Judge, Score, `expected_results.json`, Stichprobe `data/human_labels/sample_20pct.jsonl`.
5. **20-%-Stichprobe** (du, ≈ 2 h): Modus Blind-Stichprobe, `test.jsonl` + `sample_20pct.jsonl` laden, Export `labels_niklas.jsonl`.
6. **HF** (dein Go): `python src/hf_release.py card --repo <owner/name>`, dann `upload --repo … --go --public`.
