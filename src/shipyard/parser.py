from typing import List
from pathlib import Path
from enum import IntEnum
import sys


"""
CLI Grammar
=========================

Program
└── shipyard

Command
└── roadmap

Subcommand
└── done

Arguments
└── SHP-001

Options
└── --message "Finished parser"

Flags
└── --force


Parser Design
===========================

The parser works in two stages.

1. Tokenizer
------------
Converts raw `sys.argv` into structured tokens.

Example:

    roadmap done SHP-001 --message "Finished parser" --force

↓

    WORD
    WORD
    WORD
    OPTION
    FLAG

The tokenizer only understands CLI syntax, not Shipyard commands.


2. Grammar Parser
-----------------

Each parser owns a dictionary of the next valid tokens.

Root Parser

    roadmap -> RoadmapParser
    doctor  -> DoctorParser
    release -> ReleaseParser

↓

RoadmapParser

    add
    done
    remove

↓

DoneParser

    task_id
    --message
    --force

Each parser consumes only the next expected token, then delegates the remaining
tokens to the next parser.

The parser never searches the entire command line—it walks the command tree one
step at a time.
"""


registry = {
    "init": None,
    "roadmap": None,
    "Task": None,
    "idea": None,
    "doctor": None,
    "status": None,
    "generate": None,
    "update": None,
    "Release": None
}





def Tokenizer(tokens: List[str]):
    """
    to tokenize we are using it that way
    each text will be consider word
    each --text with not value consider flag
    each --text value will consider option
    
    """
    for char in tokens:
        pass
        



def get_args():
    args = sys.argv
    return args

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
