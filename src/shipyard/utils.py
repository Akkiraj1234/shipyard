from __future__ import annotations
from collections.abc import Generator
from difflib import get_close_matches
from contextlib import contextmanager
from pathlib import Path
from copy import deepcopy
from typing import IO, Any, List, TYPE_CHECKING
from types import ModuleType

import hashlib
import importlib
import importlib.util
import tempfile
import sys
import os

from .error import ShipyardFileError

if TYPE_CHECKING:
    from .core import Command

class _Skip:
    __slots__ = ()

    def __repr__(self) -> str:
        return "SKIP"

SKIP = _Skip()



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
        self.original = List(items)
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


def atomic_write(
    path: Path | str, 
    data: str, 
    *,
    create: bool = False
    
) -> None:
    """
    Atomically write text to a file.

    The text is written to a temporary file in the destination directory,
    flushed and synchronized to disk, and then atomically replaces the
    target using :func:`os.replace`.

    Args:
        path:
            Path to the destination file.

        data:
            Text to write.

        create:
            If ``False`` (default), the destination file must already exist.
            If ``True``, parent directories are created as needed and the
            destination file is created if it does not exist.

    Raises:
        ShipyardFileError:
            If the destination file does not exist when ``create=False``,
            or if ``path`` refers to a directory.

        TypeError:
            If ``data`` is not a string.
    """
    target = Path(path)
    
    if not target.exists() and not create:
        raise ShipyardFileError(f"file does not exist: {target}")
    
    if target.exists() and target.is_dir():
        raise ShipyardFileError(f"path is a directory, not a file: {target}")
    
    if not isinstance(data, str):
        raise TypeError(f"data must be str, not {type(data).__name__}")

    
    # for safety
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
            temporary_file.write(data)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        # idk if its needed since file created by python themselves
        # if target.exists():
        #     shutil.copymode(target, temporary_path)
        
        os.replace(temporary_path, target)
        # make sure replace reach disk
        try:
            dir_fd = os.open(target.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            pass
        
        temporary_path = None
    
    except OSError as exc:
        raise ShipyardFileError(str(exc)) from exc
    
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    

@contextmanager
def safe_open(
    path: Path | str, 
    binary: bool = False
    
) -> Generator[IO[str] | IO[bytes] | None, None, None]:
    """
    Safely open a file for reading.

    Yields an open file object in text or binary mode. If the file does not
    exist, ``None`` is yielded instead of raising
    :class:`FileNotFoundError`.

    Raises:
        ShipyardFileError: If the file cannot be opened for any reason other
            than it not existing.
    """
    
    target = Path(path)
    mode = "rb" if binary else "r"
    kwargs = {} if binary else {"encoding": "utf-8"}
    
    try: 
        with target.open(mode, **kwargs) as file:
            yield file
        
    except FileNotFoundError:
        yield None
        
    except OSError as exc:
        raise ShipyardFileError(str(exc)) from exc
        

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


def error_to_warning(error_list: list[Exception]) -> None:
    """
    Write non-fatal error to stderr.
    """
    for error in error_list:
        print(f"warning: {error}", file=sys.stderr)


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


def import_file(path: Path, cache: bool = False) -> ModuleType:
    """
    Import a Python source file, optionally retaining it in ``sys.modules``.
    """
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