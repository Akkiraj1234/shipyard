# from __future__ import annotations

# from dataclasses import dataclass
# from pathlib import Path
# from typing import TYPE_CHECKING, Any

# if TYPE_CHECKING:
#     from .parser import ParserStream
#     from .utils import best_matches


# # colors and stuff
# RESET = "\033[0m"
# UNDERLINE = "\033[4m"



# class ShipyardError(Exception):
#     """
#     Base class for errors that can be shown cleanly by the CLI.
#     """
#     def __init__(self, *args):
#         super().__init__(*args)


# class ShipyardFileError(ShipyardError):
#     def __init__(self, *args):
#         super().__init__(*args)
        

# class ShipyardParserError(ShipyardError):
#     def __init__(self, strem: ParserStream, message: str, *args):
#         self.strem: ParserStream = strem
#         self.message: str = message
#         super().__init__(*args)
        
#     def __str__(self):
#         print(f"ShipyardParserError: {self.message}\n > ")
#         first = []
#         secoend = []
        
#         for idx, item in enumerate(self.strem.items):
#             if idx == self.strem.idx:
#                 first.append(f"{UNDERLINE}{item}{RESET} ")
#                 "^".center(len(item)+1)
#                 secoend.append("^".center(len(item)+1))
#                 continue
            
#             first.append(f"item ")
#             secoend.append(f"{(len(item)+1)*' '}")
#         return f"{' '.join(first)}\n{' '.join(first)}" 
        
        
            


# @dataclass(slots=True)
# class RegistryError(ShipyardError):
#     """A command metadata file could not be loaded."""

#     command: str
#     path: Path
#     cause: Exception

#     def __str__(self) -> str:
#         return f"could not load command '{self.command}' from {self.path}: {self.cause}"


# class UsageError(ShipyardError):
#     """The supplied command line does not match a command grammar."""
    
    
# class ShipYardConfigNotFoundError(ShipyardError):
#     """pass"""
    


# def shipyard_error_print(error: ShipyardError, ctx: dict[str, Any]) -> int:
#     if not isinstance(error, ShipyardError):
#         print(error)
#         return 2

#     if ctx.get("dev", False):
#         print(error)  # Full error with logs, traceback, context, etc.
#     else:
#         print(error.message)  # Or error.summary / error.pretty_message

#     return 2
    
#     # if isinstance(error, ParserStream)
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .parser import ParserStream

RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[1m"
RESET = "\033[0m"


class ShipyardError(Exception):
    """Base class for all user-facing Shipyard errors."""

    title = "error"

    def pretty(self) -> str:
        return str(self)

    def debug(self) -> str:
        return repr(self)


class ShipyardParserError(ShipyardError):
    title = "parser"

    def __init__(
        self,
        stream: ParserStream,
        message: str,
        *,
        hint: str | None = None,
    ):
        self.stream = stream
        self.message = message
        self.hint = hint
        super().__init__(message)

    def _command_line(self) -> str:
        parts = []
        pointer = []

        for i, token in enumerate(self.stream.items):
            text = token["name"]

            parts.append(text)

            if i == self.stream.idx:
                pointer.append("^" * len(text))
            else:
                pointer.append(" " * len(text))

        return (
            "$ shipyard " + " ".join(parts)
            + "\n"
            + "            " + " ".join(pointer)
        )

    def pretty(self) -> str:
        out = [
            f"{RED}{BOLD}error:{RESET} {self.message}",
            "",
            self._command_line(),
        ]

        if self.hint:
            out.extend(
                [
                    "",
                    f"{CYAN}hint:{RESET} {self.hint}",
                ]
            )

        return "\n".join(out)

    def __str__(self):
        return self.pretty()


@dataclass(slots=True)
class RegistryError(ShipyardError):
    command: str
    path: Path
    cause: Exception

    def pretty(self):
        return (
            f"{RED}{BOLD}error:{RESET} "
            f"could not load command '{self.command}'\n"
            f"\n"
            f"location: {self.path}\n"
            f"reason:   {self.cause}"
        )

    def __str__(self):
        return self.pretty()


class ShipyardFileError(ShipyardError):
    pass


class UsageError(ShipyardError):
    pass


class ShipYardConfigNotFoundError(ShipyardError):
    pass


def shipyard_error_print(error: Exception, ctx: dict[str, Any]) -> int:
    if ctx.get("dev"):
        raise error

    if isinstance(error, ShipyardError):
        print(error.pretty())
    else:
        print(f"{RED}{BOLD}error:{RESET} {error}")

    return 2