# Validierungsbericht Stichtag (Entwürfe)

Erzeugt: 2026-10-04T11:59:49 mit `validate_items.py`  
Eingaben: `merged.v1.jsonl`

## Zusammenfassung

- Kern-Items (DE): **303** von Ziel 300; Zeilen gesamt (alle Sprachen): **879**
- Kerne mit DE+FR+IT: **288** (Minimum 150) → erfüllt
- Handgeschriebener Anteil: **0/303 = 0%** (Ziel 30% des fertigen Datensatzes; zählt nur `author: human` mit `authoring.mode: human_written`)
- Fehler (ERROR): **0** in 0 Zeilen/Kernen; Warnungen (WARN): **219**
- Zeilen ohne Fehler: **879** von 879

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
| WARN source.future_change | 96 |
| WARN answer.threshold_word | 30 |
| WARN answer.no_variations | 25 |
| WARN source.discretion | 17 |
| WARN question.answer_overlap | 16 |
| WARN answer.number_literal_only | 12 |
| WARN answer.inflected | 7 |
| WARN dup.near_question | 7 |
| WARN dup.same_fact | 5 |
| WARN style.long_answer | 2 |
| WARN answer.alias_only | 1 |
| WARN question.contains_answer_number | 1 |

## Verteilung (DE-Kerne)

### Autor × Gesetz

| | AHVG | ATSG | AVIG | BVG | BVV3 | ELG | EOG | IVG | KVG | KVV | OR | UVG | Summe |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claude | 20 | 13 | 0 | 0 | 0 | 8 | 0 | 12 | 19 | 15 | 5 | 13 | 105 |
| codex | 20 | 14 | 0 | 0 | 0 | 8 | 0 | 13 | 15 | 14 | 5 | 14 | 103 |
| gemini | 4 | 0 | 10 | 21 | 3 | 0 | 27 | 1 | 13 | 4 | 10 | 2 | 95 |

### Autor × Fragetyp

| | calc | false_premise | numeric | procedural | temporal | term | yes_no | Summe |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claude | 0 | 0 | 52 | 18 | 9 | 3 | 23 | 105 |
| codex | 0 | 0 | 39 | 29 | 7 | 0 | 28 | 103 |
| gemini | 20 | 20 | 38 | 3 | 0 | 0 | 14 | 95 |

### Bereich (`domain`)

| Wert | Anzahl | Anteil |
| --- | ---: | ---: |
| kvg_insured | 56 | 18% |
| uvg_atsg | 56 | 18% |
| ahv | 44 | 15% |
| iv_el | 42 | 14% |
| eo_alv | 37 | 12% |
| bvg_3a | 24 | 8% |
| kvg_billing | 24 | 8% |
| or_illness | 20 | 7% |

### Register und Schwierigkeit

| Wert | Anzahl | Anteil |
| --- | ---: | ---: |
| lay / Stufe 1 | 110 | 36% |
| professional / Stufe 2 | 83 | 27% |
| lay / Stufe 2 | 47 | 16% |
| professional / Stufe 1 | 46 | 15% |
| professional / Stufe 3 | 16 | 5% |
| lay / Stufe 3 | 1 | 0% |

### Stichtag-Gruppe (Artikelebene)

| Wert | Anzahl | Anteil |
| --- | ---: | ---: |
| stable_pre2024 | 157 | 52% |
| changed_2024_2025 | 97 | 32% |
| changed_2026 | 49 | 16% |

### Sprachen (alle Zeilen)

| | de-CH | fr-CH | it-CH | Summe |
| --- | ---: | ---: | ---: | ---: |
| claude | 105 | 90 | 90 | 285 |
| codex | 103 | 103 | 103 | 309 |
| gemini | 95 | 95 | 95 | 285 |

## Alle Befunde

| Stufe | Prüfung | ID | Befund |
| --- | --- | --- | --- |
| WARN | answer.alias_only | cx-0093-fr | Antwort 'le tribunal des assurances du canton de domicile de l’assuré' nicht wörtlich, aber ein Alias |
| WARN | answer.inflected | cx-0014-de | Antwort 'ein Arzt oder eine Ärztin' nur flektiert/umgestellt in der Evidenz |
| WARN | answer.inflected | cx-0057-de | Antwort 'die zuständige IV-Stelle' nur flektiert/umgestellt in der Evidenz |
| WARN | answer.inflected | cx-0081-de | Antwort 'die Suva oder andere zugelassene Versicherer und eine von diesen betriebene Ersatzkasse' nur flektiert/umgestellt in der Evidenz |
| WARN | answer.inflected | cx-0081-fr | Antwort 'la CNA ou d’autres assureurs autorisés et une caisse supplétive gérée par ceux-ci' nur flektiert/umgestellt in der Evidenz |
| WARN | answer.inflected | cx-0081-it | Antwort 'l’INSAI o altri assicuratori autorizzati e la cassa suppletiva da loro amministrata' nur flektiert/umgestellt in der Evidenz |
| WARN | answer.inflected | cx-0093-de | Antwort 'das Versicherungsgericht desjenigen Kantons, in dem die versicherte Person zur Zeit der Beschwerdeerhebung Wohnsitz hat' nur flektiert/umgestellt in der Evidenz |
| WARN | answer.inflected | cx-0093-it | Antwort 'il tribunale delle assicurazioni del Cantone dove l’assicurato è domiciliato' nur flektiert/umgestellt in der Evidenz |
| WARN | answer.no_variations | cl-0016-fr | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0016-it | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0023-fr | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0023-it | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0034-fr | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0034-it | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0036-fr | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0036-it | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0038-fr | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0038-it | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0052-fr | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0052-it | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0073-fr | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0073-it | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0084-fr | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0084-it | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0099-fr | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0099-it | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0100-fr | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0100-it | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cx-0090-fr | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cx-0090-it | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cx-0093-it | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cx-0094-fr | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cx-0094-it | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.number_literal_only | cx-0018-fr | Zahl 1 nicht als Ziffer/Zahlwort erkannt, Antwort 'dans le mois qui suit l’information' steht aber wörtlich in der Evidenz |
| WARN | answer.number_literal_only | cx-0018-it | Zahl 1 nicht als Ziffer/Zahlwort erkannt, Antwort 'nel mese che segue l’informazione' steht aber wörtlich in der Evidenz |
| WARN | answer.number_literal_only | cx-0030-it | Zahl 23 nicht als Ziffer/Zahlwort erkannt, Antwort 'dopo la ventitreesima settimana di gravidanza' steht aber wörtlich in der Evidenz |
| WARN | answer.number_literal_only | cx-0031-it | Zahl 56 nicht als Ziffer/Zahlwort erkannt, Antwort 'il cinquantaseiesimo giorno dopo il parto' steht aber wörtlich in der Evidenz |
| WARN | answer.number_literal_only | cx-0089-it | Zahl 7 nicht als Ziffer/Zahlwort erkannt, Antwort 'il settimo giorno' steht aber wörtlich in der Evidenz |
| WARN | answer.number_literal_only | cx-0091-de | Zahl 50 nicht als Ziffer/Zahlwort erkannt, Antwort 'die Hälfte' steht aber wörtlich in der Evidenz |
| WARN | answer.number_literal_only | cx-0091-fr | Zahl 50 nicht als Ziffer/Zahlwort erkannt, Antwort 'la moitié' steht aber wörtlich in der Evidenz |
| WARN | answer.number_literal_only | cx-0091-it | Zahl 50 nicht als Ziffer/Zahlwort erkannt, Antwort 'la metà' steht aber wörtlich in der Evidenz |
| WARN | answer.number_literal_only | cx-0101-de | Zahl 80 nicht als Ziffer/Zahlwort erkannt, Antwort 'vier Fünftel' steht aber wörtlich in der Evidenz |
| WARN | answer.number_literal_only | cx-0101-fr | Zahl 80 nicht als Ziffer/Zahlwort erkannt, Antwort 'les quatre cinquièmes' steht aber wörtlich in der Evidenz |
| WARN | answer.number_literal_only | cx-0101-it | Zahl 80 nicht als Ziffer/Zahlwort erkannt, Antwort 'i quattro quinti' steht aber wörtlich in der Evidenz |
| WARN | answer.number_literal_only | cx-0104-fr | Zahl 16 nicht als Ziffer/Zahlwort erkannt, Antwort 'seize semaines' steht aber wörtlich in der Evidenz |
| WARN | answer.threshold_word | ag-0047-de | Evidenz enthält 'höchstens', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | ag-0047-it | Evidenz enthält 'al massimo', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | ag-0066-de | Evidenz enthält 'mehr als', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | ag-0069-de | Evidenz enthält 'weniger als', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | ag-0069-it | Evidenz enthält 'meno di', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | ag-0074-fr | Evidenz enthält 'au moins', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | ag-0074-it | Evidenz enthält 'almeno', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | ag-0089-de | Evidenz enthält 'bis zu', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | ag-0089-fr | Evidenz enthält 'au plus', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cl-0006-fr | Evidenz enthält 'moins de', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cl-0047-de | Evidenz enthält 'mindestens', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cl-0047-fr | Evidenz enthält 'au moins', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cl-0051-de | Evidenz enthält 'übersteig', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cl-0051-fr | Evidenz enthält 'dépass', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cl-0051-it | Evidenz enthält 'supera', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cl-0076-it | Evidenz enthält 'fino a', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cl-0101-it | Evidenz enthält 'almeno', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0022-it | Evidenz enthält 'supera', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0064-de | Evidenz enthält 'übersteig', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0064-fr | Evidenz enthält 'dépass', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0064-it | Evidenz enthält 'supera', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0067-de | Evidenz enthält 'übersteig', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0072-de | Evidenz enthält 'übersteig', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0073-de | Evidenz enthält 'mehr als', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0073-fr | Evidenz enthält 'plus de', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0073-it | Evidenz enthält 'al massimo', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0077-de | Evidenz enthält 'höchstens', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0077-fr | Evidenz enthält 'au plus', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0077-it | Evidenz enthält 'al massimo', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0101-fr | Evidenz enthält 'au moins', Frage und Antwort nicht: Schwelle prüfen |
| WARN | dup.near_question | ag-0077-de | Sehr ähnlich zu ag-0078-de (Ratio 0.92) |
| WARN | dup.near_question | cl-0021-de | Sehr ähnlich zu cl-0022-de (Ratio 0.95) |
| WARN | dup.near_question | cl-0029-de | Sehr ähnlich zu cl-0030-de (Ratio 0.94) |
| WARN | dup.near_question | cl-0030-de | Sehr ähnlich zu ag-0026-de (Ratio 0.90) |
| WARN | dup.near_question | cl-0071-de | Sehr ähnlich zu cl-0072-de (Ratio 0.91) |
| WARN | dup.near_question | cx-0044-de | Sehr ähnlich zu cx-0061-de (Ratio 0.88) |
| WARN | dup.near_question | cx-0071-de | Sehr ähnlich zu cx-0072-de (Ratio 0.91) |
| WARN | dup.same_fact | ag-0008-de | Gleicher Fakt (EOG art_16_f Abs. 1, Wert 220) auch in: ag-0047-de |
| WARN | dup.same_fact | cl-0022-de | Gleicher Fakt (KVV art_103 Abs. 2, Wert 350) auch in: ag-0003-de |
| WARN | dup.same_fact | cl-0033-de | Gleicher Fakt (KVV art_59 Abs. 2, Wert 2) auch in: ag-0090-de |
| WARN | dup.same_fact | cl-0101-de | Gleicher Fakt (OR art_324_a Abs. 2, Wert 3) auch in: ag-0092-de |
| WARN | dup.same_fact | cl-0102-de | Gleicher Fakt (OR art_324_a Abs. 1, Wert 3) auch in: ag-0091-de |
| WARN | question.answer_overlap | ag-0056-de | Antwortwörter stehen in der Frage: ['höchstens', 'taggelder'] |
| WARN | question.answer_overlap | ag-0079-fr | Antwortwörter stehen in der Frage: ['avoir', 'vieillesse'] |
| WARN | question.answer_overlap | ag-0079-it | Antwortwörter stehen in der Frage: ['avere', 'vecchiaia'] |
| WARN | question.answer_overlap | cl-0018-de | Antwortwörter stehen in der Frage: ['wohnkantons'] |
| WARN | question.answer_overlap | cl-0018-fr | Antwortwörter stehen in der Frage: ['canton', 'résidence'] |
| WARN | question.answer_overlap | cl-0018-it | Antwortwörter stehen in der Frage: ['cantone', 'domicilio'] |
| WARN | question.answer_overlap | cl-0034-fr | Antwortwörter stehen in der Frage: ['analyses', 'laboratoire'] |
| WARN | question.answer_overlap | cl-0034-it | Antwortwörter stehen in der Frage: ['analisi', 'laboratorio'] |
| WARN | question.answer_overlap | cl-0046-fr | Antwortwörter stehen in der Frage: ['minimal', 'montant'] |
| WARN | question.answer_overlap | cl-0052-fr | Antwortwörter stehen in der Frage: ['caisse', 'compensation'] |
| WARN | question.answer_overlap | cl-0052-it | Antwortwörter stehen in der Frage: ['cassa', 'compensazione'] |
| WARN | question.answer_overlap | cx-0014-it | Antwortwörter stehen in der Frage: ['medico'] |
| WARN | question.answer_overlap | cx-0040-fr | Antwortwörter stehen in der Frage: ['employeur'] |
| WARN | question.answer_overlap | cx-0057-fr | Antwortwörter stehen in der Frage: ['office'] |
| WARN | question.answer_overlap | cx-0083-fr | Antwortwörter stehen in der Frage: ['auprès'] |
| WARN | question.answer_overlap | cx-0093-fr | Antwortwörter stehen in der Frage: ['assurances', 'assuré', 'tribunal'] |
| WARN | question.contains_answer_number | cl-0042-fr | Die Zahl der Antwort (2) steht in der Frage |
| WARN | source.discretion | cl-0002-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | cl-0016-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | cl-0037-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | cl-0038-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | cl-0040-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | cl-0044-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | cl-0050-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | cl-0054-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | cl-0066-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | cx-0015-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | cx-0041-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | cx-0051-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | cx-0058-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | cx-0059-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | cx-0073-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | cx-0080-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | cx-0083-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.future_change | ag-0008-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0008-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0008-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0009-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0009-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0009-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0018-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0018-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0018-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0019-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0019-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0019-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0027-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0027-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0027-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0029-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0029-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0029-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0034-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0034-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0034-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0037-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0037-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0037-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0042-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0042-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0042-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0044-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0044-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0044-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0045-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0045-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0045-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0047-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0047-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0047-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0048-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0048-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0048-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0049-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0049-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0049-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0051-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0051-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0051-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0052-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0052-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0052-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0053-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0053-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0053-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0054-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0054-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0054-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0055-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0055-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0055-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0056-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0056-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0056-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0094-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0094-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0094-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0095-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0095-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | ag-0095-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | cl-0071-de | Artikel ändert sich nach dem Stichtag: 2027-01-01, 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cl-0071-fr | Artikel ändert sich nach dem Stichtag: 2027-01-01, 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cl-0071-it | Artikel ändert sich nach dem Stichtag: 2027-01-01, 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cl-0072-de | Artikel ändert sich nach dem Stichtag: 2027-01-01, 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cl-0072-fr | Artikel ändert sich nach dem Stichtag: 2027-01-01, 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cl-0072-it | Artikel ändert sich nach dem Stichtag: 2027-01-01, 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0066-de | Artikel ändert sich nach dem Stichtag: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0066-fr | Artikel ändert sich nach dem Stichtag: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0066-it | Artikel ändert sich nach dem Stichtag: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0068-de | Artikel ändert sich nach dem Stichtag: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0068-fr | Artikel ändert sich nach dem Stichtag: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0068-it | Artikel ändert sich nach dem Stichtag: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0069-de | Artikel ändert sich nach dem Stichtag: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0069-fr | Artikel ändert sich nach dem Stichtag: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0069-it | Artikel ändert sich nach dem Stichtag: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0070-de | Artikel ändert sich nach dem Stichtag: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0070-fr | Artikel ändert sich nach dem Stichtag: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0070-it | Artikel ändert sich nach dem Stichtag: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0071-de | Artikel ändert sich nach dem Stichtag: 2027-01-01, 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0071-fr | Artikel ändert sich nach dem Stichtag: 2027-01-01, 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0071-it | Artikel ändert sich nach dem Stichtag: 2027-01-01, 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0072-de | Artikel ändert sich nach dem Stichtag: 2027-01-01, 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0072-fr | Artikel ändert sich nach dem Stichtag: 2027-01-01, 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0072-it | Artikel ändert sich nach dem Stichtag: 2027-01-01, 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0104-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | cx-0104-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | cx-0104-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | cx-0105-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | cx-0105-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | cx-0105-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | style.long_answer | cx-0063-fr | Antwort lang (166 Zeichen) |
| WARN | style.long_answer | cx-0063-it | Antwort lang (166 Zeichen) |
