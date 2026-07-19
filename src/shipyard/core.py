from pathlib import Path

from .types import CommandRegistry, RegistryData
from .parser import ParserStream
from .error import RegistryError
from .utils import (
    import_file, 
    resolve_entrypoint, 
    error_to_warning
)



class Command:
    
    def __init__(self):
        pass
    
    @property
    def name(self) -> str:
        pass
    
    def get_child(self, name: str) -> Command:
        pass
    
    def grammar(self):
        pass
    
    def build(self):
        pass
    
    def run(self):
        pass
    
    def __bool__(self):
        return True


def create_registry(path: Path) -> tuple[CommandRegistry, list[RegistryError]]:
    """
    Discover commands and build a registry from their metadata.

    Each subdirectory is scanned for a ``metadata.py`` file. Valid command
    metadata is normalized, resolved, and added to the returned registry.
    Any errors encountered during discovery are collected and returned.
    """
    # TODO: fix duplicate commad issue later
    
    registry: CommandRegistry = {}
    errors: list[RegistryError] = []
    
    for item in path.iterdir():
        if not item.is_dir():
            continue
        
        metadata_file = item / "metadata.py"
        
        if not metadata_file.is_file():
            continue
        
        try:
            module = import_file(
                path = metadata_file,
                cache = False
            )
            metadata = module.METADATA
        
            if not isinstance(metadata, RegistryData):
                raise TypeError("METADATA must be a RegistryData instance.")
            
            metadata.path = item.resolve()
            metadata.entrypoint = resolve_entrypoint(
                metadata.entrypoint
            )
        
            registry[metadata.name] = metadata
        
        except Exception as e:
            errors.append(
                RegistryError(
                    command = item.name,
                    path = metadata_file,
                    cause = e
                )
            )
            
    return registry, errors


def build_root_command(path: Path) -> Command:
    """
    it will try to create a registery of commands
    by scanning foldder where each command registery
    folder inside .commands should have __init__.py 
    which should contain metadata of commands.
    its scan them and build command registery and then
    root command
    """
    registery, error = create_registry(Path)
    
    if error:
        error_to_warning(registery)
        
    


def execute(parser_stream: ParserStream, command: Command) -> int:
    """
    Resolve and execute a command from the command hierarchy.

    Starting with the provided command, the executor builds its grammar and
    parses the current input. If a child command is matched, execution
    continues with that child. Once a leaf command is reached, it is
    executed and its exit status is returned.
    """

    if parser_stream is None:
        raise ValueError("parser cannot be None")

    if command is None:
        raise ValueError("command cannot be None")

    while command:
        command.build()

        parser_result = parser_stream.parse(
            command.grammar()
        )

        if parser_result.child:
            command = command.get_child(
                parser_result.child
            )
            continue

        return command.run(parser_result)

    raise RuntimeError("Execution terminated unexpectedly.")