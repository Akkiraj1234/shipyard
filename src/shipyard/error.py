from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .parser import ParserStream
    from .utils import best_matches


# colors and stuff
RESET = "\033[0m"
UNDERLINE = "\033[4m"



class ShipyardError(Exception):
    """
    Base class for errors that can be shown cleanly by the CLI.
    """
    def __init__(self, *args):
        super().__init__(*args)


class ShipyardParserError(ShipyardError):
    def __init__(self, strem: ParserStream, message: str, *args):
        self.strem: ParserStream = ParserStream
        self.message: str = message
        super().__init__(*args)
        
    def __str__(self):
        print(f"ShipyardParserError: {self.message}\n > ")
        first = []
        secoend = []
        
        for idx, item in enumerate(self.strem.items):
            if idx == self.strem.idx:
                first.append(f"{UNDERLINE}{item}{RESET} ")
                "^".center(len(item)+1)
                secoend.append("^".center(len(item)+1))
                continue
            
            first.append(f"item ")
            secoend.append(f"{(len(item)+1)*' '}")
        
        print(" ".join(first))
        print(" ".join(secoend))
        print("Did you mean these")
        
        for i in range 
            
        
        
            


@dataclass(slots=True)
class RegistryError(ShipyardError):
    """A command metadata file could not be loaded."""

    command: str
    path: Path
    cause: Exception

    def __str__(self) -> str:
        return f"could not load command '{self.command}' from {self.path}: {self.cause}"


class UsageError(ShipyardError):
    """The supplied command line does not match a command grammar."""
    
    
class ShipYardConfigNotFoundError(ShipyardError):
    """pass"""
    


def shipyard_error_print(self, error: ShipyardError):
    if not isinstance(error, ShipyardError):
        print(error)
        return 2
    
    if isinstance(error, ParserStream)