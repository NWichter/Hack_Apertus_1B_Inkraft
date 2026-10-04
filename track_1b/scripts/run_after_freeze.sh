#!/bin/sh
# Runs after the v1.0.0 freeze (Niklas' go): judge calibration, Apertus 8B/70B runs, ablation, judge,
# score, expected results and the 20 % human sample. Each step resumes where it stopped.
#
# Needs: LLM_BASE_URL, LLM_API_KEY (Apertus endpoint); JUDGE_BASE_URL, JUDGE_API_KEY, JUDGE_NAME.
# Optional: MODELS (default "apertus-v1.5-8b apertus-v1.5-70b"), ABLATION_MODEL (default apertus-v1.5-8b),
#           STEP (calibrate|generate|ablation|judge|score|sample|all, default all).
# Apertus calls: about 2 x rows (main) + 2 x ablation cores (DE); printed before the runs start.
set -eu
cd "$(dirname "$0")/.."
DATA=data
MODELS="${MODELS:-apertus-v1.5-8b apertus-v1.5-70b}"
ABLATION_MODEL="${ABLATION_MODEL:-apertus-v1.5-8b}"
STEP="${STEP:-all}"
INKRAFT="python -m inkraft --data $DATA"
export PYTHONPATH="${PYTHONPATH:-}:src"

[ -f "$DATA/FREEZE.json" ] || { echo "no data/FREEZE.json: run src/freeze.py --go first" >&2; exit 2; }
: "${JUDGE_BASE_URL:?set JUDGE_BASE_URL}" "${JUDGE_API_KEY:?set JUDGE_API_KEY}" "${JUDGE_NAME:?set JUDGE_NAME}"

want() { [ "$STEP" = all ] || [ "$STEP" = "$1" ]; }

if want calibrate; then
  $INKRAFT calibrate --out "$DATA/judge_calibration.json" | tee /dev/stderr | grep -q "below the 0.95 gate" \
    && { echo "judge below the 0.95 gate: stop, adjust the judge prompt" >&2; exit 3; }
fi

if want generate || want ablation; then
  : "${LLM_BASE_URL:?set LLM_BASE_URL}" "${LLM_API_KEY:?set LLM_API_KEY}"
  ROWS=$(wc -l < "$DATA/test.jsonl")
  ABL=$(wc -l < "$DATA/ablation_cores.txt")
  echo "planned Apertus calls: main $((ROWS * $(echo "$MODELS" | wc -w))), ablation $((ABL * 2)) (DE, $ABLATION_MODEL)"
fi

if want generate; then
  for M in $MODELS; do
    $INKRAFT generate --model "$M" --condition closed_dated
  done
fi

if want ablation; then
  $INKRAFT generate --model "$ABLATION_MODEL" --condition closed_swiss closed_plain --lang de --cores "$DATA/ablation_cores.txt"
fi

if want judge; then
  $INKRAFT judge
fi

if want score; then
  $INKRAFT score --cluster --breakdowns --out "$DATA/results.json"
  $INKRAFT expect --note "v$(python -c 'import json;print(json.load(open("data/FREEZE.json"))["version"])') main runs"
fi

if want sample; then
  $INKRAFT sample-human
  echo "blind sample: data/human_labels/sample_20pct.jsonl -> load with data/test.jsonl in tools/review (mode Blind-Stichprobe)"
fi
