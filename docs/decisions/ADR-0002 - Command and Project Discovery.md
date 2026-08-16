# ADR-0002: Command and Project Discovery

> **Status**: Accepted  
> **Author**: Akhand Raj  
> **Updated**: 16-08-2026

## Table of Contents

- [Idea](#idea)
- [Project and Root Command](#project-and-root-command)
- [Command Metadata](#command-metadata)
- [Command Discovery](#command-discovery)
- [Command Hierarchy](#command-hierarchy)
- [Parser and Discovery Boundary](#parser-and-discovery-boundary)
- [Lazy Command Loading](#lazy-command-loading)
- [Command Execution and Output](#command-execution-and-output)
- [Discovery Errors](#discovery-errors)
- [Invariants](#invariants)
- [Responsibilities](#responsibilities)

---

## Idea

Shipyard uses a hierarchical, filesystem-based, metadata-driven command
registry.

- A project provides a root command.
- A command may expose child commands.
- Each child may expose its own children.
- Discovery, parsing, and execution are separate responsibilities.

```text
Project
  ↓
Root Command
  ↓
Child Command
  ↓
Terminal Command
```

The hierarchy is discovered before the terminal command handles its remaining
arguments.

---

## Project and Root Command

A Shipyard project provides the execution root for the command hierarchy.

The project establishes the environment in which the root command is discovered
and executed. The root command owns the first command scope.

```text
Project
  │
  ▼
Root Command
  ├── child
  ├── child
  └── child
```

The project itself is not treated as a command argument.

---

## Command Metadata

A command is a registered unit of functionality defined by metadata and an
implementation.

`RegistryData` describes:

- `name` — registered command name.
- `description` — short description.
- `help` — help information.
- `hidden` — whether it is hidden from normal listings.
- `dir_path` — command directory.
- `child_path` — optional child-command directory.
- `entry_class` — implementation entry point.
- `has_child` — whether the grammar supports child discovery.

Metadata defines the command's identity and location; the command class defines
its behavior.

---

## Command Discovery

A command is discovered from a command directory containing `metadata.py`.

Discovery:

1. Finds command directories.
2. Loads and validates `METADATA`.
3. Resolves the command and child paths.
4. Resolves the entry class.
5. Registers the command by name.

Discovery does **not** import the command implementation.

```text
command directory
      ↓
metadata.py
      ↓
RegistryData
      ↓
CommandRegistry
      ↓
command selected
      ↓
load entry_class
```

Command names are unique within their parent scope. The same name may exist
under different parents.

---

## Command Hierarchy

Each command owns its immediate child scope.

```text
shipyard
└── task
    ├── add
    ├── remove
    └── list
```

- The parent resolves its immediate children.
- A child does not search its parent's directory.
- A command does not directly resolve siblings.
- `child_path` describes where children exist.
- `has_child` describes how the current grammar handles input.

`Command.child_metadata()` provides default discovery and caching. Commands with
no `child_path` receive an empty registry. Custom child sources, such as plugin
registries, may override child discovery or resolution.

---

## Parser and Discovery Boundary

The parser navigates the already-discovered hierarchy. It must not search the
filesystem while consuming tokens.

```text
Command Registry
      ↓
ParserStream
      ↓
selected command
      ↓
Command
```

Responsibilities:

- **Registry** — discovers commands and builds registries.
- **ParserStream** — navigates the command hierarchy.
- **Command** — owns its command scope and behavior.
- **Terminal command** — handles the remaining command-specific input.

When a child is identified, the current command performs a registry lookup.

---

## Lazy Command Loading

Command implementations are loaded only after the command has been resolved.

Execution:

1. Resolves the declared `entry_class`.
2. Imports the implementation module.
3. Verifies that it is a `Command` subclass.
4. Instantiates the command.

This keeps discovery lightweight and unused implementations unloaded.

---

## Command Execution and Output

Commands **return results; they do not own presentation**.

A command implements `run()` to produce its result:

```python
def run(self, result: ParseResult):
    return {"version": __version__}
```

The main executor resolves the command hierarchy and calls `deco_run()`:

```text
execute()
   ↓
resolve command hierarchy
   ↓
deco_run()
   ↓
handle root/framework context
   ↓
command.run()
   ↓
result
   ↓
format / serialize / print
```

`deco_run()` owns framework-level behavior such as:

- global/root context values;
- help and development/debug behavior;
- traceback handling;
- color and output settings;
- `--only-json`;
- final result formatting and serialization.

Commands may return:

- `str` — textual result.
- `dict` — structured result.

Structured results are preferred when meaningful data exists.

For example:

```python
return {"version": __version__}
```

may produce:

```text
version: 1.0.0
```

normally, or:

```json
{"version": "1.0.0"}
```

with `--only-json`.

A text-only result may fall back to:

```json
{"result": "text output"}
```

`--only-json` requests JSON output but does **not** guarantee a stable,
schema-specific JSON representation for every command.

This keeps command behavior independent from presentation and gives plugins the
same output contract without requiring them to implement global CLI behavior.

---

## Discovery Errors

An invalid command must not automatically prevent unrelated commands from being
discovered.

For example:

```text
commands/
├── run/      valid
├── task/     invalid
└── init/     valid
```

The registry may still contain `run` and `init` while retaining the error for
`task`.

Critical failures that prevent the registry itself from being constructed may
still abort discovery.

---

## Invariants

The command system maintains these invariants:

1. Command names are unique within a command scope.
2. Commands are discovered only from valid metadata.
3. Implementations are loaded lazily.
4. Children belong to their immediate parent scope.
5. The parser resolves children through registries, not the filesystem.
6. The same `ParserStream` is used throughout the hierarchy.
7. The terminal command handles the remaining input.
8. Unknown child words produce `UnknownCommandError`.
9. Hidden commands remain executable.
10. One invalid command does not automatically invalidate unrelated commands.
11. Commands return results; the execution layer owns presentation.
12. `deco_run()` owns framework-level execution and output behavior.

---

## Responsibilities

```text
Project
  ↓
provides the root environment

Command Registry
  ↓
discovers commands and metadata

Command
  ↓
owns its scope and command behavior

ParserStream
  ↓
navigates the command hierarchy

Terminal Command
  ↓
parses the remaining input

deco_run()
  ↓
handles framework behavior and presentation
```

In short:

> **The project provides the root.**
>
> **The registry discovers the hierarchy.**
>
> **The parser selects the command.**
>
> **The terminal command handles the input.**
>
> **The command returns the result.**
>
> **`deco_run()` handles execution policy and presentation.**
