# Validierungsbericht Stichtag (Entwürfe)

Erzeugt: 2026-10-04T03:45:34 mit `validate_items.py`  
Eingaben: `candidates.ultra.jsonl`

## Zusammenfassung

- Kern-Items (DE): **19** von Ziel 19; Zeilen gesamt (alle Sprachen): **57**
- Kerne mit DE+FR+IT: **19** (Minimum 1) → erfüllt
- Handgeschriebener Anteil: **0/19 = 0%** (Ziel 30% des fertigen Datensatzes; zählt nur `author: human` mit `authoring.mode: human_written`)
- Fehler (ERROR): **4** in 4 Zeilen/Kernen; Warnungen (WARN): **18**
- Zeilen ohne Fehler: **53** von 57

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
| WARN evidence.apostrophe | 11 |
| ERROR overlap.outdated_near_miss | 3 |
| WARN source.future_change | 3 |
| WARN style.long_answer | 3 |
| ERROR answer.not_in_evidence | 1 |
| WARN answer.alias_only | 1 |

## Verteilung (DE-Kerne)

### Autor × Gesetz

| | AHVG | AVIG | BVG | BVV2 | BVV3 | EOG | IVG | KVG | KVV | OR | Summe |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nemotron | 3 | 1 | 2 | 2 | 1 | 1 | 1 | 6 | 1 | 1 | 19 |

### Autor × Fragetyp

| | numeric | procedural | temporal | yes_no | Summe |
| --- | ---: | ---: | ---: | ---: | ---: |
| nemotron | 1 | 1 | 14 | 3 | 19 |

### Bereich (`domain`)

| Wert | Anzahl | Anteil |
| --- | ---: | ---: |
| bvg_3a | 5 | 26% |
| kvg_insured | 5 | 26% |
| ahv | 3 | 16% |
| eo_alv | 3 | 16% |
| kvg_billing | 2 | 11% |
| iv_el | 1 | 5% |

### Register und Schwierigkeit

| Wert | Anzahl | Anteil |
| --- | ---: | ---: |
| professional / Stufe 2 | 13 | 68% |
| lay / Stufe 2 | 5 | 26% |
| lay / Stufe 1 | 1 | 5% |

### Stichtag-Gruppe (Artikelebene)

| Wert | Anzahl | Anteil |
| --- | ---: | ---: |
| changed_2024_2025 | 18 | 95% |
| changed_2026 | 1 | 5% |

### Sprachen (alle Zeilen)

| | de-CH | fr-CH | it-CH | Summe |
| --- | ---: | ---: | ---: | ---: |
| nemotron | 19 | 19 | 19 | 57 |

## Alle Befunde

| Stufe | Prüfung | ID | Befund |
| --- | --- | --- | --- |
| ERROR | answer.not_in_evidence | nmu-0015-de | Antwort 'Wenn die Altersrente nach der Anmeldung bei der Invalidenversicherung und vor der Zusprache einer Invalidenrente vorbezogen wurde.' steht nicht wörtlich in der Evidenz |
| ERROR | overlap.outdated_near_miss | nmu-0016-de | Veraltete Antwort und Near-Miss überlappen: {'vaterschaftsurlaub'} |
| ERROR | overlap.outdated_near_miss | nmu-0016-fr | Veraltete Antwort und Near-Miss überlappen: {'congé de paternité'} |
| ERROR | overlap.outdated_near_miss | nmu-0016-it | Veraltete Antwort und Near-Miss überlappen: {'congedo di paternità'} |
| WARN | answer.alias_only | nmu-0009-fr | Antwort "Lorsqu'elle ne peut pas être repoussée." nicht wörtlich, aber ein Alias |
| WARN | evidence.apostrophe | nmu-0001-it | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmu-0004-fr | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmu-0004-it | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmu-0008-fr | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmu-0013-fr | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmu-0013-it | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmu-0015-fr | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmu-0015-it | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmu-0016-fr | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmu-0018-fr | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmu-0018-it | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | source.future_change | nmu-0016-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | nmu-0016-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | nmu-0016-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | style.long_answer | nmu-0015-de | Antwort lang (130 Zeichen) |
| WARN | style.long_answer | nmu-0015-fr | Antwort lang (130 Zeichen) |
| WARN | style.long_answer | nmu-0015-it | Antwort lang (147 Zeichen) |
