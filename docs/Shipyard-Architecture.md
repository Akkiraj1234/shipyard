# Shipyard Architecture

> **Status:** Working architecture / v0.1.x  
> **Basis:** Current uploaded implementation files.  
> **Scope:** Core architecture only. `error.py` and `output.py` are shown by their current direction, not treated as final.

## 1. Overview

Shipyard is a hierarchical CLI framework with a project-management application built on top of it.

Its main separation is:

```text
Discovery
   ≠
Parsing
   ≠
Execution
   ≠
Presentation
```

The overall runtime is:

```text
argv
 ↓
cli.main()
 ↓
ParserStream
 ↓
command hierarchy
 ↓
terminal Command
 ↓
deco_run()
 ↓
run() → result
 ↓
OutputFormatter
 ↓
terminal
```

`__main__.py` is only the process entry: it imports `main()` and exits with its return value. fileciteturn14file1L1-L4

## 2. CLI Boundary

`cli.main()` creates the parser, extracts root-level flags, creates the
`ShipyardCommand`, executes the command tree, catches exceptions, and always
runs cleanup. fileciteturn14file3L11-L30

```text
create_parser()
      ↓
build_core_flag()
      ↓
ShipyardCommand(root_ctx)
      ↓
execute()
      ↓
return / error
      ↓
cleanup()
```

This keeps the process boundary outside the command implementation.

## 3. Tokenization and Parsing

`parser.py` first normalizes `argv` into `word`, `option`, and `flag` tokens.
`ParserStream` then walks the same token sequence while the executor resolves
the command hierarchy. fileciteturn14file8L51-L92
fileciteturn14file8L118-L145

```text
argv
 ↓
tokenize()
 ↓
TokenList
 ↓
ParserStream
 ↓
parse(GrammarRegistry)
 ↓
ParseResult
```

A grammar with children uses a word token as a child-command candidate.
Otherwise the remaining tokens are validated as the current command's input.
fileciteturn14file8L133-L175

## 4. Core Data Contracts

`types.py` provides the contracts shared between parsing and the command runtime:

```text
Token
 ├── type
 ├── name
 └── value

GrammarRegistry
 ├── has_child
 ├── words
 ├── options
 └── flags

ParseResult
 ├── child
 ├── arguments
 ├── options
 └── flags

RegistryData
 ├── name
 ├── paths
 ├── entry_class
 └── command metadata

CommandRegistry
 └── command name → RegistryData
```

`RegistryData.has_child` is derived from `child_path`. `GrammarRegistry.has_child`
controls how the parser interprets words at the current scope. fileciteturn14file10L44-L87
fileciteturn14file10L90-L112

## 5. Command Runtime

`core.py` is the main command framework.

A `Command` owns:

- root execution context;
- command metadata;
- grammar;
- child discovery;
- child lookup;
- bootstrap/context;
- command-specific `run()`.

fileciteturn14file5L42-L65

### Discovery

`child_metadata()` discovers child metadata from the configured `child_path`,
caches it, and reports non-fatal registry warnings. Leaf commands receive an
empty registry. fileciteturn14file5L135-L157

### Loading

`load_command()` resolves `entry_class`, imports the isolated command package,
checks that the entry is a `Command` subclass, and creates the command instance.
fileciteturn14file5L411-L448

### Execution

The executor repeatedly parses the current grammar:

```text
parse()
 ↓
child?
 ├─ yes → get_child() → load_command() → continue
 └─ no  → deco_run()
```

The same `ParserStream` is reused through the hierarchy. fileciteturn14file5L361-L377

## 6. Root Command and Command Packages

`shipyard.py` defines the root command and points it at the `commands/` directory.
Its grammar uses discovered command names as child words and defines root-level
flags such as `version`. fileciteturn14file9L13-L24 fileciteturn14file9L47-L57

Commands are package-based:

```text
commands/
├── init/
│   ├── __init__.py
│   ├── metadata.py
│   └── main.py
├── doctor/
│   ├── __init__.py
│   ├── metadata.py
│   └── main.py
└── task/
    ├── __init__.py
    ├── metadata.py
    ├── main.py
    └── ...
```

`import_command_module()` requires `__init__.py` and gives each command package an
isolated synthetic import namespace, while preserving relative imports inside
the command. fileciteturn14file11L489-L520

This makes a command a package boundary rather than a single file.

## 7. Configuration

`config.py` owns project configuration discovery and persistence.

```text
current directory
      ↓
search upward
      ↓
nearest shipyard.toml
      ↓
merge defaults + user config
      ↓
(root_path, config)
```

`load_config()` searches upward for the nearest `shipyard.toml`, merges the file
with defaults, and raises configuration/file errors when loading fails.
fileciteturn14file4L55-L76 fileciteturn14file4L80-L104

Bootstrap currently loads this context when a command needs project state.
This is intentionally later than raw CLI startup because `init` must work when
`shipyard.toml` does not yet exist. fileciteturn14file5L85-L96

A shared runtime configuration instance is a planned direction, but its final
API is not yet defined.

## 8. Output Direction

`core.py` now makes `deco_run()` the framework-owned execution boundary.
It is marked `@final`, handles help, invokes `run()`, and sends the result to
`print_output()`. fileciteturn14file5L323-L377

```text
terminal Command
      ↓
deco_run()
      ↓
command.run()
      ↓
result
      ↓
print_output()
      ↓
OutputFormatter
 ┌────┴─────┐
format     json
```

`OutputFormatter` currently supports human-readable formatting and JSON
serialization. Dictionary values are formatted recursively, and Blessed is
already used for the first key-styling direction. fileciteturn14file7L12-L26
fileciteturn14file7L44-L107

This layer is intentionally still in development.

## 9. Error Direction

`error.py` defines the current error hierarchy:

```text
ShipyardError
├── UsageError
│   └── ShipyardParserError
│       ├── UnknownCommandError
│       └── InvalidInputError
├── CommandLoadError
├── RegistryError
├── ShipyardFileError
└── ShipYardConfigNotFoundError
```

The CLI catches exceptions and routes them to `shipyard_error_print()` before
cleanup. fileciteturn14file6L29-L67 fileciteturn14file6L162-L190

The final error/output relationship is not settled yet. In particular, direct
terminal styling inside error rendering is expected to move toward the shared
output/style system.

## 10. Utility Layer

`utils.py` contains shared infrastructure rather than command behavior.

Important responsibilities include:

- `ListStream` for cursor-based traversal;
- `atomic_write()` and `safe_open()` for file operations;
- `merge_dicts()` for configuration merging;
- dynamic import helpers;
- isolated command-package loading.

`ListStream` preserves both the original input and the active traversal sequence,
which lets the parser maintain stable positions for diagnostics. fileciteturn14file11L48-L68

## 11. Complete Flow

### Normal execution

```text
argv
 ↓
__main__.py
 ↓
cli.main()
 ↓
create_parser()
 ↓
tokenize()
 ↓
ParserStream
 ↓
build_core_flag()
 ↓
ShipyardCommand
 ↓
execute()
 ↓
grammar()
 ↓
parse()
 ↓
child?
 ├─ yes → get_child()
 │          ↓
 │      load_command()
 │          ↓
 │      child Command
 │
 └─ no → terminal Command
           ↓
        deco_run()
           ↓
        run()
           ↓
        result
           ↓
        print_output()
           ↓
        OutputFormatter
           ↓
        print()
```

### Error path

```text
any framework/command error
          ↓
      cli.main()
          ↓
     except Exception
          ↓
 shipyard_error_print()
          ↓
       finally
          ↓
       cleanup()
          ↓
     process exit code
```

## 12. Main Architectural Boundaries

```text
CLI
 │
 ├── Parser
 │      ↓
 │   command selection
 │
 ├── Command Runtime
 │      ↓
 │   discovery / loading / execution
 │
 ├── Configuration
 │      ↓
 │   project state
 │
 ├── Output
 │      ↓
 │   result presentation
 │
 └── Error Boundary
        ↓
     failure presentation
```

The most important design rule is that these concerns are not merged:

> **The parser selects. The command runtime resolves and executes.
> Commands produce results. Presentation renders those results.**

## 13. What the Current Architecture Makes Possible

The current seams already leave room for later replacement or extension without
requiring everything to become a plugin.

Examples:

```text
filesystem child discovery
        ↓
future plugin registry

command.run() result
        ↓
human formatter / JSON consumers

command package
        ↓
future installed command/plugin package
```

The current design does not make every layer replaceable, and that is intentional.
The stable boundaries are more important than making every implementation
configurable.

## 14. Current Non-Final Areas

Do not treat these as settled yet:

- `error.py` presentation;
- `output.py` formatting/styling;
- semantic color registry;
- exact configuration source for color and output preferences;
- shared runtime configuration API;
- final JSON result/error schemas;
- global configuration;
- final plugin mechanism.

These should be settled after the new output/error system is exercised by
`init`, `doctor`, and the upcoming project-management commands.

## 15. Architecture Diagram

See the accompanying:

`shipyard-architecture.svg`

The SVG is intentionally editable and shows the current module relationships,
data contracts, command-discovery flow, configuration flow, execution flow, and
the not-yet-final output/error direction.
