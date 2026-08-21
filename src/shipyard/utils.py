from __future__ import annotations
from collections.abc import Generator
from difflib import get_close_matches
from contextlib import contextmanager
from pathlib import Path
from copy import deepcopy
from typing import IO, Any, List, TYPE_CHECKING, Callable
from types import ModuleType

import hashlib
import importlib
import importlib.util
import tempfile
import sys
import os

from .error import ShipyardFileError, ShipyardInternalError

if TYPE_CHECKING:
    from .core import Command



class _Skip:
    """
    Sentinel used by :class:`ListStream` to mark an item as excluded from
    stream traversal without removing it from the underlying sequence.

    ``SKIP`` preserves the original index of a masked item, allowing the
    stream to maintain a stable cursor position while treating the item as
    invisible during traversal. This is useful when an item must remain
    available for diagnostics or source inspection but should no longer be
    processed by the stream.

    The sentinel is compared by identity using ``is``.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return "SKIP"


class _Null:
    """
    Sentinel used to explicitly represent the absence of a value.

    ``NULL`` is used instead of ``None`` so that an absent value can be
    distinguished from ``None`` when ``None`` is a valid value.

    The sentinel is compared by identity using ``is``.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return "NULL"


SKIP = _Skip()
NULL = _Null()


class ListStream:
    """
    Cursor-based stream for sequential traversal of a list.

    The stream maintains a stable index into the original sequence while
    supporting cursor navigation, lookahead, and selective masking of items
    with the :data:`SKIP` sentinel.

    Masked items remain at their original positions and are ignored during
    traversal. This allows the active stream to exclude items without
    changing their original indexes, preserving the relationship between
    parser state and source positions.

    The stream maintains two list views:

    - ``original``: An untouched copy of the input sequence, preserved for
      source inspection and diagnostics.
    - ``items``: The active traversal sequence, where excluded items may be
      replaced with :data:`SKIP`.

    The cursor invariant is that ``idx`` always points to a traversable item
    or to ``end_idx`` when the stream is exhausted.
    """

    def __init__(self, items: List, s_idx: int = 0):
        """
        Initialize the stream with a sequence and starting cursor position.

        Args:
            items: Sequence of items to traverse.
            s_idx: Initial cursor position within the sequence.
        """
        self.original = list(items)
        self.items = list(items)
        self.idx = s_idx
        self.end_idx = len(items)
    
    def _next_index(self, start: int) -> int:
        """
        Find the next traversable index from the given position.

        Starting at ``start``, advances past all positions containing
        :data:`SKIP`. If no traversable item remains, ``end_idx`` is returned,
        representing the end-of-file position.

        Args:
            start: Index from which to begin searching.

        Returns:
            The index of the next non-skipped item, or ``end_idx`` if the
            stream has no remaining traversable items.
        """
        idx = start

        while idx < self.end_idx and self.items[idx] is SKIP:
            idx += 1

        return idx

    @property
    def eof(self) -> bool:
        """
        Return whether the cursor has reached or passed the end of the stream.

        Returns:
            ``True`` when the cursor is at or beyond ``end_idx``; otherwise ``False``.
        """
        return self.idx >= self.end_idx

    @property
    def current(self) -> Any | None:
        """
        Return the item at the current cursor position.

        The cursor is expected to point to a traversable item whenever the
        stream is not exhausted. Reaching a :data:`SKIP` item at the current
        position indicates a violation of the stream's traversal invariant
        and raises :class:`ShipyardInternalError`.

        Returns:
            The current item, or ``None`` if the stream is exhausted.

        Raises:
            ShipyardInternalError: If the cursor points to a :data:`SKIP`
                item while the stream is not exhausted.
        """
        if self.eof:
            return None

        # its handling this error becuse of invariant
        # that its never get skip idx
        if self.items[self.idx] is SKIP:
            raise ShipyardInternalError(
                "ListStream invariant violated: current item is SKIP"
            )
        
        return self.items[self.idx]

    @property
    def peek(self) -> Any | None:
        """
        Return the next traversable item without advancing the cursor.

        Skipped positions are ignored while searching for the next item.
        Calling this method does not modify the current cursor position.

        Returns:
            The next non-skipped item, or ``None`` if no traversable item
            remains.
        """
        idx = self._next_index(self.idx + 1)
        
        if idx >= self.end_idx:
            return None
        
        return self.items[idx]

    def move(self, count: int = 1) -> None:
        """
        Advance the cursor by the requested number of traversable items.

        Skipped positions are ignored during traversal. If the stream reaches
        the end before the requested number of moves is completed, traversal
        stops at the end-of-file position.

        Args:
            count: Number of traversable items to advance over.
        """
        for _ in range(count):
            if self.eof: break
            self.idx = self._next_index(self.idx + 1)
        
    def next(self) -> Any | None:
        """
        Advance the cursor by one traversable item and return the new item.

        Returns:
            The item at the new cursor position, or ``None`` if advancing
            reaches the end of the stream.
        """
        self.move()
        return self.current
    
    def remove_items(
        self,
        removable: list[str],
        key: Callable[[Any], Any] | None = None,
    ) -> list[str]:
        """
        Mark matching items as excluded from stream traversal.

        Matching positions are replaced with :data:`SKIP` rather than being
        physically removed from the active sequence. This preserves their
        original indexes while preventing them from being returned during
        traversal.

        If ``key`` is provided, it extracts the value used for matching each
        item. This is useful when stream items are structured objects, such as
        parser tokens, and the match should be performed against one field.
        If the current position is skipped, the cursor advances to the next
        traversable item or EOF.

        Args:
            removable: Values identifying items to exclude from stream traversal.
            key: Optional function used to extract a comparison value from each
                item before matching.

        Returns:
            A list containing the values of items that were successfully marked
            as skipped.
        """
        items = set(removable)
        found = []

        for idx, item in enumerate(self.items):
            candidate = key(item) if key else item
            
            if candidate in items:
                found.append(candidate)
                self.items[idx] = SKIP

        if not self.eof and self.items[self.idx] is SKIP:
            self.idx = self._next_index(self.idx)

        return found
            
    def __str__(self) -> str:
        """
        Return a human-readable representation of the stream and cursor state.

        The representation displays all positions in the active sequence and
        marks the current cursor position. When the cursor has reached the
        end of the stream, an explicit EOF marker is displayed.

        Returns:
            A formatted string describing the current stream state.
        """
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


class DictBacked:
    """
    Base class for objects whose attributes are backed by a dictionary.

    Dictionary keys are exposed as object attributes, allowing values to be
    accessed directly using attribute notation. The underlying dictionary can
    be replaced or updated at any time using :meth:`update`.

    Args:
        data: Dictionary containing attribute names and their corresponding
            values.
    """
    def __init__(self, data: dict[str, str]) -> None:
        self.data = data
        self.update()

    def update(self, data: dict[str, str] | None = None) -> None:
        """
        Update the attributes from the backing dictionary.

        If ``data`` is provided, it replaces the current backing dictionary
        before the attributes are updated. Existing attributes are overwritten
        when their corresponding keys are present in the dictionary.

        Args:
            data: Optional dictionary to use as the new backing data.
        """
        if data is not None:
            self.data = data

        for key, value in self.data.items():
            setattr(self, key, value)


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
    """
    Load a Python module by dotted name or file path.
    
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


def import_command_module(path: Path, command_dir: Path | None = None) -> ModuleType:
    """
    Import a module from an isolated Shipyard command package.

    The command directory must contain ``__init__.py``. It is loaded under a
    stable synthetic package name derived from its absolute path. Modules in
    that directory can therefore use relative imports such as
    ``from .logic import run`` without sharing an import namespace with other
    commands or plugins.

    Args:
        path: Python module file to import from the command package.
        command_dir: Root directory of the command package. Defaults to the
            directory containing ``path``.

    Returns:
        The imported command-package module.

    Raises:
        ImportError: If the command directory is not a Python package or the
            requested module cannot be loaded.
        ValueError: If ``path`` is outside the command package.
    """
    path = Path(path).resolve()
    command_dir = Path(command_dir or path.parent).resolve()
    init_file = command_dir / "__init__.py"

    if not path.is_file():
        raise FileNotFoundError(f"module file does not exist: {path}")
    if path.suffix != ".py":
        raise ValueError(f"module file must have a .py extension: {path}")
    if not init_file.is_file():
        raise ImportError(f"command package is missing __init__.py: {command_dir}")

    try:
        relative_path = path.relative_to(command_dir).with_suffix("")
    except ValueError as exc:
        raise ValueError(
            f"module file '{path}' is outside command package '{command_dir}'"
        ) from exc

    package_digest = hashlib.sha256(os.fspath(command_dir).encode()).hexdigest()[:12]
    package_name = f"_shipyard_command_{package_digest}"

    if package_name not in sys.modules:
        package_spec = importlib.util.spec_from_file_location(
            package_name,
            init_file,
            submodule_search_locations=[os.fspath(command_dir)],
        )
        if package_spec is None or package_spec.loader is None:
            raise ImportError(f"could not create command package for {command_dir}")

        package = importlib.util.module_from_spec(package_spec)
        sys.modules[package_name] = package

        try:
            package_spec.loader.exec_module(package)
        except Exception:
            sys.modules.pop(package_name, None)
            raise

    module_name = f"{package_name}.{'/'.join(relative_path.parts).replace('/', '.')}"

    if module_name in sys.modules:
        return sys.modules[module_name]

    module_spec = importlib.util.spec_from_file_location(module_name, path)
    if module_spec is None or module_spec.loader is None:
        raise ImportError(f"could not create import specification for {path}")

    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_name] = module

    try:
        module_spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise

    return module
