from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any
import tomllib
import tomli_w

from .utils import merge_dicts
from .error import ShipYardConfigNotFoundError


DEFAULT_TOML = """
[project]
name = "My Project"
version = "0.1.0"
description = "A simple project built with Shipyard."

[github]
repository = "https://github.com/Akkiraj1234/Shipyard"
default_branch = "main"

[files]
roadmap = "ROADMAP.md"
tasks = "TASKS.md"
ideas = "IDEAS.md"
changelog = "CHANGELOG.md"

[settings]
auto_sync = true
"""

RECURSIVE_CONFIG_SEARCH = 5
CONFIG_FILE_NAME = "shipyard.toml"
DEFAULT_CONFIG = tomllib.loads(DEFAULT_TOML)



def load_config(start: Path | None = None) -> dict[str, Any]:
    """
    Load an existing ``shipyard.toml`` configuration.

    Searches from ``start`` (or the current working directory) upwards for up
    to ``RECURSIVE_CONFIG_SEARCH`` parent directories. The loaded
    configuration is merged with the default configuration before being
    returned.

    Args:
        start: Directory to begin searching from.

    Returns:
        The merged configuration dictionary.

    Raises:
        ShipYardConfigNotFoundError: If no ``shipyard.toml`` file is found.
    """
    current = (start or Path.pwd()).resolve()
    
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
    
    raise ShipYardConfigNotFoundError()


def create_config(dir_path: Path | None = None) -> dict[str, Any]:
    """
    Create a default ``shipyard.toml`` if one does not already exist.

    If a configuration file already exists, it is left unchanged.

    Args:
        dir_path: Directory where the configuration file should be created.

    Returns:
        A copy of the default configuration dictionary.
    """
    current = (dir_path or Path.pwd()).resolve()
    file_path = current / CONFIG_FILE_NAME
    
    if not file_path.is_file():
        with file_path.open("wb") as file:
            tomli_w.dump(DEFAULT_CONFIG, file)
            
    merged = deepcopy(DEFAULT_CONFIG)
    merged["root"] = str(current)
    return merged