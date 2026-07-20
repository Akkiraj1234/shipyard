from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ShipyardError(Exception):
    """Base class for errors that can be shown cleanly by the CLI."""


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
