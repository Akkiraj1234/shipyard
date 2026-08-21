from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import TypeAlias, TypedDict


class TokenType(IntEnum):
    """
    Categories of normalized command-line tokens.

    ``word`` represents a positional value, ``option`` represents a named
    value such as ``--output=file``, and ``flag`` represents a named boolean
    switch such as ``--verbose``.
    """

    word = 0
    option = 1
    flag = 2


class Token(TypedDict):
    """
    A normalized command-line token produced by the tokenizer.

    Attributes:
        type: The token category.
        name: A positional value, or an option or flag name without its
            leading hyphens.
        value: The value associated with an option; ``None`` for words and
            flags.
    """

    type: TokenType
    name: str
    value: str | None


TokenList: TypeAlias = list[Token]
"""The ordered token sequence consumed by :class:`ParserStream`."""


@dataclass(slots=True)
class RegistryData:
    """
    Metadata and filesystem structure for a discovered command.

    This type describes what a command is and where its implementation and
    child commands are located. In ADR-0001 terms, it is the structural source
    used by a command to build its input grammar; it is not itself parsed.

    Args:
        name: The command's registered name.
        description: A short summary suitable for command listings.
        help: Help text for the command.
        hidden: Whether the command is omitted from normal listings.
        dir_path: Directory containing the command metadata and entry module.
        child_path: Directory containing child commands, if any.
        entry_class: Import path for the command implementation.
    """

    name: str
    description: str
    help: str
    hidden: bool = False

    dir_path: Path | str | None = None
    # Directory containing this command's metadata and entrypoint.

    child_path: Path | str | None = None
    # A command has children only when this directory is configured.

    entry_class: str | None = None
    # Import path of the command entry, relative to ``dir_path``.
    # Example: "main:command" or "doctor.main:DoctorCommand"

    @property
    def has_child(self) -> bool:
        """
        Return whether this command has a child-command directory.

        ``child_path`` is the source of truth. Commands use this derived value
        when building a :class:`GrammarRegistry` for ADR-0001 command
        discovery.
        """
        return self.child_path is not None


@dataclass(slots=True, frozen=True)
class GrammarRegistry:
    """
    Input grammar for one command scope.

    The parser uses this value to decide how to interpret its current token.
    If ``has_child`` is true, a word token must name a child command from
    ``words``. Otherwise, ``words`` contains positional arguments accepted by
    the current command. Options and flags are always handled by the current
    command.

    Args:
        has_child: Whether word tokens trigger child-command discovery.
        words: Accepted child-command names or positional argument values,
            depending on ``has_child``.
        options: Accepted option names without leading hyphens.
        flags: Accepted flag names without leading hyphens.
    """

    has_child: bool = False
    words: set[str] = field(default_factory=set)
    options: set[str] = field(default_factory=set)
    flags: set[str] = field(default_factory=set)


@dataclass(slots=True, frozen=True)
class ParseResult:
    """
    The outcome of parsing one command scope.

    A non-``None`` ``child`` means the parser consumed a child-command name
    and the executor should descend into that command. When ``child`` is
    ``None``, the remaining fields contain input accepted by the current
    command.

    Args:
        child: The selected child-command name, if command discovery succeeded.
        arguments: Accepted positional argument values.
        options: Accepted option names mapped to their values.
        flags: Accepted flag names.
    """

    child: str | None = None
    arguments: list[str] = field(default_factory=list)
    options: dict[str, str] = field(default_factory=dict)
    flags: set[str] = field(default_factory=set)


CommandRegistry = dict[str, RegistryData]
"""A mapping of child-command names to their discovered metadata."""

