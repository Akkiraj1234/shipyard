import sys

import pytest

from shipyard.utils import atomic_write, load_module, safe_read


def test_atomic_write_replaces_content_and_safe_read_returns_text(tmp_path):
    path = tmp_path / "metadata" / "README.md"

    atomic_write(path, "first")
    atomic_write(path, "second")

    assert safe_read(path) == "second"
    assert not list(path.parent.glob(f".{path.name}.*.tmp"))


def test_atomic_write_and_safe_read_round_trip_json(tmp_path):
    path = tmp_path / "metadata.json"

    atomic_write(path, {"version": "1", "name": "shipyard"})

    assert safe_read(path) == {"name": "shipyard", "version": "1"}


def test_safe_read_returns_none_for_a_missing_file(tmp_path):
    assert safe_read(tmp_path / "missing.md") is None


def test_load_module_imports_a_dotted_module():
    assert load_module("json") is sys.modules["json"]


def test_load_module_imports_a_python_file(tmp_path):
    path = tmp_path / "plugin.py"
    path.write_text("value = 42\n", encoding="utf-8")

    plugin = load_module(path)

    assert plugin.value == 42


def test_load_module_rejects_a_non_python_file(tmp_path):
    path = tmp_path / "plugin.txt"
    path.write_text("not python", encoding="utf-8")

    with pytest.raises(ValueError, match=".py extension"):
        load_module(path)
