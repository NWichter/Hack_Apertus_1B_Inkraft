# Inkraft — Swiss Legal Temporal & Factual Q&A Benchmark (Track 1B)

[![License: Apache-2.0](https://img.shields.io/badge/Code_License-Apache_2.0-blue.svg)](LICENSE)
[![Data License: CDLA-Permissive-2.0](https://img.shields.io/badge/Data_License-CDLA_Permissive_2.0-green.svg)](track_1b/data/LICENSE)
[![Docs License: CC-BY-4.0](https://img.shields.io/badge/Docs_License-CC_BY_4.0-lightgrey.svg)](LICENSE-docs)
[![Hack Apertus](https://img.shields.io/badge/Hack_Apertus-2026-red.svg)](https://hackapertus.ch/)

**Inkraft** is a trilingual factual and temporal benchmark evaluating large language models (specifically the Swiss open-weights Apertus model family) on Swiss federal social and health insurance law (19 acts and ordinances: KVG/KVV/KLV, AHVG/AHVV, IVG/IVV, ELG/ELV, UVG, ATSG, AVIG/AVIV, EOG, BVG/BVV, FamZG, OR) as of **1 October 2026**. Release candidate v1.0.0-rc1: 327 core questions (312 in all three languages, 15 German only), 951 rows, 53 STALE pairs.

Every question is anchored in a verified federal law provision ([fedlex.admin.ch](https://www.fedlex.admin.ch/)). Inkraft measures:
1. **Core Factuality & Hallucination Rate** across German, French, and Italian.
2. **Temporal Drift (`STALE`)**: Distinguishing genuinely outdated legal knowledge (from training cutoff) vs. invented answers.
3. **Cross-Lingual Consistency**: Evaluating whether parallel legal questions receive identical answers in all national languages.
4. **Training Corpus Contamination**: Verbatim and n-gram overlap checks against Swiss legal pretraining corpora (`Multi_Legal_Pile / switzerland_lexfind`).

Part of the **Apertool** submission suite for [Hack Apertus 2026](https://hackapertus.ch/).

---

## 🚀 Quickstart (`make run`)

Judges can run the reproducible benchmark directly via Docker on a clean checkout:

```bash
make run
```

By default, `make run` executes the offline replay without API credentials: it recomputes all eight result blocks (Apertus 1.5 8B and 70B × `closed_dated`, `open_book`, `closed_swiss`, `closed_plain`) from the stored responses and judgements in `track_1b/data/` and compares them with `track_1b/data/expected_results.json` (PASS/FAIL). Expected runtime: under a minute after the image build; no GPU, no keys.

### Live Evaluation (`MODE=full`)

To evaluate a live OpenAI-compatible Apertus endpoint:

```bash
export LLM_NAME="apertus-v1.5-8b"
export LLM_BASE_URL="https://your-apertus-endpoint.cscs.ch/v1"
export LLM_API_KEY="your-api-key"

# Optional judge endpoint (the reported results use Qwen3-235B-A22B-2507 via OpenRouter)
export JUDGE_NAME="qwen/qwen3-235b-a22b-2507"
export JUDGE_BASE_URL="https://openrouter.ai/api/v1"
export JUDGE_API_KEY="your-judge-key"

make run MODE=full
```

---

## 📦 Benchmark Structure

| Directory | Content |
| --- | --- |
| `track_1b/` | Official track root directory (contains `Makefile`, `run.sh`, `technical_report.md`) |
| `track_1b/src/inkraft/` | Python CLI and evaluation library (`generate`, `judge`, `score`, `human`, `contam`) |
| `track_1b/data/` | Release candidate v1.0.0-rc1 (`test.jsonl`, `metadata.jsonl`, `FREEZE.json`), model responses, judgements, `expected_results.json`, `results.json`; all rows `auto_verified`, human spot check in progress |
| `track_1b/docs/` | Dataset Card, annotation guidelines, and CLI usage documentation |
| `track_1b/src/*.py` | Dataset construction: `fetch_fedlex.py` (sources), `make_batches.py` / `build_items.py` / `assemble.py` (drafting), `validate_items.py`, `apply_review.py`, `find_changes.py` (version diff and sentence-level change check), `calibration_pilot.py` |
| `track_1b/src/*.py` (pipeline after drafting) | `gen_nemotron.py` (temporal candidates from version diffs, open model), `gen_proposals.py` (review proposals), `check_candidates.py`, `make_review_package.py`, `after_review.py` (apply the human review), `freeze.py` (v1.0.0), `hf_release.py` (dataset card and upload); `track_1b/scripts/run_after_freeze.sh` (judge calibration, runs, scoring, human sample) |
| `tools/review/` | Local review tool (`index.html`, no server): every core next to the statute text, decisions logged; loads the review package `track_1b/data/review/review_package.v1.jsonl`. Guide (German): `tools/review/ANLEITUNG.md`. `fedlex_texte.js` is built locally with `build_fedlex.py` and not committed |
| `track_1b/report/` | Report build (`build.sh`, `build.ps1`), `analysis.py` and `make_figures.py` (every number and the figure of the report) |
| `track_1b/src/*.py` (release candidate) | `auto_fix.py` (open-model fixes of candidate notes), `auto_review.py` (logged automatic decisions), `second_check.py` (independent check by Qwen3-235B), `make_check_file.py` / `import_human.py` (human spot check page and its analysis), `judge_agreement.py` |
| `website/` | Project landing page and interactive report preview; demo video embedded (`website/media/video.mp4`, subtitles `website/media/video.vtt`) |

### Results (v1.0.0-rc1, judge Qwen3-235B)

Apertus 1.5 70B answers 51.0 % of the 951 rows correctly (8B: 32.9 %). On the 157 rows of the 53 STALE pairs the 70B is correct in 7.6 % and gives the earlier law in 28.7 %; with the cited paragraph in the prompt (`open_book`) it is correct in 97.5 % of the same rows. On all 235 rows whose cited sentence changed since 2024 the 70B is correct in 17.0 % (8B: 10.6 %). A date in the system prompt does not change accuracy (German rows, exact McNemar p = 1.0 for the 70B). Details, intervals and limitations in `track_1b/technical_report.md`; numbers in `track_1b/data/results.json` and `track_1b/report/analysis.json`. The rows are automatically verified against Fedlex and by an independent model check; two human checks are in progress: a random sample of 35 dataset cores, and a blind re-grade of 211 judge grades (22 % of the 70B `closed_dated` run) for the human–judge κ.

---

## 🛠 Local CLI Installation

```bash
cd track_1b
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -e .
python -m pytest -q
```

---

## 📜 License

Licensed as required by the Hack Apertus [Terms & Conditions](https://hackapertus.ch/terms-and-conditions) (§ 6, "What you build is open source"):

| Part | License | File |
| --- | --- | --- |
| Code (`track_1b/src/`, `track_1b/tests/`, build and run scripts, website code) | Apache-2.0 | [`LICENSE`](LICENSE) |
| Documentation and technical report (`README.md`, `track_1b/docs/`, `track_1b/technical_report.md`, `track_1b/report/`, `Apertool_Report.pdf`) | CC-BY-4.0 | [`LICENSE-docs`](LICENSE-docs) |
| Submitted dataset (`track_1b/data/`: questions, answers, metadata; licence stored per item in `metadata.jsonl`) | CDLA-Permissive-2.0 | [`track_1b/data/LICENSE`](track_1b/data/LICENSE) |

Third-party material keeps its own licence and is not relicensed:

- **Swiss federal statute text** quoted from [fedlex.admin.ch](https://www.fedlex.admin.ch/) (`source.quote` in each item): not protected by copyright (Art. 5 para. 1 lit. a URG, SR 231.1); marked per item as `source.license: public-domain-ch-urg-art5`.
- **MultiLegalPile** (CC BY-NC-SA): used only locally for the exposure check, not redistributed.
- **SimpleQA grader** of [openai/simple-evals](https://github.com/openai/simple-evals) (MIT): the judge prompt adapts its grading rules.
- **Inter** font in `website/assets/fonts/` (SIL Open Font License 1.1, see `LICENSE-Inter.txt`).

## 📖 Citation

```bibtex
@misc{apertool2026inkraft,
  title={Inkraft: A Trilingual Benchmark for Temporal and Factual Knowledge in Swiss Federal Law},
  author={Wichter, Niklas and Team Apertool},
  year={2026},
  howpublished={\url{https://inkraft.apertool.ch}},
  note={Hack Apertus 2026 Submission}
}
```
