# Nemotron pilot (candidates only)

Pilot of 2026-10-04: can an open model draft temporal items from fedlex version diffs? **Nothing in this folder is part of the dataset.** `merged.v1.jsonl`, `test.jsonl` and `metadata.jsonl` are unchanged. Every row has `status: draft`, `needs_human_review: true`, `candidate.merged: false`.

## What was done

1. Paragraph-level diff of the current vs. previous consolidated version of 13 acts (fedlex-v2, as of 2026-10-01). 19 changed paragraphs that no existing core covers were picked by hand from the diff list (`targets.json`, with `change_kind`): 5 amounts/rates/periods, 14 rule changes.
2. One OpenRouter call per paragraph with `prompt_nemotron_pilot_v1.txt` (current and previous paragraph in DE/FR/IT). Main model `nvidia/nemotron-3-ultra-550b-a55b:free`, comparison run `nvidia/nemotron-3-super-120b-a12b:free`. Temperature 0.3, provider reasoning left on.
3. Compact output expanded with `src/build_items.py` (source metadata from fedlex, never from the model): IDs `nmu-` (Ultra) and `nms-` (Super), `generator: nemotron`, model ID, `generated_at`, `prompt_version`.
4. Checked with the unchanged `src/validate_items.py` (`validate_candidates.py` only adds `nemotron` to the allowed authors) and against `merged.v1.jsonl` for duplicates.
5. Agent pre-assessment of the Ultra cores against the annotation guidelines (`assessment.ultra.json`). This is not a human review.

## Results

| | Ultra | Super |
| --- | --- | --- |
| Parsed cores | 19/19 | 18/19 (one output cut at 8000 tokens) |
| Cores without validator errors | 17/19 | 16/18 |
| Duplicates against merged.v1 | 0 | 0 |
| Agent verdict | 6 accept, 5 accept with minor fix, 6 revise, 2 reject | not assessed in detail; many answers are full sentences copied from the statute or circular |
| Tokens (prompt / completion) | 32k / 74k | 32k / 66k |
| Cost | 0 USD (free tier); ≈ 0.18 USD at paid prices | 0 USD |
| Wall time | 1138 s (≈ 60 s per core) | 596 s |
| Rate limits | none hit (all first attempt) | none hit |

Lessons for prompt v2: forbid answers that repeat words of the question; an outdated answer must answer the same question (otherwise use a non-temporal type); never put a value of the current version into the question when that value also changed; one-word or number answers with unit; check terms against the statute (e.g. "Erwerbsersatzordnung").

## Files

| File | Content |
| --- | --- |
| `targets.json` | 19 changed paragraphs with `change_kind` |
| `prompt_nemotron_pilot_v1.txt` | prompt template |
| `gen_nemotron_pilot.py` | generator (reads `OPENROUTER_API_KEY` from an .env file with a parser, never prints it) |
| `raw/<tag>/` | raw model output per call with usage and latency (reasoning text not stored, only its length) |
| `compact.<tag>.jsonl`, `candidates.<tag>.jsonl` | compact and expanded candidates |
| `run_log.<tag>.json` | per-call log (tokens, cost, latency, attempts) |
| `validate_candidates.py`, `validation.<tag>.md`, `issues.<tag>.json`, `duplicates_vs_merged.<tag>.json` | validator output |
| `assessment.ultra.json` | agent pre-assessment per core |

Reproduce: `python gen_nemotron_pilot.py --fedlex <fedlex-v2> --env <.env> --tag ultra`, then `python validate_candidates.py --fedlex <fedlex-v2> --tag ultra`.

The Ultra candidates were also sent once to Apertus 8B/70B (closed_dated) in a calibration pilot. If any of them enters the dataset, the decision must rest on the review, never on those responses.
