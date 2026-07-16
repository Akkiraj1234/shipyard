from __future__ import annotations
import sys

from .parser import create_parser


def main(argv: list[str] | None = None) -> None:
    """
    its works is to start the main application
    currently bootstrap is handle by main 
    later it will be divided.
    """
    stream = create_parser()
    print(stream)


if __name__ == "__main__":
    sys.exit(main())

