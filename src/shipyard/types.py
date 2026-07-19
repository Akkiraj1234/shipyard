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
    
    has_child: bool = True
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
    hidden: bool
    entrypoint: str

    path: Path | None = None


TokenList: TypeAlias = list[Token]

CommandRegistry = dict[str, RegistryData]