#!/bin/sh
# Hugging Face release of the frozen dataset. Default is a dry run: builds hf/README.md (fails on any missing
# value) and lists every file with its size. The upload happens only with GO=1 (the curator's decision).
#
#   ENV=<.env with HF_TOKEN> [REPO=NWichter/inkraft] sh scripts/hf_upload.sh            # dry run
#   ENV=<.env with HF_TOKEN> [REPO=NWichter/inkraft] GO=1 sh scripts/hf_upload.sh       # upload, public
#
# PRIVATE=1 uploads privately; ALLOW_RC=1 allows uploading a release candidate (version with "-rc").
set -eu
cd "$(dirname "$0")/.."
REPO="${REPO:-NWichter/inkraft}"
export PYTHONPATH=src

VERSION=$(python -c 'import json;print(json.load(open("data/FREEZE.json"))["version"])')
case "$VERSION" in
  *-rc*) [ "${ALLOW_RC:-0}" = 1 ] || { echo "FREEZE.json is $VERSION: run scripts/after_human_check.sh (GO=1) first, or set ALLOW_RC=1" >&2; exit 2; } ;;
esac
python -m inkraft --data data replay | tail -n 1
python src/hf_release.py card --repo "$REPO"
grep -n -E 'TBD|More Information Needed|\{\{' hf/README.md && { echo "placeholder left in hf/README.md" >&2; exit 3; } || true

if [ "${GO:-0}" != 1 ]; then
  python src/hf_release.py upload --repo "$REPO"
  echo "dry run only (version $VERSION). Upload: GO=1 ENV=<.env> sh scripts/hf_upload.sh"
  exit 0
fi
VIS="--public"; [ "${PRIVATE:-0}" = 1 ] && VIS=""
python src/hf_release.py upload --repo "$REPO" --go $VIS ${ENV:+--env "$ENV"}
echo "done: https://huggingface.co/datasets/$REPO (tag v$VERSION). Put this URL into technical_report.md, README.md and the pitch."
