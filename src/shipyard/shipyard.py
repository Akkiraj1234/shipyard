from __future__ import annotations
from typing import Any
from pathlib import Path

from .__version__ import __version__
from .types import RegistryData, CommandRegistry, GrammarRegistry
from .core import Command



SHIPYARD_METADATA = RegistryData(
    name = "shipyard",
    description = (
        "A Git-inspired project companion for managing project metadata, "
        "roadmaps, releases, and documentation."
    ),
    help = "Here are all the Shipyard commands.",
    hidden = False,
    has_child = True,
    child_path = Path(__file__).resolve().parent,
)


class RootCommand(Command):
    def __init__(self, root_ctx, name = None):
        name = "shipyard"
        super().__init__(root_ctx, name)
        self.__child_metadata_data = None
        
    def metadata(self) -> dict[str, Any]:
        return SHIPYARD_METADATA
    
    def grammar(self) -> GrammarRegistry:
        
        words = self._build_word_by_command_registry(
            self.child_metadata()
        )
        optiones = set()
        flags = {
            "version",
            "force"
        }
        
        return GrammarRegistry(
            has_child = True,
            words = words,
            options = optiones,
            flags = flags
        )
    
    def get_child(self, name: str) -> RegistryData | None:
        data = self.child_metadata()
        return data.get(name, None)
    
    def child_metadata(self) -> CommandRegistry:
        if self.__child_metadata_data is not None:
            return self.__child_metadata_data
        
        metadata = self.metadata()
        child_path = metadata.child_path
        
        self.__child_metadata_data = \
            self._get_child_metadata(child_path)[0]
            
        return self.__child_metadata_data
    
    def run(self):
        print("i am runninge")