# data/

License: CDLA-Permissive-2.0 (see [`LICENSE`](LICENSE)) for our questions, answers and metadata, stored per item in the `license` field. Quoted federal statute text (`source.quote`) is public domain under Art. 5 para. 1 lit. a URG (`source.license: public-domain-ch-urg-art5`) and is not relicensed.

Current state: release candidate **v1.0.0-rc1** (`FREEZE.json`, 2026-10-13): 327 German cores / 951 rows (`cl-` Claude, `cx-` GPT-5.5 via Codex, `ag-` Gemini via an Antigravity agent, `nm*-` Nemotron 3 Ultra), every row `status: auto_verified`, `needs_human_review: true` until the human spot check. `make run` replays `expected_results.json` from `responses/` and `judgements/`.

```
merged.v1.jsonl                              all rows with every field (source of test.jsonl + metadata.jsonl, `inkraft build`)
antigravity.compact.jsonl / .expanded.jsonl  original Gemini drafts of the ag- cores before review v2 (formerly handwritten.*; mislabelled as human until 2026-10-03)
review_v2.json                               review decisions applied with src/apply_review.py
validation_report.v1.md                      output of src/validate_items.py on merged.v1.jsonl
sources/fedlex_manifest.v2.json              fedlex retrieval (src/fetch_fedlex.py): ELI and HTML URLs, SHA-256 per act, version and language;
                                             13 acts of 2026-10-01 plus AHVV, IVV, ELV, AVIV of 2026-10-04 (retrieved_at_per_act)
review_v3_cx0063.json                        rewrite of cx-0063 (circular question, decision N3), applied with src/apply_review.py
temporal/                                    src/find_changes.py output: sentence_buckets.json (bucket per evidence sentence over all
                                             stored versions), sentence_stability.json, diffpool.json, amount_candidates.json
candidates/                                  NOT part of the dataset (candidate.merged: false, needs_human_review: true):
  nemotron-pilot/                            pilot of 2026-10-04 (19 Ultra + 18 Super cores)
  nemotron-v2/                               temporal candidates from version diffs (src/gen_nemotron.py, prompt src/prompts/nemotron_temporal_v2.txt)
  review-v3/                                 review proposals for existing cores (src/gen_proposals.py): yes/no -> open question,
                                             missing variants (Nemotron), cluster and duplicate drops (rules)
  checks/                                    automatic checks and tiers of all candidates (src/check_candidates.py)
review/review_package.v1.jsonl               review package for tools/review (src/make_review_package.py): existing cores + candidates,
                                             ranked, with hints; summary in review_package.v1.md
```

After the human review (exports of `tools/review` into `review/`): `src/after_review.py` applies the decisions
to the dataset and the accepted candidates and writes `merged.v2.jsonl`; `src/freeze.py --go` freezes v1.0.0;
`scripts/run_after_freeze.sh` runs judge calibration, Apertus runs, scoring and the 20 % sample;
`src/hf_release.py` builds the Hugging Face card and uploads.

Release candidate files (2026-10-13):

```
merged.v1.0.0-rc1.jsonl                      frozen rows with every field (review block per row); test.jsonl + metadata.jsonl are built from it
FREEZE.json                                  version, SHA-256 of the files, statistics, review status
validation_report.v1.0.0-rc1.md              validator in frozen mode: 0 errors, 216 warnings
contamination.jsonl / .summary.json          exposure check against MultiLegalPile switzerland_lexfind
ablation_cores.txt                           core list of the ablation subset written by freeze.py
review/auto/                                 automatic decisions and log (src/auto_review.py); review/second_check.jsonl (Qwen3-235B)
candidates/auto-fix/                         Nemotron fixes of the candidate notes (src/auto_fix.py), raw outputs
candidates/nemotron-v3/                      four candidates from FamZG, EOV and KLV (2026-10-13)
judge_calibration*.json                      judge calibration (Qwen3-235B, Apertus-70B for comparison)
judge_agreement_qwen_vs_apertus70b.json      agreement of the two judges (diagnostic)
results.json                                 inkraft score --cluster --breakdowns
human_labels/                                human spot check: dataset_sample.jsonl, sample_20pct.jsonl, sample_meta.json
```

Layout:

```
test.jsonl                                   evaluation items (question, gold answer, variants, outdated and near-miss answers)
metadata.jsonl                               provenance per item (fedlex ELI, verbatim quote, licence, authoring, canary)
responses/<model>__<condition>.jsonl         model responses
judgements/<judge>__<model>__<condition>.jsonl   judge grades with the rule-based pre-grade
human_labels/                                blind human labels for the 20 % sample
expected_results.json                        frozen scores; `make run` recomputes and compares them
```
