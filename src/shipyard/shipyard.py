from __future__ import annotations

from collections.abc import Callable
from typing import Any
from pathlib import Path

from .__version__ import __version__
from .core import Command, command_help, load_command
from .error import CommandLoadError
from .types import RegistryData, CommandRegistry, GrammarRegistry, ParseResult
from .utils import error_to_warning, import_file



SHIPYARD_METADATA = RegistryData(
    name = "shipyard",
    description = (
        "A Git-inspired project companion for managing project metadata, "
        "roadmaps, releases, and documentation."
    ),
    help = "Here are all the Shipyard commands.",
    hidden = False,
    child_path = Path(__file__).parent / "commands",
    entry_class = "shipyard:ShipyardCommand",
)


class ShipyardCommand(Command):
    
    CORE_FLAGS = {"version", "force"}
    
    def __init__(self, root_ctx: dict[str, bool]) -> None:
        super().__init__(root_ctx, SHIPYARD_METADATA.name)
        self._child_metadata: CommandRegistry | None = None
        
    @property
    def metadata(self) -> RegistryData:
        return SHIPYARD_METADATA
    
    def grammar(self) -> GrammarRegistry: 
        return GrammarRegistry(
            has_child = self.metadata.has_child,
            words = set(self.child_metadata()),
            flags = ShipyardCommand.CORE_FLAGS
        )
    
    def get_child(self, name: str) -> Command:
        metadata = self.child_metadata().get(name)
        
        if metadata is None:
            raise CommandLoadError(f"unknown command '{name}'")
        return load_command(self.root_ctx, metadata)
    
    def child_metadata(self) -> CommandRegistry:
        if self._child_metadata is None:
            self._child_metadata, errors = \
                self._get_child_metadata(
                    self.metadata.child_path
                )
            error_to_warning(errors)
        
        return self._child_metadata
    
    def run(self, result: ParseResult) -> int:
        print("i am runninge")
        return self.bootstrap()
