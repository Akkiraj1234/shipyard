from __future__ import annotations
from pathlib import Path

from .__version__ import __version__
from .core import Command
from .types import (
    RegistryData, 
    GrammarRegistry, 
    ParseResult
)


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
    """
    Root command for the Shipyard CLI.

    Defines the root-level grammar, discovers Shipyard's child commands,
    initializes project context, and handles commands that belong directly
    to the Shipyard root.
    """
    
    CORE_FLAGS = {"version"}
    
    def __init__(self, root_ctx: dict[str, bool]) -> None:
        super().__init__(root_ctx, SHIPYARD_METADATA.name)
        
    @property
    def metadata(self) -> RegistryData:
        """
        Return the registry metadata describing the Shipyard root command.
        """
        return SHIPYARD_METADATA
    
    def grammar(self) -> GrammarRegistry:
        """
        Build the grammar for the Shipyard root command.

        The root grammar contains the dynamically discovered child commands
        and the flags supported directly by Shipyard.
        """
        return GrammarRegistry(
            has_child = self.metadata.has_child,
            words = set(self.child_metadata()),
            flags = ShipyardCommand.CORE_FLAGS
        )
    
    def run(self, result: ParseResult) -> int:
        """
        Execute the resolved Shipyard root command.

        Bootstraps the project context and combines it with the root CLI context
        before handling flags supported directly by Shipyard.
        """
        ctx = self.bootstrap()
        
        if "version" in result.flags:
            return {"version": __version__}
        
        
