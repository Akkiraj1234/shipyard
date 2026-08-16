# Creating Shipyard Commands

This guide explains how to add a command to Shipyard's filesystem-based
command registry.

Read [ADR-0001](../decisions/ADR-0001%20-%20Command%20Discovery.md) for the
parser's command-discovery rules and
[ADR-0002](../decisions/ADR-0002%20-%20Command%20and%20Project%20Discovery.md)
for metadata discovery and lazy loading.

## Command lifecycle

Shipyard discovers command metadata before it imports a command implementation.
The implementation is imported only after the user selects that command.

```text
shipyard task add hello.py
   │
   ▼
cli.main()
   │
   ▼
ShipyardCommand
   │
   ├── discover commands/task/metadata.py
   ├── load TaskCommand when "task" is selected
   ├── discover task children/add/metadata.py
   ├── load AddCommand when "add" is selected
   └── parse "hello.py" using AddCommand.grammar()
             │
             ▼
       AddCommand.run(ParseResult)
```

`execute()` in `core.py` repeats this process until parsing no longer finds a
child command. It then calls `run()` exactly once on the terminal command.

## Command directory

Every command is a directory containing a `metadata.py` file and its Python
implementation.

```text
src/shipyard/commands/
└── status/
    ├── metadata.py
    └── main.py
```

The directory name does not register a command by itself. `METADATA.name` in
`metadata.py` is the registered command name.

## Define command metadata

`metadata.py` must export a `METADATA` value that is a `RegistryData` object.

```python
from shipyard.types import RegistryData


METADATA = RegistryData(
    name="status",
    description="Show the Shipyard project status.",
    help="Show the current Shipyard project status.",
    entry_class="main:StatusCommand",
)
```

The fields have these responsibilities:

- `name`: the word the user types, such as `status` in `shipyard status`.
- `description`: a short summary for command listings.
- `help`: longer command help text.
- `hidden`: optional; excludes the command from normal listings when `True`.
- `entry_class`: the implementation in `module:ClassName` form, relative to
  the command directory. For example, `main:StatusCommand` means
  `main.py`, class `StatusCommand`.
- `child_path`: optional directory of child commands. Omit it for a leaf
  command.

Do not import the command class from `metadata.py`. Metadata is loaded during
discovery, so it must stay small and free of command-execution work.

## Write a leaf command

A leaf command has no child commands. It implements `metadata`, `grammar`, and
`run`. `Command` supplies an empty child registry and normal child lookup, so
a leaf does not implement child methods.

```python
from shipyard.core import Command
from shipyard.types import GrammarRegistry, ParseResult

from .metadata import METADATA


class StatusCommand(Command):
    @property
    def metadata(self):
        return METADATA

    def grammar(self):
        return GrammarRegistry(flags={"verbose"})

    def run(self, result: ParseResult) -> int:
        context = self.bootstrap()

        if "verbose" in result.flags:
            print(context["project"]["description"])
        else:
            print(context["project"]["name"])

        return 0
```

`grammar()` declares the input the command accepts:

```python
GrammarRegistry(
    words={"start", "stop"},
    options={"output"},
    flags={"verbose", "force"},
)
```

- `words` are accepted positional words for a leaf command.
- `options` accept a value, such as `--output report.json` or
  `--output=report.json`.
- `flags` are switches, such as `--verbose`.

The parser removes the leading hyphens. Use `"verbose"`, not `"--verbose"`,
in a grammar and in `result.flags`.

`run()` receives the validated `ParseResult` and must return an integer exit
status: `0` for success and a non-zero value for an expected failure.

## Write a parent command

A parent command owns a directory of child commands.

```text
src/shipyard/commands/
└── task/
    ├── metadata.py
    ├── main.py
    └── children/
        └── add/
            ├── metadata.py
            └── main.py
```

The parent metadata declares the child directory:

```python
from shipyard.types import RegistryData


METADATA = RegistryData(
    name="task",
    description="Manage working tasks.",
    help="Create, update, and list working tasks.",
    child_path="children",
    entry_class="main:TaskCommand",
)
```

The parent implementation also inherits child discovery, caching, and lookup
from `Command`. The base class uses `METADATA.child_path` to discover child
metadata, reports non-fatal discovery warnings, caches the result, and lazily
loads the selected child class.

```python
from shipyard.core import Command
from shipyard.types import GrammarRegistry, ParseResult

from .metadata import METADATA


class TaskCommand(Command):
    @property
    def metadata(self):
        return METADATA

    def grammar(self):
        return GrammarRegistry(
            has_child=self.metadata.has_child,
            words=set(self.child_metadata()),
        )

    def run(self, result: ParseResult) -> int:
        # This runs only when no child command was selected.
        return 0
```

Use the same `metadata.py` and leaf-command structure for the `add` child.
Its `entry_class` is resolved relative to `children/add/`.

## How parent and child grammars differ

When `child_path` is set, `metadata.has_child` is `True`. At that scope:

- a word is treated as a child-command name;
- an option or flag is parsed by the parent command;
- an unknown word raises `UnknownCommandError`;
- no input produces an empty `ParseResult` for the parent command.

After Shipyard descends into a leaf command, its grammar parses the remaining
words, options, and flags as that command's input.

For example:

```text
shipyard task add "write tests"
         │    │   │
         │    │   └── argument for AddCommand
         │    └────── child of TaskCommand
         └─────────── child of ShipyardCommand
```

## Context and configuration

`root_ctx` contains root CLI flags collected before command parsing, such as
`dev` or `only-json`.

Call `self.bootstrap()` in `run()` when the command needs the active project
configuration. It loads `shipyard.toml` and returns a context containing the
configuration plus `root_path`.

```python
context = self.bootstrap()
project_root = context["root_path"]
project_name = context["project"]["name"]
```

Do not search for `shipyard.toml` separately inside a command. See the
[configuration guide](configuration.md) for the configuration fields.

`init` is the exception: it creates a project before `shipyard.toml` exists.
Its `run()` must create the initial files directly and should not call
`bootstrap()` before it creates the configuration.

## Custom child sources

The default child behavior is correct for normal Shipyard commands at every
level. Override `child_metadata()` only when a command gets children from a
different source, such as an installed plugin registry or a user-provided
command location. Override `get_child()` only when that custom source also
needs a different way of loading the selected command.

## Test a command

Test the public command behavior and its grammar. At minimum, cover:

- successful execution returns `0`;
- accepted flags, options, and positional words reach `run()` correctly;
- unknown flags, options, and arguments fail;
- child command selection loads the expected child;
- commands requiring configuration work from a nested project directory;
- `init` works in a directory without `shipyard.toml`.

The existing `test/test_core.py` shows small command doubles for testing
`execute()`, metadata discovery, and lazy loading.

## Current implementation status

The framework in `core.py`, `parser.py`, and `shipyard.py` supports this
model. The existing `init` and `doctor` command classes are still scaffolding:
their real helper functions are not yet connected to `run()`, and their
abstract methods currently return `None`.

When wiring them up, make each class return its `METADATA`, return a real
`GrammarRegistry`, and return an integer from `run()`. Both leaf and normal
parent commands inherit child discovery from `Command`. Move or call the
existing helper logic from that `run()` method.

## Common mistakes

- Returning `None` from `grammar()` instead of `GrammarRegistry(...)`.
- Returning a dictionary or string from `run()` instead of an integer exit
  status.
- Writing `"--force"` in `flags`; use `"force"`.
- Giving a leaf command a `child_path`.
- Importing the command class from `metadata.py`.
- Calling `bootstrap()` before `init` has created `shipyard.toml`.
- Treating an unknown word under a parent command as a normal argument. Under
  a parent, words are child-command candidates by design.
