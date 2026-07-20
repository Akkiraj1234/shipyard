from shipyard.types import RegistryData


METADATA = RegistryData(
    name = "init",
    description = "Initialize a new Shipyard project.",
    help = "Create a new Shipyard project.",
    hidden = False,
    entrypoint = "main:command",
    has_child = False
)
