from __future__ import annotations

from pathlib import Path

from shipyard.config import CONFIG_FILE_NAME, DEFAULT_TOML
from shipyard.types import ParseResult

flags = {"force"}
options: dict[str, str] = {}

_FILES = {
    "README.md": "# Project\n\nManaged with Shipyard.\n",
    "ROADMAP.md": "# Roadmap\n\n## Additional Changes\n\n",
    "CHANGELOG.md": "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n## [Unreleased]\n\n",
    "ideas/_index.md": "# Ideas\n\nProject proposals and unscheduled ideas live in this directory.\n",
    ".shipyard/registry.json": "{}\n",
}


def command(result: ParseResult) -> int:
    """Create Shipyard's repository-local metadata structure."""
    root = Path.cwd()
    created: list[str] = []
    existing: list[str] = []
    for relative_path, contents in _FILES.items():
        path = root / relative_path
        if path.exists():
            existing.append(relative_path)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
        created.append(relative_path)

    config = root / CONFIG_FILE_NAME
    if not config.exists():
        config.write_text(DEFAULT_TOML.lstrip(), encoding="utf-8")
        created.append(CONFIG_FILE_NAME)
    else:
        existing.append(CONFIG_FILE_NAME)

    if created:
        print("Initialized Shipyard:")
        print("\n".join(f"  created {path}" for path in created))
    else:
        print("Shipyard is already initialized.")
    if existing:
        print("\n".join(f"  kept    {path}" for path in existing))
    return 0
