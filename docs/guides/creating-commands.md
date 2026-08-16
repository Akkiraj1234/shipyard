# Creating Shipyard Commands

This guide explains how to add a command to Shipyard's filesystem-based
command registry.

For command discovery and parser behavior, see:

- [ADR-0001 — Command Discovery](../decisions/ADR-0001%20-%20Command%20Discovery.md)
- [ADR-0002 — Command and Project Discovery](../decisions/ADR-0002%20-%20Command%20and%20Project%20Discovery.md)
- [ADR-0003 — Project Configuration and Root Discovery](../decisions/ADR-0003%20-%20Project%20Configuration%20and%20Root%20Discovery.md)

This guide focuses on **how to create a command**, not why the architecture
works that way.

## Command lifecycle

Shipyard discovers metadata first and loads the implementation only when the
command is selected.

```text
shipyard task add hello.py
        │
        ▼
    execute()
        │
        ├── ShipyardCommand
        ├── TaskCommand
        └── AddCommand
                │
                ▼
             run()
                │
                ▼
           command result
                │
                ▼
           deco_run()
                │
                ▼
        final terminal output
```

`execute()` resolves the command hierarchy using the same `ParserStream`.
`deco_run()` is the execution/output layer and calls the terminal command's
`run()`.

See ADR-0001 and ADR-0002 for the detailed rules.

---

## Command directory

Every command is a Python package containing `metadata.py` and its
implementation.

```text
src/shipyard/commands/
└── status/
    ├── __init__.py
    ├── metadata.py
    └── main.py
```

`__init__.py` is required for the command package.

The directory name does not register the command. `METADATA.name` does.

A larger command may contain additional modules:

```text
status/
├── __init__.py
├── metadata.py
├── main.py
├── logic.py
└── templates/
    └── status.py
```

Use normal relative imports inside the command package.

```python
from .logic import build_status
from .metadata import METADATA
```

Shipyard gives command packages isolated internal import names, so relative
imports remain local to the command.

---

## Define command metadata

`metadata.py` must export a `METADATA` value containing `RegistryData`.

```python
from shipyard.types import RegistryData


METADATA = RegistryData(
    name="status",
    description="Show the Shipyard project status.",
    help="Show the current Shipyard project status.",
    entry_class="main:StatusCommand",
)
```

Important fields:

- `name` — command name, such as `status`.
- `description` — short listing description.
- `help` — command help text.
- `hidden` — optionally hide the command from normal listings.
- `entry_class` — implementation in `module:ClassName` form.
- `child_path` — optional directory containing child commands.

> NOTE: Keep `metadata.py` small. Do not import or execute the command implementation
from metadata.

---

## Write a leaf command

A leaf command has no children.

```python
from shipyard.core import Command
from shipyard.types import GrammarRegistry, ParseResult

from .metadata import METADATA


class StatusCommand(Command):

    @property
    def metadata(self):
        return METADATA

    def grammar(self):
        return GrammarRegistry(
            flags={"verbose"},
        )

    def run(self, result: ParseResult):
        context = self.bootstrap()

        if "verbose" in result.flags:
            return context["project"]["description"]

        return context["project"]["name"]
```

A command's `run()` returns its **result**, not an exit status and not printed
output.

The framework handles presentation through `deco_run()`.

Commands may return:

- `str` — textual result.
- `dict` — structured result.

Prefer a dictionary when the command naturally produces structured data:

```python
return {
    "name": context["project"]["name"],
    "version": context["project"]["version"],
}
```

Do not call `print()` for normal command results.

---

## Define the grammar

`grammar()` declares the input accepted at the current command scope.

```python
GrammarRegistry(
    words={"start", "stop"},
    options={"output"},
    flags={"verbose", "force"},
)
```

- `words` — accepted command words.
- `options` — options that take a value.
- `flags` — switches without a value.

The parser removes leading hyphens.

Use:

```python
flags={"verbose"}
```

not:

```python
flags={"--verbose"}
```

The same names are used in `ParseResult`.

For parent-command behavior, see ADR-0001.

---

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

Parent metadata declares the child directory:

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

The parent implementation can use the child discovery provided by `Command`:

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

    def run(self, result: ParseResult):
        return {"command": "task"}
```

A parent `run()` is used only when no child command is selected.

You normally do not need to implement `child_metadata()` or `get_child()`.
`Command` provides them.

---

## Parent and child input

For:

```text
shipyard task add "write tests"
```

the hierarchy is:

```text
shipyard
   ↓
task
   ↓
add
   ↓
"write tests"
```

`task` resolves `add` as its child. `AddCommand.grammar()` then handles the
remaining input.

At a parent scope, an unknown word is treated as an unknown child command, not
as a normal argument.

See ADR-0001 for the parser rules.

---

## Context and configuration

`root_ctx` contains root-level CLI context collected before command execution,
such as global flags.

Use `self.bootstrap()` when a command needs the active project configuration:

```python
context = self.bootstrap()

project_root = context["root_path"]
project_name = context["project"]["name"]
```

Do not search for `shipyard.toml` inside a command. Project discovery and
configuration are handled by the framework.

See [ADR-0003](../decisions/ADR-0003%20-%20Project%20Configuration%20and%20Root%20Discovery.md).

`init` is the exception because it creates the project before
`shipyard.toml` exists. It should create the initial configuration before
calling `bootstrap()`.

---

## Global output behavior

Commands should return data and leave global output behavior to `deco_run()`.

Examples of framework-level behavior include:

- help;
- development/debug flags;
- traceback handling;
- output formatting;
- color settings;
- `--only-json`.

For example:

```python
return {"version": __version__}
```

can be presented normally as:

```text
version: 1.0.0
```

or as JSON when requested:

```json
{"version": "1.0.0"}
```

A text result can use the generic JSON form:

```json
{"result": "text output"}
```

`--only-json` controls output mode; it does not promise a fixed schema for every
command.

See ADR-0002 for the execution/output architecture.

---

## Custom child sources

Normal commands should use the default child discovery provided by `Command`.

Override `child_metadata()` only when children come from another source, such as:

- an installed plugin registry;
- a user-provided command location.

Override `get_child()` only when that source also requires custom command
resolution.

See ADR-0002 for the discovery model.

---

## Test a command

At minimum, test:

- valid grammar and command execution;
- accepted flags, options, and words;
- invalid input;
- child selection;
- configuration-dependent commands from nested directories;
- `init` without an existing `shipyard.toml`;
- returned command data and its expected output representation.

Keep tests focused on public command behavior rather than internal discovery
details.

---

## Common mistakes

- Returning `None` from `grammar()`.
- Printing command results from `run()` instead of returning them.
- Treating `run()`'s return value as an integer exit status.
- Writing `"--force"` instead of `"force"` in `flags`.
- Giving a leaf command a `child_path`.
- Importing the command class from `metadata.py`.
- Calling `bootstrap()` before `init` creates `shipyard.toml`.
- Treating an unknown parent-level word as a normal argument.
- Reimplementing child discovery when the default `Command` behavior is enough.

For architectural decisions, refer to the ADRs rather than duplicating their
full explanation here.
