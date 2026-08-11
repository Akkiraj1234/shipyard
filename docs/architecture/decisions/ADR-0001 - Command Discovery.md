# ADR-0001: Command Discovery

> **Status**: Accepted
> **Author**: Akhand Raj
> **Updated**: 10-08-2026

## Idea

Shipyard uses a hierarchy-based command discovery system instead of `argparse`.

The parser walks through the command hierarchy one child at a time until it finds the command that should run.

## Rules

1. If the current token is not a `word`, parse the remaining input as arguments.
2. If the current token is a `word`, try to match it against the current `GrammarRegistry`.
3. If a match is found, move to that child command.
4. If no match is found, raise `UnknownCommandError`.

## Why `UnknownCommandError`?

When `has_child` is `true`, the command expects the next `word` to be a child command.

Therefore, an unknown `word` cannot be treated as an argument at that level.

For example:

```text
shipyard task add hello.py

shipyard
   ↓
  task
   ↓
   add
   ↓
hello.py
```

`task` and `add` are commands. `hello.py` is an argument of `add`.

The same `ParserStream` is used while moving through child commands.

## Why?

This keeps command routing simple and predictable.

The parser finds the command. The command handles its own input.

---

## RegistryData

`RegistryData` stores metadata and information about a command.

| Field         | Purpose                                                            |
| ------------- | ------------------------------------------------------------------ |
| `name`        | Command name.                                                      |
| `description` | Short description of the command.                                  |
| `help`        | Help text for the command.                                         |
| `hidden`      | Whether the command should be hidden from normal command listings. |
| `dir_path`    | Directory where the command exists.                                |
| `child_path`  | Directory where the command's children are located.                |
| `entry_class` | Python import path of the command class.                           |
| `has_child`   | Defines whether the command accepts child commands.                |

`name`, `description`, and `help` describe the command.

`hidden` controls whether the command is visible.

`dir_path` points to the command's directory.

`child_path` points to the directory containing its child commands.

`entry_class` identifies the Python class that implements the command.

`has_child` tells the parser whether the next `word` should be treated as a child command.

---

## GrammarRegistry

`GrammarRegistry` defines how the current command should parse its input.

| Field       | Purpose                                                               |
| ----------- | --------------------------------------------------------------------- |
| `has_child` | Defines whether the next `word` should be treated as a child command. |
| `words`     | Allowed words for the current grammar.                                |
| `options`   | Allowed options.                                                      |
| `flags`     | Allowed flags.                                                        |

When `has_child` is `true`, `words` are used to find child commands.

When `has_child` is `false`, `words`, `options`, and `flags` are parsed as input for the current command.

`GrammarRegistry` describes **how the current command parses input**, while `RegistryData` describes **what the command is and where it is located**.
