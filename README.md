# Inkraft — Swiss Legal Temporal & Factual Q&A Benchmark (Track 1B)

[![License: Apache-2.0](https://img.shields.io/badge/Code_License-Apache_2.0-blue.svg)](LICENSE)
[![Data License: CDLA-Permissive-2.0](https://img.shields.io/badge/Data_License-CDLA_Permissive_2.0-green.svg)](track_1b/data/LICENSE)
[![Docs License: CC-BY-4.0](https://img.shields.io/badge/Docs_License-CC_BY_4.0-lightgrey.svg)](LICENSE-docs)
[![Hack Apertus](https://img.shields.io/badge/Hack_Apertus-2026-red.svg)](https://hackapertus.ch/)

**Inkraft** is a trilingual factual and temporal benchmark evaluating large language models (specifically the Swiss open-weights Apertus model family) on Swiss federal social and health insurance law (KVG/KVV, AHVG, IVG, ELG, UVG, ATSG, OR) as of **1 October 2026**.

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

By default, `make run` executes the offline replay check without API credentials. The dataset is not frozen yet and no model has been evaluated, so `data/` holds no `expected_results.json`; until then the replay runs on the bundled 6-row test fixture (`track_1b/tests/fixtures/mini`) and only shows that scoring is reproducible.

### Live Evaluation (`MODE=full`)

To evaluate a live OpenAI-compatible Apertus endpoint:

```bash
export LLM_NAME="apertus-v1.5-8b"
export LLM_BASE_URL="https://your-apertus-endpoint.cscs.ch/v1"
export LLM_API_KEY="your-api-key"

# Optional judge endpoint (Qwen2.5 / Qwen3 recommended)
export JUDGE_NAME="Qwen/Qwen2.5-72B-Instruct"
export JUDGE_BASE_URL="https://api.together.xyz/v1"
export JUDGE_API_KEY="your-judge-key"

make run MODE=full
```

---

## 📦 Benchmark Structure

| Directory | Content |
| --- | --- |
| `track_1b/` | Official track root directory (contains `Makefile`, `run.sh`, `technical_report.md`) |
| `track_1b/src/inkraft/` | Python CLI and evaluation library (`generate`, `judge`, `score`, `human`, `contam`) |
| `track_1b/data/` | Benchmark draft (`test.jsonl`, `metadata.jsonl`); 303 LLM-drafted cores, human review pending, not frozen |
| `track_1b/docs/` | Dataset Card, annotation guidelines, and CLI usage documentation |
| `track_1b/src/*.py` | Dataset construction: `fetch_fedlex.py` (sources), `make_batches.py` / `build_items.py` / `assemble.py` (drafting), `validate_items.py`, `apply_review.py`, `find_changes.py` (version diff and sentence-level change check), `calibration_pilot.py` |
| `track_1b/report/` | Report build (`build.sh`, `build.ps1`), figure script and the aggregates of the preliminary run |
| `website/` | Project landing page and interactive report preview |

### Preliminary results (unreviewed draft)

One run on the unreviewed draft (879 rows, 2026-10-04), graded only by the rule-based pre-grade (no judge, no human check): Apertus 1.5 70B answers 52 % of rows correctly, 8B 35 %. On the 48 rows whose rule changed since 2024 only 6–10 % are correct, a date in the prompt does not help, and accuracy differs by exposure bucket (70B: 57 % with the current wording in the training corpus, 19 % with only the previous wording). Details and intervals in the technical report; final results follow on v1.0.0.

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
