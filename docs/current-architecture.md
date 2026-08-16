# Current Architecture

This document describes Shipyard as it is implemented today. It is a snapshot
of the current foundation, not a description of every planned v1 feature.

## Overview

Shipyard is a Python CLI built around a small command framework. Commands are
declared with lightweight metadata, discovered from the filesystem, and loaded
only when the user selects them.

```text
shell
  │
  ▼
cli.py ──► parser.py ──► root command ──► command metadata discovery
  │                           │                    │
  │                           │                    ▼
  │                           └────────────► lazy command import
  │                                                │
  ▼                                                ▼
error.py ◄────────────────────────────── command.run(ParseResult)
```

The important separation is:

- The parser understands command-line syntax and applies a command grammar.
- Commands own their grammar and execution.
- The registry discovers commands and resolves their entry classes.
- The CLI is the process boundary and sends raised exceptions to the error
  renderer.

For the contributor workflow for defining a command and its children, see the
[command creation guide](guides/creating-commands.md).

## Application Entry Points

The installed `shipyard` command points to `shipyard.cli:main`.

- `__main__.py` makes `python -m shipyard` call the same entry point.
- `cli.py` builds a `ParserStream`, extracts recognised root flags, creates
  `ShipyardCommand`, and calls `core.execute`.
- Exceptions raised during execution are caught in `cli.py` and rendered by
  `shipyard_error_print`.
- `cleanup()` is the reserved lifecycle hook for future shutdown work.

## Parsing

`parser.py` has two levels of responsibility.

### Tokenization

`tokenize()` converts `sys.argv` into normalized tokens:

- `word`: a positional value or command name
- `flag`: a prefixed value without a value, such as `--force`
- `option`: a prefixed value with a value, such as `--title Parser` or
  `--title=Parser`

`ParserStream` is a cursor over those tokens. The input is tokenized once and
the same stream is advanced as command scopes are resolved.

### Grammar-driven parsing

Each command provides a `GrammarRegistry` containing its allowed child words,
arguments, flags, and options. `ParserStream.parse()` either:

1. consumes a valid child command name and returns `ParseResult(child=...)`, or
2. parses the remaining values for the current command and returns arguments,
   options, and flags.

The parser raises Shipyard usage errors for unknown commands, arguments,
flags, and options. It does not print errors or terminate the process itself.

## Commands and Dispatch

`core.Command` is the common interface for all commands. A command provides:

- `metadata`: its `RegistryData`
- `grammar()`: the input accepted in its scope
- `get_child(name)`: child-command resolution
- `child_metadata()`: known child declarations
- `run(result)`: execution and an integer exit status

`core.execute()` repeatedly parses the current scope. When parsing identifies
a child, execution moves to that child and continues with the same token
stream. When no child remains, it calls that command's `run()` method.

This allows nested command paths without importing the entire command tree at
startup.

## Registry and Lazy Loading

Commands live below `src/shipyard/commands/` in directories such as:

```text
commands/
└── init/
    ├── metadata.py
    └── main.py
```

`metadata.py` exports a `METADATA` value, which is a `RegistryData` instance.
Important fields are:

- `name`: the command word, for example `init`
- `description` and `help`: command-facing documentation
- `child_path`: an optional directory containing child commands
- `entry_class`: a `module:ClassName` reference

`Command._get_child_metadata()` scans a command directory for `metadata.py`
files. It validates metadata, resolves relative paths to absolute paths, and
collects invalid declarations as `RegistryError` warnings so one bad command
does not hide the others.

`load_command()` imports the selected command module only after it has been
chosen and verifies that the declared entry is a `Command` subclass.

`ShipyardCommand` is the root command. Its child path is
`src/shipyard/commands`, so it discovers the top-level `init` and `doctor`
commands when its grammar or registry is requested.

## Context and Configuration

`config.py` owns `shipyard.toml` handling.

- `load_config()` searches upward from the current directory for a bounded
  number of parent directories.
- Loaded TOML is recursively merged with `DEFAULT_CONFIG`.
- `create_config()` creates a default configuration.
- `save_config()` writes configuration through `atomic_write()`.
- The default schema has project, author, GitHub, path, file-location, and
  settings sections. The configuration guide describes the fields; ADR-0003
  records the decision behind project-root discovery.

`Command.bootstrap()` calls `build_context()`, which loads the configuration
and adds the configuration directory as `root_path`.

At present this is configuration-root discovery. Full managed-path resolution
and `.shipyard` directory management are planned foundation work.

## Errors and Terminal Output

`error.py` defines user-facing `ShipyardError` types. They can provide a
title, message, details, and a recovery hint. Important specializations are:

- `ShipyardParserError` for an error with a command-line pointer
- `UnknownCommandError` and `InvalidInputError` for suggestions and usage
  validation
- `CommandLoadError` for invalid registry declarations or entry classes
- `RegistryError` for non-fatal discovery warnings
- `ShipyardFileError` and `ShipYardConfigNotFoundError` for repository files
  and configuration

`shipyard_error_print()` is the root renderer used by `cli.py`:

- known Shipyard errors use their `pretty()` rendering;
- unexpected exceptions are shown as a fatal error with their type and reason;
- the `--dev` root flag adds the exception type and stack frames.

Direct `print()` calls still exist in commands and utility warnings. A single
general output-printer abstraction is planned but is not implemented yet.

## Shared Utilities and Types

`utils.py` currently provides:

- `ListStream`, the parser's cursor abstraction
- atomic text-file writes
- safe file opening
- recursive dictionary merging
- close-match suggestions
- dynamic Python module/file imports

`types.py` contains the shared data structures used across the framework:

- token and token-type definitions
- `GrammarRegistry`
- `ParseResult`
- `RegistryData`
- command and token collection aliases

## Current Command Status

The command registry can discover and load `init` and `doctor`. Their modules
also contain initial helper functions for creating and checking Shipyard files.

Their `Command` subclasses are intentionally still scaffolding: their
`metadata`, `grammar`, and `run` implementations are not wired to the helper
functions yet. Consequently, discovery and loading are implemented, while
end-to-end `shipyard init` and `shipyard doctor` behavior is not complete.

Likewise, root flags such as `--version` exist in the root grammar, but the
version/help output behavior is still planned work.

## Testing

The test suite focuses on public behavior of the foundation rather than
duplicating command-routing tests for every child. It covers:

- CLI execution and error boundary behavior
- configuration creation, loading, saving, and failures
- parser tokenization and grammar validation
- command dispatch, metadata discovery, and lazy loading
- root command discovery
- error rendering and developer diagnostics
- core utility behavior

Run it with:

```bash
poetry run pytest -q
```
