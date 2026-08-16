from __future__ import annotations

from .metadata import METADATA
from shipyard import (
    Command, 
    GrammarRegistry, 
    ParseResult
)


class InitCommand(Command):
    
    flags = {"force"}
    
    def __init__(self, root_ctx, name = None):
        super().__init__(root_ctx, name)
        
    @property
    def metadata(self):
        return METADATA
    
    def grammar(self): 
        return GrammarRegistry(
            has_child = self.metadata.has_child,
            words = set(self.child_metadata()),
            flags = InitCommand.flags
        )
    
    def run(self, result: ParseResult) -> int:
        self.bootstrap()
        return 0