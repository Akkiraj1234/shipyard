from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypeAlias, TypedDict
from pathlib import Path
from enum import IntEnum



class TokenType(IntEnum):
    """
    Categories of tokens recognized from command-line input.
    """

    word = 0
    option = 1
    flag = 2


class Token(TypedDict):
    """
    Normalized token produced during lexical analysis.
    """

    type: TokenType
    name: str
    value: str | None


@dataclass(slots=True, frozen=True)
class GrammarRegistry:
    """
    Grammar definition for a command scope.
    """
    
    has_child: bool = False
    words: set[str] = field(default_factory=set)
    options: set[str] = field(default_factory=set)
    flags: set[str] = field(default_factory=set)

    
@dataclass(slots=True, frozen=True)
class ParseResult:
    """
    Normalized command input produced by ParserStream.
    """
    
    child: str | None = None
    arguments: list[str] = field(default_factory=list)
    options: dict[str, str] = field(default_factory=dict)
    flags: set[str] = field(default_factory=set)
    
    
@dataclass(slots=True)
class RegistryData:
    """
    Metadata stored for a command in the registry.
    """

    name: str
    description: str
    help: str

    hidden: bool = False
    has_child: bool = False
    # Whether this command can delegate input to a child command.
    # This does not mean the command must have a child.

    dir_path: Path | None = None
    # Directory containing this command's metadata and entrypoint.
    child_path: Path | None = None
    # Directory containing this command's child commands, if any.

    entry_class: str = ...
    # Import path of the command's entry class, relative to the project root.
    # Example: "doctor.main:DoctorCommand"


TokenList: TypeAlias = list[Token]

CommandRegistry = dict[str, RegistryData]
