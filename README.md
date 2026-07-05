# 🚢 Shipyard

> **A repository-first project lifecycle companion.**

Shipyard helps developers manage the information surrounding their source code.

Modern software projects naturally accumulate project metadata—roadmaps, changelogs, documentation, release notes, implementation notes, and ideas. Keeping these files synchronized quickly becomes repetitive and easy to forget.

Shipyard exists to solve that problem.

Rather than replacing tools such as Git, Poetry, MkDocs, or GitHub Actions, Shipyard works alongside them. It coordinates the project's information lifecycle, manages project metadata, and automates repetitive maintenance while allowing every tool to continue doing the job it does best.

---

## Philosophy

Shipyard is built around a few simple principles.

* 📝 CommonMark Markdown is the source of truth.
* 📦 Project metadata belongs inside the repository.
* 🔗 Existing tools should be integrated, not replaced.
* 👨‍💻 Developers remain in complete control.
* 📚 Every piece of project information has one canonical location.

> **Developers build software. Shipyard manages everything around the software.**

---

## Current Status

Shipyard is currently under active **v0.1** development.

The initial release focuses on managing project metadata throughout the software development lifecycle.

Current features include:

* Roadmap management
* Working task management
* Additional change tracking
* Changelog generation
* Metadata synchronization
* Metadata registry
* Idea management
* Release preparation

---

## Information Lifecycle

```text
Ideas
   ↓
Roadmap
   ↓
Current Feature
   ↓
Working Tasks
   ↓
Development
   ↓
Additional Changes
   ↓
Release
   ↓
Changelog
   ↓
Project Metadata
```

---

## Standards

Shipyard follows established community standards whenever possible.

* **Semantic Versioning (SemVer 2.0.0)** — https://semver.org/
* **Keep a Changelog** — https://keepachangelog.com/en/1.1.0/
* **CommonMark** — https://commonmark.org/

---

## Documentation

| Document                                       | Description                          |
| ---------------------------------------------- | ------------------------------------ |
| [`ROADMAP.md`](./ROADMAP.md)                   | Planned features and future releases |
| [`CHANGELOG.md`](./CHANGELOG.md)               | Release history                      |
| [`ideas/`](./ideas/_index.md)                  | Proposals and future ideas           |
| [`docs/design/v1.0.md`](./docs/design/v1.0.md) | Architecture and design decisions    |

---

## License

Licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

See the `LICENSE` file for details.
