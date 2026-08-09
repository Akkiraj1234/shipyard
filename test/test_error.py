from pathlib import Path

from shipyard.error import (
    InvalidInputError,
    ShipYardConfigNotFoundError,
    UnknownCommandError,
    shipyard_error_print,
)
from shipyard.parser import create_parser


def test_unknown_command_includes_a_command_pointer_and_suggestion():
    stream = create_parser(["shipyard", "docter"])

    rendered = str(UnknownCommandError(stream, "docter", {"doctor", "init"}))

    assert "unknown command 'docter'" in rendered
    assert "$ shipyard docter" in rendered
    assert "Did you mean 'shipyard doctor'?" in rendered


def test_unknown_flag_includes_a_suggestion():
    stream = create_parser(["shipyard", "--forse"])

    rendered = str(InvalidInputError(stream, "flag", "forse", {"force"}))

    assert "unknown flag '--forse'" in rendered
    assert "$ shipyard --forse" in rendered
    assert "Did you mean '--force'?" in rendered


def test_missing_configuration_explains_how_to_recover():
    rendered = str(ShipYardConfigNotFoundError(Path("/tmp/project")))

    assert "could not find shipyard.toml" in rendered
    assert "Run 'shipyard init'" in rendered


def test_error_printer_renders_known_and_unknown_errors(capsys):
    stream = create_parser(["shipyard", "docter"])

    assert shipyard_error_print(UnknownCommandError(stream, "docter", {"doctor"}), {}) == 2
    assert "unknown command 'docter'" in capsys.readouterr().out

    assert shipyard_error_print(RuntimeError("broken registry"), {}) == 2
    rendered = capsys.readouterr().out
    assert "fatal:" in rendered
    assert "reason: RuntimeError: broken registry" in rendered


def test_error_printer_includes_a_traceback_in_dev_mode(capsys):
    try:
        raise RuntimeError("broken registry")
    except RuntimeError as error:
        shipyard_error_print(error, {"dev": True})

    rendered = capsys.readouterr().out
    assert "debug:" in rendered
    assert "traceback:" in rendered
    assert "RuntimeError" in rendered
