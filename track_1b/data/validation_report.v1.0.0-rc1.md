# Validierungsbericht Stichtag (Entwürfe)

Erzeugt: 2026-10-13T20:02:39 mit `validate_items.py`  
Eingaben: `merged.v1.0.0-rc1.jsonl`

## Zusammenfassung

- Kern-Items (DE): **327** von Ziel 300; Zeilen gesamt (alle Sprachen): **951**
- Kerne mit DE+FR+IT: **312** (Minimum 150) → erfüllt
- Handgeschriebener Anteil: **0/327 = 0%** (Ziel 30% des fertigen Datensatzes; zählt nur `author: human` mit `authoring.mode: human_written`)
- Fehler (ERROR): **0** in 0 Zeilen/Kernen; Warnungen (WARN): **216**
- Zeilen ohne Fehler: **951** von 951

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
| WARN source.future_change | 87 |
| WARN answer.threshold_word | 44 |
| WARN source.discretion | 23 |
| WARN question.answer_overlap | 16 |
| WARN answer.inflected | 12 |
| WARN answer.number_literal_only | 12 |
| WARN evidence.apostrophe | 12 |
| WARN answer.no_variations | 4 |
| WARN answer.alias_only | 2 |
| WARN style.long_answer | 2 |
| WARN question.contains_answer_number | 1 |
| WARN temporal.evidence_unchanged | 1 |

## Verteilung (DE-Kerne)

### Autor × Gesetz

| | AHVG | AHVV | ATSG | AVIG | AVIV | BVG | BVV2 | BVV3 | ELG | ELV | EOG | FamZG | IVG | IVV | KLV | KVG | KVV | OR | UVG | Summe |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claude | 20 | 0 | 13 | 0 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 12 | 0 | 0 | 19 | 11 | 3 | 13 | 97 |
| codex | 19 | 0 | 14 | 0 | 0 | 0 | 0 | 0 | 7 | 0 | 0 | 0 | 12 | 0 | 0 | 15 | 14 | 3 | 14 | 98 |
| gemini | 4 | 0 | 0 | 9 | 0 | 15 | 0 | 2 | 0 | 0 | 26 | 0 | 1 | 0 | 0 | 13 | 4 | 10 | 2 | 86 |
| nemotron | 7 | 6 | 0 | 1 | 3 | 4 | 4 | 0 | 0 | 1 | 2 | 2 | 0 | 3 | 1 | 7 | 4 | 1 | 0 | 46 |

### Autor × Fragetyp

| | calc | false_premise | numeric | procedural | temporal | term | yes_no | Summe |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claude | 0 | 0 | 45 | 18 | 8 | 3 | 23 | 97 |
| codex | 0 | 0 | 37 | 29 | 6 | 0 | 26 | 98 |
| gemini | 20 | 18 | 31 | 3 | 0 | 0 | 14 | 86 |
| nemotron | 0 | 0 | 1 | 11 | 31 | 0 | 3 | 46 |

### Bereich (`domain`)

| Wert | Anzahl | Anteil |
| --- | ---: | ---: |
| kvg_insured | 57 | 17% |
| ahv | 56 | 17% |
| uvg_atsg | 56 | 17% |
| iv_el | 42 | 13% |
| eo_alv | 41 | 13% |
| kvg_billing | 31 | 9% |
| bvg_3a | 25 | 8% |
| or_illness | 17 | 5% |
| famz | 2 | 1% |

### Register und Schwierigkeit

| Wert | Anzahl | Anteil |
| --- | ---: | ---: |
| professional / Stufe 2 | 115 | 35% |
| lay / Stufe 1 | 107 | 33% |
| lay / Stufe 2 | 49 | 15% |
| professional / Stufe 1 | 40 | 12% |
| professional / Stufe 3 | 15 | 5% |
| lay / Stufe 3 | 1 | 0% |

### Stichtag-Gruppe (Artikelebene)

| Wert | Anzahl | Anteil |
| --- | ---: | ---: |
| stable_pre2024 | 248 | 76% |
| changed_2024_2025 | 71 | 22% |
| changed_2026 | 8 | 2% |

### Sprachen (alle Zeilen)

| | de-CH | fr-CH | it-CH | Summe |
| --- | ---: | ---: | ---: | ---: |
| claude | 97 | 82 | 82 | 261 |
| codex | 98 | 98 | 98 | 294 |
| gemini | 86 | 86 | 86 | 258 |
| nemotron | 46 | 46 | 46 | 138 |

## Alle Befunde

| Stufe | Prüfung | ID | Befund |
| --- | --- | --- | --- |
| WARN | answer.alias_only | cx-0093-fr | Antwort 'le tribunal des assurances du canton de domicile de l’assuré' nicht wörtlich, aber ein Alias |
| WARN | answer.alias_only | nmv-0057-de | Antwort 'Vereinigtes Königreich' nicht wörtlich, aber ein Alias |
| WARN | answer.inflected | cx-0014-de | Antwort 'ein Arzt oder eine Ärztin' nur flektiert/umgestellt in der Evidenz |
| WARN | answer.inflected | cx-0057-de | Antwort 'die zuständige IV-Stelle' nur flektiert/umgestellt in der Evidenz |
| WARN | answer.inflected | cx-0081-de | Antwort 'die Suva oder andere zugelassene Versicherer und eine von diesen betriebene Ersatzkasse' nur flektiert/umgestellt in der Evidenz |
| WARN | answer.inflected | cx-0081-fr | Antwort 'la CNA ou d’autres assureurs autorisés et une caisse supplétive gérée par ceux-ci' nur flektiert/umgestellt in der Evidenz |
| WARN | answer.inflected | cx-0081-it | Antwort 'l’INSAI o altri assicuratori autorizzati e la cassa suppletiva da loro amministrata' nur flektiert/umgestellt in der Evidenz |
| WARN | answer.inflected | cx-0093-de | Antwort 'das Versicherungsgericht desjenigen Kantons, in dem die versicherte Person zur Zeit der Beschwerdeerhebung Wohnsitz hat' nur flektiert/umgestellt in der Evidenz |
| WARN | answer.inflected | cx-0093-it | Antwort 'il tribunale delle assicurazioni del Cantone dove l’assicurato è domiciliato' nur flektiert/umgestellt in der Evidenz |
| WARN | answer.inflected | nmv-0097-de | Antwort 'ein Arzt oder eine Ärztin und eine Pflegefachperson' nur flektiert/umgestellt in der Evidenz |
| WARN | answer.inflected | nmv-0097-it | Antwort 'un medico e un infermiere' nur flektiert/umgestellt in der Evidenz |
| WARN | answer.inflected | nmv-0115-de | Antwort 'Mitgliedstaat der Europäischen Union, Island, Norwegen, Vereinigtes Königreich' nur flektiert/umgestellt in der Evidenz |
| WARN | answer.inflected | nmv-0115-fr | Antwort "État membre de l'Union européenne, Islande, Norvège, Royaume-Uni" nur flektiert/umgestellt in der Evidenz |
| WARN | answer.inflected | nmv-0115-it | Antwort "Stato membro dell'Unione europea, Islanda, Norvegia, Regno Unito" nur flektiert/umgestellt in der Evidenz |
| WARN | answer.no_variations | cl-0099-fr | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0099-it | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0100-fr | Weder answer_aliases noch near_miss/outdated angegeben |
| WARN | answer.no_variations | cl-0100-it | Weder answer_aliases noch near_miss/outdated angegeben |
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
| WARN | answer.number_literal_only | nmv-0008-fr | Zahl 35.3 nicht als Ziffer/Zahlwort erkannt, Antwort '35 fr. 30' steht aber wörtlich in der Evidenz |
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
| WARN | answer.threshold_word | cx-0022-it | Evidenz enthält 'supera', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0064-de | Evidenz enthält 'übersteig', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0064-fr | Evidenz enthält 'dépass', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0064-it | Evidenz enthält 'supera', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0067-de | Evidenz enthält 'übersteig', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0073-de | Evidenz enthält 'mehr als', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0073-fr | Evidenz enthält 'plus de', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0073-it | Evidenz enthält 'al massimo', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0077-de | Evidenz enthält 'höchstens', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0077-fr | Evidenz enthält 'au plus', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0077-it | Evidenz enthält 'al massimo', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | cx-0101-fr | Evidenz enthält 'au moins', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | nmf-0001-de | Evidenz enthält 'mindestens', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | nmf-0001-it | Evidenz enthält 'almeno', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | nmf-0002-de | Evidenz enthält 'mindestens', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | nmf-0002-it | Evidenz enthält 'almeno', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | nmf-0004-fr | Evidenz enthält 'dépass', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | nmu-0003-fr | Evidenz enthält 'au moins', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | nmu-0003-it | Evidenz enthält 'almeno', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | nmu-0004-de | Evidenz enthält 'mindestens', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | nmu-0004-fr | Evidenz enthält 'au moins', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | nmu-0004-it | Evidenz enthält 'almeno', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | nmu-0018-fr | Evidenz enthält 'au plus', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | nmu-0018-it | Evidenz enthält 'al massimo', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | nmv-0001-de | Evidenz enthält 'übersteig', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | nmv-0001-it | Evidenz enthält 'supera', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | nmv-0002-de | Evidenz enthält 'weniger als', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | nmv-0002-fr | Evidenz enthält 'au moins', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | nmv-0002-it | Evidenz enthält 'almeno', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | nmv-0068-fr | Evidenz enthält 'plus de', Frage und Antwort nicht: Schwelle prüfen |
| WARN | answer.threshold_word | nmv-0068-it | Evidenz enthält 'più di', Frage und Antwort nicht: Schwelle prüfen |
| WARN | evidence.apostrophe | nmu-0001-it | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmu-0004-fr | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmu-0004-it | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmu-0008-fr | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmu-0018-fr | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmu-0018-it | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmv-0017-fr | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmv-0027-fr | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmv-0027-it | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmv-0097-fr | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmv-0127-fr | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
| WARN | evidence.apostrophe | nmv-0127-it | Evidenz nutzt ' statt ’ (nur normalisiert gefunden) |
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
| WARN | source.discretion | nmu-0001-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | nmu-0002-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | nmv-0059-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | nmv-0075-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | nmv-0080-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
| WARN | source.discretion | nmv-0115-de | Absatz nennt Bundesrat/Departement/Reglement/Kanton: prüfen, ob der Wert Ermessen ist |
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
| WARN | source.future_change | cx-0105-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | cx-0105-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | cx-0105-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | nmv-0049-de | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | nmv-0049-fr | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | source.future_change | nmv-0049-it | Artikel ändert sich nach dem Stichtag: 2027-07-01 |
| WARN | style.long_answer | cx-0063-fr | Antwort lang (166 Zeichen) |
| WARN | style.long_answer | cx-0063-it | Antwort lang (166 Zeichen) |
| WARN | temporal.evidence_unchanged | nmu-0007-it | veraltete Antwort angegeben, aber der Belegsatz steht unverändert in allen früheren Fassungen |
