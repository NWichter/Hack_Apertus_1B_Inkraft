# Inkraft — does Apertus know the law in force? (Hack Apertus 2026, Track 1B)

[![Code: Apache-2.0](https://img.shields.io/badge/Code-Apache_2.0-blue.svg)](LICENSE)
[![Data: CDLA-Permissive-2.0](https://img.shields.io/badge/Data-CDLA_Permissive_2.0-green.svg)](track_1b/data/LICENSE)
[![Docs: CC-BY-4.0](https://img.shields.io/badge/Docs-CC_BY_4.0-lightgrey.svg)](LICENSE-docs)

**Inkraft** is a trilingual (German, French, Italian) short-answer benchmark on Swiss federal social and health
insurance law as of **1 October 2026** (dimension: Core Task Intelligence). Release v<!--n:version-->1.0.0-rc1<!--/n-->:
<!--n:cores-->327<!--/n--> core questions (<!--n:trilingual-->312<!--/n--> in all three languages, <!--n:de_only-->15<!--/n--> German only), <!--n:rows-->951<!--/n--> question–answer
rows from <!--n:acts-->19<!--/n--> acts and ordinances. Every gold answer is backed by a verbatim quote from the authentic Fedlex text (calculation and yes/no answers are
derived from the quoted values; the validator recomputes calculations); for
<!--n:stale_pairs-->53<!--/n--> amended provisions the previous answer is stored verbatim from the earlier version, so a wrong answer
can be classed as _stale_ (earlier law) rather than invented.

**Results** (Apertus 1.5, majority of a panel of <!--n:panel_size-->3<!--/n--> open-weight judges):
the 70B answers <!--n:correct_70b-->50.7<!--/n--> % of the rows correctly (8B: <!--n:correct_8b-->33.0<!--/n--> %). On the <!--n:stale_rows-->157<!--/n--> rows whose rule
changed and whose earlier answer is stored, the 70B is correct in <!--n:stalepair_correct_70b-->7.0<!--/n--> % and gives the earlier law in
<!--n:stalepair_stale_70b-->29.9<!--/n--> %; with the cited paragraph in the prompt it is correct in <!--n:openbook_stalepair_70b-->98.7<!--/n--> %. A date in the
as-of date in the system prompt does not change accuracy significantly (German rows). <!--when:human:offHuman check: Cohen's κ human–judge <!~~n:kappa_qwen~~>pending (human check in progress – results on 16 October)<!~~[[NIKLAS-PRÜFUNG: kappa_qwen]]~~><!~~/n~~>
(panel majority <!~~n:kappa_panel~~>pending (human check in progress – results on 16 October)<!~~[[NIKLAS-PRÜFUNG: kappa_panel]]~~><!~~/n~~>) on <!~~n:judge_sample~~>211<!~~/n~~> judgements of the 70B main run;
<!~~n:human_drops~~>pending (human check in progress – results on 16 October)<!~~[[NIKLAS-PRÜFUNG: human_drops]]~~><!~~/n~~> of <!~~n:sample_cores~~>35<!~~/n~~> sampled cores rejected and removed./when:human:off--><!--when:pending-->Human check of
<!--n:judge_sample-->211<!--/n--> judgements of the 70B main run and <!--n:sample_cores-->35<!--/n--> sampled cores: in progress, results with release v1.0.0.<!--/when:pending-->

## For the jury: where to look

1. **Technical report:** [`track_1b/Apertool_Report.pdf`](track_1b/Apertool_Report.pdf) (source: `track_1b/technical_report.md`).
2. **Data card:** [`track_1b/docs/DATA_CARD.md`](track_1b/docs/DATA_CARD.md) <!--when:hf:off(also the Hugging Face card: <!~~n:hf_url~~>Hugging Face link follows on 16 October<!~~[[NIKLAS-PRÜFUNG: hf_url]]~~><!~~/n~~>)/when:hf:off--><!--when:nohf-->(also the Hugging Face card; link follows after the upload)<!--/when:nohf-->.
3. **Reproduce:** `make run` and `make test` (below).
4. **Data:** `track_1b/data/` — `test.jsonl`, `metadata.jsonl`, `responses/`, `judgements/`, `human_labels/`,
   `expected_results.json`, `FREEZE.json` (file hashes); see [`track_1b/data/README.md`](track_1b/data/README.md).
5. **Code:** `track_1b/src/inkraft/` (evaluation package), `track_1b/src/*.py` (dataset construction and checks),
   usage in [`track_1b/docs/USAGE.md`](track_1b/docs/USAGE.md).

## Reproduce

Requirements: Docker and GNU make. **Runtime** a few minutes (image build) plus seconds for the replay;
**hardware** any laptop, no GPU; **API keys** none for the replay; **model weights** none (the stored Apertus answers
are replayed).

```bash
make run     # replay: recompute every result block from the stored answers and grades, compare with expected_results.json -> PASS/FAIL
make test    # unit tests in the same image
```

Evaluate another model or rerun Apertus (OpenAI-compatible endpoint; the judges are graded the same way):

```bash
export LLM_BASE_URL=https://…/v1 LLM_API_KEY=… LLM_NAME=apertus-v1.5-70b
export JUDGE_BASE_URL=https://openrouter.ai/api/v1 JUDGE_API_KEY=… JUDGE_NAME=qwen/qwen3-235b-a22b-2507
make run MODE=full LIMIT=50   # LIMIT for a smoke test; without JUDGE_* the rule pre-grade is used (provisional)
```

The full pipeline (Fedlex download → version diff → drafting → checks → human sample → freeze → runs → panel →
scores) is described in the report, section Reproducibility, and in `track_1b/docs/USAGE.md`.

## Repository layout

| Path | Content |
| --- | --- |
| `Makefile` | `make run`, `make test` (delegate to `track_1b/Makefile`) |
| `track_1b/` | official track directory: `Makefile`, `Dockerfile`, `run.sh`, `technical_report.md`, `Apertool_Report.pdf` |
| `track_1b/src/inkraft/` | evaluation package and CLI (`generate`, `judge`, `calibrate`, `score`, `replay`, `expect`, `contam`, `agreement`) |
| `track_1b/src/` | dataset construction (`fetch_fedlex.py`, `find_changes.py`, `make_batches.py`, `build_items.py`, `gen_nemotron.py`, `validate_items.py`), release checks (`auto_fix.py`, `auto_review.py`, `second_check.py`, `after_review.py`, `panel_fixes.py`, `freeze.py`), human check (`draw_human_sample.py`, `translate_sample.py`, `import_human.py`), judge panel (`panel.py`, `rejudge_changed.py`, `judge_agreement.py`), release (`hf_release.py`) |
| `track_1b/scripts/` | `run_after_freeze.sh` (calibration, runs, judging), `after_human_check.sh` (import, freeze, rescoring), `hf_upload.sh` (Hugging Face release, dry run by default) |
| `track_1b/report/` | report build (`build.sh`, `build.ps1`), `analysis.py`, `make_figures.py`, `fill_numbers.py` (every number in the documents) |
| `track_1b/tests/` | unit tests and the replay fixture |
| `website/` | project page https://inkraft.apertool.ch with pitch and demo video |

## License

| Part | License | File |
| --- | --- | --- |
| Code (`track_1b/src/`, `track_1b/tests/`, build and run scripts, website code) | Apache-2.0 | [`LICENSE`](LICENSE) |
| Documentation and technical report | CC-BY-4.0 | [`LICENSE-docs`](LICENSE-docs) |
| Dataset (`track_1b/data/`: questions, answers, metadata; licence stored per item) | CDLA-Permissive-2.0 | [`track_1b/data/LICENSE`](track_1b/data/LICENSE) |

Third-party material keeps its own licence: Swiss federal statute text (not protected by copyright, Art. 5 para. 1
lit. a URG; marked per item as `source.license: public-domain-ch-urg-art5`); MultiLegalPile (CC BY-NC-SA, used only
locally for the exposure check, not redistributed); SimpleQA grader of openai/simple-evals (MIT, adapted judge
prompt); Inter font in `website/assets/fonts/` (SIL OFL 1.1).

## Citation

```bibtex
@misc{apertool2026inkraft,
  title={Inkraft: A Trilingual Benchmark for Temporal and Factual Knowledge in Swiss Federal Law},
  author={Wichter, Niklas and Team Apertool},
  year={2026},
  howpublished={\url{https://inkraft.apertool.ch}},
  note={Hack Apertus 2026 Submission}
}
```
