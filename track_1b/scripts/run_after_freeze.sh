#!/bin/sh
# Runs after a freeze (FREEZE.json): judge calibration, Apertus 8B/70B runs, ablation, judge, score,
# expected results and the human sample page. Each step resumes where it stopped.
#
# Needs: LLM_BASE_URL, LLM_API_KEY (Apertus endpoint); JUDGE_BASE_URL, JUDGE_API_KEY, JUDGE_NAME.
# Optional: MODELS (default "apertus-v1.5-8b apertus-v1.5-70b"),
#           STEP (calibrate|generate|ablation|judge|score|sample|all, default all).
# Apertus calls: 2 conditions x rows x models (closed_dated, open_book) + 2 x German rows x models (ablation).
set -eu
cd "$(dirname "$0")/.."
DATA=data
MODELS="${MODELS:-apertus-v1.5-8b apertus-v1.5-70b}"
STEP="${STEP:-all}"
INKRAFT="python -m inkraft --data $DATA"
export PYTHONPATH="${PYTHONPATH:-}:src"

[ -f "$DATA/FREEZE.json" ] || { echo "no data/FREEZE.json: run src/freeze.py first" >&2; exit 2; }
: "${JUDGE_BASE_URL:?set JUDGE_BASE_URL}" "${JUDGE_API_KEY:?set JUDGE_API_KEY}" "${JUDGE_NAME:?set JUDGE_NAME}"

want() { [ "$STEP" = all ] || [ "$STEP" = "$1" ]; }

if want calibrate; then
  $INKRAFT calibrate --out "$DATA/judge_calibration.json"
  python -c "import json,sys; a=json.load(open('$DATA/judge_calibration.json'))['grade_accuracy']; sys.exit(0 if a is not None and a >= 0.95 else 3)" \
    || { echo "judge below the 0.95 gate: stop, adjust the judge prompt" >&2; exit 3; }
fi

if want generate || want ablation; then
  : "${LLM_BASE_URL:?set LLM_BASE_URL}" "${LLM_API_KEY:?set LLM_API_KEY}"
fi

if want generate; then
  for M in $MODELS; do
    $INKRAFT generate --model "$M" --workers 6 --condition closed_dated open_book
  done
fi

if want ablation; then
  for M in $MODELS; do
    $INKRAFT generate --model "$M" --workers 6 --lang de --condition closed_swiss closed_plain
  done
fi

if want judge; then
  $INKRAFT judge --workers 8
fi

if want score; then
  $INKRAFT score --cluster --breakdowns --out "$DATA/results.json"
  $INKRAFT expect --note "v$(python -c 'import json;print(json.load(open("data/FREEZE.json"))["version"])') runs"
fi

if want sample; then
  python src/make_check_file.py --judge-model "$JUDGE_NAME" --out human_check.html
  echo "open human_check.html, label, export JSON, then: python src/import_human.py <export.json> --judge-model $JUDGE_NAME"
fi
