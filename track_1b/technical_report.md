# Technical report — Inkraft

> Three sentence summary: Swiss residents, municipal AHV offices, medical practices and social services need exact amounts, deadlines and responsibilities from Swiss social and health insurance law, and a model that states last year's rule is worse than one that says it does not know. Inkraft is a trilingual (German, French, Italian) short-answer benchmark in which every gold answer is quoted from the authentic text of a federal act as of 1 October 2026 and, for amended provisions, the previously valid answer is stored as well, so that wrong answers split into _stale_ and _invented_. Preliminary results on the unreviewed draft (rule-based grading only): Apertus 1.5 70B answers 52 % and 8B 35 % of rows correctly, but only 6–10 % of the questions on rules changed since 2024, and a date in the prompt does not help.

**Track:** Apertus Readiness - Track 1B (Swiss Voices, Core Task Intelligence)  
**Event:** Online  
**Team:** Apertool — Niklas Wichter  
**Demo:** project page https://inkraft.apertool.ch; Hugging Face dataset and video planned with v1.0.0 (by 2026-10-15)

---

### Use of Apertus

- **Model:** swiss-ai/Apertus-v1.5-8B and swiss-ai/Apertus-v1.5-70B [@apertus2025; @swissai2026apertus15]
- **How it is used:** evaluation
- **Where it runs:** hosted Hack Apertus endpoint (OpenAI-compatible); any other endpoint via `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_NAME`

---

## Use Case Description

Every person living in Switzerland is insured under the Federal Health Insurance Act (KVG) and the old-age and survivors' insurance (AHV). Questions about deductibles, contribution rates, waiting periods and registration deadlines reach municipal AHV branch offices, front-office staff in medical practices, social services and the insured themselves. Mistakes cost money: a missed switching deadline binds a person to an insurer for another year, a wrong waiting period delays an invalidity insurance (IV) claim. Public administrations already deploy Apertus [@swissai2026apertus15], so the question is not only whether the model knows this law, but whether it knows the law _in force_.

Social insurance law changes on fixed dates. The minimum full AHV old-age pension in Art. 34 para. 5 AHVG was CHF 1,225 in the consolidated version of 1 January 2024 and is CHF 1,260 since the version of 1 January 2025. A model trained on older web text may give the earlier figure with confidence. Language models have source-specific effective knowledge cutoffs [@cheng2024dateddata], legal hallucinations are frequent [@dahl2024legalfictions], and outdated statutory knowledge has been shown for German law [@prior2026oldfriend]. Inkraft therefore separates three kinds of failure: an answer that matches the rule before an amendment (_stale_), an answer that matches no version (_invented_), and an honest refusal (_not attempted_).

## Dataset Summary

Inkraft targets the federal acts on health insurance (KVG, KVV), old-age, invalidity and supplementary benefits (AHVG, IVG, ELG), accident insurance and the general part of social insurance law (UVG, ATSG), and continued payment of wages in case of illness (Art. 324a OR). Each item is a single-turn question with a short gold answer, accepted variants, _near-miss_ answers (a related but wrong value, e.g. the amount for children instead of adults) and, for amended provisions, the outdated answer. Every item is anchored to one paragraph: fedlex ELI with version date and the verbatim quote in the language of the item. The as-of date is 1 October 2026 for all items.

Table 1 places Inkraft among related benchmarks. SwitzerlandQA [@apertus2025] covers Swiss civics including insurance, but as machine-translated multiple choice without sources. Swiss-Bench SBP-002 and 003 cover FINMA, data protection and contract law [@uenal2026sbp002; @uenal2026sbp003], LEXam covers law exams [@fan2025lexam], and Prior et al. measure outdated knowledge of German statutes [@prior2026oldfriend]. To our knowledge no open benchmark combines Swiss social insurance law, gold answers from three authentic language versions, an as-of date with the previous rule, credit for abstention, and an exposure check against the published training data of the evaluated model.

| Benchmark     | Domain, format                                      | Stale   | Abst.   |
| ------------- | --------------------------------------------------- | ------- | ------- |
| SwitzerlandQA | civics incl. insurance; MC                          | no      | no      |
| Swiss-Bench   | FINMA, nDSG, OR; mixed                              | n. r.   | n. r.   |
| LEXam         | law exams; open + MC                                | n. r.   | n. r.   |
| Prior et al.  | German law; temporal QA                             | yes     | n. r.   |
| **Inkraft**   | **social insurance; short, DE/FR/IT, fedlex quote** | **yes** | **yes** |

: Related benchmarks. Stale: separates outdated from wrong answers. Abst.: credits abstention. n. r.: not reported in the abstract (for SwitzerlandQA: Appendix K of the Apertus report).

Table 2 describes the current draft (not yet frozen; every row is still marked for human review). It comprises **303 German core questions** and **879 rows in total**; 288 cores exist in all three languages (DE, FR, IT). All cores are LLM drafts: 105 by Claude, 103 by GPT-5.5 (Codex) and 95 by Gemini (gemini-3.8-flash in an Antigravity agent); the Gemini cores contain all 20 calculation items (`calc`) and all 20 false-premise items (`false_premise`). No item is hand-written yet. 16 cores are `temporal` items whose provision was amended since 2024.

| Domain                                    | Cores | Question type  | Cores |
| ----------------------------------------- | ----- | -------------- | ----- |
| Accident insurance / ATSG                 | 56    | numeric        | 129   |
| Health insurance, insured                 | 56    | yes / no       | 65    |
| AHV                                       | 44    | procedural     | 50    |
| IV / EL                                   | 42    | calc           | 20    |
| EO / ALV                                  | 37    | false_premise  | 20    |
| Occupational pensions & 3a (BVG / BVV3)   | 24    | temporal       | 16    |
| Health insurance, billing                 | 24    | term           | 3     |
| Wage during illness (OR)                  | 20    | **Total**      | **303** |

: Draft (not frozen), German cores by domain and question type (879 total rows across DE, FR, IT). Automatic checks against fedlex: 0 errors.

## Data Collection Method

**Truth comes from the statute, never from a language model.** The pipeline runs fedlex → paragraphs → item drafting → automatic checks → review → freeze (v1.0.0) → evaluation. It fetches the acts from the fedlex SPARQL endpoint in German, French and Italian: the consolidation applicable on 1 October 2026, the one applicable at the end of 2023 for `temporal` items, and every already published future version to flag provisions that will change. Articles are split into paragraphs.

Two routes create items. (a) _LLM-drafted, then human-reviewed:_ a drafting model receives a single paragraph and proposes a question, answer variants and near misses; the gold answer must occur verbatim (or as a normalised number) in that paragraph, otherwise the draft is rejected automatically. The draft questions were written this way by Claude (Anthropic) and GPT-5.5 (OpenAI, via Codex); a third batch of 95 cores (calculations, false premises, EO, ALV, BVG) was drafted by Gemini (Google) inside an Antigravity agent that wrote the items into Python scripts. Every row records `generator`, `generator_model`, `prompt_version` and the date. (b) _Hand-written_ items by the author are planned (target ≥ 30 % of the final set) but do not exist yet; the hand-written share of the current draft is 0 %.

French and Italian questions are translations, but their gold answers and evidence come from the authentic French and Italian text of the same paragraph, because all three language versions of federal law are equally binding [@publg2023art14]. Terminology follows the official versions (e.g. _Selbstbehalt / quote-part / aliquota_).

**Automatic checks** (script `validate_items.py`, run on every version): schema and allowed values; the evidence occurs verbatim in the cited paragraph of the version valid on the as-of date; the answer or its normalised number occurs in the evidence; for `temporal` items the outdated answer occurs in the previous version and differs from the current value; a near-miss value that occurs in an earlier stored version but not in the current one is rejected (it belongs to the outdated answers); duplicate and near-duplicate questions; language and value consistency across DE/FR/IT; Swiss spelling and a PII scan. The current draft passes with **0 errors on 879 rows**; 153 warnings remain (mostly future amendments published in the Federal Gazette for 2027+).

**Review.** Each item is checked against four questions: does the answer stand in the linked paragraph, is there exactly one defensible short answer, is the question understandable without the article, and do FR/IT match DE. Review v1 removed 2 cores and corrected 7; review v2 corrected 8 more (e.g. outdated amounts listed as near misses) and left one circular item open. Review v1 included, for example, restricting the women's reference age question to cohorts born in 1964 or later because the AHV 21 transitional rules give earlier cohorts an age between 64 and 65. Every change is logged in the item. Exclusion rules: no canton-dependent answers, no facts that are politically open during the evaluation period, no questions with more than one defensible answer.

**Exposure check.** Apertus 1.5 was trained on the Swiss legislation subset `switzerland_lexfind` of MultiLegalPile [@swissai2026transparency; @niklaus2024multilegalpile]. We downloaded the German, French and Italian files at the published revision of 12 January 2024 (16,981 German documents, federal and cantonal law) and checked, per item, whether the verbatim evidence of the current version and, for `temporal` items, of the previous version occurs in that corpus; we also count 13-gram overlaps between questions and the corpus [@brown2020gpt3; @sainz2023contamination]. On the current draft (879 rows, recomputed on 2026-10-04) the current evidence occurs in 602 rows, only the previous wording in 26, neither in 232; 19 evidences are too short to search. For the 48 `temporal` rows the current wording occurs **never**; the previous wording occurs in 24. Apertus has therefore seen the old rule, not the new one, for every amended provision in the draft that the corpus covers. The 52 questions with 13-gram hits reuse statutory phrasing; the questions themselves are new. The check is recomputed on v1.0.0.

**Consent.** No personal data is collected; case vignettes use roles only. A consent form template for optional native-speaker reviewers is provided (`docs/consent_form_template.md`).

## Dataset Details

The statute texts are not protected by copyright (Art. 5 para. 1 URG) [@urg2025art5]; fedlex linked data is offered for free use [@opendataswiss2026terms]. Questions, answers and metadata are released under CDLA-Permissive-2.0; the licence is stored per item. Pages of admin.ch and ahv-iv.ch were used only to cross-check facts, never as text. The intermediate MultiLegalPile files (CC BY-NC-SA) are analysed locally and not redistributed. The data card follows the Hack Apertus template, Datasheets and Data Cards [@gebru2021datasheets; @pushkarna2022datacards]. A canary GUID in every file lets future model builders exclude the set from training [@srivastava2023bigbench]. Quality figures in the data card: validator errors and warnings, PII hits (0) and the corrections of reviews v1 and v2; the human-review rejection rate per generator and the ambiguity rate are planned, not yet available, and follow with v1.0.0.

## Evaluation

### Method

Grading follows SimpleQA [@wei2024simpleqa]: each answer is CORRECT, INCORRECT or NOT_ATTEMPTED; INCORRECT answers carry the subtype STALE (matches the outdated answer) or NEAR_MISS, otherwise OTHER (_invented_). Reported metrics: correct, incorrect and not-attempted rates; correct given attempted (CGA); the SimpleQA F-score; hallucination rate I/(C+I); share of stale errors; a penalised score C − λ·I with λ = 1 and λ = 3, which rewards abstention over guessing [@kalai2025hallucinate; @wen2025abstention]; language consistency (same grade in DE, FR and IT for a core) [@qi2023crosslingual]; and the open-book gain (accuracy with the cited paragraph in the prompt minus closed-book accuracy), which separates a knowledge gap from a reading gap. All figures carry 95 % percentile bootstrap intervals (1,000 resamples, fixed seed); language differences use paired resampling.

Grading has three stages. (1) A deterministic pre-grade extracts numbers, number words, ordinals and units in all three languages, compares durations in days and detects refusals; it never overrules the judge but serves as a hint and as a check. (2) An LLM judge from a different model family than the examinee grades every answer against gold, variants, outdated and near-miss answers [@zheng2023judging]; self-preference is avoided by construction [@panickssery2024selfpreference]. Before use, the judge must reach at least 95 % on 61 constructed answers with known grades (correct, verbose, hedged, wrong language, stale, near miss, conflicting, refusal). Planned judge: Qwen3-235B, a family different from all examinees and drafting models; its calibration accuracy is reported with v1.0.0. (3) A human grades a stratified 20 % sample of every model × condition blind to the judge's grade; we report raw agreement and Cohen's κ with bootstrap intervals [@cohen1960kappa; @bavaresco2025llmjudges].

### Evaluation setup and inference parameters

Conditions: `closed_dated` (main): system prompt on Swiss federal law with the date and the instruction to answer briefly and say when unsure; `closed_swiss`: the same prompt without the date (date effect); `closed_plain`: the bare question (context effect); `open_book`: as `closed_dated` plus the cited paragraph; `thinking`: as `closed_dated` with Apertus' reasoning mode. Parameters: temperature 0, top-p 1, max. 256 output tokens (3,000 with reasoning), seed 20261001, native chat template via the endpoint. Examinees: Apertus-v1.5-8B and -70B on the hosted Hack Apertus endpoint. Preliminary run: 2026-10-04, `closed_swiss` and `closed_dated`, 3,516 answers (3,748 HTTP calls including retries, 0 failures). Final runs on v1.0.0 are planned for 2026-10-12/13.

### Preliminary results (unreviewed draft, rule-based grading only)

> **Preliminary.** One run on the unreviewed draft (879 rows, 2026-10-04), graded only by the deterministic pre-grade, without the LLM judge and without human review. 21–25 % of the answers stay undecided (mostly procedural items), so correct rates are lower bounds; some wrong answers may come from wrong gold answers in the draft. No item was selected, changed or removed on these outcomes. Final results follow on v1.0.0 with the judge and the 20 % human sample.

| Rows (`closed_dated`)         | n   | 8B          | 70B         |
| ----------------------------- | --- | ----------- | ----------- |
| All rows                      | 879 | 35 (32–38)  | 52 (49–55)  |
| Stable before 2024            | 451 | 39 (35–44)  | 56 (51–60)  |
| Changed since 2024 (temporal) | 48  | 6 (2–17)    | 10 (5–22)   |
| Current wording in corpus     | 602 | 38 (34–42)  | 57 (53–61)  |
| No wording found              | 232 | 31 (25–37)  | 43 (37–49)  |
| Only previous wording         | 26  | 12 (4–29)   | 19 (9–38)   |

: Preliminary correct rates in % with 95 % Wilson intervals; the last three rows are the exposure buckets. `closed_swiss` (same prompt without the date) differs by at most 2.2 points per row, except 3.8 points (one row of 26) for the 70B on the only-previous-wording bucket.

![Preliminary correct rates per group and model (`closed_dated`), with 95 % Wilson intervals.](report/fig_preliminary.svg){width=100%}

Three findings hold for both models. **(1) Changed rules are rarely known.** On the 48 rows whose rule changed since 2024, only 6–10 % of the answers are correct, against 39–56 % on stable rules; the 70B gives the earlier rule in 16 of the 48 rows, the 8B in 6. **(2) The date in the prompt does not help.** Adding "today is 1 October 2026" changes the correct rate by +0.8 points for the 8B (paired exact McNemar test, p = 0.35) and by ±0 for the 70B (p = 1.0); only the 8B's not-attempted rate falls by 1.7 points (p = 0.006). **(3) Accuracy differs by exposure bucket:** the 70B is correct in 57 % of the rows whose current wording occurs in its training corpus, in 43 % where no wording is found and in 19 % where only the previous wording occurs. This is an association, not a causal effect: bucket, act and change date are confounded. Across all rows the 70B is 17 points ahead of the 8B (paired, 95 % CI 13–21, equally in DE, FR and IT); the 8B abstains more often (56–71 rows against 3–4).

Planned for v1.0.0: a full results table with C, I, NA, CGA, F, hallucination rate and penalised scores per model × language with intervals; stacked bars correct / stale / near miss / other / not attempted; judge–human κ.

## Dataset Limitations

Only federal law; cantonal rules (e.g. premium reductions) are excluded. A single annotator who is not a native Swiss speaker will review all items; French and Italian questions are machine-translated, although their gold answers come from the authentic texts. All questions so far were drafted by closed models (Claude, GPT-5.5, Gemini), disclosed per row, and human review is still pending; once hand-written items exist we report accuracy separately for hand-written and drafted items to detect drafting artefacts. The `temporal` bucket is determined per article, so an item can sit in an amended article whose paragraph did not change: only 39 of the 146 `changed_*` cores cite a sentence that changed, and only 19 carry an outdated answer (`src/find_changes.py`). The as-of date ages: the set needs a new version after each amendment (e.g. on 1 January 2027). The exposure check covers only the Swiss legislation subset of MultiLegalPile, not web crawls such as Nemotron-CC [@su2025nemotroncc] or FineWeb-2 [@penedo2025fineweb2]. Short answers measure knowledge, not the quality of advice.

## Lessons Learnt and Recommendations

For the dataset: yearly updates on 1 January, a cantonal extension, native-speaker review of French and Italian, more `temporal` items. For the model (from the preliminary run): a date in the system prompt does not make Apertus more current, so the fix has to come from data or retrieval: a refreshed legislation corpus, retrieval with a version filter instead of parametric recall [@prior2026oldfriend], and training abstention instead of rewarding guesses [@kalai2025hallucinate].

A practical lesson from building the grader: number extraction must treat indefinite articles (_un mois_, _eine Rente_), calendar dates, ordinals and units explicitly; a naive extractor counted refusals as wrong answers and accepted "three months" for "three weeks". The calibration set caught these errors before any judge or human grade was produced.

## Reproducibility

`make run` builds a Docker image (Python 3.12, no GPU, no API keys) and recomputes every reported number from the stored responses and judgements; it compares the result with `data/expected_results.json` and prints PASS or FAIL. `make run MODE=full` evaluates any OpenAI-compatible model given `LLM_*` (and grades with `JUDGE_*`). `make test` runs the unit tests. Seeds: 20261001 (generation, sampling of pilot cores), 20261016 (bootstrap, human sample). The commit and Hugging Face revision of v1.0.0 will be listed here at the freeze. The replay needs no GPU and no keys; on a clean checkout it finishes within a few minutes including the image build.

## License

This report and the documentation: CC-BY-4.0. Code: Apache-2.0. Dataset (questions, answers, metadata): CDLA-Permissive-2.0, licence stored per item in `metadata.jsonl`. Statute quotes: not protected by copyright (Art. 5 URG). The judge prompt adapts the SimpleQA grader of OpenAI simple-evals (MIT).

## References
