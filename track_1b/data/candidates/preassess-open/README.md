# Open-model repeat of the candidate pre-assessment (2026-10-14)

The pre-assessment of the 156 Nemotron candidates (2026-10-04, `nemotron-v2/assessment.json`,
`nemotron-pilot/assessment.ultra.json`) was done by claude-opus-5-5 agents. It was repeated with two open models,
same candidates, same criteria and verdict scale (prompt `src/prompts/preassess_v1.txt`, recovered from the
original agent instructions; script `src/preassess_open.py`). Nothing in the dataset was changed.

| Rater pair (n = 156) | 4 classes: agreement / κ | keep vs reject: agreement / κ |
| --- | --- | --- |
| claude-opus-5-5 vs Qwen3-235B-A22B-2507 | 0.256 / 0.108 | 0.474 / 0.051 |
| claude-opus-5-5 vs Nemotron 3 Ultra | 0.269 / 0.114 | 0.519 / 0.119 |
| Qwen3-235B vs Nemotron 3 Ultra | 0.590 / 0.439 | – |

Verdicts: claude accept 15, accept_minor 26, revise 28, reject 87; Qwen 37 / 65 / 49 / 5; Nemotron 76 / 32 / 32 / 16
(Nemotron also drafted the candidates). The open models are far more lenient: of the 28 candidates that the original
pre-assessment rejected because the change is only a renaming (e.g. "ordentliches Rentenalter" → "Referenzalter"),
Qwen accepted 7, asked for a minor fix on 16 and a revision on 5, although criterion 3 excludes such changes.
None of the 46 candidates in v1.0.0-rc1 is rejected by Qwen; Nemotron rejects one.

Files: `assessment.jsonl` and `comparison.json` (confusion matrix, all disagreements with both reasons) per model
in this folder (Qwen, cost 0.042 USD) and in `../preassess-open-nemotron/` (free); `variant_b.json` lists what
would change if only the open model counted (`src/preassess_variant_b.py`).
