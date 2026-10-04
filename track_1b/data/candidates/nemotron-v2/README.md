# Nemotron temporal candidates v2 (candidates only)

Second batch of temporal candidates, 2026-10-04. **Nothing in this folder is part of the dataset.** Every row has
`status: draft`, `needs_human_review: true`, `candidate.merged: false`; a core enters the dataset only through a
human review decision (`src/after_review.py`).

## What was done

1. `src/find_changes.py --targets 140` ranked every changed, uncovered paragraph of 17 acts and ordinances (13 acts plus
   AHVV, IVV, ELV, AVIV) by how likely it gives a clean pair of current and outdated answer (amounts and rates first,
   then changed numbers, then changed rules; administrative paragraphs down-weighted; at most 2 per article and 22 per
   act; the 19 pilot paragraphs excluded). Result: `targets.json`.
2. One OpenRouter call per paragraph with `src/prompts/nemotron_temporal_v2.txt` (current paragraph and up to three
   distinct earlier wordings, previous **and** intermediate versions, each in DE/FR/IT). Model
   `nvidia/nemotron-3-ultra-550b-a55b:free`, temperature 0.3, `max_tokens` 9000; 40 outputs were cut by the token
   limit (reasoning) and regenerated with `max_tokens` 24000 and `reasoning.effort: medium` (`settings` in `raw/`).
3. `src/build_items.py` adds source, version and quote from fedlex (never from the model). Outdated answers are located
   in the stored earlier versions (`temporal.outdated_versions`, `evidence_found`); the bucket is set per evidence
   sentence (`temporal.bucket_level: sentence`). Near misses equal to an outdated value were removed by rule and logged
   in `authoring.manual_correction`.
4. `src/check_candidates.py` (validator, duplicates against merged.v1 and among candidates, quote verbatim, outdated
   evidence verbatim in an earlier version, provenance) → `../checks/`.
5. Agent pre-assessment (claude-opus-5-5, three parallel readers, not a human review) → `assessment.json`. The review
   tool hides it until the reviewer has decided.

## Results

| | |
| --- | ---: |
| Targets | 140 |
| Parsed cores (DE/FR/IT) | 137 (98 %) |
| Without validator error | 119 |
| Clean STALE pair (temporal, outdated evidence found, no error) | 79 |
| Yes/no | 4 (3 %) |
| Duplicates | 2 |
| Provenance complete (generator, model, date, prompt version with hash, `needs_human_review`) | 137 |
| Agent pre-assessment | accept 9, accept with minor fix 21, revise 22, reject 85 |
| Usable after pre-assessment (accept + minor) | 30 (22 % of targets) |
| Of these with a STALE pair | 16 (+ 15 among "revise") |
| Tokens prompt / completion | 287k / 919k |
| Cost | 0 USD (free tier) |
| Wall time | ≈ 100 min at 4–6 parallel calls (≈ 150 s per call) |

Main reject reasons: the "change" is a renamed term only (ordentliches Rentenalter → Referenzalter in AHV 21,
Vaterschaftsurlaub → Urlaub des andern Elternteils, Kasse → Arbeitslosenkasse, Bundesamt → BSV), the answer is an
article reference, the question asks for an item of a list, administrative detail. `src/find_changes.py` now unifies
these renamed terms before ranking; the remaining diff pool holds few further amount or rule changes.

## Files

| File | Content |
| --- | --- |
| `targets.json` | ranked paragraphs with `change_kind` and score |
| `raw/` | raw model output per call (content, usage, latency, settings; reasoning not stored, only its length) |
| `compact.jsonl`, `candidates.jsonl` | compact and expanded candidates (`nmv-` IDs) |
| `run_log.json`, `run.out`, `retry*.out` | per-call log |
| `assessment.json` | agent pre-assessment per core |

Reproduce: `python src/gen_nemotron.py --fedlex <fedlex-v2> --env <.env> --targets data/candidates/nemotron-v2/targets.json --out data/candidates/nemotron-v2`,
then `--only <failed numbers> --max-tokens 24000 --reasoning-effort medium`, then `--build-only`.
