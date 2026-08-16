import sys

import pytest

from shipyard.error import ShipyardFileError, ShipyardInternalError
from shipyard.utils import (
    atomic_write,
    best_matches,
    import_command_module,
    load_module,
    merge_dicts,
    ListStream,
    SKIP,
    safe_open,
)


def test_atomic_write_creates_and_replaces_text(tmp_path):
    path = tmp_path / "metadata" / "README.md"

    atomic_write(path, "first", create=True)
    atomic_write(path, "second")

    assert path.read_text(encoding="utf-8") == "second"
    assert not list(path.parent.glob(f".{path.name}.*.tmp"))


def test_atomic_write_requires_an_existing_file_unless_create_is_requested(tmp_path):
    with pytest.raises(ShipyardFileError, match="file does not exist"):
        atomic_write(tmp_path / "missing.md", "content")


def test_safe_open_returns_none_for_missing_files_and_reads_existing_text(tmp_path):
    missing = tmp_path / "missing.txt"
    with safe_open(missing) as file:
        assert file is None

    path = tmp_path / "notes.txt"
    path.write_text("hello", encoding="utf-8")
    with safe_open(path) as file:
        assert file.read() == "hello"


def test_merge_dicts_merges_nested_values_without_mutating_defaults():
    defaults = {"project": {"name": "Shipyard", "version": "0.1"}, "enabled": True}

    merged = merge_dicts(defaults, {"project": {"version": "0.2"}, "enabled": False})

    assert merged == {"project": {"name": "Shipyard", "version": "0.2"}, "enabled": False}
    assert defaults["project"]["version"] == "0.1"


def test_list_stream_traverses_items_with_peek_move_and_next():
    stream = ListStream(["shipyard", "doctor", "init"])

    assert stream.current == "shipyard"
    assert stream.peek == "doctor"

    stream.move()
    assert stream.current == "doctor"
    assert stream.peek == "init"

    assert stream.next() == "init"
    assert stream.current == "init"

    stream.move()
    assert stream.eof is True
    assert stream.current is None
    assert stream.peek is None


def test_list_stream_remove_items_skips_values_without_changing_indexes():
    stream = ListStream(["shipyard", "doctor", "init", "doctor"])

    removed = stream.remove_items(["doctor"])

    assert removed == ["doctor", "doctor"]
    assert stream.items == ["shipyard", SKIP, "init", SKIP]
    assert stream.current == "shipyard"

    stream.move()
    assert stream.current == "init"
    assert stream.peek is None


def test_list_stream_current_raises_when_cursor_points_at_skip():
    stream = ListStream(["shipyard", "doctor"])
    stream.items[0] = SKIP

    with pytest.raises(
        ShipyardInternalError,
        match="ListStream invariant violated: current item is SKIP",
    ):
        _ = stream.current


def test_best_matches_and_load_module_support_public_lookup_forms(tmp_path):
    plugin_path = tmp_path / "plugin.py"
    plugin_path.write_text("value = 42\n", encoding="utf-8")

    assert best_matches("docter", ["doctor", "init"])[0] == "doctor"
    assert load_module("json") is sys.modules["json"]
    assert load_module(plugin_path).value == 42


def test_import_command_module_supports_relative_imports(tmp_path):
    command_dir = tmp_path / "status"
    command_dir.mkdir()
    (command_dir / "__init__.py").write_text("", encoding="utf-8")
    (command_dir / "logic.py").write_text("VALUE = 42\n", encoding="utf-8")
    (command_dir / "main.py").write_text(
        "from .logic import VALUE\n",
        encoding="utf-8",
    )

    module = import_command_module(command_dir / "main.py", command_dir)

    assert module.VALUE == 42
