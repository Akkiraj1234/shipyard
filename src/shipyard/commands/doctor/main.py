from __future__ import annotations

from pathlib import Path

from shipyard import GrammarRegistry
from shipyard.config import CONFIG_FILE_NAME
from shipyard.types import ParseResult
from shipyard.core import Command
from .metadata import METADATA


flags: set[str] = set()
options: dict[str, str] = {}

_REQUIRED = (
    "README.md",
    "ROADMAP.md",
    "CHANGELOG.md",
    "ideas",
    ".shipyard",
    CONFIG_FILE_NAME,
)


def command(result: ParseResult) -> int:
    """Report whether the current repository has Shipyard's required files."""
    root = Path.cwd()
    missing = [item for item in _REQUIRED if not (root / item).exists()]
    if missing:
        print("Shipyard needs initialization:")
        print("\n".join(f"  missing {item}" for item in missing))
        print("Run: shipyard init")
        return 1
    print(f"Shipyard project is healthy: {root}")
    return 0


class DoctorCommand(Command):

    def __init__(self, root_ctx, name = None):
        super().__init__(root_ctx, name)
        
    @property
    def metadata(self):
        return METADATA
    
    def grammar(self): 
        return GrammarRegistry(
            has_child=self.metadata.has_child,
            words=set(self.child_metadata()),
        )
    
    def run(self, result: ParseResult) -> int:
        self.bootstrap()
        return 0