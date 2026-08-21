from blessed import Terminal
from typing import Any
import json

from .utils import DictBacked
from .config import config


class Colors(DictBacked):
    """
    Concrete terminal colors available to Shipyard's output system.

    Colors represent visual values rather than semantic meanings. Semantic
    output styles defined by :class:`Style` can use these colors to determine
    how different types of terminal output are displayed.
    """
    
    def __init__(self) -> None:
        term = Terminal()

        data = {
            "black": term.black,
            "red": term.red,
            "green": term.green,
            "yellow": term.yellow,
            "blue": term.blue,
            "magenta": term.magenta,
            "cyan": term.cyan,
            "white": term.white,

            "bright_black": term.bright_black,
            "bright_red": term.bright_red,
            "bright_green": term.bright_green,
            "bright_yellow": term.bright_yellow,
            "bright_blue": term.bright_blue,
            "bright_magenta": term.bright_magenta,
            "bright_cyan": term.bright_cyan,
            "bright_white": term.bright_white,
        }
        super().__init__(data)


class Style(DictBacked):
    """
    Semantic terminal styles used by Shipyard for formatted output.

    Each style represents the purpose of the output rather than a specific
    color. The default styles provide a consistent visual language for
    Shipyard and may be customized through configuration.

    Styles include:

    ``error``
        Used for failures, invalid input, and unrecoverable errors.

    ``success``
        Used when an operation completes successfully.

    ``warning``
        Used for conditions that require attention but do not prevent
        execution.

    ``info``
        Used for neutral informational messages and progress information.

    ``key``
        Used for names, identifiers, configuration keys, and other
        emphasized labels.

    ``value``
        Used for values associated with keys or descriptive output.
    """

    def __init__(self, colors: Colors) -> None:
        data = {
            "error": colors.red,
            "success": colors.green,
            "warning": colors.yellow,
            "info": colors.cyan,
            "key": colors.cyan,
            "value": colors.white,
        }

        super().__init__(data)


style: Style = Style()
color: Colors = Colors()
reset = Terminal().normal



class OutputFormatter:
    """
    Format command results for human-readable or JSON output.
    """

    def __init__(self) -> None:
        self.term = Terminal()
        self.no_color = config.get_flag(
            "settings.no-color"
        )
    
    def format(self, data: Any) -> str:
        """
        Format command data as human-readable text.
        """
        if isinstance(data, str):
            return data

        if isinstance(data, dict):
            return self._format_dict(data)

        return str(data)

    def json(self, data: Any) -> str:
        """
        Serialize command data as JSON without presentation formatting.
        """
        if isinstance(data, str):
            data = {"output": data}

        try:
            return json.dumps(data, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            return json.dumps(
                {"output": str(data)},
                indent=2,
                ensure_ascii=False,
            )

    def _format_dict(self, data: dict) -> str:
        """
        Format a dictionary as readable terminal output.
        """
        lines = []

        for key, value in data.items():
            lines.extend(self._format_value(key, value))

        return "\n".join(lines)

    def _format_value(
        self,
        key: str,
        value: Any,
        level: int = 0,
    ) -> list[str]:
        """
        Format one dictionary value recursively.
        """
        indent = "  " * level

        if isinstance(value, dict):
            lines = [f"{indent}{self._key(key)}:"]
            for child_key, child_value in value.items():
                lines.extend(
                    self._format_value(
                        child_key,
                        child_value,
                        level + 1,
                    )
                )
            return lines

        if isinstance(value, list):
            lines = [f"{indent}{self._key(key)}:"]

            for item in value:
                if isinstance(item, dict):
                    lines.append(f"{indent}  -")

                    for child_key, child_value in item.items():
                        lines.extend(
                            self._format_value(
                                child_key,
                                child_value,
                                level + 2,
                            )
                        )
                else:
                    lines.append(f"{indent}  - {item}")

            return lines

        return [f"{indent}{self._key(key)}: {value}"]

    def _key(self, key: str) -> str:
        """
        Format a dictionary key for terminal output.
        """
        if self.no_color:
            return key

        return f"{self.term.cyan}{self.term.bold}{key}{self.term.normal}"