# Inkraft — Swiss Legal Temporal & Factual Q&A Benchmark (Track 1B)

[![License: Apache-2.0](https://img.shields.io/badge/Code_License-Apache_2.0-blue.svg)](LICENSE)
[![Data License: CDLA-Permissive-2.0](https://img.shields.io/badge/Data_License-CDLA_Permissive_2.0-green.svg)](https://cdla.dev/permissive-2-0/)
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
| `website/` | Project landing page and interactive report preview |

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

## 📜 Licenses & Citation

- **Code:** [Apache-2.0](LICENSE)
- **Dataset:** [CDLA-Permissive-2.0](https://cdla.dev/permissive-2-0/)
- **Statutory Source Texts:** Public domain according to Art. 5 Swiss Federal Act on Copyright (URG).

```bibtex
@misc{apertool2026inkraft,
  title={Inkraft: A Trilingual Benchmark for Temporal and Factual Knowledge in Swiss Federal Law},
  author={Wichter, Niklas and Team Apertool},
  year={2026},
  howpublished={\url{https://inkraft.apertool.ch}},
  note={Hack Apertus 2026 Submission}
}
```
