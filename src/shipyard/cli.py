from __future__ import annotations
import sys

from .parser import create_parser
from .core import execute
from .shipyard import build_root_command
from .error import ShipyardError


def main() -> int:
    """
    Bootstrap the Shipyard CLI and execute the requested command.

    Creates the parser, builds the root command, and delegates execution
    to the command framework.
    """
    
    stream = create_parser(sys.argv)
    command = build_root_command()
    
    try: 
        return execute(stream, command)
    
    except ShipyardError as error:
        return error.io_print()

    except Exception as error:
        print(f"Unknown error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())