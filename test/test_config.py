import pytest

from shipyard.config import (
    CONFIG_FILE_NAME,
    create_config,
    load_config,
    save_config,
)
from shipyard.error import ShipYardConfigNotFoundError, ShipyardFileError


def test_create_load_and_save_config_round_trip(tmp_path):
    root, created = create_config(tmp_path)
    created["project"]["name"] = "Updated Project"
    save_config(created, root)

    loaded_root, loaded = load_config(root)

    assert loaded_root == root
    assert loaded["project"]["name"] == "Updated Project"
    assert (root / CONFIG_FILE_NAME).is_file()


def test_default_config_defines_project_metadata_and_managed_locations(tmp_path):
    _, config = create_config(tmp_path)

    assert config["author"]["name"] == "Your Name"
    assert config["github"]["default_branch"] == "main"
    assert config["paths"]["shipyard"] == ".shipyard"
    assert config["files"]["current_feature"] == ".shipyard/CURRENT.md"
    assert config["settings"]["auto_sync"] is False


def test_load_config_finds_a_parent_project_config_and_merges_defaults(tmp_path):
    root = tmp_path / "project"
    nested = root / "src" / "shipyard"
    nested.mkdir(parents=True)
    (root / CONFIG_FILE_NAME).write_text("[project]\nname = 'Test Project'\n", encoding="utf-8")

    found_root, config = load_config(nested)

    assert found_root == root
    assert config["project"]["name"] == "Test Project"
    assert config["project"]["version"] == "0.1.0"


def test_load_config_reports_missing_and_invalid_configuration(tmp_path):
    with pytest.raises(ShipYardConfigNotFoundError):
        load_config(tmp_path)

    config_path = tmp_path / CONFIG_FILE_NAME
    config_path.write_text("[project\n", encoding="utf-8")
    with pytest.raises(ShipyardFileError, match="could not parse configuration file"):
        load_config(tmp_path)


def test_save_config_requires_an_initialized_project(tmp_path):
    with pytest.raises(ShipYardConfigNotFoundError):
        save_config({}, tmp_path)
