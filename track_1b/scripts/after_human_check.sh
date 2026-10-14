#!/bin/sh
# After the human spot check: import the export of the check page, drop rejected cores, add the panel-derived
# answer variants (checked against the cited paragraph), freeze v1.0.0 (needs GO=1: the curator's decision),
# re-judge only the rows whose variants changed, and recompute every score from the stored Apertus answers.
#
#   EXPORT=<export.json> FEDLEX=<fedlex-v2 dir> ENVFILE=<.env> [CORPUS=<multilegalpile dir>] GO=1 sh scripts/after_human_check.sh
#
# report/fill_numbers.py then writes every number into the report, the data card, the READMEs and the project page;
# rebuild the PDF, then scripts/hf_upload.sh (dry run; upload only after the curator's go).
set -eu
cd "$(dirname "$0")/.."
: "${EXPORT:?set EXPORT}" "${FEDLEX:?set FEDLEX}" "${ENVFILE:?set ENVFILE}"
PRIMARY="qwen/qwen3-235b-a22b-2507"
PANEL="${PANEL:-qwen/qwen3-235b-a22b-2507 z-ai/glm-5.3 deepseek/deepseek-v3.2}"
export PYTHONPATH=src

python src/import_human.py "$EXPORT" --judge-model "$PRIMARY" --also panel
python src/auto_review.py --out data/review/auto \
  --validator-issues data/review/auto/validator_issues.pass1.json \
  --second-check data/review/second_check.jsonl \
  --human-log data/review/human_check_log.jsonl
python src/after_review.py --fedlex "$FEDLEX" --decisions data/review/auto/review_decisions.json \
  --log data/review/auto/review_log.jsonl --out data/merged.v2.jsonl
python src/panel_fixes.py --env "$ENVFILE" --src data/merged.v2.jsonl
python src/apply_review.py data/review/panel_fixes.json data/merged.v2.jsonl data/review/_merged.v2.fixed.jsonl
mv data/review/_merged.v2.fixed.jsonl data/merged.v2.jsonl

[ "${GO:-0}" = 1 ] || { echo "stop before the freeze: set GO=1 when the curator decides" >&2; exit 0; }
python src/freeze.py --fedlex "$FEDLEX" --go --version 1.0.0 ${CORPUS:+--corpus "$CORPUS"}
python src/rejudge_changed.py --env "$ENVFILE" --judges $PANEL
python src/panel.py --judges $PANEL
python -m inkraft --data data score --cluster --breakdowns --judge-model panel --out data/results.json
python -m inkraft --data data expect --judge-model panel --note "v1.0.0 runs, judge panel majority ($PANEL); ablation rows judged by $PRIMARY"
python -m inkraft --data data replay
python report/analysis.py --judge-model panel
python report/make_figures.py --judge-model panel
python report/fill_numbers.py
