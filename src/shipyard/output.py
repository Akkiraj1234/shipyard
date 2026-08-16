from blessed import Terminal
from typing import Any
import json



class OutputFormatter:
    """
    Format command results for human-readable or JSON output.
    """

    def __init__(self, *, no_color: bool = False) -> None:
        self.term = Terminal()
        self.no_color = no_color

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