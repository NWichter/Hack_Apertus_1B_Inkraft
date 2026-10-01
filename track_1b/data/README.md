# data/

Filled at the dataset freeze (v1.0.0). Until then `make run` checks itself on `tests/fixtures/mini`.

```
test.jsonl                                   evaluation items (question, gold answer, variants, outdated and near-miss answers)
metadata.jsonl                               provenance per item (fedlex ELI, verbatim quote, licence, authoring, canary)
responses/<model>__<condition>.jsonl         model responses
judgements/<judge>__<model>__<condition>.jsonl   judge grades with the rule-based pre-grade
human_labels/                                blind human labels for the 20 % sample
expected_results.json                        frozen scores; `make run` recomputes and compares them
```
