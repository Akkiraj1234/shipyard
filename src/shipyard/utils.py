from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import os
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any, List, TYPE_CHECKING
from difflib import get_close_matches
from copy import deepcopy

if TYPE_CHECKING:
    from .core import Command


    
class ListStream:
    """
    Sequential stream interface for traversing a list.

    Provides cursor-based navigation with lookahead support.
    """

    def __init__(self, items: List, s_idx: int = 0):
        """
        Initialize a stream over a list.

        Args:
            items: Sequence to traverse.
            s_idx: Starting index within the sequence.
        """
        self.items = items
        self.idx = s_idx
        self.end_idx = len(items)

    @property
    def eof(self) -> bool:
        """
        Return whether the stream has reached the end.
        """
        return self.idx >= self.end_idx

    @property
    def current(self) -> Any | None:
        """
        Return the current item, or `None` if the stream is exhausted.
        """
        if self.eof:
            return None
        
        return self.items[self.idx]

    @property
    def peek(self) -> Any | None:
        """
        Return the next item without advancing the stream.
        """
        if self.idx + 1 >= self.end_idx:
            return None
        
        return self.items[self.idx + 1]

    def move(self, count: int = 1) -> None:
        """
        Advance the stream by the given number of elements.
        """
        self.idx += count

    def next(self) -> Any | None:
        """
        Advance the stream and return the new current item.
        """
        self.move()
        return self.current
    
    def __str__(self) -> str:
        lines = ["ListStream"]
        
        for num, item in enumerate(self.items):
            connector = "└──" if num == self.end_idx else "├──"
            end = "  <- curr" if num == self.idx else ""
            lines.append(f"{connector} {item} {end}")
            
        if self.eof:
            lines.append("└──  <eof>  <── curr")
        
        return "\n".join(lines)
    
    def __repr__(self):
        return self.__str__()


def load_module(module: str | Path | Command) -> ModuleType | Command:
    """Load a Python module by dotted name or file path.

    A ``Command`` instance is returned unchanged, which lets callers accept
    either an already-created command or a module containing one.  File paths
    must point to a Python source file; import errors raised by the module are
    intentionally propagated to make broken plugins visible to the caller.
    """
    # Importing ``Command`` at module import time would create a cycle because
    # ``core`` imports parser, which imports this module.
    from .core import Command as RuntimeCommand

    if isinstance(module, RuntimeCommand):
        return module

    if isinstance(module, Path):
        path = module
    elif isinstance(module, str):
        candidate = Path(module)
        if candidate.suffix == ".py" or candidate.is_file():
            path = candidate
        else:
            return importlib.import_module(module)
    else:
        raise TypeError("module must be a dotted module name, Python file path, or Command")

    path = path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"module file does not exist: {path}")
    if path.suffix != ".py":
        raise ValueError(f"module file must have a .py extension: {path}")

    digest = hashlib.sha256(os.fspath(path).encode()).hexdigest()[:12]
    module_name = f"_shipyard_plugin_{path.stem}_{digest}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not create an import specification for {path}")

    loaded_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded_module)
    return loaded_module


def atomic_write(path: Path | str, data: dict[str, str] | str) -> None:
    """Atomically replace *path* with text or a JSON object.

    Dictionaries are written as stable, indented JSON.  The temporary file is
    created beside the target so ``os.replace`` is atomic on the same
    filesystem.  Parent directories are created when needed.
    """
    target = Path(path)
    if target.exists() and target.is_dir():
        raise IsADirectoryError(target)

    if isinstance(data, dict):
        if not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in data.items()
        ):
            raise TypeError("dictionary data must have string keys and values")
        contents = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    elif isinstance(data, str):
        contents = data
    else:
        raise TypeError("data must be a string or a dictionary of strings")

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(contents)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        os.replace(temporary_path, target)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def safe_read(path: Path | str) -> dict[str, str] | str | None:
    """Read a UTF-8 file, returning ``None`` when it does not exist.

    JSON files written by :func:`atomic_write` are decoded back into a mapping;
    all other files are returned as text.  Read and decode errors are allowed
    to propagate so callers do not silently operate on corrupt metadata.
    """
    target = Path(path)
    try:
        contents = target.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None

    if target.suffix.lower() != ".json":
        return contents

    data = json.loads(contents)
    if not isinstance(data, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in data.items()
    ):
        raise ValueError(f"expected a JSON object with string keys and values: {target}")
    return data


def import_file(path: Path, cache: bool = False) -> ModuleType:
    """Import a Python source file, optionally retaining it in ``sys.modules``."""
    path = path.resolve()
    digest = hashlib.sha256(os.fspath(path).encode()).hexdigest()[:12]
    name = f"_shipyard_metadata_{path.stem}_{digest}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not create an import specification for {path}")
    module = importlib.util.module_from_spec(spec)
    if cache:
        import sys
        sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def error_to_warning(error_list: list[Exception]) -> None:
    """Write non-fatal registry failures to stderr."""
    import sys
    for error in error_list:
        print(f"warning: {error}", file=sys.stderr)


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


def best_matches(word: str, choices: list[str], n: int = 3) -> list[str]:
    """
    Return the `n` closest matches to `word` from `choices`.
    """
    return get_close_matches(word, choices, n=n, cutoff=0.0)