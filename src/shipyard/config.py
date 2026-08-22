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
no-color = false
only-json = false

[styles]
error = "red"
success = "green"
warning = "yellow"
info = "cyan"
key = "cyan"
value = "white"

# can also use hax decimal
# error = "#FF5555"
# success = "#50FA7B"
# warning = "#F1FA8C"
# info = "#8BE9FD"
# key = "#BD93F9"
# value = "#F8F8F2"
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
            
            # no need to do now its handle by Config class
            # config = merge_dicts(DEFAULT_CONFIG, config)
            
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
    Process-wide runtime configuration manager for Shipyard.

    ``Config`` combines three configuration sources with the following
    precedence:

        root_ctx -> toml_ctx -> default

    Values are resolved independently at each level of a dotted key, allowing
    higher-priority sources to provide specific values while lower-priority
    sources supply missing nested values.

    Configuration reads are cached for repeated lookups. The cache is
    automatically invalidated whenever configuration state changes.

    Public API:
        initialize():
            Initialize one or more configuration sources.

        get():
            Resolve a configuration value using source precedence and nested
            fallback.

        get_flag():
            Resolve a configuration value as a boolean flag.

        set():
            Set a value in the project TOML configuration.

        update():
            Recursively merge values into the project TOML configuration.

        save():
            Persist modified TOML configuration to ``shipyard.toml``.

        root_context():
            Return a copy of the current runtime configuration.

        toml_context():
            Return a copy of the current project TOML configuration.

        default_context():
            Return a copy of Shipyard's default configuration.

    Only the TOML configuration may be modified through ``set()`` and
    ``update()``. Modifications are tracked through the ``dirty`` state and
    can be persisted with ``save()``.
    """
    __instance: Config | None = None
    __slots__ = (
        "_root_ctx",
        "_toml_ctx",
        "_default",
        "_dir_path",
        "_dirty",
    )
    
    def __new__(cls):
        """
        Return the process-wide ``Config`` instance.

        The configuration state is initialized lazily when the singleton is
        created for the first time.
        """
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.__initialize_state()
            
        return cls.__instance
        
    def __initialize_state(self) -> None:
        """
        Initialize the internal configuration state.

        Creates empty runtime and TOML contexts, copies the default
        configuration, initializes the lookup cache, and resets persistence
        state.
        """
        self._root_ctx: dict[str, Any] | None = None
        self._toml_ctx: dict[str, Any] | None = None
        self._default: dict[str, Any] = deepcopy(DEFAULT_CONFIG)
        self._cache: dict[str, Any] = {}

        self._dir_path: Path | None = None
        self._dirty = False
    
    @property
    def initialized(self) -> bool:
        """
        Return whether the project TOML configuration has been initialized.

        This property is ``True`` once ``toml_ctx`` has been provided to
        ``initialize()`` and ``False`` otherwise.

        Note:
            ``root_ctx`` and ``dir_path`` may be initialized independently;
            this property specifically indicates TOML configuration readiness.
        """
        return self._toml_ctx is not None

    @property
    def dirty(self) -> bool:
        """
        Return whether the project TOML configuration has unsaved changes.

        The value becomes ``True`` when ``set()`` or ``update()`` changes the
        TOML configuration and returns to ``False`` after a successful
        ``save()``.
        """
        return self._dirty
    
    @staticmethod
    def _parse_key(name: str) -> list[str]:
        """
        Validate and split a dotted configuration key.

        Args:
            name: Configuration key such as ``"project.name"``.

        Returns:
            The individual key components.

        Raises:
            ValueError: If the key is empty or contains an empty component.
        """
        if not name or any(not part for part in name.split(".")):
            raise ValueError(
                f"invalid configuration key: {name!r}"
            )

        return name.split(".")
    
    def _merge_into(
        self,
        target: dict[str, Any],
        incoming: dict[str, Any],
    ) -> bool:
        """
        Recursively merge configuration values into ``target``.

        Nested dictionaries are merged recursively. All other values from
        ``incoming`` replace the corresponding values in ``target``.

        Values assigned from ``incoming`` are deep-copied so external
        references cannot mutate the target configuration after the merge.

        Args:
            target: Configuration dictionary to modify.
            incoming: Configuration values to merge into ``target``.

        Returns:
            ``True`` if the target was modified, otherwise ``False``.
        """
        changed = False

        for key, value in incoming.items():
            current = target.get(key, NULL)

            if (
                isinstance(current, dict)
                and isinstance(value, dict)
            ):
                if self._merge_into(current, value):
                    changed = True

            elif current != value:
                target[key] = deepcopy(value)
                changed = True

        return changed

    def _invalidate_cache(self) -> None:
        """
        Discard all cached configuration lookup results.

        The cache must be invalidated whenever a configuration source changes
        because previously resolved values may no longer be valid.
        """
        self._cache.clear()
    
    def initialize(
        self,
        *,
        root_ctx: dict[str, Any] | None = None,
        toml_ctx: dict[str, Any] | None = None,
        dir_path: Path | None = None,
    ) -> None:
        """
        Initialize one or more configuration sources.

        Each source is optional and may be initialized independently. A
        source passed as ``None`` is ignored, while each non-``None`` source
        may only be initialized once.

        Provided dictionaries are deep-copied so callers cannot mutate
        ``Config``'s internal state through their original objects.

        Args:
            root_ctx: Runtime configuration for the current CLI invocation.
            toml_ctx: Project configuration loaded from ``shipyard.toml``.
            dir_path: Project root directory containing ``shipyard.toml``.

        Raises:
            TypeError: If a provided context is not a dictionary or
                ``dir_path`` is not a ``Path``.
            RuntimeError: If a configuration source has already been
                initialized.
        """
        changed = False
        
        if root_ctx is not None:
            if not isinstance(root_ctx, dict):
                raise TypeError("root_ctx must be a dict")

            if self._root_ctx is not None:
                raise RuntimeError("root_ctx is already initialized")

            self._root_ctx = deepcopy(root_ctx)
            changed = True

        if toml_ctx is not None:
            if not isinstance(toml_ctx, dict):
                raise TypeError("toml_ctx must be a dict")

            if self._toml_ctx is not None:
                raise RuntimeError("toml_ctx is already initialized")

            self._toml_ctx = deepcopy(toml_ctx)
            changed = True

        if dir_path is not None:
            if not isinstance(dir_path, Path):
                raise TypeError("dir_path must be a Path")

            if self._dir_path is not None:
                raise RuntimeError("dir_path is already initialized")

            self._dir_path = dir_path.resolve()
        
        if changed:
            self._invalidate_cache()

    def get(self, name: str) -> Any | None:
        """
        Resolve a configuration value using source precedence.

        Dotted keys are resolved recursively, applying the precedence

            root_ctx -> toml_ctx -> default

        independently at each nesting level. This allows missing nested
        values in a higher-priority source to fall back to lower-priority
        sources.

        Resolved values are cached to speed up repeated lookups. The cache is
        invalidated whenever configuration state changes.

        Args:
            name: Configuration key, optionally using dotted notation such as
                ``"project.name"`` or ``"files.roadmap"``.

        Returns:
            The resolved configuration value, or ``None`` when no value is
            available from any source.

        Raises:
            ValueError: If ``name`` is not a valid configuration key.
        """
        if name in self._cache:
            return self._cache[name]

        levels = self._parse_key(name)

        def resolve(
            sources: tuple[dict[str, Any] | None, ...],
            index: int,
        ) -> Any | None:
            key = levels[index]

            for source in sources:
                if source is None:
                    continue
                value = source.get(key, NULL)

                if value is NULL:
                    continue

                if index == len(levels) - 1:
                    return value

                if not isinstance(value, dict):
                    continue

                nested_sources = tuple(
                    nested_value
                    if isinstance(nested_value, dict)
                    else None
                    for nested_source in sources
                    for nested_value in (
                        (
                            nested_source.get(key, NULL)
                            if nested_source is not None
                            else NULL
                        ),
                    )
                )

                return resolve(nested_sources, index + 1)

            return None

        value = resolve(
            (
                self._root_ctx,
                self._toml_ctx,
                self._default,
            ),
            0,
        )

        self._cache[name] = value
        return value
    
    def get_flag(self, name: str) -> bool:
        """
        Resolve a configuration value as a boolean flag.

        The resolved value follows the same precedence and lookup behavior as
        ``get()`` and is converted using Python's ``bool()`` semantics.

        Undefined values therefore resolve to ``False``.

        Args:
            name: Configuration key to resolve.

        Returns:
            The resolved value converted to ``bool``.
        """
        return bool(self.get(name))
    
    def set(self, name: str, value: Any) -> None:
        """
        Set a value in the project's TOML configuration.

        Dotted keys may be used to address nested values. Missing intermediate
        mappings are created automatically. Existing non-mapping intermediate
        values cause the operation to fail.

        The value is deep-copied before being stored. If the value differs from
        the existing value, the configuration is marked dirty and cached
        lookups are invalidated.

        Args:
            name: Configuration key, optionally using dotted notation.
            value: Value to store.

        Raises:
            RuntimeError: If TOML configuration has not been initialized.
            TypeError: If an intermediate key is not a mapping.
            ValueError: If ``name`` is not a valid configuration key.
        """
        if not self.initialized:
            raise RuntimeError("config is not initialized")

        levels = self._parse_key(name)
        target = self._toml_ctx

        for level in levels[:-1]:
            current = target.get(level, NULL)

            if current is NULL:
                current = {}
                target[level] = current

            if not isinstance(current, dict):
                raise TypeError(
                    f"cannot set '{name}': "
                    f"'{level}' is not a mapping"
                )

            target = current

        key = levels[-1]

        if target.get(key, NULL) != value:
            target[key] = deepcopy(value)
            self._dirty = True
            self._invalidate_cache()
    
    def update(self, values: dict[str, Any]) -> None:
        """
        Recursively merge values into the project's TOML configuration.

        Nested dictionaries are merged recursively while scalar values and
        other non-mapping values replace existing values.

        If the configuration changes, the instance is marked dirty and cached
        lookups are invalidated.

        Args:
            values: Configuration values to merge.

        Raises:
            RuntimeError: If TOML configuration has not been initialized.
            TypeError: If ``values`` is not a dictionary.
        """
        if not self.initialized:
            raise RuntimeError("config is not initialized")
        
        if not isinstance(values, dict):
            raise TypeError("values must be a dict")

        changed = self._merge_into(
            self._toml_ctx, 
            values
        )

        if changed:
            self._dirty = True
            self._invalidate_cache()
    
    def save(self) -> None:
        """
        Persist pending TOML configuration changes to ``shipyard.toml``.

        If project configuration has not been initialized, or if no changes are
        pending, no action is taken. When the configuration is initialized and
        marked dirty, the current TOML context is written atomically to the
        configured project directory.

        The dirty state is cleared only after a successful save.

        Raises
        ------
        RuntimeError
            If the project configuration is marked as initialized but its
            project directory is not available.
        ShipYardConfigNotFoundError
            If the project configuration file does not exist when saving.
        ShipyardFileError
            If the configuration cannot be serialized or written.
        """
        if not self.initialized or not self._dirty:
            return

        if self._dir_path is None:
            raise RuntimeError("config directory is not initialized")

        save_config(
            self._toml_ctx,
            self._dir_path,
        )

        self._dirty = False
        
    def root_context(self) -> dict[str, Any]:
        """
        Return a deep copy of the runtime configuration context.

        The returned dictionary is detached from the internal state, so
        modifying it does not affect the ``Config`` instance.

        Returns:
            A copy of ``root_ctx`` or an empty dictionary when it is unset.
        """
        return deepcopy(self._root_ctx or {})

    def toml_context(self) -> dict[str, Any]:
        """
        Return a deep copy of the project's TOML configuration.

        The returned dictionary is detached from the internal state, so
        modifying it does not affect the ``Config`` instance.

        Returns:
            A copy of ``toml_ctx`` or an empty dictionary when it is unset.
        """
        return deepcopy(self._toml_ctx or {})

    def default_context(self) -> dict[str, Any]:
        """
        Return a deep copy of Shipyard's default configuration.

        The returned dictionary is detached from the internal state and can
        be modified safely without affecting the defaults used by ``Config``.

        Returns:
            A copy of the default configuration.
        """
        return deepcopy(self._default)
    
    
config: Config = Config()