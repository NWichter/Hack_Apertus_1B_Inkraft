# Validation report

Generated: 2026-10-16T09:49:23 with `validate_items.py`  
Inputs: `merged.v1.0.0.jsonl`

## Summary

- Core items (DE): **326** of target 300; rows in total (all languages): **948**
- Cores with DE+FR+IT: **311** (minimum 150) → met
- Errors (ERROR): **0** in 0 rows/cores; warnings (WARN): **216**
- Rows without errors: **948** of 948

## Checks

| Check | What exactly |
| --- | --- |
| Format | required fields, allowed values, ID pattern, `status`, `needs_human_review`, generator fields, `as_of` |
| Evidence | `source.evidence` appears verbatim (whitespace normalised) in the cited paragraph of the as-of-date version, in the item's language; `source.quote` = paragraph text |
| Answer in the article | Numbers: `answer_normalized.value` appears in answer and evidence (digits, thousands spaces, decimal comma, number words DE/FR/IT); text: answer (without leading articles/prepositions) appears verbatim in the evidence; yes/no: allowed form |
| Outdated (`temporal`) | article changed since 2024; outdated answer present; its evidence appears verbatim in the previous version; old value ≠ new value |
| Near-miss vs. earlier versions | a near-miss number appears in a stored earlier version of the article but not in the current one → error (belongs in `outdated_answers`) |
| Duplicates | identical DE question (error), similar DE questions from ratio 0.85 (warning), same fact = same paragraph + same value (warning) |
| Language consistency | language of the question (stop words), same type/value/paragraph per core, yes/no identical in all languages, ELI URL in the item's language |
| Style/PII | no ß in de-CH, no article number in the question, question mark, AHV number/IBAN/phone/email |
| As-of date | note if a version after 1 October 2026 is already published for the article |

## Errors and warnings by check

| Check | Count |
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

Warnings that occur:

- `answer.alias_only`: the answer is not verbatim in the evidence, but one of its aliases is
- `answer.inflected`: the answer appears in the evidence only inflected or reordered, not verbatim
- `answer.no_variations`: neither answer_aliases nor near_miss/outdated answers are given
- `answer.number_literal_only`: the number was not recognised as digit or number word, but the answer is verbatim in the evidence
- `answer.threshold_word`: the evidence contains a threshold word (e.g. 'at least', 'more than') that is missing from question and answer; check the threshold
- `evidence.apostrophe`: the evidence uses ' where the paragraph has the typographic apostrophe ’ (found only after normalisation)
- `question.answer_overlap`: most content words of the answer already appear in the question
- `question.contains_answer_number`: the number of the answer already appears in the question
- `source.discretion`: the paragraph mentions Bundesrat/Departement/Reglement/Kanton, so the value may be discretionary; check it
- `source.future_change`: a later version of the paragraph is already published after 1 October 2026 (the as-of date)
- `style.long_answer`: the answer is longer than the length limit
- `temporal.evidence_unchanged`: an outdated answer is given, but the evidence sentence is unchanged in all earlier versions

## Distribution (DE cores)

### Author × statute

| | AHVG | AHVV | ATSG | AVIG | AVIV | BVG | BVV2 | BVV3 | ELG | ELV | EOG | FamZG | IVG | IVV | KLV | KVG | KVV | OR | UVG | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claude | 20 | 0 | 13 | 0 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 12 | 0 | 0 | 19 | 11 | 3 | 13 | 97 |
| codex | 19 | 0 | 14 | 0 | 0 | 0 | 0 | 0 | 7 | 0 | 0 | 0 | 12 | 0 | 0 | 15 | 14 | 3 | 14 | 98 |
| gemini | 4 | 0 | 0 | 9 | 0 | 15 | 0 | 2 | 0 | 0 | 26 | 0 | 1 | 0 | 0 | 13 | 4 | 10 | 2 | 86 |
| nemotron | 6 | 6 | 0 | 1 | 3 | 4 | 4 | 0 | 0 | 1 | 2 | 2 | 0 | 3 | 1 | 7 | 4 | 1 | 0 | 45 |

### Author × question type

| | calc | false_premise | numeric | procedural | temporal | term | yes_no | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claude | 0 | 0 | 45 | 18 | 8 | 3 | 23 | 97 |
| codex | 0 | 0 | 37 | 29 | 6 | 0 | 26 | 98 |
| gemini | 20 | 18 | 31 | 3 | 0 | 0 | 14 | 86 |
| nemotron | 0 | 0 | 1 | 11 | 30 | 0 | 3 | 45 |

### Domain (`domain`)

| Value | Count | Share |
| --- | ---: | ---: |
| kvg_insured | 57 | 17% |
| uvg_atsg | 56 | 17% |
| ahv | 55 | 17% |
| iv_el | 42 | 13% |
| eo_alv | 41 | 13% |
| kvg_billing | 31 | 10% |
| bvg_3a | 25 | 8% |
| or_illness | 17 | 5% |
| famz | 2 | 1% |

### Register and difficulty

| Value | Count | Share |
| --- | ---: | ---: |
| professional / level 2 | 114 | 35% |
| lay / level 1 | 107 | 33% |
| lay / level 2 | 49 | 15% |
| professional / level 1 | 40 | 12% |
| professional / level 3 | 15 | 5% |
| lay / level 3 | 1 | 0% |

### As-of-date group (article level)

| Value | Count | Share |
| --- | ---: | ---: |
| stable_pre2024 | 248 | 76% |
| changed_2024_2025 | 70 | 21% |
| changed_2026 | 8 | 2% |

### Languages (all rows)

| | de-CH | fr-CH | it-CH | Total |
| --- | ---: | ---: | ---: | ---: |
| claude | 97 | 82 | 82 | 261 |
| codex | 98 | 98 | 98 | 294 |
| gemini | 86 | 86 | 86 | 258 |
| nemotron | 45 | 45 | 45 | 135 |

## All findings

| Level | Check | ID | Finding |
| --- | --- | --- | --- |
| WARN | answer.alias_only | cx-0093-fr | Answer 'le tribunal des assurances du canton de domicile de l’assuré' not verbatim, but an alias is |
| WARN | answer.alias_only | nmv-0057-de | Answer 'Vereinigtes Königreich' not verbatim, but an alias is |
| WARN | answer.inflected | cx-0014-de | Answer 'ein Arzt oder eine Ärztin' appears in the evidence only inflected/reordered |
| WARN | answer.inflected | cx-0057-de | Answer 'die zuständige IV-Stelle' appears in the evidence only inflected/reordered |
| WARN | answer.inflected | cx-0081-de | Answer 'die Suva oder andere zugelassene Versicherer und eine von diesen betriebene Ersatzkasse' appears in the evidence only inflected/reordered |
| WARN | answer.inflected | cx-0081-fr | Answer 'la CNA ou d’autres assureurs autorisés et une caisse supplétive gérée par ceux-ci' appears in the evidence only inflected/reordered |
| WARN | answer.inflected | cx-0081-it | Answer 'l’INSAI o altri assicuratori autorizzati e la cassa suppletiva da loro amministrata' appears in the evidence only inflected/reordered |
| WARN | answer.inflected | cx-0093-de | Answer 'das Versicherungsgericht desjenigen Kantons, in dem die versicherte Person zur Zeit der Beschwerdeerhebung Wohnsitz hat' appears in the evidence only inflected/reordered |
| WARN | answer.inflected | cx-0093-it | Answer 'il tribunale delle assicurazioni del Cantone dove l’assicurato è domiciliato' appears in the evidence only inflected/reordered |
| WARN | answer.inflected | nmv-0097-de | Answer 'ein Arzt oder eine Ärztin und eine Pflegefachperson' appears in the evidence only inflected/reordered |
| WARN | answer.inflected | nmv-0097-it | Answer 'un medico e un infermiere' appears in the evidence only inflected/reordered |
| WARN | answer.inflected | nmv-0115-de | Answer 'Mitgliedstaat der Europäischen Union, Island, Norwegen, Vereinigtes Königreich' appears in the evidence only inflected/reordered |
| WARN | answer.inflected | nmv-0115-fr | Answer "État membre de l'Union européenne, Islande, Norvège, Royaume-Uni" appears in the evidence only inflected/reordered |
| WARN | answer.inflected | nmv-0115-it | Answer "Stato membro dell'Unione europea, Islanda, Norvegia, Regno Unito" appears in the evidence only inflected/reordered |
| WARN | answer.no_variations | cl-0099-fr | Neither answer_aliases nor near_miss/outdated given |
| WARN | answer.no_variations | cl-0099-it | Neither answer_aliases nor near_miss/outdated given |
| WARN | answer.no_variations | cl-0100-fr | Neither answer_aliases nor near_miss/outdated given |
| WARN | answer.no_variations | cl-0100-it | Neither answer_aliases nor near_miss/outdated given |
| WARN | answer.number_literal_only | cx-0018-fr | Number 1 not recognised as digit/number word, but answer 'dans le mois qui suit l’information' is verbatim in the evidence |
| WARN | answer.number_literal_only | cx-0018-it | Number 1 not recognised as digit/number word, but answer 'nel mese che segue l’informazione' is verbatim in the evidence |
| WARN | answer.number_literal_only | cx-0030-it | Number 23 not recognised as digit/number word, but answer 'dopo la ventitreesima settimana di gravidanza' is verbatim in the evidence |
| WARN | answer.number_literal_only | cx-0031-it | Number 56 not recognised as digit/number word, but answer 'il cinquantaseiesimo giorno dopo il parto' is verbatim in the evidence |
| WARN | answer.number_literal_only | cx-0089-it | Number 7 not recognised as digit/number word, but answer 'il settimo giorno' is verbatim in the evidence |
| WARN | answer.number_literal_only | cx-0091-de | Number 50 not recognised as digit/number word, but answer 'die Hälfte' is verbatim in the evidence |
| WARN | answer.number_literal_only | cx-0091-fr | Number 50 not recognised as digit/number word, but answer 'la moitié' is verbatim in the evidence |
| WARN | answer.number_literal_only | cx-0091-it | Number 50 not recognised as digit/number word, but answer 'la metà' is verbatim in the evidence |
| WARN | answer.number_literal_only | cx-0101-de | Number 80 not recognised as digit/number word, but answer 'vier Fünftel' is verbatim in the evidence |
| WARN | answer.number_literal_only | cx-0101-fr | Number 80 not recognised as digit/number word, but answer 'les quatre cinquièmes' is verbatim in the evidence |
| WARN | answer.number_literal_only | cx-0101-it | Number 80 not recognised as digit/number word, but answer 'i quattro quinti' is verbatim in the evidence |
| WARN | answer.number_literal_only | nmv-0008-fr | Number 35.3 not recognised as digit/number word, but answer '35 fr. 30' is verbatim in the evidence |
| WARN | answer.threshold_word | ag-0069-de | Evidence contains 'weniger als', question and answer do not: check the threshold |
| WARN | answer.threshold_word | ag-0069-it | Evidence contains 'meno di', question and answer do not: check the threshold |
| WARN | answer.threshold_word | ag-0074-fr | Evidence contains 'au moins', question and answer do not: check the threshold |
| WARN | answer.threshold_word | ag-0074-it | Evidence contains 'almeno', question and answer do not: check the threshold |
| WARN | answer.threshold_word | ag-0089-de | Evidence contains 'bis zu', question and answer do not: check the threshold |
| WARN | answer.threshold_word | ag-0089-fr | Evidence contains 'au plus', question and answer do not: check the threshold |
| WARN | answer.threshold_word | cl-0006-fr | Evidence contains 'moins de', question and answer do not: check the threshold |
| WARN | answer.threshold_word | cl-0047-de | Evidence contains 'mindestens', question and answer do not: check the threshold |
| WARN | answer.threshold_word | cl-0047-fr | Evidence contains 'au moins', question and answer do not: check the threshold |
| WARN | answer.threshold_word | cl-0051-de | Evidence contains 'übersteig', question and answer do not: check the threshold |
| WARN | answer.threshold_word | cl-0051-fr | Evidence contains 'dépass', question and answer do not: check the threshold |
| WARN | answer.threshold_word | cl-0051-it | Evidence contains 'supera', question and answer do not: check the threshold |
| WARN | answer.threshold_word | cl-0076-it | Evidence contains 'fino a', question and answer do not: check the threshold |
| WARN | answer.threshold_word | cx-0022-it | Evidence contains 'supera', question and answer do not: check the threshold |
| WARN | answer.threshold_word | cx-0064-de | Evidence contains 'übersteig', question and answer do not: check the threshold |
| WARN | answer.threshold_word | cx-0064-fr | Evidence contains 'dépass', question and answer do not: check the threshold |
| WARN | answer.threshold_word | cx-0064-it | Evidence contains 'supera', question and answer do not: check the threshold |
| WARN | answer.threshold_word | cx-0067-de | Evidence contains 'übersteig', question and answer do not: check the threshold |
| WARN | answer.threshold_word | cx-0073-de | Evidence contains 'mehr als', question and answer do not: check the threshold |
| WARN | answer.threshold_word | cx-0073-fr | Evidence contains 'plus de', question and answer do not: check the threshold |
| WARN | answer.threshold_word | cx-0073-it | Evidence contains 'al massimo', question and answer do not: check the threshold |
| WARN | answer.threshold_word | cx-0077-de | Evidence contains 'höchstens', question and answer do not: check the threshold |
| WARN | answer.threshold_word | cx-0077-fr | Evidence contains 'au plus', question and answer do not: check the threshold |
| WARN | answer.threshold_word | cx-0077-it | Evidence contains 'al massimo', question and answer do not: check the threshold |
| WARN | answer.threshold_word | cx-0101-fr | Evidence contains 'au moins', question and answer do not: check the threshold |
| WARN | answer.threshold_word | nmf-0001-de | Evidence contains 'mindestens', question and answer do not: check the threshold |
| WARN | answer.threshold_word | nmf-0001-it | Evidence contains 'almeno', question and answer do not: check the threshold |
| WARN | answer.threshold_word | nmf-0002-de | Evidence contains 'mindestens', question and answer do not: check the threshold |
| WARN | answer.threshold_word | nmf-0002-it | Evidence contains 'almeno', question and answer do not: check the threshold |
| WARN | answer.threshold_word | nmf-0004-fr | Evidence contains 'dépass', question and answer do not: check the threshold |
| WARN | answer.threshold_word | nmu-0003-fr | Evidence contains 'au moins', question and answer do not: check the threshold |
| WARN | answer.threshold_word | nmu-0003-it | Evidence contains 'almeno', question and answer do not: check the threshold |
| WARN | answer.threshold_word | nmu-0004-de | Evidence contains 'mindestens', question and answer do not: check the threshold |
| WARN | answer.threshold_word | nmu-0004-fr | Evidence contains 'au moins', question and answer do not: check the threshold |
| WARN | answer.threshold_word | nmu-0004-it | Evidence contains 'almeno', question and answer do not: check the threshold |
| WARN | answer.threshold_word | nmu-0018-fr | Evidence contains 'au plus', question and answer do not: check the threshold |
| WARN | answer.threshold_word | nmu-0018-it | Evidence contains 'al massimo', question and answer do not: check the threshold |
| WARN | answer.threshold_word | nmv-0001-de | Evidence contains 'übersteig', question and answer do not: check the threshold |
| WARN | answer.threshold_word | nmv-0001-it | Evidence contains 'supera', question and answer do not: check the threshold |
| WARN | answer.threshold_word | nmv-0002-de | Evidence contains 'weniger als', question and answer do not: check the threshold |
| WARN | answer.threshold_word | nmv-0002-fr | Evidence contains 'au moins', question and answer do not: check the threshold |
| WARN | answer.threshold_word | nmv-0002-it | Evidence contains 'almeno', question and answer do not: check the threshold |
| WARN | answer.threshold_word | nmv-0068-fr | Evidence contains 'plus de', question and answer do not: check the threshold |
| WARN | answer.threshold_word | nmv-0068-it | Evidence contains 'più di', question and answer do not: check the threshold |
| WARN | evidence.apostrophe | nmu-0001-it | Evidence uses ' instead of ’ (found only after normalisation) |
| WARN | evidence.apostrophe | nmu-0004-fr | Evidence uses ' instead of ’ (found only after normalisation) |
| WARN | evidence.apostrophe | nmu-0004-it | Evidence uses ' instead of ’ (found only after normalisation) |
| WARN | evidence.apostrophe | nmu-0008-fr | Evidence uses ' instead of ’ (found only after normalisation) |
| WARN | evidence.apostrophe | nmu-0018-fr | Evidence uses ' instead of ’ (found only after normalisation) |
| WARN | evidence.apostrophe | nmu-0018-it | Evidence uses ' instead of ’ (found only after normalisation) |
| WARN | evidence.apostrophe | nmv-0017-fr | Evidence uses ' instead of ’ (found only after normalisation) |
| WARN | evidence.apostrophe | nmv-0027-fr | Evidence uses ' instead of ’ (found only after normalisation) |
| WARN | evidence.apostrophe | nmv-0027-it | Evidence uses ' instead of ’ (found only after normalisation) |
| WARN | evidence.apostrophe | nmv-0097-fr | Evidence uses ' instead of ’ (found only after normalisation) |
| WARN | evidence.apostrophe | nmv-0127-fr | Evidence uses ' instead of ’ (found only after normalisation) |
| WARN | evidence.apostrophe | nmv-0127-it | Evidence uses ' instead of ’ (found only after normalisation) |
| WARN | question.answer_overlap | ag-0056-de | Answer words appear in the question: ['höchstens', 'taggelder'] |
| WARN | question.answer_overlap | ag-0079-fr | Answer words appear in the question: ['avoir', 'vieillesse'] |
| WARN | question.answer_overlap | ag-0079-it | Answer words appear in the question: ['avere', 'vecchiaia'] |
| WARN | question.answer_overlap | cl-0018-de | Answer words appear in the question: ['wohnkantons'] |
| WARN | question.answer_overlap | cl-0018-fr | Answer words appear in the question: ['canton', 'résidence'] |
| WARN | question.answer_overlap | cl-0018-it | Answer words appear in the question: ['cantone', 'domicilio'] |
| WARN | question.answer_overlap | cl-0034-fr | Answer words appear in the question: ['analyses', 'laboratoire'] |
| WARN | question.answer_overlap | cl-0034-it | Answer words appear in the question: ['analisi', 'laboratorio'] |
| WARN | question.answer_overlap | cl-0046-fr | Answer words appear in the question: ['minimal', 'montant'] |
| WARN | question.answer_overlap | cl-0052-fr | Answer words appear in the question: ['caisse', 'compensation'] |
| WARN | question.answer_overlap | cl-0052-it | Answer words appear in the question: ['cassa', 'compensazione'] |
| WARN | question.answer_overlap | cx-0014-it | Answer words appear in the question: ['medico'] |
| WARN | question.answer_overlap | cx-0040-fr | Answer words appear in the question: ['employeur'] |
| WARN | question.answer_overlap | cx-0057-fr | Answer words appear in the question: ['office'] |
| WARN | question.answer_overlap | cx-0083-fr | Answer words appear in the question: ['auprès'] |
| WARN | question.answer_overlap | cx-0093-fr | Answer words appear in the question: ['assurances', 'assuré', 'tribunal'] |
| WARN | question.contains_answer_number | cl-0042-fr | The number of the answer (2) appears in the question |
| WARN | source.discretion | cl-0002-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | cl-0016-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | cl-0037-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | cl-0038-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | cl-0040-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | cl-0044-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | cl-0050-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | cl-0054-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | cl-0066-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | cx-0015-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | cx-0041-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | cx-0051-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | cx-0058-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | cx-0059-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | cx-0073-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | cx-0080-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | cx-0083-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | nmu-0001-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | nmu-0002-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | nmv-0059-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | nmv-0075-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | nmv-0080-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.discretion | nmv-0115-de | Paragraph mentions Bundesrat/Departement/Reglement/Kanton: check whether the value is discretionary |
| WARN | source.future_change | ag-0008-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0008-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0008-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0009-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0009-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0009-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0018-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0018-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0018-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0019-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0019-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0019-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0027-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0027-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0027-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0029-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0029-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0029-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0034-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0034-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0034-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0037-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0037-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0037-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0042-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0042-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0042-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0044-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0044-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0044-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0045-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0045-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0045-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0048-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0048-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0048-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0049-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0049-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0049-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0051-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0051-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0051-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0052-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0052-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0052-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0053-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0053-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0053-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0054-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0054-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0054-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0055-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0055-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0055-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0056-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0056-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0056-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0094-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0094-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0094-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0095-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0095-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | ag-0095-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | cl-0071-de | Article changes after the as-of date: 2027-01-01, 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cl-0071-fr | Article changes after the as-of date: 2027-01-01, 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cl-0071-it | Article changes after the as-of date: 2027-01-01, 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0066-de | Article changes after the as-of date: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0066-fr | Article changes after the as-of date: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0066-it | Article changes after the as-of date: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0068-de | Article changes after the as-of date: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0068-fr | Article changes after the as-of date: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0068-it | Article changes after the as-of date: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0069-de | Article changes after the as-of date: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0069-fr | Article changes after the as-of date: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0069-it | Article changes after the as-of date: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0070-de | Article changes after the as-of date: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0070-fr | Article changes after the as-of date: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0070-it | Article changes after the as-of date: 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0071-de | Article changes after the as-of date: 2027-01-01, 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0071-fr | Article changes after the as-of date: 2027-01-01, 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0071-it | Article changes after the as-of date: 2027-01-01, 2028-01-01, 2029-01-01 |
| WARN | source.future_change | cx-0105-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | cx-0105-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | cx-0105-it | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | nmv-0049-de | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | nmv-0049-fr | Article changes after the as-of date: 2027-07-01 |
| WARN | source.future_change | nmv-0049-it | Article changes after the as-of date: 2027-07-01 |
| WARN | style.long_answer | cx-0063-fr | Answer is long (166 characters) |
| WARN | style.long_answer | cx-0063-it | Answer is long (166 characters) |
| WARN | temporal.evidence_unchanged | nmu-0007-it | outdated answer given, but the evidence sentence is unchanged in all earlier versions |
