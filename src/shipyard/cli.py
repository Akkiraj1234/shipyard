from __future__ import annotations
import sys

from .parser import create_parser
from .core import build_core_flag, cleanup, execute
from .shipyard import ShipyardCommand
from .error import shipyard_error_print



def main() -> int:
    """
    Bootstrap the Shipyard CLI and execute the requested command.

    Creates the parser, builds the root command, and delegates execution
    to the command framework.
    """
    
    stream = create_parser(sys.argv)
    ctx = build_core_flag(stream)
    command = ShipyardCommand(ctx)
    
    try: 
        return execute(stream, command)
    
    except Exception as error:
        return shipyard_error_print(error, ctx)
    
    finally:
        cleanup(command, ctx)


if __name__ == "__main__":
    sys.exit(main())
