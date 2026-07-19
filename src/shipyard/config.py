from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any
import tomllib
import tomli_w


RECURSIVE_CONFIG_SEARCH = 5
CONFIG_FILE_NAME = "shipyard.toml"

# Default config for application
DEFAULT_CONFIG: dict[str, Any] = {
    "theme": "dark",
    "refresh_rate": 60,
    "ui": {
        "border": True,
        "padding": 2,
        "window_margin_y": 1,
        "window_margin_x": 3,
    },
    "TEST_DIR": "./test/",
}

DEFAULT_TOML = """
[app]
TEST_DIR = "./test/"

[style]
theme = "tokyo-night"
border = true
padding = 2
window_margin_y = 1
window_margin_x = 3
refresh_rate = 60


[custom.Theme.dark-god]
Text = None
Text_Active = None
Text_Inactive = None

Border = None
Border_Active = None
Border_Inactive = None

Main_Border = None
Main_Border_Active = None
Main_Border_Inactive = None

H1 = None
H1_Active = None
H1_Inactive = None

H2 = None
H2_Active = None
H2_Inactive = None

Command = None
Command_Active = None
Command_Inactive = None

Suggestion = None
Suggestion_Active = None
Suggestion_Inactive = None

# Status messages
Error = None
Error_Active = None
Error_Inactive = None

Warning = None
Warning_Active = None
Warning_Inactive = None

Success = None
Success_Active = None
Success_Inactive = None

# Selection / focus
Selected = None
Focused = None
Disabled = None
"""


def merge_dicts(defaults: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively merge a user configuration into the default configuration.

    Nested dictionaries are merged key by key, while non-dictionary values
    from the user configuration override the corresponding default values.

    Args:
        defaults: Base configuration containing default values.
        user: User-provided configuration values.

    Returns:
        A new dictionary containing the merged configuration. The input
        dictionaries are not modified.
    """
    
    merged = deepcopy(defaults)

    def merge_into(target: dict[str, Any], incoming: dict[str, Any]) -> None:
        for key, value in incoming.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                merge_into(target[key], value)
            else:
                target[key] = value

    merge_into(merged, user)
    return merged


def find_config(start: Path | None = None) -> dict[str, Any]:
    """
    Locate, load, and merge the project configuration.

    Starting from ``start`` (or the current working directory if not
    provided), this function searches parent directories for a
    ``testpy.toml`` file up to ``RECURSIVE_CONFIG_SEARCH`` levels.

    If a configuration file is found, its contents are merged with
    ``DEFAULT_CONFIG`` and returned. A ``root`` key containing the
    directory where the configuration file was found is added to the
    resulting configuration.

    If no configuration file is found, a default ``testpy.toml`` file is
    created in the current working directory (if it does not already
    exist), and the default configuration is returned with ``root`` set
    to the current working directory.

    Args:
        start: Directory from which to begin the search.

    Returns:
        The resolved configuration dictionary with default values applied
        and a ``root`` key indicating the project root directory.
    """
    
    current = (start or Path.cwd()).resolve()

    for _ in range(RECURSIVE_CONFIG_SEARCH):
        config_path = current / CONFIG_FILE_NAME
        
        if config_path.is_file():
            with config_path.open("rb") as file:
                config = tomllib.load(file)
            
            merged = merge_dicts(DEFAULT_CONFIG, config)
            merged["root"] = str(current)
            return merged

        if current == current.parent:
            break

        current = current.parent
    
    config_path = Path.cwd().resolve() / CONFIG_FILE_NAME
    
    if not config_path.exists():
        with config_path.open("wb") as file:
            tomli_w.dump(DEFAULT_CONFIG, file)
    
    merged = deepcopy(DEFAULT_CONFIG)
    merged["root"] = str(Path.cwd().resolve())
    return merged
