# Proposal: Project Bootstrap & Standards Assistant

## Status

Future Idea (Not planned for v0.x)

---

# Overview

Shipyard should eventually help developers start projects using established community standards instead of requiring them to manually discover and configure everything.

The goal is **not** to invent new standards.

The goal is to help users choose, configure, and generate existing ones.

---

# Philosophy

Shipyard should never replace existing standards.

Instead, it should:

* Ask questions.
* Understand the project's needs.
* Recommend existing solutions.
* Generate configuration and documentation.

The developer always makes the final decision.

---

# Initialization Wizard

Example:

```text
$ shipyard init

Project name?

Description?

Open source?

Public or private?

Primary language?

Package manager?

Documentation generator?

License?

CI provider?

Testing framework?
```

Based on these answers, Shipyard can recommend suitable tools and generate project files.

---

# License Assistant

Instead of asking users to choose from a long list of licenses, Shipyard should guide them through simple questions.

Example:

* Allow commercial use?
* Allow modification?
* Require attribution?
* Require derivative work to remain open source?
* Need patent protection?

Based on the answers, Shipyard recommends an existing license such as:

* MIT
* Apache-2.0
* GPL-3.0
* BSD-3-Clause
* MPL-2.0

Shipyard should never generate custom licenses.

It should always use official license texts.

---

# Documentation Templates

Shipyard may generate:

* README.md
* CONTRIBUTING.md
* SECURITY.md
* CODE_OF_CONDUCT.md
* ROADMAP.md
* CHANGELOG.md

These should be customizable templates based on the user's answers.

---

# Environment Detection

Detect available tooling, for example:

* Git
* Poetry
* uv
* Hatch
* PDM
* setuptools
* GitHub Actions
* MkDocs
* Sphinx
* pytest
* tox
* nox

Shipyard should never install tools automatically.

Instead, it should provide recommendations and suggested commands.

Example:

```text
MkDocs not detected.

Documentation generation is available with MkDocs.

Suggested command:

poetry add --group docs mkdocs-material
```

---

# Suggested Integrations

Shipyard may optionally generate:

* GitHub Actions workflow
* MkDocs configuration
* Release workflow examples
* Documentation structure
* Project metadata templates

Generation should always require user confirmation.

---

# Design Principles

* Do not replace existing developer tools.
* Do not replace package managers.
* Do not replace documentation generators.
* Do not invent legal licenses.
* Prefer official standards over custom implementations.
* Ask questions before generating files.
* Never modify a project without explicit user approval.

---

# Long-Term Vision

Shipyard should become a project lifecycle assistant that understands the development environment, manages project metadata, and helps developers adopt proven tools and standards with minimal setup while keeping them in full control.
