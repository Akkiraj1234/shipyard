from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

from .error import RegistryError, UsageError
from .parser import ParserStream
from .types import CommandRegistry, GrammarRegistry, ParseResult, RegistryData
from .utils import error_to_warning, import_file, load_module


class Command:
    """A lazily-loaded command discovered from a ``metadata.py`` file."""

    def __init__(self, data: RegistryData):
        self.data = data
        self._built = False
        self.registry: CommandRegistry = {}
        self.module: ModuleType | None = None

    @property
    def name(self) -> str:
        return self.data.name

    def build(self) -> None:
        if self._built:
            return

        if self.data.path is None:
            raise RuntimeError(f"command '{self.data.name}' has no source path")

        children_path = self.data.path / "commands"
        if children_path.is_dir():
            self.registry, _ = create_registry(children_path)

        if self.data.entrypoint:
            module_path, separator, attribute = self.data.entrypoint.partition(":")
            if not separator or not attribute:
                raise UsageError(
                    f"invalid entrypoint for '{self.data.name}': {self.data.entrypoint}"
                )
            module = load_module(Path(module_path))
            if not isinstance(module, ModuleType):
                raise RuntimeError(f"invalid module for command '{self.data.name}'")
            if not callable(getattr(module, attribute, None)):
                raise UsageError(
                    f"entrypoint '{self.data.entrypoint}' is not callable"
                )
            self.module = module

        self._built = True

    def grammar(self) -> GrammarRegistry:
        if not self._built:
            raise RuntimeError("command must be built before reading its grammar")
        options = set(getattr(self.module, "options", {}).keys()) if self.module else set()
        flags = set(getattr(self.module, "flags", set())) if self.module else set()
        return GrammarRegistry(
            has_child=bool(self.registry),
            words=set(self.registry) if self.registry else set(getattr(self.module, "words", set())),
            options=options,
            flags=flags | {"help"},
        )

    def get_child(self, name: str) -> Command:
        try:
            return Command(self.registry[name])
        except KeyError as error:
            raise UsageError(f"unknown command '{name}'") from error

    def run(self, result: ParseResult) -> int:
        if self.module is None:
            return 0
        entrypoint = self.data.entrypoint.rpartition(":")[2]
        handler: Callable[[ParseResult], Any] = getattr(self.module, entrypoint)
        status = handler(result)
        return 0 if status is None else int(status)


def create_registry(path: Path, show_error: bool = True) -> tuple[CommandRegistry, list[RegistryError]]:
    """Discover immediate child commands without importing their implementations."""
    registry: CommandRegistry = {}
    errors: list[RegistryError] = []
    if not path.is_dir():
        return registry, errors

    for item in sorted(path.iterdir()):
        metadata_file = item / "metadata.py"
        if not item.is_dir() or not metadata_file.is_file():
            continue
        try:
            metadata_module = import_file(metadata_file, cache=False)
            metadata = metadata_module.METADATA
            if not isinstance(metadata, RegistryData):
                raise TypeError("METADATA must be a RegistryData instance")
            if metadata.name in registry:
                raise ValueError(f"duplicate command name '{metadata.name}'")
            metadata.path = item.resolve()
            if metadata.entrypoint:
                module_name, separator, attribute = metadata.entrypoint.partition(":")
                if not separator or not module_name or not attribute:
                    raise ValueError("entrypoint must have the form 'module:callable'")
                module_file = item / f"{module_name.replace('.', '/')}.py"
                metadata.entrypoint = f"{module_file}:{attribute}"
            registry[metadata.name] = metadata
        except Exception as error:
            errors.append(RegistryError(item.name, metadata_file, error))

    if show_error:
        error_to_warning(errors)
    return registry, errors


def build_root_command() -> Command:
    root = Path(__file__).resolve().parent
    return Command(
        RegistryData(
            name="shipyard",
            description="Developer workflow and project management CLI.",
            help="Shipyard manages repository metadata.",
            hidden=False,
            entrypoint=None,
            has_child=True,
            path=root,
        )
    )


def command_help(command: Command) -> str:
    command.build()
    command_name = "" if command.name == "shipyard" else f" {command.name}"
    lines = [f"Usage: shipyard{command_name}", "", command.data.description]
    visible = [data for data in command.registry.values() if not data.hidden]
    if visible:
        lines.extend(["", "Commands:"])
        lines.extend(f"  {data.name:<12} {data.description}" for data in visible)
    if command.module and (getattr(command.module, "options", {}) or getattr(command.module, "flags", set())):
        lines.extend(["", "Options:"])
        lines.extend(f"  --{name}" for name in getattr(command.module, "options", {}))
        lines.extend(f"  --{name}" for name in getattr(command.module, "flags", set()))
    return "\n".join(lines)


def execute(parser_stream: ParserStream, command: Command) -> int:
    """Resolve the command hierarchy, validate arguments, and dispatch once."""
    while True:
        command.build()
        result = parser_stream.parse(command.grammar())
        if result.child:
            command = command.get_child(result.child)
            continue
        if "help" in result.flags:
            print(command_help(command))
            return 0
        return command.run(result)
