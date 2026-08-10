# ADR-0001: Command Discovery

> **Status**: Accepted  
> **Author**: Akhand Raj  
> **Updated**: 10-08-2026

## Idea

Shipyard uses a hierarchy-based command discovery system instead of `argparse`.

The parser walks through the command hierarchy one child at a time until it finds the command that should run.

## Rules

1. If the current token is not a `word`, parse the remaining arguments and return them.
2. If the current token is a `word`, try to match it with the current `GrammarRegistry`.
3. If a match is found, move to that child command.
4. If no match is found, raise `UnknownCommandError`.

## Why `UnknownCommandError`?

If `has_child` is `true`, the command says that the next `word` must be a child command.

Therefore, an unknown word cannot be treated as an argument at that level.

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

`task` and `add` are commands. `hello.py` belongs to `add`.

The same `ParserStream` is used while moving through child commands.

## Why

This keeps command routing simple and predictable.

The parser finds the command. The command handles its own input.
