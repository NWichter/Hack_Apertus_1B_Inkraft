# data/

License: CDLA-Permissive-2.0 (see [`LICENSE`](LICENSE)) for our questions, answers and metadata, stored per item in the
`license` field. Quoted federal statute text (`source.quote`) is public domain under Art. 5 para. 1 lit. a URG
(`source.license: public-domain-ch-urg-art5`) and is not relicensed.

Release **v<!--n:version-->1.0.0-rc1<!--/n-->**: <!--n:cores-->327<!--/n--> German cores, <!--n:rows-->951<!--/n--> rows. Data card: [`../docs/DATA_CARD.md`](../docs/DATA_CARD.md).

| File | Content |
| --- | --- |
| `test.jsonl`, `metadata.jsonl` | the benchmark (graded fields) and the provenance per row, built from `merged.v<version>.jsonl` |
| `merged.v<version>.jsonl` | frozen rows with every field; `FREEZE.json` = version, SHA-256 of the files (LF line endings), statistics |
| `responses/<model>__<condition>.jsonl` | Apertus 1.5 answers |
| `judgements/<judge>__<model>__<condition>.jsonl` | grades per judge; `panel__*` = majority of the judge panel; `apertus-v1.5-70b__*` = comparison judge (diagnostic) |
| `judge_panel.json`, `judge_calibration*.json`, `judge_agreement_qwen_vs_apertus70b.json` | panel statistics, calibration of every judge on 61 constructed answers, self-preference diagnostic |
| `expected_results.json`, `results.json` | what `make run` replays; full scores with breakdowns |
| `human_labels/` | human samples, labels, agreement, summary; `translations_de.json` = reading aid for FR/IT rows of the judge sample |
| `validation_report.v<version>.md`, `contamination.summary.json` | validator in frozen mode; exposure check against MultiLegalPile (per-row hits stay local because they quote the corpus) |
| `sources/fedlex_manifest.v2.json` | Fedlex retrieval: ELI and HTML URLs, SHA-256 per act, version and language |
| `temporal/` | version diff (`src/find_changes.py`): bucket per evidence sentence, changed paragraphs, amount candidates |
| `review/` | logged release decisions (`auto/`), independent second check, panel-derived variants (`panel_fixes*.json`), human decisions |
| `candidates/` | temporal candidates drafted by Nemotron with their checks, fixes and generation logs |
| `merged.v1.jsonl`, `antigravity.*.jsonl`, `review_v2.json`, `review_v3_cx0063.json` | the first draft and its earlier corrections (input of the release pipeline) |
| `ablation_cores.txt`, `judge_extra_reasoning_low.json` | ablation subset written by `freeze.py`; request option for GLM-5.3 (reasoning cannot be switched off) |
