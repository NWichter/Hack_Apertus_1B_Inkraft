# Inkraft annotation guidelines

These rules apply to every item, whether a person writes it or reviews a model draft, and to the human
check of judge grades. Version 1, 1 October 2026.

## 1. Writing or reviewing an item

**Source.** The truth is the Swiss federal statute on fedlex, in the consolidated version applicable on the
as-of date (1 October 2026). Official web pages (admin.ch, ahv-iv.ch, ch.ch) may be used to cross-check a
fact, never as text and never as the source of a gold answer.

**Checklist per item** (all must be "yes"):

1. Does the answer stand in the linked paragraph, word for word or as the same number?
2. Is there exactly one defensible short answer? Every condition that decides the answer (adult or child,
   employed or not, before or after the probation period) is part of the question.
3. Can the question be understood without the article? It names the insurance branch in plain words
   ("in the AHV", "in compulsory health insurance") and no article number.
4. Do the French and Italian versions ask the same question, with answer and evidence taken from the
   authentic French and Italian text of the same paragraph?
5. For `temporal` items: is the outdated answer the rule of the previous version, with evidence copied
   from that version, and different from the current value?

**Fields.**

| Field               | Rule                                                                                                                      |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `answer`            | short: a number with unit, a body or step as named in the act, or exactly "Ja/Nein", "Oui/Non", "Sì/No"                   |
| `answer_aliases`    | other correct spellings ("3 Monate", "drei Monate"); never a different value                                              |
| `near_miss_answers` | plausible wrong values from the same context (child amount instead of adult amount); must differ from the outdated answer |
| `outdated_answers`  | only for amended provisions; must be stated in the previous version, never inferred                                       |
| `source.evidence`   | a short span copied character for character from the cited paragraph                                                      |

**Exclude** canton-dependent answers without a named canton, facts that are politically open during the
evaluation period (e.g. the financing of the 13th AHV pension), values the act leaves to the Federal Council
or the cantons, and any item with more than one defensible answer.

**Style.** German items use Swiss spelling ("ss", "CHF 300", "1'300"). No personal data: vignettes use
roles ("a 40-year-old employee"), never names, AHV numbers or IBANs.

**Corrections** are made with a logged decision (`apply_review.py`): the item keeps the previous values and
the reason under `authoring.manual_correction`. Dropped items are listed with the reason.

## 2. Human check of judge grades

The v1.0.0 check was done in a self-contained offline HTML page with the same fields and grades; `inkraft label
--annotator <name>` is the command-line equivalent. Both show the question, gold answer, accepted variants,
outdated and near-miss answers and the model response, never a judge's grade. The samples are drawn by
`src/draw_human_sample.py` (seed 20261013 for the 35 cores, 20261016 for the judgement sample, `inkraft.human.SEED`);
`src/import_human.py` imports the exported labels.

| Key | Grade         | When                                                                                                                                                                             |
| --- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `c` | CORRECT       | the response contains the gold answer or an accepted variant or an equivalent value ("12 Monate" for "ein Jahr"), and nothing contradicts it; hedging with one final answer counts |
| `i` | INCORRECT     | a different value or fact, several conflicting answers, or a contradiction anywhere in the response                                                                              |
| `n` | NOT_ATTEMPTED | no definite answer: refuses, says it does not know, only refers to an office or a website, or asks back                                                                          |

Add `?` to a key (`c?`) when unsure; such rows are reported separately. Ignore language mixing, spelling and
length. Do not use your own knowledge to overrule the gold answer; if the gold answer itself looks wrong,
note the item id and report it for the next patch version.
