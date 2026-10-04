# data/

License: CDLA-Permissive-2.0 (see [`LICENSE`](LICENSE)) for our questions, answers and metadata, stored per item in the `license` field. Quoted federal statute text (`source.quote`) is public domain under Art. 5 para. 1 lit. a URG (`source.license: public-domain-ch-urg-art5`) and is not relicensed.

Current state: draft, not frozen. 303 German cores / 879 rows, all drafted by LLMs (`cl-` Claude, `cx-` GPT-5.5 via Codex, `ag-` Gemini via an Antigravity agent), every row `status: draft`, `needs_human_review: true`. No responses, judgements or `expected_results.json` yet, so `make run` checks itself on `tests/fixtures/mini`.

```
merged.v1.jsonl                              all rows with every field (source of test.jsonl + metadata.jsonl, `inkraft build`)
antigravity.compact.jsonl / .expanded.jsonl  original Gemini drafts of the ag- cores before review v2 (formerly handwritten.*; mislabelled as human until 2026-10-03)
review_v2.json                               review decisions applied with src/apply_review.py
validation_report.v1.md                      output of src/validate_items.py on merged.v1.jsonl
```

Planned after the freeze:

```
test.jsonl                                   evaluation items (question, gold answer, variants, outdated and near-miss answers)
metadata.jsonl                               provenance per item (fedlex ELI, verbatim quote, licence, authoring, canary)
responses/<model>__<condition>.jsonl         model responses
judgements/<judge>__<model>__<condition>.jsonl   judge grades with the rule-based pre-grade
human_labels/                                blind human labels for the 20 % sample
expected_results.json                        frozen scores; `make run` recomputes and compares them
```
