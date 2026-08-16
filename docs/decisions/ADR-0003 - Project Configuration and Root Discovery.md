# ADR-0003: Project Configuration and Root Discovery

> **Status**: Accepted  
> **Author**: Akhand Raj  
> **Updated**: 16-08-2026

## Table of Contents

- [Idea](#idea)
- [Project Discovery](#project-discovery)
- [Rules](#rules)
- [Configuration Structure](#configuration-structure)
- [Configuration Loading](#configuration-loading)
- [Command Context](#command-context)
- [Why](#why)
- [Examples](#examples)
- [Responsibilities](#responsibilities)
- [Invariants](#invariants)

---

## Idea

Shipyard uses `shipyard.toml` as both:

- the project configuration file; and
- the marker that identifies a Shipyard project.

Shipyard may be executed from the project root or from a subdirectory.

```text
current directory
       ↓
search upward
       ↓
nearest shipyard.toml
       ↓
project root
```

The directory containing the active `shipyard.toml` becomes `root_path`.

The configuration stores project identity, author and GitHub information,
managed project-file locations, and Shipyard's own working directory.

---

## Project Discovery

Configuration discovery starts from the current working directory.

Shipyard searches one parent directory at a time until it finds
`shipyard.toml`.

```text
my-project/
├── shipyard.toml
└── src/
    └── package/
        └── module.py

run Shipyard here
        ↓
src/package
        ↓
src
        ↓
my-project
        ↓
shipyard.toml
```

The nearest configuration file is always selected.

The search stops when either:

- `shipyard.toml` is found;
- five parent levels have been checked; or
- the filesystem root is reached.

The directory containing the selected configuration becomes `root_path`.

This bounded search prevents an unrelated distant parent directory from
silently becoming the active project.

---

## Rules

1. `shipyard.toml` identifies a Shipyard project.
2. Search begins in the current working directory.
3. Search moves upward one parent at a time.
4. Search is limited to five parent levels.
5. The nearest `shipyard.toml` is the active configuration.
6. Its directory becomes `root_path`.
7. User configuration is recursively merged with Shipyard defaults.
8. User values override matching defaults.
9. Omitted values retain their defaults.
10. Configuration writes replace the file atomically.
11. Relative `[paths]` and `[files]` values are resolved from `root_path`.
12. `[paths].shipyard` controls Shipyard's working directory and is separate
    from project-document locations.

---

## Configuration Structure

```toml
[project]
name = "My Project"
version = "0.1.0"
description = "A project managed with Shipyard."

[author]
name = "Your Name"

[github]
username = "your-github-username"
repository = "https://github.com/your-github-username/your-project"
default_branch = "main"

[paths]
shipyard = ".shipyard"

[files]
roadmap = "ROADMAP.md"
tasks = ".shipyard/TASKS.md"
current_feature = ".shipyard/CURRENT.md"
additional_changes = ".shipyard/CHANGES.md"
ideas = "docs/proposals"
changelog = "CHANGELOG.md"

[settings]
auto_sync = false
```

The configuration intentionally separates:

- **project information** — `[project]`, `[author]`, `[github]`;
- **Shipyard's working directory** — `[paths]`;
- **managed project documents** — `[files]`;
- **behavioral settings** — `[settings]`.

---

## Configuration Loading

`shipyard.toml` is loaded after the project root has been identified.

Loading performs:

```text
defaults
   ↓
read shipyard.toml
   ↓
recursive merge
   ↓
resolved configuration
```

Defaults provide a complete configuration shape while allowing a new project
configuration to remain small.

For example:

```toml
[project]
name = "Harbor"
```

overrides only the project name. Other values retain their defaults.

Configuration writes are atomic so an interrupted save does not leave a
partially written TOML file.

TOML is used because it is readable, supports grouped configuration, and can be
read using Python's standard library.

---

## Command Context

Project discovery and configuration loading are part of command initialization,
not command-specific behavior.

`build_context()` places the resolved configuration and `root_path` into the
command context.

```text
shipyard.toml
      ↓
project discovery
      ↓
config loading
      ↓
build_context()
      ↓
root_path + configuration
      ↓
command execution
```

Commands consume this context and **must not independently search for
`shipyard.toml` or determine the project root**.

The command execution layer may combine this project context with the root
execution context before invoking a command's `run()`.

The command itself remains responsible only for its command-specific result.

---

## Why

Shipyard manages information belonging to a repository. A configuration file
inside that repository provides an explicit project boundary without requiring
every command to receive a project path.

Upward discovery allows commands to work naturally from directories such as:

```text
src/
docs/
nested/package/
```

while selecting the nearest configuration makes nested repositories
predictable.

The five-level limit prevents an unrelated parent directory from becoming the
active project.

The `.shipyard` directory is the default location for Shipyard-managed working
files, but it is configurable independently from project documents such as a
roadmap or changelog.

---

## Examples

### Running from a nested directory

```text
my-project/
├── shipyard.toml
└── src/
    └── package/
        └── module.py
```

Running Shipyard from `src/package` finds the project's `shipyard.toml` and
sets:

```text
root_path = my-project/
```

### Moving Shipyard's working directory

```toml
[paths]
shipyard = "tools/shipyard"
```

The project root remains unchanged. Only Shipyard's working directory moves.

### Overriding one default

```toml
[project]
name = "Harbor"
```

Only the project name is changed; unspecified values retain their defaults.

---

## Responsibilities

```text
config.py
   ↓
find + read + create + merge + save
   ↓
shipyard.toml

build_context()
   ↓
resolved configuration + root_path
   ↓
Command context

Command
   ↓
consumes project context

deco_run()
   ↓
handles framework/root execution behavior
```

Responsibilities remain separated:

- **`config.py`** — discovers, reads, creates, merges, and saves configuration.
- **`build_context()`** — creates command context from the resolved project.
- **Commands** — consume context and implement command behavior.
- **`deco_run()`** — handles framework-level execution and presentation.

---

## Invariants

The project configuration system maintains these invariants:

1. `shipyard.toml` is the project marker.
2. The nearest valid configuration is selected.
3. Discovery never searches beyond five parent levels.
4. `root_path` is always the directory containing the active configuration.
5. Relative project paths are resolved from `root_path`.
6. User configuration overrides matching defaults.
7. Missing configuration values retain defaults.
8. Configuration writes are atomic.
9. `[paths].shipyard` does not define the project root.
10. Commands do not independently discover or load project configuration.
11. Project configuration is available to commands through command context.
