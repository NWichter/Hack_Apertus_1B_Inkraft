$track = Split-Path $PSScriptRoot -Parent
docker run --rm -v "${track}:/data" -w /data --entrypoint sh pandoc/core:latest -c 'pandoc technical_report.md -t typst --shift-heading-level-by=-1 -o report/body.typ && sed -i "s#image(\"report/#image(\"/report/#g" report/body.typ'
docker run --rm -v "${track}:/data" -w /data ghcr.io/typst/typst:latest compile --root /data report/main.typ Apertool_Report.pdf
