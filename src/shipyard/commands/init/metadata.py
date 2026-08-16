from shipyard import RegistryData
from pathlib import Path


METADATA = RegistryData(
    name = "init",
    description = "Initialize a new Shipyard project.",
    help = "Create a new Shipyard project.",
    hidden = False,
    
    dir_path = Path(__file__).parent,
    child_path = None,
    
    entry_class = "main:InitCommand"
)
