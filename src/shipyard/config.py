from __future__ import annotations
from pathlib import Path
from copy import deepcopy
from typing import Any
import tomllib
import tomli_w

from .utils import (
    merge_dicts, 
    safe_open, 
    atomic_write,
    NULL
)
from .error import (
    ShipYardConfigNotFoundError, 
    ShipyardFileError
)




DEFAULT_TOML = """
[project]
name = "My Project"
version = "0.1.0"
description = "A project managed with Shipyard."

[author]
name = "Your Name"

[github]
username = "your-github-username"
repository = "https://github.com/your-github-username/your-project"
default_branch = "main"

[paths]
shipyard = ".shipyard"

[files]
roadmap = "ROADMAP.md"
tasks = ".shipyard/TASKS.md"
current_feature = ".shipyard/CURRENT.md"
additional_changes = ".shipyard/CHANGES.md"
ideas = "docs/proposals"
changelog = "CHANGELOG.md"

[settings]
auto_sync = false
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
    
    
def save_config(config: dict[str, Any], dir_path: Path | str) -> None:
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


class Config:
    """
    Runtime configuration resolver for Shipyard.

    Configuration sources are resolved in this order:

        root_ctx -> toml_ctx -> default

    ``root_ctx`` contains current CLI invocation state.
    ``toml_ctx`` contains the project's loaded ``shipyard.toml`` data.
    ``default`` contains Shipyard's fallback configuration.

    Only the Config instance may mutate persisted configuration state.
    """
    
    def __init__(self):
        """
        inisialize the config class
        """
        self._root_ctx: dict[str, Any] | None = None
        self._toml_ctx: dict[str, Any] | None = None
        self._default:  dict[str, Any] = deepcopy(DEFAULT_CONFIG)
        
        self._dir_path: Path | None = None
        self._dirty = False
    
    @property
    def initialized(self) -> bool:
        """
        Return whether toml configuration has insialized
        """
        return bool(self._toml_ctx)

    @property
    def dirty(self) -> bool:
        """
        Return whether persisted configuration has been modified.
        """
        return self._dirty
    
    def _get_source_value(self, source: dict[str, Any] | None, name: str) -> Any:
        """
        Return a value from one configuration source.

        ``NULL`` distinguishes an absent key from a key whose value is
        explicitly ``None``.
        """
        if source is None:
            return NULL

        return source.get(name, NULL)
    
    def _get_data(self, name: str) -> Any | None:
        """
        Resolve a top-level value using configuration precedence.

        Precedence:
            root_ctx -> toml_ctx -> default
        """
        for source in (
            self._root_ctx,
            self._toml_ctx,
            self._default,
        ):
            value = self._get_source_value(source, name)

            if value is not NULL:
                return value

        return None

    def _merge_into(self, target: dict[str, Any], incoming: dict[str, Any]) -> bool:
        """
        Recursively merge ``incoming`` into ``target``.
        
        Returns ``True`` when the target changed.
        """
        
        changed = False

        for key, value in incoming.items():
            if (
                isinstance(target.get(key), dict)
                and isinstance(value, dict)
            ):
                if self._merge_into(target[key], value):
                    changed = True

            else:
                if target.get(key, NULL) != value:
                    target[key] = deepcopy(value)
                    changed = True

        return changed
    
    def initialize(
        self,
        *,
        root_ctx: dict[str, Any] | None = None,
        toml_ctx: dict[str, Any] | None = None,
        dir_path: Path | None = None
    ) -> None:
        """
        Initialize the runtime configuration sources once.
        """
        if isinstance(root_ctx, dict):
            if self.root_ctx is not None:
                raise RuntimeError("cant set root_ctx already insialize")
            
            self.root_ctx = deepcopy(root_ctx)
            
        if isinstance(toml_ctx, dict):
            if self.toml_ctx is not None:
                raise RuntimeError("cant set toml_ctx already insialize")
            
            self.toml_ctx = deepcopy(toml_ctx)
        
        if isinstance(dir_path, Path):
            if self._dir_path is not None:
                raise RuntimeError("cant set toml_ctx already insialize")
            
            self._dir_path = dir_path

        self._dirty = False
    
    def get(self, name: str) -> Any | None:
        """
        Resolve a possibly nested configuration value.

        Examples
        --------
        ``config.get("project.name")``

        ``config.get("files.roadmap")``
        """
        
        levels = name.split(".")
        data = self._get_data(levels[0])

        for level in levels[1:]:
            if not isinstance(data, dict):
                return None

            data = data.get(level, None)

        return data
    
    def get_flag(self, name: str) -> bool:
        """
        Return a configuration value as a boolean.

        An undefined value resolves to ``False``.
        """
        return bool(self.get(name))

    def set(self, name: str, value: Any) -> None:
        """
        Set a value in the project TOML configuration.

        Nested keys may be written using dotted paths.

        Example
        -------
        ``config.set("project.name", "Shipyard")``
        """
        if not self.initialized:
            raise RuntimeError("config is not initialized")

        levels = name.split(".")
        target = self._toml_ctx

        for level in levels[:-1]:
            current = target.get(level)

            if current is None:
                current = {}
                target[level] = current

            if not isinstance(current, dict):
                raise TypeError(
                    f"cannot set '{name}': '{level}' is not a mapping"
                )

            target = current

        key = levels[-1]

        if target.get(key, NULL) != value:
            target[key] = value
            self._dirty = True
    
    def update(self, values: dict[str, Any]) -> None:
        """
        Update project configuration using a recursive mapping merge.
        """
        if not self.initialized:
            raise RuntimeError("config is not initialized")

        changed = self._merge_into(
            self._toml_ctx, 
            values
        )

        if changed:
            self._dirty = True
    
    def save(self) -> None:
        """
        Persist the current TOML configuration.

        This method only saves when the configuration is dirty.
        """
        
        if not self.initialized:
            raise RuntimeError("config is not initialized")

        if not self._dirty:
            return

        if not isinstance(self._dir_path, Path) \
            and not self._dir_path.exists():
                raise RuntimeError("config path is not saved well")
            
        root_path = self._dir_path 


        save_config(
            self._toml_ctx,
            self.root_path,
        )

        self._dirty = False
        

    def root_context(self) -> dict[str, Any]:
        """
        Return a copy of the root context.

        The returned dictionary cannot mutate Config's internal state.
        """
        return deepcopy(self._root_ctx or {})

    def toml_context(self) -> dict[str, Any]:
        """
        Return a copy of the TOML configuration.

        The returned dictionary cannot mutate Config's internal state.
        """
        return deepcopy(self._toml_ctx or {})

    def default_context(self) -> dict[str, Any]:
        """
        Return a copy of the default configuration.
        """
        return deepcopy(self._default)

    
    
    
    