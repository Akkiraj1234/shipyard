from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, final
from pathlib import Path

from .config import load_config, config, Config
from .parser import ParserStream
from .utils import error_to_warning, import_command_module
from .error import CommandLoadError, RegistryError
from .output import OutputFormatter

from .types import (
    GrammarRegistry,
    RegistryData,
    ParseResult,
    CommandRegistry
)

_CORE_ROOT_FLAGS = {
    "help",
    "no-color",
    "only-json",
    "dev", 
    "dev-trackback" 
}



def build_context() -> Config:
    """
    Initialize and return the shared project configuration.

    Project configuration is loaded lazily when a command requires it.
    If the shared configuration has already been initialized, the existing
    instance is returned unchanged.
    """
    if config.initialized:
        return config

    root_path, data = load_config()

    config.initialize(
        toml_ctx = data,
        dir_path = root_path,
    )

    return config


class Command(ABC):
    """
    Base class for commands managed by the Shipyard command registry.

    A command is discovered from its ``metadata.py`` definition and
    loaded lazily when it needs to be executed. Commands may optionally
    delegate input to child commands before handling the remaining
    arguments themselves.
    """

    def __init__(self, name: str | None = None) -> None:
        """
        Initialize a command.

        Parameters
        ----------
        name
            Optional registered command name. When omitted, the class name
            is used.
        """
        
        self.command_name = name
        self._child_metadata: CommandRegistry | None = None
    
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

    def bootstrap(self) -> Config:
        """
        Initialize project configuration for the current command.

        Returns
        -------
        Config
            The shared runtime configuration instance.
        """
        
        config = build_context()
        return config
    
    @abstractmethod
    def grammar(self) -> GrammarRegistry:
        """
        Return the grammar used to parse this command's input.
        """
        ...
    
    def get_child(self, name: str) -> Command:
        """
        Resolve and return a child command by name.

        The default implementation resolves a child from ``child_metadata()``
        and loads its declared command class. Normal parent and leaf commands
        inherit this behavior.

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
        CommandLoadError
            If no child command with the given name exists.
        """
        metadata = self.child_metadata().get(name)

        if metadata is None:
            raise CommandLoadError(f"unknown command '{name}'")

        return load_command( metadata )
    
    def child_metadata(self) -> CommandRegistry:
        """
        Return the registry metadata for this command's children.

        The default implementation discovers and caches metadata from the
        command's configured ``child_path``. Discovery warnings are rendered
        without preventing valid children from being used.

        Leaf commands have no ``child_path``, so they receive an empty
        registry. Override this method only when children come from a custom
        source, such as a plugin registry.
        """
        if self._child_metadata is None:
            if self.metadata.child_path is None:
                self._child_metadata = {}
                
            else:
                self._child_metadata, errors = self._get_child_metadata(
                    self.metadata.child_path
                )
                error_to_warning(errors)

        return self._child_metadata
    
    @abstractmethod
    def run(self, result: ParseResult) -> str | dict[str, Any]:
        """
        Execute the command and return its result.

        Parameters
        ----------
        result
            Parsed command-line input produced by the command's grammar.

        Returns
        -------
        str | dict[str, Any]
            Command result consumed by Shipyard's output layer.
        """
        ...
    
    def _get_child_metadata(self, path: Path | str) -> tuple[CommandRegistry, list[RegistryError]]:
        """
        Discover and load child commands from a directory.

        Searches the given directory for command directories containing
        ``metadata.py`` files. Invalid command metadata is collected as
        a ``RegistryError`` so that one invalid command does not prevent
        other commands from being discovered.
        follow ADR-0002

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
        """
        Load, validate, and resolve command metadata.

        Imports the ``METADATA`` object from a command's ``metadata.py``,
        validates its registry definition, and resolves filesystem paths
        and the command entry class into usable forms.
        its follow ADR-0002

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
        
        metadata_module = import_command_module(
            metadata_file,
            metadata_file.parent,
        )
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
            
            module_path = Path(module_name)

            if module_path.is_absolute():
                module_file = module_path
            else:
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
    
    @final
    def deco_run(self, parser_stream: ParserStream) -> int:
        """
        Execute a resolved command through Shipyard's common runtime pipeline.

        Handles framework-level behavior such as help, invokes the command's
        ``run()`` method, and passes the returned result to the output layer.

        Returns
        -------
        int
            Process exit status for successful command execution.
        """
        if config.get_flag("settings.help"):
            value = command_help(self)
            
        else: 
            value = self.run(parser_stream)

        print_output(value)
        return 0


def print_output(data: object) -> None:
    """
    Format and print a command result according to the active output mode.

    JSON output is selected through the shared runtime configuration;
    otherwise the human-readable formatter is used.
    """
    formatter = OutputFormatter()
    
    if config.get("settings.only-json"):
        output = formatter.json(data)
    else:
        output = formatter.format(data)

    print(output)
               

def command_help(command: Command) -> str:
    """
    hello keep it simple stupid
    """
    return command.metadata.help


def execute(parser_stream: ParserStream, command: Command) -> int:
    """
    Resolve the command hierarchy, validate arguments, and dispatch once.
    its follow ADR-0001
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
        
        return command.deco_run(result)


def build_core_flag(parser: ParserStream) -> None:
    """
    Extract recognized root-level flags from the token stream.

    Recognized core flags are removed from the parser and added to the
    runtime configuration under the ``settings`` section. Each detected
    flag
    is stored with a boolean value of ``True``.

    Unknown flags are left untouched for later validation.
    """
    result: dict[str, bool] = {}
    
    flags = parser.remove_items(
        _CORE_ROOT_FLAGS,
        key = lambda token: token["name"]
    )

    for flag in flags:
        result[flag] = True
    
    config.initialize(
        root_ctx = {"settings": result}
    )


def cleanup(command: Command) -> None:
    """
    Persist pending project configuration changes.

    ``Config.save()`` safely does nothing when project configuration has not
    been initialized or when no changes are pending.
    """
    config.save()


def load_command(metadata: RegistryData) -> Command:
    """
    Instantiate a command implementation declared by registry metadata.
    follow ADR-0002
    """
    
    if metadata.entry_class is None:
        raise CommandLoadError(f"command '{metadata.name}' has no entry_class")

    module_file, separator, attribute = metadata.entry_class.rpartition(":")
    if not separator:
        raise CommandLoadError(f"invalid entry_class for '{metadata.name}'")

    try:
        module = import_command_module(
            Path(module_file),
            metadata.dir_path,
        )
        
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
        return entry(metadata.name)
    
    raise CommandLoadError(
        f"entry_class for '{metadata.name}' must resolve to a Command subclass"
    )
