from typing import Any, Callable, TextIO
from dataclasses import dataclass
from enum import StrEnum
import json
import sys

from blessed import Terminal
from .config import config



class Style(StrEnum):
    """
    Semantic styles used to classify terminal output.

    Styles describe the purpose of output rather than its concrete visual
    representation. The associated colors or terminal attributes are resolved
    separately by Shipyard's output system and may be customized through
    configuration.

    Attributes
    ----------
    ERROR
        Used for errors, failures, and other unsuccessful output.

    SUCCESS
        Used to indicate that an operation completed successfully.

    WARNING
        Used for warnings or conditions that require attention.

    INFO
        Used for neutral informational messages.

    KEY
        Used for dictionary keys, labels, identifiers, and other structured
        output names.

    VALUE
        Used for values associated with keys or structured output data.
    """

    ERROR = "error"
    SUCCESS = "success"
    WARNING = "warning"
    INFO = "info"
    KEY = "key"
    VALUE = "value"


StyleFunction = Callable[[str], str]
term = Terminal()

_styles: dict[Style, StyleFunction] = {
    Style.ERROR: term.red,
    Style.SUCCESS: term.green,
    Style.WARNING: term.yellow,
    Style.INFO: term.cyan,
    Style.KEY: term.cyan,
    Style.VALUE: term.white,
}


@dataclass(frozen=True, slots=True)
class Styled:
    """
    Text explicitly associated with a semantic terminal style.
    """

    text: str
    style: Style



def styled(text: str, style: Style) -> Styled:
    """
    Create styled terminal output data.
    """
    return Styled(text, style)


def update_styles(colors: dict[str, str]) -> None:
    """
    Update semantic styles from configured color names.

    Unknown style names are ignored. Invalid terminal colors raise
    ``ValueError``.
    """
    for name, color in colors.items():
        try:
            semantic_style = Style(name)
        except ValueError:
            continue

        formatter = getattr(term, color, None)

        if formatter is None or not callable(formatter):
            raise ValueError(f"unknown terminal color: {color!r}")

        _styles[semantic_style] = formatter


def apply_style(value: str, style: Style) -> str:
    """
    Apply the configured terminal formatter for a semantic style.
    """
    return _styles[style](value)


def _format_value(value: Any, level: int = 0) -> list[str]:
    indent = "  " * level

    if isinstance(value, Styled):
        return [apply_style(value.text, value.style)]

    if isinstance(value, dict):
        lines = []

        for key, child in value.items():
            lines.extend(
                _format_mapping_item(
                    key,
                    child,
                    level,
                )
            )

        return lines

    if isinstance(value, list):
        lines = []

        for item in value:
            if isinstance(item, dict):
                lines.append(f"{indent}-")
                lines.extend(_format_value(item, level + 1))
            else:
                lines.append(
                    f"{indent}- {item}"
                )

        return lines

    return [f"{indent}{value}"]


def _format_mapping_item(
    key: str,
    value: Any,
    level: int,
) -> list[str]:
    indent = "  " * level

    key_text = apply_style(
        str(key),
        Style.KEY,
    )

    if isinstance(value, dict):
        lines = [f"{indent}{key_text}:"]

        for child_key, child_value in value.items():
            lines.extend(
                _format_mapping_item(
                    child_key,
                    child_value,
                    level + 1,
                )
            )

        return lines

    if isinstance(value, Styled):
        return [
            f"{indent}{key_text}: "
            f"{apply_style(value.text, value.style)}"
        ]

    return [
        f"{indent}{key_text}: "
        f"{apply_style(str(value), Style.VALUE)}"
    ]


def print_output(
    data: Any,
    stream: TextIO = sys.stdout,
) -> None:
    """
    Render command output according to Shipyard's active configuration.

    Normal dictionaries and collections are formatted automatically.
    Explicit ``Styled`` values use their semantic style. JSON output skips
    terminal styling and serializes the underlying data.
    """
    if config.get_flag("settings.only-json"):
        print(
            json.dumps(
                _to_plain_data(data),
                indent=2,
                ensure_ascii=False,
            ),
            file=stream,
        )
        return

    print(
        "\n".join(_format_value(data)),
        file=stream,
    )