# Inkraft: evaluation package

`inkraft` is the evaluation code for the Inkraft dataset: short questions on Swiss federal social and
health insurance law (KVG, AHV/IV/EL, UVG/ATSG, EO, OR 324a) in German, French and Italian, as of
1 October 2026. Every gold answer is quoted from fedlex. Grading follows SimpleQA
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
| Judge             | `inkraft judge`                                                                                    | `data/judgements/<judge>__<model>__<condition>.jsonl`                       |
| Score             | `inkraft score --out results.json`                                                                 | metrics with 95 % bootstrap intervals                                       |
| Human check       | `inkraft sample-human`, `inkraft label --annotator <name>`, `inkraft agreement --annotator <name>` | 20 % stratified blind sample, Cohen's κ                                     |
| Exposure check    | `inkraft contam --corpus <dir with *_legislation_switzerland_lexfind.jsonl.xz>`                    | evidence of current / previous version in the corpus; question 13-gram hits |
| Freeze            | `inkraft expect --judge-model <judge>`                                                             | `data/expected_results.json`                                                |
| Reproduce         | `inkraft replay`                                                                                   | PASS / FAIL                                                                 |

Environment: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_NAME` for the examinee; `JUDGE_BASE_URL`,
`JUDGE_API_KEY`, `JUDGE_NAME` for the judge. Both are OpenAI-compatible chat endpoints.

## Conditions

| Condition             | Prompt                                                                                                             |
| --------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `closed_dated` (main) | system prompt with the date (1 October 2026), "questions concern Swiss federal law", answer briefly, say if unsure |
| `closed_plain`        | the bare question, no system prompt                                                                                |
| `open_book`           | as `closed_dated`, plus the cited paragraph of the act                                                             |
| `thinking`            | as `closed_dated`, with Apertus' reasoning mode (`enable_thinking`); the reasoning is stored separately            |

Parameters: temperature 0, top_p 1, max_tokens 256 (3000 for `thinking`), seed 20261001.

## Grading

1. **Rule-based pre-grade** (`pregrade.py`): extracts numbers (digits, number words, ordinals, units)
   in DE/FR/IT, drops article references, calendar dates and percent words, compares durations in days,
   and detects refusals. Result: `match`, `mixed`, `stale`, `near_miss`, `conflict`, `abstain` or `none`.
   It is a hint for the judge and the basis for rule–human agreement.
2. **LLM judge** (`judge.py`): a model from a different family than the examinee, SimpleQA rules,
   JSON output, temperature 0. The prompt is versioned (`JUDGE_PROMPT_VERSION`).
3. **Human check** (`human.py`): 20 % of every model × condition, stratified by language × judge
   grade (seed 20261016), labelled blind (the judge grade is never shown).

Without a judge, `score` falls back to the rule grade and reports which rows were graded how
(`grade_source`); rows the rules cannot decide stay ungraded. Rule-only numbers are provisional.

## Metrics

Correct, incorrect, not attempted; correct given attempted (CGA); SimpleQA F; hallucination rate
I / (C + I); share of stale errors; penalised score C − λ·I (λ = 1, 3); language consistency on cores
graded in all three languages; breakdowns by domain and question type. All with 95 % percentile
bootstrap intervals (1000 resamples, seed 20261016).
