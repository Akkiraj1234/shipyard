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
    its follow ADR-0001
    please check docs/architecture/decisions/ADR-0001 - Command Discovery.md
    """

    name: str
    description: str
    help: str
    hidden: bool = False

    dir_path: Path | str | None = None
    # Directory containing this command's metadata and entrypoint.

    child_path: Path | str | None = None
    # Directory containing this command's child commands.
    # If None, this command does not support child commands.

    entry_class: str | None = None
    # Import path of the command entry, relative to ``dir_path``.
    # Example: "main:command" or "doctor.main:DoctorCommand"
    
    @property
    def has_child(self) -> bool:
        """
        Whether this command supports child-command delegation.
        """
        return self.child_path is not None


TokenList: TypeAlias = list[Token]

CommandRegistry = dict[str, RegistryData]
