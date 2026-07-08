from pathlib import Path
from enum import IntEnum
import sys

class TokenType(IntEnum):
    word = 0
    option = 1
    flag = 3


def get_args_token():
    args = sys.argv[1:]
    token = []
    i = 0
    
    while i < len(args):
        if args[i].startswith("-") or args[i].startswith("--"):
            if i < len(args)-1 and not args[i+1].startswith("-"):
                token.append({"type:": TokenType.option, "key": args[i], "value": args[i+1]})
                i += 2
            else:
                token.append({"type": TokenType.flag, "value": args[i]})
                i += 1
        
        token.append({"type": TokenType.word, "value": args[i]})
        i += 1
    
    return token