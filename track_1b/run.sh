#!/bin/sh
# Container entry point: replay (default) | full | test
set -eu
MODE="${1:-replay}"
DATA=/app/data

case "$MODE" in
  replay)
    if [ -f "$DATA/expected_results.json" ]; then
      exec inkraft --data "$DATA" replay
    fi
    echo "data/ holds no frozen results yet. Running the replay self-check on the bundled fixture."
    exec inkraft --data /app/tests/fixtures/mini replay
    ;;
  full)
    : "${LLM_BASE_URL:?set LLM_BASE_URL}" "${LLM_API_KEY:?set LLM_API_KEY}" "${LLM_NAME:?set LLM_NAME}"
    # shellcheck disable=SC2086
    inkraft --data "$DATA" generate --condition ${CONDITIONS:-closed_dated} ${LIMIT:+--limit $LIMIT}
    if [ -n "${JUDGE_BASE_URL:-}" ] && [ -n "${JUDGE_NAME:-}" ]; then
      inkraft --data "$DATA" judge --examinee "$LLM_NAME"
    else
      echo "JUDGE_* not set: scoring with the rule-based pre-grade only (provisional)."
    fi
    exec inkraft --data "$DATA" score --out "$DATA/results_${LLM_NAME}.json"
    ;;
  test)
    exec python -m pytest -q /app/tests
    ;;
  *)
    echo "usage: run.sh [replay|full|test]" >&2
    exit 2
    ;;
esac
