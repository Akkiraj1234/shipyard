from __future__ import annotations
import sys

from .parser import create_parser
from .core import execute, build_root_command


def main(argv: list[str] | None = None) -> int:
    """
    Bootstrap the Shipyard CLI and execute the requested command.

    This function initializes the application, constructs the parser and
    root command, and delegates execution to the command framework.
    Additional startup tasks, such as configuration loading and logging,
    may be added here as the application grows.
    """
    
    stream = create_parser(sys.argv)
    command = build_root_command()
    
    return execute(stream, command)


if __name__ == "__main__":
    sys.exit(main())