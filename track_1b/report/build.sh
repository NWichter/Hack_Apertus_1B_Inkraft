#!/bin/sh
cd "$(dirname "$0")/.." || exit 1
export MSYS_NO_PATHCONV=1
HERE=$(pwd -W 2>/dev/null || pwd)
docker run --rm -v "$HERE:/data" -w /data --entrypoint sh pandoc/core:latest -c \
  'pandoc technical_report.md -t typst --shift-heading-level-by=-1 -o report/body.typ && sed -i "s#image(\"report/#image(\"/report/#g" report/body.typ'
docker run --rm -v "$HERE:/data" -w /data ghcr.io/typst/typst:latest compile --root /data report/main.typ Apertool_Report.pdf
