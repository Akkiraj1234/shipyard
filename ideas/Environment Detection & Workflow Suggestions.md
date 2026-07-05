# Idea: Environment Detection & Workflow Suggestions

## Motivation

Every project uses different tools and workflows.

For example:

* Poetry
* uv
* Git
* GitHub Actions
* MkDocs
* Sphinx

Instead of Shipyard trying to replace these tools, it should detect them and suggest useful integrations.

Shipyard should **adapt to the project**, not require the project to adapt to Shipyard.

---

## Philosophy

Shipyard does not replace existing tools.

Shipyard discovers them and helps connect them together.

Each tool remains responsible for its own job.

Examples:

* Poetry → dependency management, packaging, publishing
* Git → version control
* GitHub Actions → CI/CD
* Shipyard → project lifecycle metadata

---

## Possible Detection

### Version Control

* Git

### Package Managers

* Poetry
* uv
* Hatch
* PDM
* setuptools

### Documentation

* MkDocs
* Sphinx
* Docusaurus (future)

### CI/CD

* GitHub Actions
* GitLab CI (future)

### Testing

* pytest
* tox
* nox

---

## Example

Running:

shipyard init

could produce:

✓ Git repository detected

✓ Poetry project detected

✓ GitHub Actions detected

✓ MkDocs configuration detected

Shipyard can generate example workflows for this environment.

No files are modified automatically without user confirmation.

---

## Suggested Workflow

Shipyard may offer to create example workflows such as:

Release

1. Update roadmap
2. Generate changelog
3. Update README
4. Stage generated files

or

Publish

1. shipyard release
2. poetry build
3. poetry publish

These workflows are examples and remain fully editable by the user.

---

## Design Rules

* Shipyard never replaces external tools.
* Shipyard never assumes a specific package manager.
* Shipyard only suggests integrations.
* Generated workflows belong to the project and can be modified freely.
* Environment detection should never modify files without explicit user approval.

---

## Status

Future idea.

Not planned for v0.x.
