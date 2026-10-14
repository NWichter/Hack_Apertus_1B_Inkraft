"""Every Hugging Face configuration must have one type per field, otherwise load_dataset fails."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import check_hf_schema as c  # noqa: E402


def test_published_files_have_consistent_types():
    for name, pats in c.CONFIGS.items():
        files = c.files_of(pats)
        assert files, name
        assert c.conflicts(files) == {}, name


def test_detects_mixed_types(tmp_path):
    p = tmp_path / "x.jsonl"
    p.write_text('{"a": {"m": ["x"]}}\n{"a": {"m": "x"}}\n{"a": {"m": null}}\n', encoding="utf-8")
    assert c.conflicts([p]) == {".a.m": ["list", "string"]}
