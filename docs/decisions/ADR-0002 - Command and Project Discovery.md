# ADR-0002: Command and Project Discovery

> **Status**: Accepted
> **Author**: Akhand Raj
> **Updated**: 14-08-2026

## Idea

Shipyard discovers commands through a hierarchical command registry.

A project provides a root command. The root command may expose child
commands, and each child command may expose its own child commands.

Command discovery is filesystem-based and metadata-driven. A command is
discovered from a command directory containing a `metadata.py` definition.
The metadata describes the command, its implementation, and optionally the
directory containing its children.

Discovery and execution are separate responsibilities:

- Discovery determines which commands exist and where they are.
- Parsing determines which command the user selected.
- Execution loads and runs the resolved command.

The command hierarchy is therefore discovered before the terminal command
executes its remaining arguments.

---

## Project

A Shipyard project provides the execution root for the command hierarchy.

The project root is responsible for providing the root command and the
configuration required by the command system.

The root command is the starting point of command discovery.

```text
Project
   │
   ▼
Root Command
   │
   ├── child
   ├── child
   └── child
```

The project itself is not treated as a command argument. It establishes the
environment in which the root command hierarchy is discovered and executed.

---

## Command

A command is a registered unit of functionality in the Shipyard hierarchy.

A command is defined by its metadata and implementation.

Command metadata describes:

1. `name` — registered command name.
2. `description` — short command description.
3. `help` — command help information.
4. `hidden` — whether the command is hidden from discovery/help output.
5. `dir_path` — directory where the command exists.
6. `child_path` — directory containing the command's children.
7. `entry_class` — import path of the command implementation.
8. `has_child` — whether the command participates in child discovery.

The metadata describes the command's identity and location. The command class
provides its behavior.

---

## Command Directory

A command directory is a directory containing a `metadata.py` file.

```text
commands/
└── run/
    ├── metadata.py
    └── command.py
```

`metadata.py` must provide a valid `RegistryData` object.

A directory without `metadata.py` is not considered a command.

Files that are not command directories are ignored during discovery.

---

## Command Discovery

Command discovery searches the configured child directory for command
directories.

For each directory:

1. Check whether the directory contains `metadata.py`.
2. Import the metadata definition.
3. Validate that `METADATA` is a `RegistryData`.
4. Validate the command name.
5. Resolve the command directory.
6. Resolve the child directory, if one is configured.
7. Resolve the command entry class, if one is configured.
8. Register the command by name.

Discovery must not require importing the command implementation itself.

Command implementations are loaded lazily when the command is actually
resolved for execution.

```text
command directory
       │
       ▼
metadata.py
       │
       ▼
RegistryData
       │
       ▼
CommandRegistry
       │
       ▼
command selected
       │
       ▼
load entry_class
```

This keeps command discovery lightweight and allows invalid command
implementations to remain unloaded until they are actually required.

---

## Command Registry

A `CommandRegistry` maps command names to their registry metadata.

```text
CommandRegistry

"run"  → RegistryData(...)
"task" → RegistryData(...)
"init" → RegistryData(...)
```

The command name is the unique identifier within its parent command scope.

Two commands with the same name cannot exist in the same command scope.

Command names are scoped to their parent command. Therefore, the same name
may exist under different parents.

For example:

```text
shipyard
├── task
│   └── add
└── project
    └── add
```

`task add` and `project add` are valid because `add` belongs to different
command scopes.

---

## Child Commands

A command may optionally define a child command directory.

```text
shipyard
└── task
    ├── add
    ├── remove
    └── list
```

The parent command owns the child command domain.

A child command is discovered from the parent's configured `child_path`.

If a command does not provide a child directory, it has no discovered
children.

`Command` provides child discovery and caching by default. When a command has
a `child_path`, `child_metadata()` discovers that directory once, reports any
non-fatal registry warnings, and returns the cached registry. A command with
no `child_path` receives an empty registry. Therefore, normal parent and leaf
commands do not implement child lookup or child metadata methods.

The default `get_child(name)` resolves that name from the registry and lazily
loads the declared command class. A command may override `child_metadata()` or
`get_child()` only when it needs a custom child source or resolution behavior,
such as a plugin registry.

The existence of a child directory determines command structure. The
`GrammarRegistry.has_child` value determines whether the parser should
perform child discovery for the current command.

These concepts must remain separate:

- `child_path` describes where children exist.
- `has_child` describes how the current grammar handles input.

---

## Child Discovery

When the parser identifies a word as a child-command candidate, the current
command resolves that child from its command registry.

```text
current command
      │
      ▼
child registry
      │
      ▼
child name
      │
      ├── exists → load child
      │
      └── missing → UnknownCommandError
```

The parser does not search the filesystem during token parsing.

Filesystem discovery occurs when the command registry is constructed.

The parser only performs a registry lookup.

This keeps parsing deterministic and prevents filesystem concerns from being
mixed into token consumption.

---

## Hierarchical Discovery

Command discovery may continue through multiple levels.

For:

```text
shipyard task add hello.py
```

the hierarchy is resolved as:

```text
shipyard
   ↓
task
   ↓
add
```

After `add` is resolved, its grammar handles:

```text
hello.py
```

The hierarchy may contain any number of supported child levels.

Each level owns its own command scope and child registry.

---

## Parent and Child Behavior

A parent command is responsible for resolving its immediate children.

A child command does not search its parent's command directory.

Each command only knows about its own command scope.

For example:

```text
shipyard
└── task
    ├── add
    └── remove
```

`shipyard` knows about `task`.

`task` knows about `add` and `remove`.

`add` does not know about `remove`.

This prevents command implementations from depending on unrelated command
scopes.

---

## Parser and Discovery Boundary

The parser is responsible for navigating the already-discovered command
hierarchy.

The registry is responsible for discovering commands.

The command implementation is responsible for executing command behavior.

Therefore:

```text
Registry
    ↓
discovers commands

ParserStream
    ↓
selects commands

Command
    ↓
executes behavior
```

The parser must not inspect command directories directly.

The command implementation must not perform command discovery as part of
normal execution.

---

## Terminal Command

Command discovery ends when the resolved command does not produce another
child command from the remaining input.

The terminal command receives the remaining tokens and validates them using
its own `GrammarRegistry`.

```text
shipyard task add hello.py

shipyard
   ↓
task
   ↓
add
   ↓
terminal command
   ↓
parse hello.py
   ↓
run add
```

The terminal command is the only command responsible for interpreting the
remaining command-specific arguments.

This follows ADR-0001:

> The parser discovers the command. The terminal command handles its input.

---

## Same Parser Stream

The same `ParserStream` instance must be used throughout command discovery.

A child command must not create a new parser stream for its remaining input.

For example:

```text
shipyard task add hello.py
       │
       └── same ParserStream ────────────────┐
                                             │
       shipyard → task → add                 │
                                             ▼
                                      hello.py remains
```

This preserves a single cursor and a single source position throughout the
entire command hierarchy.

It also allows diagnostics to map parser positions back to the original
command line.

---

## Command Loading

Command implementations are loaded only after the command has been
resolved.

The registry stores the location of the entry class, but discovery does not
instantiate the command.

When execution resolves a command:

1. Resolve its `entry_class`.
2. Import the implementation module.
3. Resolve the entry class.
4. Verify that it is a `Command` subclass.
5. Instantiate the command.
6. Continue parsing or execute it as appropriate.

An invalid entry class is a command-loading error.

---

## Discovery Errors

An invalid command must not necessarily prevent unrelated commands from
being discovered.

When scanning a command directory, discovery collects registry errors for
individual invalid command definitions.

For example:

```text
commands/
├── run/
│   └── metadata.py      valid
├── task/
│   └── metadata.py      invalid
└── init/
    └── metadata.py      valid
```

The registry may contain:

```text
run
init
```

while retaining an error describing the invalid `task` command.

This allows discovery to report multiple invalid command definitions instead
of failing at the first invalid entry.

Critical failures that prevent the command registry itself from being
constructed may still abort discovery.

---

## Hidden Commands

A command may be marked as hidden through its metadata.

A hidden command:

- remains discoverable by name;
- may be executed normally;
- is omitted from normal command listings and help output.

Hidden status affects presentation, not command resolution.

---

## Unknown Commands

If a command scope has child discovery enabled and the parser encounters a
word that does not exist in that scope's registry, the word is an invalid
child command.

It must not be silently treated as an argument of the parent command.

```text
shipyard hello

hello
  ↓
child lookup
  ↓
not found
  ↓
UnknownCommandError
```

This follows ADR-0001.

---

## Command Scope

Every command has its own scope.

A command's scope consists of:

```text
Command
├── metadata
├── grammar
└── child registry
```

Child discovery operates only within the current scope.

A command cannot directly resolve a sibling or descendant outside its own
child registry.

---

## Discovery Invariants

The command system must maintain the following invariants:

1. Command names are unique within a command scope.
2. A command is discovered only from valid command metadata.
3. A command implementation is loaded lazily.
4. Child commands belong to their immediate parent scope.
5. The parser resolves children through a registry, not the filesystem.
6. The same `ParserStream` is used throughout command discovery.
7. The terminal command parses the remaining input.
8. Unknown child words produce `UnknownCommandError`.
9. Hidden commands remain executable.
10. Discovery errors from one invalid command do not automatically invalidate
   unrelated commands.

---

## Responsibility

The responsibilities are intentionally separated:

```text
Project
    ↓
provides the root environment

Command Registry
    ↓
discovers commands and their metadata

Command
    ↓
owns its command scope and behavior

Parser
    ↓
navigates the command hierarchy

Terminal Command
    ↓
parses and executes remaining input
```

In short:

> **The project provides the root.**
>
> **The registry discovers the hierarchy.**
>
> **The parser selects the command.**
>
> **The terminal command handles the input.**
