"""User-facing errors and rendering for the Shipyard command line."""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import get_close_matches
from pathlib import Path
import traceback
from typing import TYPE_CHECKING, Any, Iterable

from .types import TokenType

if TYPE_CHECKING:
    from .parser import ParserStream


RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _suggest(value: str, choices: Iterable[str]) -> str | None:
    """Return the closest known spelling of ``value``, when one exists."""
    matches = get_close_matches(value, sorted(set(choices)), n=1, cutoff=0.6)
    return matches[0] if matches else None


class ShipyardError(Exception):
    """Base class for errors Shipyard can explain directly to a user."""

    title = "error"

    def __init__(
        self,
        message: str,
        *,
        hint: str | None = None,
        details: Iterable[str] = (),
    ) -> None:
        self.message = message
        self.hint = hint
        self.details = tuple(details)
        super().__init__(message)

    def pretty(self) -> str:
        lines = [f"{RED}{BOLD}{self.title}:{RESET} {self.message}"]
        if self.details:
            lines.extend(["", *self.details])
        if self.hint:
            lines.extend(["", f"{CYAN}hint:{RESET} {self.hint}"])
        return "\n".join(lines)

    def debug(self) -> str:
        return repr(self)

    def __str__(self) -> str:
        return self.pretty()


class UsageError(ShipyardError):
    """The supplied command line does not match a command grammar."""

    title = "usage error"
    
    
class ShipyardInternalError(RuntimeError):
    """Raised when an internal application invariant is violated."""


class ShipyardParserError(UsageError):
    """A parse error with a pointer to the offending command token."""

    def __init__(
        self,
        stream: ParserStream,
        message: str,
        *,
        hint: str | None = None,
    ) -> None:
        self.stream = stream
        super().__init__(message, hint=hint)

    def _command_line(self) -> str:
        parts: list[str] = []
        pointer: list[str] = []
        for index, token in enumerate(self.stream.items):
            name = token["name"]
            value = token["value"]
            if token["type"] is TokenType.option:
                text = f"--{name}={value}"
            elif token["type"] is TokenType.flag:
                text = f"--{name}"
            else:
                text = str(name)
            parts.append(text)
            pointer.append("^" * len(text) if index == self.stream.idx else " " * len(text))
        return "$ shipyard " + " ".join(parts) + "\n" + "            " + " ".join(pointer)

    def pretty(self) -> str:
        self.details = (self._command_line(),)
        return super().pretty()


class UnknownCommandError(ShipyardParserError):
    """A requested subcommand is not registered at the current level."""

    def __init__(self, stream: ParserStream, command: str, choices: Iterable[str]) -> None:
        suggestion = _suggest(command, choices)
        hint = f"Did you mean 'shipyard {suggestion}'?" if suggestion else "Run 'shipyard --help' to see available commands."
        super().__init__(stream, f"unknown command '{command}'", hint=hint)


class InvalidInputError(ShipyardParserError):
    """An argument, flag, or option is invalid in the current command scope."""

    def __init__(
        self,
        stream: ParserStream,
        kind: str,
        value: str,
        choices: Iterable[str],
    ) -> None:
        prefix = "--" if kind in {"flag", "option"} else ""
        suggestion = _suggest(value, choices)
        hint = f"Did you mean '{prefix}{suggestion}'?" if suggestion else None
        super().__init__(stream, f"unknown {kind} '{prefix}{value}'", hint=hint)


class CommandLoadError(ShipyardError):
    """A discovered command cannot be instantiated from its metadata."""

    title = "command error"


@dataclass(slots=True)
class RegistryError(ShipyardError):
    """A command metadata file could not be loaded during discovery."""

    command: str
    path: Path
    cause: Exception
    title: str = field(init=False, default="registry error")

    def __post_init__(self) -> None:
        Exception.__init__(self, self.command)

    def pretty(self) -> str:
        cause = self.cause.message if isinstance(self.cause, ShipyardError) else str(self.cause)
        return (
            f"{YELLOW}{BOLD}warning:{RESET} could not load command '{self.command}'\n"
            f"location: {self.path}\n"
            f"reason: {cause}"
        )

    def __str__(self) -> str:
        return self.pretty()


class ShipyardFileError(ShipyardError):
    """A repository file could not be read, written, or parsed."""

    title = "file error"


class ShipYardConfigNotFoundError(ShipyardError):
    """No ``shipyard.toml`` was found while searching from a directory."""

    title = "configuration error"

    def __init__(self, searched_from: Path) -> None:
        super().__init__(
            "could not find shipyard.toml",
            details=(f"searched from: {searched_from}",),
            hint="Run 'shipyard init' to create a Shipyard project.",
        )


def shipyard_error_print(error: Exception, ctx: dict[str, Any]) -> int:
    """Render every exception at the CLI boundary and return a failure code."""
    if isinstance(error, ShipyardError):
        print(error.pretty())
    else:
        print(f"{RED}{BOLD}fatal:{RESET} Shipyard encountered an unexpected error")
        print(f"reason: {type(error).__name__}: {error}")

    if ctx.get("dev"):
        print()
        error_type = f"{type(error).__module__}.{type(error).__qualname__}"
        print(f"{CYAN}{BOLD}debug:{RESET} {error_type}")
        print("traceback:")
        print("".join(traceback.format_tb(error.__traceback__)).rstrip())

    return 2
