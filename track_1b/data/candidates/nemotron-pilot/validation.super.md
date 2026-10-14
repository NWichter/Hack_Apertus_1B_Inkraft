> Historical pilot report (German, superseded). The release is checked by `data/validation_report.v<version>.md`; the hand-written share target mentioned below was an early development goal and was dropped (all cores are LLM drafts, disclosed per row).

# Validierungsbericht Stichtag (Entwürfe)

Erzeugt: 2026-10-04T03:46:41 mit `validate_items.py`  
Eingaben: `candidates.super.jsonl`

## Zusammenfassung

- Kern-Items (DE): **18** von Ziel 19; Zeilen gesamt (alle Sprachen): **54**
- Kerne mit DE+FR+IT: **18** (Minimum 1) → erfüllt
- Handgeschriebener Anteil: **0/18 = 0%** (Ziel 30% des fertigen Datensatzes; zählt nur `author: human` mit `authoring.mode: human_written`)
- Fehler (ERROR): **3** in 3 Zeilen/Kernen; Warnungen (WARN): **6**
- Zeilen ohne Fehler: **51** von 54

## Prüfungen

| Prüfung | Was genau |
| --- | --- |
| Format | Pflichtfelder, erlaubte Werte, ID-Muster, `status: draft`, `needs_human_review: true`, Generator-Felder, `as_of` |
| Evidenz | `source.evidence` steht wörtlich (Leerraum normalisiert) im zitierten Absatz der Fassung vom Stichtag in der Sprache des Items; `source.quote` = Absatztext |
| Antwort im Artikel | Zahlen: `answer_normalized.value` steht in Antwort und Evidenz (Ziffern, Tausender-Leerzeichen, Dezimalkomma, Zahlwörter DE/FR/IT); Text: Antwort (ohne führende Artikel/Präpositionen) steht wörtlich in der Evidenz; Ja/Nein: erlaubte Form |
| Veraltet (`temporal`) | Artikel seit 2024 geändert; veraltete Antwort vorhanden; deren Evidenz steht wörtlich in der Vorfassung; alter Wert ≠ neuer Wert |
| Near-Miss vs. frühere Fassungen | Zahl eines Near-Miss steht in einer gespeicherten früheren Fassung des Artikels, aber nicht in der geltenden → Fehler (gehört nach `outdated_answers`) |
| Duplikate | gleiche DE-Frage (Fehler), ähnliche DE-Fragen ab Ratio 0,85 (Warnung), gleicher Fakt = gleicher Absatz + gleicher Wert (Warnung) |
| Sprachkonsistenz | Sprache der Frage (Stoppwörter), gleicher Typ/Wert/Absatz je Kern, Ja/Nein gleich in allen Sprachen, ELI-URL in Item-Sprache |
| Stil/PII | kein ß in de-CH, keine Artikelnummer in der Frage, Fragezeichen, AHV-Nr./IBAN/Telefon/E-Mail |
| Stichtag | Hinweis, wenn für den Artikel bereits eine Fassung nach dem 01.10.2026 publiziert ist |

## Fehler und Warnungen nach Prüfung

| Prüfung | Anzahl |
| --- | ---: |
| WARN source.future_change | 3 |
| WARN style.long_answer | 3 |
| ERROR temporal.prev_evidence | 2 |
| ERROR lang.question | 1 |

## Verteilung (DE-Kerne)

### Autor × Gesetz

| | AHVG | AVIG | BVG | BVV2 | BVV3 | EOG | KVG | KVV | OR | Summe |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nemotron | 3 | 1 | 2 | 2 | 1 | 1 | 6 | 1 | 1 | 18 |

### Autor × Fragetyp

| | numeric | procedural | temporal | yes_no | Summe |
| --- | ---: | ---: | ---: | ---: | ---: |
| nemotron | 1 | 5 | 10 | 2 | 18 |

### Bereich (`domain`)

| Wert | Anzahl | Anteil |
| --- | ---: | ---: |
| bvg_3a | 5 | 28% |
| kvg_insured | 5 | 28% |
| ahv | 3 | 17% |
| eo_alv | 3 | 17% |
| kvg_billing | 2 | 11% |

### Register und Schwierigkeit

| Wert | Anzahl | Anteil |
| --- | ---: | ---: |
| lay / Stufe 2 | 13 | 72% |
| professional / Stufe 2 | 5 | 28% |

### Stichtag-Gruppe (Artikelebene)

| Wert | Anzahl | Anteil |
| --- | ---: | ---: |
| changed_2024_2025 | 17 | 94% |
| changed_2026 | 1 | 6% |

### Sprachen (alle Zeilen)

| | de-CH | fr-CH | it-CH | Summe |
| --- | ---: | ---: | ---: | ---: |
| nemotron | 18 | 18 | 18 | 54 |

## Alle Befunde

| Stufe | Prüfung | ID | Befund |
| --- | --- | --- | --- |
| ERROR | lang.question | nms-0018-de | Frage wirkt wie 'it', erwartet 'de' {'de': 2, 'fr': 0, 'it': 3} |
| ERROR | temporal.prev_evidence | nms-0015-fr | Evidenz der veralteten Antwort steht nicht in der Vorfassung |
| ERROR | temporal.prev_evidence | nms-0015-it | Evidenz der veralteten Antwort steht nicht in der Vorfassung |
| WARN | source.future_change | nms-0015-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | nms-0015-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | nms-0015-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | style.long_answer | nms-0016-de | Antwort lang (121 Zeichen) |
| WARN | style.long_answer | nms-0016-fr | Antwort lang (121 Zeichen) |
| WARN | style.long_answer | nms-0016-it | Antwort lang (126 Zeichen) |
