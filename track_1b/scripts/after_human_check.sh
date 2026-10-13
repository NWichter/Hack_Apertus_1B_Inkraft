#!/bin/sh
# After the human spot check: import the export of the check page, drop rejected cores, freeze v1.0.0
# (needs GO=1: the curator's decision) and recompute every score from the stored responses (no model calls).
#
#   EXPORT=<inkraft-pruefung-*.json> FEDLEX=<fedlex-v2 dir> [CORPUS=<multilegalpile dir>] GO=1 sh scripts/after_human_check.sh
#
# Afterwards: update the numbers in technical_report.md and docs/DATA_CARD.md from report/analysis.json,
# rebuild the PDF, `python src/hf_release.py card --repo <owner/name>`, upload only after the curator's go.
set -eu
cd "$(dirname "$0")/.."
: "${EXPORT:?set EXPORT}" "${FEDLEX:?set FEDLEX}"
JUDGE="${JUDGE_NAME:-qwen/qwen3-235b-a22b-2507}"
export PYTHONPATH=src

python src/import_human.py "$EXPORT" --judge-model "$JUDGE"
python src/auto_review.py --out data/review/auto \
  --validator-issues data/review/auto/validator_issues.pass1.json \
  --second-check data/review/second_check.jsonl \
  --human-log data/review/human_check_log.jsonl
python src/after_review.py --fedlex "$FEDLEX" --decisions data/review/auto/review_decisions.json \
  --log data/review/auto/review_log.jsonl --out data/merged.v2.jsonl

[ "${GO:-0}" = 1 ] || { echo "stop before the freeze: set GO=1 when the curator decides" >&2; exit 0; }
python src/freeze.py --fedlex "$FEDLEX" --go --version 1.0.0 ${CORPUS:+--corpus "$CORPUS"}
python -m inkraft --data data score --cluster --breakdowns --judge-model "$JUDGE" --out data/results.json
python -m inkraft --data data expect --judge-model "$JUDGE" --note "v1.0.0 runs (closed_dated, open_book; ablation closed_swiss/closed_plain on German rows), judge $JUDGE"
python -m inkraft --data data replay
python report/analysis.py --judge-model "$JUDGE"
python report/make_figures.py --judge-model "$JUDGE"
