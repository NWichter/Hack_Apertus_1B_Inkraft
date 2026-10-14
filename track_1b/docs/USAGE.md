# Inkraft: evaluation package

`inkraft` is the evaluation code for the Inkraft dataset: short questions on Swiss federal social and
health insurance law (KVG/KVV/KLV, AHV/IV/EL, UVG/ATSG, EO/ALV, BVG, FamZG, OR 324a) in German, French and Italian, as of
1 October 2026. Every gold answer is backed by a verbatim fedlex quote. Grading follows SimpleQA
(correct / incorrect / not attempted), extended by the error subtypes `STALE` (the rule before an
amendment) and `NEAR_MISS` (a related but wrong value).

Python ≥ 3.11, no runtime dependencies (standard library only). Apache-2.0.

## Quick start

```sh
make run                 # Docker: recompute every reported number, compare with data/expected_results.json
make test                # Docker: unit tests
make run MODE=full LIMIT=50   # Docker: query LLM_* (and JUDGE_* if set), then score
```

Without Docker:

```sh
uv run inkraft replay                       # same as make run
uv run --with pytest python -m pytest -q    # tests
```

## Pipeline

| Step              | Command                                                                                            | Output                                                                      |
| ----------------- | -------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Split built items | `inkraft build <items.jsonl>`                                                                      | `data/test.jsonl`, `data/metadata.jsonl`                                    |
| Query a model     | `inkraft generate --condition closed_dated closed_plain open_book thinking`                        | `data/responses/<model>__<condition>.jsonl`                                 |
| Check the judge   | `inkraft calibrate`                                                                                | accuracy on 61 constructed answers; gate 0.95                               |
| Judge             | `inkraft judge [--judge-model M] [--judge-extra extra.json]`, once per panel judge                 | `data/judgements/<judge>__<model>__<condition>.jsonl`                       |
| Judge panel       | `python src/panel.py --judges <primary> <judge2> <judge3>`                                         | `data/judgements/panel__…`, `data/judge_panel.json` (Fleiss' κ)             |
| Score             | `inkraft score --judge-model panel --cluster --breakdowns --out data/results.json`                 | metrics with 95 % bootstrap intervals                                       |
| Human check       | `python src/draw_human_sample.py`, then `python src/import_human.py <export.json>` (or `inkraft label` / `inkraft agreement` in a terminal) | stratified samples of cores and judgements, item error rate, Cohen's κ against the first judge and the panel |
| Exposure check    | `inkraft contam --corpus <dir with *_legislation_switzerland_lexfind.jsonl.xz>`                    | evidence of current / previous version in the corpus; question 13-gram hits |
| Expected results  | `inkraft expect --judge-model panel`                                                               | `data/expected_results.json`                                                |
| Reproduce         | `inkraft replay`                                                                                   | PASS / FAIL                                                                 |

Environment: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_NAME` for the examinee; `JUDGE_BASE_URL`,
`JUDGE_API_KEY`, `JUDGE_NAME` for the judge. Both are OpenAI-compatible chat endpoints.

## Conditions

| Condition             | Prompt                                                                                                             |
| --------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `closed_dated` (main) | system prompt with the date (1 October 2026), "questions concern Swiss federal law", answer briefly, say if unsure |
| `closed_swiss`        | as `closed_dated` without the date (date effect)                                                                   |
| `closed_plain`        | the bare question, no system prompt                                                                                |
| `open_book`           | as `closed_dated`, plus the cited paragraph of the act                                                             |
| `thinking`            | as `closed_dated`, with Apertus' reasoning mode (`enable_thinking`); the reasoning is stored separately            |

Parameters: temperature 0, top_p 1, max_tokens 256 (3000 for `thinking`), seed 20261001.

## Grading

1. **Rule-based pre-grade** (`pregrade.py`): extracts numbers (digits, number words, ordinals, units)
   in DE/FR/IT, drops article references, calendar dates and percent words, compares durations in days,
   and detects refusals. Result: `match`, `mixed`, `stale`, `near_miss`, `conflict`, `abstain` or `none`.
   It is a hint for the judge and the basis for rule–human agreement.
2. **LLM judge panel** (`judge.py`, `src/panel.py`): open-weight models from families other than the
   examinee, SimpleQA rules, JSON output, temperature 0, prompt versioned (`JUDGE_PROMPT_VERSION`); every judge
   must pass the calibration gate; the majority grade counts, the first judge breaks ties.
3. **Human check** (`human.py`, `src/draw_human_sample.py`, `src/import_human.py`): a stratified random share
   of the judgements (by language × judge grade), labelled blind; κ against the first judge and the panel.

Without a judge, `score` falls back to the rule grade and reports which rows were graded how
(`grade_source`); rows the rules cannot decide stay ungraded. Rule-only numbers are provisional.

## Metrics

Correct, incorrect, not attempted; correct given attempted (CGA); SimpleQA F; hallucination rate
I / (C + I); share of stale errors; penalised score C − λ·I (λ = 1, 3); language consistency on cores
graded in all three languages; breakdowns by domain and question type. All with 95 % percentile
bootstrap intervals (1000 resamples, seed 20261016).

## Release pipeline (dataset v1.0.0)

```sh
python src/fetch_fedlex.py --out <fedlex> --cache <cache>             # sources (Fedlex SPARQL + filestore)
python src/find_changes.py --fedlex <fedlex> --out data/temporal       # version diff, buckets per evidence sentence
python src/gen_nemotron.py ... ; python src/check_candidates.py ...    # temporal candidates (open model) and checks
python src/auto_fix.py ... ; python src/auto_review.py ...             # logged release decisions
python src/second_check.py ...                                         # independent model check of every core
python src/after_review.py ... ; python src/freeze.py --rc ...         # release candidate
sh scripts/run_after_freeze.sh                                         # calibration, Apertus runs, judging
python src/draw_human_sample.py ...                                    # human samples (fixed seed)
EXPORT=... FEDLEX=... ENVFILE=... GO=1 sh scripts/after_human_check.sh # import, freeze v1.0.0, re-judge changed rows, rescore
python report/numbers.py                                               # every number in report, card, READMEs, website
sh scripts/hf_upload.sh                                                # Hugging Face release (dry run by default)
```
