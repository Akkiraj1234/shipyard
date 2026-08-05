from .__version__ import __version__
from .core import Command


def build_root_command():
    pass


class RootCommand(Command):
    pass


# def create_registry(path: Path, show_error: bool = True) -> tuple[CommandRegistry, list[RegistryError]]:
#     """Discover immediate child commands without importing their implementations."""
#     registry: CommandRegistry = {}
#     errors: list[RegistryError] = []
#     if not path.is_dir():
#         return registry, errors

#     for item in sorted(path.iterdir()):
#         metadata_file = item / "metadata.py"
#         if not item.is_dir() or not metadata_file.is_file():
#             continue
#         try:
#             metadata_module = import_file(metadata_file, cache=False)
#             metadata = metadata_module.METADATA
#             if not isinstance(metadata, RegistryData):
#                 raise TypeError("METADATA must be a RegistryData instance")
#             if metadata.name in registry:
#                 raise ValueError(f"duplicate command name '{metadata.name}'")
#             metadata.path = item.resolve()
#             if metadata.entrypoint:
#                 module_name, separator, attribute = metadata.entrypoint.partition(":")
#                 if not separator or not module_name or not attribute:
#                     raise ValueError("entrypoint must have the form 'module:callable'")
#                 module_file = item / f"{module_name.replace('.', '/')}.py"
#                 metadata.entrypoint = f"{module_file}:{attribute}"
#             registry[metadata.name] = metadata
#         except Exception as error:
#             errors.append(RegistryError(item.name, metadata_file, error))

#     if show_error:
#         error_to_warning(errors)
#     return registry, errors
