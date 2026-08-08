from __future__ import annotations
import sys

from .parser import create_parser
from .core import build_core_flag, cleanup, execute
from .shipyard import Shipyard_Command
from .error import shipyard_error_print


def test_command(command):
    print("command_metdata\n", command.metadata(), "\n")
    print("command_grammer\n", command.grammar(), "\n")
    print("command_get_child\n", command.get_child("init"), "\n")
    print("command_child_metadata\n", command.child_metadata(), "\n")
    print("command_run", command.run(), "\n")

def main() -> int:
    """
    Bootstrap the Shipyard CLI and execute the requested command.

    Creates the parser, builds the root command, and delegates execution
    to the command framework.
    """
    
    stream = create_parser(sys.argv)
    ctx = build_core_flag(stream)
    command = Shipyard_Command(ctx)
    test_command(command)
    return
    try: 
        return execute(stream, command, ctx)
    
    except Exception as error:
        raise error
        return shipyard_error_print(error, ctx)
    
    finally:
        cleanup(command, ctx)


if __name__ == "__main__":
    sys.exit(main())