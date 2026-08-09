from __future__ import annotations
from pathlib import Path
from typing import Any
import tomllib
import tomli_w

from .utils import (
    merge_dicts, 
    safe_open, 
    atomic_write
)
from .error import (
    ShipYardConfigNotFoundError, 
    ShipyardFileError
)




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



def load_config(start: Path | None = None) -> tuple[Path, dict[str, Any]]:
    """
    Load the nearest ``shipyard.toml`` configuration.

    Starting from ``start`` (or the current working directory), searches upward
    through parent directories for up to ``RECURSIVE_CONFIG_SEARCH`` levels.
    Once found, the configuration is loaded, merged with
    ``DEFAULT_CONFIG``, and returned along with the project root (the directory
    containing ``shipyard.toml``).

    Args:
        start: Directory from which to begin the search. Defaults to the
            current working directory.

    Returns:
        A tuple containing the project root directory and the merged
        configuration dictionary.

    Raises:
        ShipYardConfigNotFoundError: If no ``shipyard.toml`` file is found
            within the search limit.
        ShipyardFileError: If the configuration file cannot be opened or
            contains invalid TOML.
    """
    
    current = (start or Path.cwd()).resolve()
    
    for _ in range(RECURSIVE_CONFIG_SEARCH + 1):
        config_path = current / CONFIG_FILE_NAME
        
        if config_path.is_file():
            try:
                with safe_open(config_path, binary=True) as file:
                    config = tomllib.load(file)
                    
            except tomllib.TOMLDecodeError as exc:
                raise ShipyardFileError(
                    f"could not parse configuration file '{config_path}': {exc}"
                ) from exc
            
            config = merge_dicts(DEFAULT_CONFIG, config)
            
            return current, config
            
        if current == current.parent:
            break

        current = current.parent
    
    raise ShipYardConfigNotFoundError(current)


def create_config(dir_path: Path | None = None) -> tuple[Path, dict[str, Any]]:
    """
    Create a default ``shipyard.toml`` if one does not already exist.

    If a configuration file already exists, it is left unchanged. The directory
    containing ``shipyard.toml`` is considered the project root.

    Args:
        dir_path: Directory where the configuration file should be created.
            Defaults to the current working directory.

    Returns:
        A tuple containing the project root directory and a copy of the
        default configuration dictionary.
    """
    current = (dir_path or Path.cwd()).resolve()
    file_path = current / CONFIG_FILE_NAME
    
    if not file_path.is_file():
        data = tomli_w.dumps(DEFAULT_CONFIG)
        atomic_write(file_path, data, create = True)
            
    config = merge_dicts(DEFAULT_CONFIG, {})
    
    return current, config
    
    
def save_config(
    config: dict[str, Any],
    dir_path: Path | str,
) -> None:
    """
    Save the configuration to ``shipyard.toml``.

    The provided directory is treated as the project root and must contain
    ``shipyard.toml``. The given configuration replaces the existing
    configuration atomically.

    Args:
        config: Configuration dictionary to write.
        dir_path: Project root containing ``shipyard.toml``.

    Raises:
        ShipYardConfigNotFoundError: If ``shipyard.toml`` does not exist.
        ShipyardFileError: If the configuration cannot be serialized or written.
    """
    file_path = Path(dir_path).resolve() / CONFIG_FILE_NAME

    if not file_path.is_file():
        raise ShipYardConfigNotFoundError(file_path)

    try:
        data = tomli_w.dumps(config)
        
    except Exception as exc:
        raise ShipyardFileError(
            f"failed to serialize configuration: {exc}"
        ) from exc
        
    atomic_write(file_path, data)
