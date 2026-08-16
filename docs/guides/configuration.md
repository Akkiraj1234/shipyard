# Configuring a Shipyard Project

`shipyard.toml` is the configuration file for one Shipyard project. Put it in
the repository root. Shipyard can then be run from that directory or from a
subdirectory of it.

For the decision behind this behavior, see
[ADR-0003](../decisions/ADR-0003%20-%20Project%20Configuration%20and%20Root%20Discovery.md).

## Complete example

```toml
[project]
name = "Harbor"
version = "0.1.0"
description = "A small service for tracking shipments."

[author]
name = "Akhand Raj"

[github]
username = "Akkiraj1234"
repository = "https://github.com/Akkiraj1234/harbor"
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

All paths are relative to the directory containing `shipyard.toml`, unless an
absolute path is supplied. Use forward slashes in the file, including on
Windows.

At the current foundation stage, Shipyard creates, loads, merges, and saves
this configuration. Commands that create and synchronize every managed file
are planned work, so these locations are the configuration contract for that
work rather than all being acted on today.

## Project information

```toml
[project]
name = "Harbor"
version = "0.1.0"
description = "A small service for tracking shipments."
```

- `name`: the project name used in Shipyard output and generated metadata.
- `version`: the current project version. Shipyard’s v0.1 design follows
  Semantic Versioning, such as `0.1.0`.
- `description`: a short, human-readable description of the project.

## Author and GitHub information

```toml
[author]
name = "Akhand Raj"

[github]
username = "Akkiraj1234"
repository = "https://github.com/Akkiraj1234/harbor"
default_branch = "main"
```

- `author.name`: the person or organisation writing and maintaining the
  project.
- `github.username`: the GitHub account that owns the repository.
- `github.repository`: the repository URL.
- `github.default_branch`: the normal integration branch, usually `main`.

## Shipyard working directory

```toml
[paths]
shipyard = ".shipyard"
```

This is the location reserved for Shipyard’s own working files. `.shipyard`
is the default, but it may live elsewhere in the repository:

```toml
[paths]
shipyard = "tools/shipyard"
```

This changes neither the project root nor the locations listed in `[files]`.

## Managed project files

```toml
[files]
roadmap = "ROADMAP.md"
tasks = ".shipyard/TASKS.md"
current_feature = ".shipyard/CURRENT.md"
additional_changes = ".shipyard/CHANGES.md"
ideas = "docs/proposals"
changelog = "CHANGELOG.md"
```

- `roadmap`: the release plan containing planned features.
- `tasks`: implementation tasks for the feature currently being worked on.
- `current_feature`: the active roadmap feature.
- `additional_changes`: unplanned changes collected for the next release.
- `ideas`: a directory for proposal documents and unscheduled ideas.
- `changelog`: the user-facing release history.

Choose paths that fit the project. For example, a team that keeps all
documentation together could use `docs/roadmap.md` and `docs/changelog.md`.

## Settings

```toml
[settings]
auto_sync = false
```

`auto_sync` expresses whether Shipyard should automatically synchronize its
managed metadata when that behavior is implemented. It defaults to `false` so
Shipyard does not modify project files without an explicit choice.

For now, configuration loading and saving preserve this setting; automatic
synchronization itself is not implemented yet.

## What to change first

After `shipyard.toml` is created, replace the example values in this order:

1. Set `[project]` to the project’s name, version, and description.
2. Set `[author].name`.
3. Set the GitHub repository details if the project uses GitHub.
4. Keep the default paths or change `[files]` to match the repository’s
   existing documentation layout.
5. Move `[paths].shipyard` only when `.shipyard` is not the desired working
   directory.
