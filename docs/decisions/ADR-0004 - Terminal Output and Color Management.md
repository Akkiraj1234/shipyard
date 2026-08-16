# ADR-0004: Terminal Output and Color Management

> **Status**: Draft  
> **Author**: Akhand Raj  
> **Updated**: 17-08-2026

## Table of Contents

- [Idea](#idea)
- [Output Pipeline](#output-pipeline)
- [Command Results](#command-results)
- [Human-Readable Output](#human-readable-output)
- [JSON Output](#json-output)
- [Color Management](#color-management)
- [Semantic Styles](#semantic-styles)
- [Configuration](#configuration)
- [Error Output](#error-output)
- [Terminal](#terminal)
- [Rules](#rules)
- [Responsibilities](#responsibilities)
- [Open Questions](#open-questions)

---

## Idea

Shipyard separates command data from terminal presentation.

Commands return data. The framework decides how that data is presented.

```text
Command
   ↓
result
   ↓
deco_run()
   ↓
OutputFormatter
   ↓
terminal output
```

Human-readable output may use terminal styling. JSON output must contain data
only and must not contain terminal styling.

This ADR is a starting point and may change as the output system is implemented.

---

## Output Pipeline

The output system has three main stages:

```text
command.run()
      ↓
result
      ↓
deco_run()
      ↓
OutputFormatter
      ↓
print
```

`deco_run()` handles framework-level behavior such as:

- help;
- root execution context;
- output mode;
- color settings;
- final presentation.

Commands should not print their normal results directly.

---

## Command Results

Commands may return structured or textual data.

```python
return {"version": "0.1.1"}
```

or:

```python
return "Shipyard initialized."
```

Structured data is preferred when the result naturally contains multiple
values.

The output layer is responsible for converting the result into the requested
presentation.

---

## Human-Readable Output

Normal output is intended for people using the terminal.

For example:

```python
{
    "project": {
        "name": "Shipyard",
        "version": "0.1.1",
    }
}
```

may be rendered as:

```text
project:
  name: Shipyard
  version: 0.1.1
```

The formatter owns this representation.

Python's raw `str(dict)` representation must not be used as the normal terminal
representation.

---

## JSON Output

`--only-json` selects JSON output.

JSON output:

- contains data only;
- does not use terminal colors;
- does not use human-readable styling;
- is produced by serialization rather than the human formatter.

For:

```python
{"version": "0.1.1"}
```

the output is:

```json
{
  "version": "0.1.1"
}
```

A string result may be represented as:

```json
{
  "output": "Shipyard initialized."
}
```

`--only-json` controls the presentation mode. It does not guarantee that every
command has a fixed schema across releases.

See ADR-0002 for the command result and execution boundary.

---

## Color Management

Color is a presentation concern.

Commands should not directly depend on terminal color codes.

Instead, the output system uses semantic styles such as:

```text
normal
message
heading
key
value
list
success
warning
error
hint
debug
```

The style system maps these semantic names to terminal capabilities and
Blessed formatting.

For example:

```text
error   → red
warning → yellow
heading → bold/cyan
hint    → cyan
```

The exact palette is implementation detail and may change without changing
command behavior.

---

## Semantic Styles

Output should describe **what something is**, rather than directly specifying
how it should look.

Prefer:

```python
style.error("Could not load configuration.")
```

over:

```python
term.red("Could not load configuration.")
```

This keeps terminal styling centralized.

Dictionary formatting should follow the same model. Keys, values, headings, and
lists may receive different semantic styles.

The formatter decides which semantic style applies to each part of the output.

---

## Configuration

Color preferences come from the resolved project configuration when it is
available.

Project configuration is not loaded during initial CLI startup because
`shipyard.toml` may not exist yet. Commands such as `init` must be able to run
before a project has been initialized.

Therefore:

```text
CLI startup
    ↓
command resolution
    ↓
command bootstrap
    ↓
configuration loaded
```

The resolved configuration may then be shared by components that need it.

If configuration is unavailable, output must still work using safe defaults.

A framework error must never require project configuration in order to be
rendered.

### Color precedence

The exact precedence remains under development, but the intended direction is:

```text
--only-json
    ↓
JSON has no color

--no-color
    ↓
disable terminal styling

project color setting
    ↓
configured preference

terminal capability
    ↓
actual terminal support
```

The final precedence rules will be finalized before this ADR is accepted.

---

## Error Output

Errors use the same output system as normal command results.

The error layer should produce structured error information rather than embed
terminal escape sequences directly.

Conceptually:

```python
{
    "type": "error",
    "title": "configuration error",
    "message": "Could not find shipyard.toml.",
    "hint": "Run 'shipyard init'.",
}
```

The output layer then decides how this appears.

Human-readable:

```text
configuration error: Could not find shipyard.toml.

hint: Run 'shipyard init'.
```

JSON:

```json
{
  "type": "error",
  "title": "configuration error",
  "message": "Could not find shipyard.toml.",
  "hint": "Run 'shipyard init'."
}
```

Errors must be renderable even when project configuration could not be loaded.

---

## Terminal

Shipyard uses Blessed for terminal capabilities and styling.

The formatter should use the terminal abstraction instead of hard-coded ANSI
escape sequences.

Terminal capabilities are presentation details. Command implementations should
not need to know whether the terminal uses ANSI, Blessed, or another
implementation in the future.

The terminal layer is also responsible for determining whether styling can
actually be used.

---

## Rules

1. Commands return results instead of printing normal command output.
2. `deco_run()` owns framework-level output behavior.
3. `OutputFormatter` owns result presentation.
4. Human-readable output may use semantic terminal styles.
5. JSON output contains no terminal styling.
6. `--only-json` bypasses human-readable presentation.
7. Commands must not directly embed terminal color codes.
8. Color names are semantic rather than terminal-specific.
9. `--no-color` disables terminal styling.
10. Project configuration may provide color preferences.
11. Project configuration is loaded during command bootstrap, not forced at CLI
    startup.
12. Output must still work when project configuration is unavailable.
13. Error rendering must not depend on successful project configuration loading.
14. Terminal-specific implementation remains inside the output/terminal layer.

---

## Responsibilities

```text
Command
   ↓
returns result

deco_run()
   ↓
framework execution + output mode

OutputFormatter
   ↓
human / JSON presentation

Style system
   ↓
semantic styling

Terminal
   ↓
Blessed capabilities and terminal output
```

In short:

> **Commands produce data.**
>
> **The framework chooses the output mode.**
>
> **The formatter presents the data.**
>
> **The style system decides how semantic output looks.**
>
> **The terminal layer handles terminal capabilities.**

---

## Open Questions

This ADR is intentionally not final.

The following still need to be decided during implementation:

- exact configuration key for color;
- whether color is enabled by default;
- final color precedence;
- complete semantic style list;
- whether styles should support nested formatting;
- how tables and more complex collections should be rendered;
- exact error result structure;
- terminal capability detection;
- whether `OutputFormatter` should own the style system or receive it;
- how global runtime configuration is exposed after successful bootstrap.
