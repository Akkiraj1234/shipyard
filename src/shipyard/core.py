from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from pathlib import Path

from .config import load_config
from .parser import ParserStream
from .utils import import_file
from .error import CommandLoadError, RegistryError

from .types import (
    TokenList,
    TokenType,
    GrammarRegistry,
    RegistryData,
    ParseResult,
    CommandRegistry
)


def build_context() -> dict[str, Any]:
    """
    context build currently has simple logic
    """
    root_path, data = load_config()
    
    return {
        **data,
        "root_path": root_path
    }

class Command(ABC):
    """
    Base class for commands managed by the Shipyard command registry.

    A command is discovered from its ``metadata.py`` definition and
    loaded lazily when it needs to be executed. Commands may optionally
    delegate input to child commands before handling the remaining
    arguments themselves.
    """

    def __init__(self, root_ctx, name: str | None = None) -> None:
        """
        Initialize a command with its root execution context.

        Parameters
        ----------
        root_ctx
            Context shared across the command hierarchy.
        name
            Optional command name. When omitted, the class name is used.
        """
        
        self.root_ctx = root_ctx
        self.command_name = name
    
    @property
    def name(self) -> str:
        """
        Return the command's registered name.
        """
        
        return self.command_name or \
            self.__class__.__name__.lower()
    
    @property
    @abstractmethod
    def metadata(self) -> RegistryData:
        """
        Return the registry metadata for this command.
        """
        ...

    def bootstrap(self) -> dict[str, Any]:
        """
        Build and initialize the command's execution context.

        Returns
        -------
        dict[str, Any]
            The context created for the command.
        """
        
        self.ctx = build_context()
        return self.ctx
    
    @abstractmethod
    def grammar(self) -> GrammarRegistry:
        """
        Return the grammar used to parse this command's input.
        """
        ...
    
    @abstractmethod
    def get_child(self, name: str) -> Command:
        """
        Resolve and return a child command by name.

        Parameters
        ----------
        name
            Name of the child command to resolve.

        Returns
        -------
        Command
            The resolved child command.

        Raises
        ------
        KeyError
            If no child command with the given name exists.
        """
        ...
    
    @abstractmethod
    def child_metadata(self) -> CommandRegistry:
        """
        Return the registry metadata for this command's children.
        """
        ...
    
    @abstractmethod
    def run(self, result: ParseResult) -> int:
        """
        Execute the command using the parsed input.

        Parameters
        ----------
        result
            Parsed command-line input produced by the command's grammar.

        Returns
        -------
        int
            Process exit status returned by the command.
        """
        ...
    
    def _get_child_metadata(self, path: Path | str) -> tuple[CommandRegistry, list[RegistryError]]:
        """
        Discover and load child commands from a directory.

        Searches the given directory for command directories containing
        ``metadata.py`` files. Invalid command metadata is collected as
        a ``RegistryError`` so that one invalid command does not prevent
        other commands from being discovered.

        Returns
        -------
        tuple[CommandRegistry, list[RegistryError]]
            The discovered command registry and any errors encountered
            during discovery.
        """
        
        path = Path(path)
        registry: CommandRegistry = {}
        errors: list[RegistryError] = []
        
        if not path.is_dir():
            raise CommandLoadError(f"command directory does not exist: {path}")
        
        for item in sorted(path.iterdir()):
            if not item.is_dir():
                continue

            metadata_file = item / "metadata.py"
            if not metadata_file.is_file():
                continue
            
            try:
                metadata = self.__import_metadata(
                    metadata_file,
                    registry
                )
                registry[metadata.name] = metadata
                
            except Exception as error:
                errors.append(
                    RegistryError(item.name, metadata_file, error)
                )
                
        return registry, errors
    
    def _build_word_by_command_registry(self, command_registry: CommandRegistry):
        """
        Return command names as parser words.
        """
        return set(command_registry.keys())
    
    def __import_metadata(self, metadata_file: Path, registry: CommandRegistry) -> RegistryData:
            """Load, validate, and resolve command metadata.
    
            Imports the ``METADATA`` object from a command's ``metadata.py``,
            validates its registry definition, and resolves filesystem paths
            and the command entry class into usable forms.
    
            Raises
            ------
            TypeError
                If ``METADATA`` is not a ``RegistryData`` instance.
            ValueError
                If the command name is already registered or the entry class
                has an invalid format.
            NotADirectoryError
                If the configured child path does not point to a directory.
            FileNotFoundError
                If the entry class module does not exist.
            """
            
            metadata_module = import_file(metadata_file, cache = False)
            metadata = metadata_module.METADATA
            
            if not isinstance(metadata, RegistryData):
                raise CommandLoadError(
                    f"{metadata_file} must define METADATA as a RegistryData instance"
                )
            
            if metadata.name in registry:
                raise CommandLoadError(f"duplicate command name '{metadata.name}'")
            
            command_dir = metadata_file.parent.resolve()
            
            # resolving metadata.dir_path
            if metadata.dir_path is None:
                metadata.dir_path = command_dir
                
            else:
                metadata.dir_path = Path(metadata.dir_path)
                
                if not metadata.dir_path.is_absolute():
                    metadata.dir_path = command_dir / metadata.dir_path
                
                metadata.dir_path = metadata.dir_path.resolve()
                
            # resolve child_path
            if metadata.child_path is not None:
                metadata.child_path = Path(metadata.child_path)
                
                if not metadata.child_path.is_absolute():
                    metadata.child_path = (
                        metadata.dir_path / metadata.child_path
                    )
                
                metadata.child_path = metadata.child_path.resolve()
                
                if not metadata.child_path.is_dir():
                    raise CommandLoadError(
                        f"child command directory does not exist: {metadata.child_path}"
                    )
                
            # resolve entry class
            if metadata.entry_class:
                module_name, separator, attribute = (
                    metadata.entry_class.partition(":")
                )
                
                if not separator or not module_name or not attribute:
                    raise CommandLoadError(
                        "entry_class must have the form 'module:class'"
                    )
                
                module_file = (
                    metadata.dir_path
                    / f"{module_name.replace('.', '/')}.py"
                )
                
                if not module_file.is_file():
                    raise CommandLoadError(
                        f"entry class module not found: {module_file}"
                    )
                
                metadata.entry_class = f"{module_file}:{attribute}"
            
            return metadata



def command_help(command: Command) -> str:
    """
    hello keep it simple stupid
    """
    return command.metadata.help


def execute(parser_stream: ParserStream, command: Command) -> int:
    """
    Resolve the command hierarchy, validate arguments, and dispatch once.
    """
    while True:
        result = parser_stream.parse(
            command.grammar()
        )
        
        if result.child:
            command = command.get_child(
                result.child
            )
            continue
        
        return command.run(result)


def build_core_flag(parser: ParserStream) -> dict[str, bool]:
    """
    Extract recognized root-level flags from the token stream.

    Scans the parser's token list and returns a mapping of supported
    core flags that were provided on the command line. Unknown flags
    are ignored and left for later validation.

    Returns
    -------
    dict[str, bool]
        A mapping of each detected core flag to ``True``.
    """
    _CORE_ROOT_FLAGS = {
        "help",
        "dev",
        "no-color",
        "only-json",
    }
    
    items: TokenList = parser.items
    result: dict[str, bool] = {}

    for token in items:
        if token["type"] is TokenType.flag and token["name"] in _CORE_ROOT_FLAGS:
            result[token["name"]] = True
    
    return result


def cleanup(command: Command, ctx: dict[str, Any]) -> None:
    # no need right now
    pass


def load_command(root_ctx: dict[str, bool], metadata: RegistryData) -> Command:
    """
    Instantiate a command implementation declared by registry metadata.
    """
    
    if metadata.entry_class is None:
        raise CommandLoadError(f"command '{metadata.name}' has no entry_class")

    module_file, separator, attribute = metadata.entry_class.rpartition(":")
    if not separator:
        raise CommandLoadError(f"invalid entry_class for '{metadata.name}'")
    

    try:
        module = import_file(Path(module_file), cache=False)
    except (ImportError, OSError) as exc:
        raise CommandLoadError(
            f"could not import command '{metadata.name}' from {module_file}: {exc}"
        ) from exc
    try:
        entry = getattr(module, attribute)
    except AttributeError as exc:
        raise CommandLoadError(
            f"command '{metadata.name}' entry class '{attribute}' was not found"
        ) from exc
    
    if isinstance(entry, type) and issubclass(entry, Command):
        return entry(root_ctx, metadata.name)
    
    raise CommandLoadError(
        f"entry_class for '{metadata.name}' must resolve to a Command subclass"
    )
