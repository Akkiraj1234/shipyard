# ADR-0001: Command Discovery

> **Status**: Accepted\
> **Author**: Akhand Raj\
> **Updated**: 10-08-2026

## Idea

Shipyard uses a hierarchy-based command discovery system instead of
`argparse`.

The parser walks through the command hierarchy one child at a time until
it reaches the command that should handle the remaining input.

Command discovery is based on the current grammar's `has_child` state
and the type of the next token.

## Rules

The first decision is whether the current grammar has child commands.

``` text
has_child?
   │
   ├── false ──────────────→ parse current input
   │
   └── true
        │
        ▼
   next token?
        │
        ├── no token ──────→ empty ParseResult
        │
        ├── option/flag ───→ parse current grammar
        │
        └── word
             │
             ▼
        child exists?
          │       │
         yes      no
          │        │
          ▼        ▼
       move      error
       child
```

1. If `has_child` is `false`, do not perform child discovery. Parse the
   remaining input using the current grammar.
2. If `has_child` is `true`, inspect the next token.
3. If the next token is an `option` or `flag`, do not perform child
   discovery. Parse it using the current grammar.
4. If the next token is a `word`, use the current `GrammarRegistry` to
   find a matching child command.
5. If the word matches a child, move to that child command and continue
   discovery using the same `ParserStream`.
6. If the word does not match a child, raise `UnknownCommandError`.
7. If there is no current token, return an empty `ParseResult`.

### Command discovery invariant

When a grammar has children:

- `word` → child-command discovery
- `option` → current command
- `flag` → current command
- no token → empty `ParseResult`

Therefore, having child commands does **not** prevent the current
command from accepting options or flags.

## Examples

### Child command

``` text
shipyard run some.txt
         │
         └── word → child lookup → run exists → descend
```

`run` is a child command of `shipyard`.

After descending into `run`, `some.txt` is parsed by the `run` command's
grammar.

### Current-command option

``` text
shipyard --version
         │
         └── option → parse using shipyard grammar
```

`--version` is handled by the `shipyard` command and is not considered a
child command.

The same applies to:

``` text
shipyard --help
shipyard --clear-unused-data
```

### Unknown child command

``` text
shipyard hello world
         │
         └── word → child lookup → no "hello" child
                              │
                              ▼
                    UnknownCommandError
```

Because `hello` is a `word` and `shipyard` has children, it is
interpreted as a child-command candidate. It cannot be treated as an
argument of `shipyard`.

### Hierarchical command

``` text
shipyard task add hello.py

shipyard
   ↓
  task
   ↓
   add
   ↓
hello.py
```

`task` is a child command of `shipyard`.

`add` is a child command of `task`.

Once the parser reaches `add`, if `add` has no children, child discovery
stops and `hello.py` is parsed as an argument by the `add` command's
grammar.

## ParserStream

The same `ParserStream` is used while moving through the command
hierarchy.

The parser does not create a new stream when descending into a child
command. Each command consumes tokens from the same stream until the
terminal command is reached.

This keeps token consumption consistent across the entire command
hierarchy.

## RegistryData

`RegistryData` stores metadata and structural information about a
command.

1. `name` --- command name.
2. `description` --- short command description.
3. `help` --- command help text.
4. `hidden` --- whether the command is hidden.
5. `dir_path` --- directory where the command exists.
6. `child_path` --- directory where the command's children exist.
7. `entry_class` --- Python import path of the command class.
8. `has_child` --- whether the command has child commands.

`RegistryData` describes **what the command is and where it exists**.

## GrammarRegistry

`GrammarRegistry` defines how the current command handles input.

1. `has_child` --- whether the current grammar participates in
    child-command discovery.
2. `words` --- words accepted by the current grammar.
3. `options` --- options accepted by the current grammar.
4. `flags` --- flags accepted by the current grammar.

When `has_child` is `true`:

- `word` tokens are used for child-command discovery.
- `options` and `flags` are handled by the current grammar.

When `has_child` is `false`:

- child discovery is skipped.
- `words`, `options`, and `flags` are parsed as input for the current
    command.

`GrammarRegistry` describes **how the current command handles input**.

## Why?

`has_child` determines whether a `word` can be interpreted as a child
command at the current command scope.

For example:

``` text
shipyard run some.txt
```

Since `shipyard` has children, `run` is treated as a child-command
candidate.

However:

``` text
shipyard --version
```

`--version` is an option, not a `word`, so child discovery is skipped
and the current `shipyard` grammar handles it.

This gives command discovery a simple and predictable rule:

> **When the current grammar has children, words are used for child
> discovery; options and flags remain part of the current command's
> grammar.**

If a word is encountered while child discovery is active and no matching
child exists, the parser raises `UnknownCommandError` rather than
treating the word as an argument of the parent command.

## Responsibility

The parser is responsible for **discovering the command hierarchy**.

The terminal command's grammar is responsible for **parsing the
remaining input**.

In short:

> **The parser discovers the command. The terminal command handles its
> input.**
