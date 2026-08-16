from shipyard import RegistryData
from pathlib import Path


METADATA = RegistryData(
    name = "doctor",
    description = "Check the Shipyard installation and project environment.",
    help = "Run diagnostics to verify the current Shipyard setup.",
    hidden = False,
    
    dir_path = Path(__file__).resolve().parent,
    child_path = None,
    
    entry_class = "main:DoctorCommand"
)
