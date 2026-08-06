from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from pathlib import Path

from .config import load_config
from .parser import ParserStream
from .types import (
    TokenList, 
    TokenType, 
    GrammarRegistry, 
    RegistryData, 
    ParseResult,
    CommandRegistry
)
from .parser import ParserStream
from .utils import import_file 
from .error import RegistryError



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
    A lazily-loaded command discovered from a ``metadata.py`` file.
    """
    def __init__(self, root_ctx, name: str | None = None) -> None:
        self.root_ctx = root_ctx
        self.command_name = name
    
    @property
    def name(self) -> str:
        return self.command_name or \
            self.__class__.__name__.lower()
    
    def bootstrap(self) -> None:
        self.ctx = build_context()
    
    @abstractmethod
    def metadata(self) -> RegistryData:
        ...
    
    @abstractmethod
    def grammar(self) -> GrammarRegistry:
        ...
        
    @abstractmethod
    def get_child(self, name: str) -> Command:
        ...
        
    @abstractmethod
    def child_metadata(self) -> list[GrammarRegistry]:
        ...
        
    @abstractmethod
    def run(self, result: ParseResult) -> int:
        ...
        
    def _get_child_metadata(self, path: Path | str) -> tuple[CommandRegistry, list[RegistryError]]:
        registry: CommandRegistry = {}
        errors: list[RegistryError] = []
        
        if not path.is_dir():
            return registry, errors
        
        for item in sorted(path.iterdir()):
            metadata_file = item / "metadata.py"
            
            if not item.is_dir() or not metadata_file.is_file():
                continue
            
            try:
                metadata_module = import_file(metadata_file, cache=False)
                metadata = metadata_module.METADATA
                
                if not isinstance(metadata, RegistryData):
                    raise TypeError("METADATA must be a RegistryData instance")
                
                if metadata.name in registry:
                    raise ValueError(f"duplicate command name '{metadata.name}'")

                metadata.path = item.resolve()
                if metadata.entrypoint:
                    module_name, separator, attribute = metadata.entrypoint.partition(":")
                    
                    if not separator or not module_name or not attribute:
                        raise ValueError("entrypoint must have the form 'module:callable'")
                    
                    module_file = item / f"{module_name.replace('.', '/')}.py"
                    metadata.entrypoint = f"{module_file}:{attribute}"
                    
                registry[metadata.name] = metadata
                
            except Exception as error:
                errors.append(RegistryError(item.name, metadata_file, error))
        
        return registry, errors
    
    def _build_word_by_command_registry(self, command_registry: CommandRegistry):
        return set(command_registry.keys())



def command_help(command: Command) -> str:
    """
    hello keep it simple stupid
    """
    # do recursive search to create help message for current level
    # of commmand block
    print("hello i am help command")


def execute(parser_stream: ParserStream, command: Command, ctx: dict[str, Any]) -> int:
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