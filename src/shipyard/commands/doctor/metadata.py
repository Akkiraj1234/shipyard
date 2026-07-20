from shipyard.types import RegistryData


METADATA = RegistryData(
    name = "doctor",
    description = "Check the Shipyard installation and project environment.",
    help = "Run diagnostics to verify the current Shipyard setup.",
    hidden = False,
    entrypoint = "main:command",
    has_child = False
)
