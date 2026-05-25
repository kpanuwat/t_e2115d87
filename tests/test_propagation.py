import os
import json
import sys
from pathlib import Path
# Make the repo root importable for tests
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.hermes.propagation import diff_dict, filter_excluded_keys, apply_safe


def test_diff_dict_simple():
    a = {"a": 1, "b": {"x": 1, "y": 2}}
    b = {"a": 1, "b": {"x": 9, "y": 2}, "c": 3}
    d = diff_dict(a, b)
    assert d == {"b": {"x": 9}, "c": 3}


def test_filter_excluded():
    changes = {"a": 1, "secret": 2, "nested": {"auth": 1, "ok": 2}}
    out = filter_excluded_keys(changes, ["secret", "nested.auth"])
    assert out == {"a": 1, "nested": {"ok": 2}}


def test_apply_safe(tmp_path):
    pd = tmp_path / "profile"
    pd.mkdir()
    cfg = {"a": 1}
    (pd / "config.json").write_text(json.dumps(cfg, ensure_ascii=False))
    changes = {"b": 2}
    res = apply_safe(str(pd), changes, origin="test", dry_run=False)
    assert res["outcome"] == "applied"
    newcfg = json.loads((pd / "config.json").read_text())
    assert newcfg["b"] == 2

