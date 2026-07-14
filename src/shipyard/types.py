from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, TypeAlias, TypedDict



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
    name: str | None
    value: str | None


class GrammarRegistry(TypedDict):
    """
    Grammar definition for a command scope.
    """

    words: dict[str, Any]
    options: dict[str, Any]
    flags: dict[str, Any]
    accepts_arguments: bool


@dataclass(slots=True, frozen=True)
class ParseResult:
    """
    Normalized command input produced by ParserStream.
    """

    arguments: list[str] = field(default_factory=list)
    flags: set[str] = field(default_factory=set)
    options: dict[str, str] = field(default_factory=dict)


TokenList: TypeAlias = list[Token]
