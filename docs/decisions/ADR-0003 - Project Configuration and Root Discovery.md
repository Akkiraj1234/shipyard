# ADR-0003: Project Configuration and Root Discovery

> **Status**: Accepted  
> **Author**: Akhand Raj  
> **Updated**: 16-08-2026

## Idea

Shipyard uses `shipyard.toml` as the project configuration file and as the
marker that identifies a Shipyard project.

A developer may run Shipyard from the project root or from a subdirectory.
Shipyard searches upward from the current directory for the nearest
`shipyard.toml`. The directory containing that file becomes the project root.

The configuration records project identity, author and GitHub details, the
locations of managed project files, and the location of Shipyard's working
directory.

## Rules

1. A `shipyard.toml` file identifies a Shipyard project.
2. Configuration search starts in the current working directory.
3. Search moves upward one parent directory at a time.
4. Search stops after five parent levels or when the filesystem root is
   reached.
5. The nearest `shipyard.toml` is the active project configuration.
6. The directory containing the active configuration is `root_path`.
7. User configuration is recursively merged with Shipyard's defaults.
8. A user value overrides its matching default; omitted values retain their
   default.
9. Configuration writes replace the file atomically.
10. Relative paths in `[paths]` and `[files]` are relative to `root_path`.
11. `[paths].shipyard` is Shipyard's configurable working directory. It is
    separate from the locations of project documents in `[files]`.

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

## Why?

Shipyard manages information that belongs to one repository. A configuration
file in that repository gives the tool one explicit project boundary without
requiring a project path in every command.

Upward discovery lets a developer use Shipyard from places such as
`src/`, `docs/`, or a nested package directory. Choosing the nearest file
makes the result predictable when repositories are nested. The search limit
prevents an unrelated distant parent directory from silently becoming the
active project.

TOML is readable in a text editor, supports the grouped configuration that
Shipyard needs, and can be read with Python's standard library.

The configuration distinguishes project documents from Shipyard's working
directory. A roadmap or changelog is project information that may be placed
where the developer wants. The `.shipyard` directory is a default location
for Shipyard-managed working files, but it can be moved without changing the
project root.

Defaults keep a new configuration small while still giving every command a
complete shape to work with. Atomic writes avoid leaving a half-written TOML
file if saving is interrupted.

## Examples

### Running from a nested directory

```text
my-project/
├── shipyard.toml
└── src/
    └── package/
        └── module.py
```

When Shipyard runs from `src/package`, it searches upward and finds
`my-project/shipyard.toml`. `my-project` becomes `root_path`.

### Moving Shipyard's working directory

```toml
[paths]
shipyard = "tools/shipyard"
```

The project root remains the directory containing `shipyard.toml`.
Only the location reserved for Shipyard's own working files changes.

### Overriding one default

```toml
[project]
name = "Harbor"
```

The supplied name replaces the default. Other project fields, GitHub fields,
paths, files, and settings retain their defaults after loading.

## Responsibility

`config.py` is responsible for finding, reading, creating, merging, and
saving `shipyard.toml`.

`build_context()` is responsible for placing the loaded configuration and its
`root_path` into the command context.

Commands use that context. They do not independently search for configuration
or decide the project root.
