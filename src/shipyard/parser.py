from typing import List, Optional
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
                i += 1
            else:
                token.append({"type": TokenType.flag, "value": args[i]})
        else:
            token.append({"type": TokenType.word, "value": args[i]})
        
        i += 1
    
    return token


class List_steam:
    def __init__(self, list: List, s_idx: int = 0):
        self.list = list
        self.idx = s_idx
        self.end_idx = len(list)
    
    @property
    def eof(self) -> bool:
        return self.index >= len(self.items)
    
    @property
    def current(self):
        return self.list[self.idx]
    
    def move(self, count: int = 1) -> None:
        self.idx += count
        
    
        
    def peek(self) -> Optional[any]:
        if self.idx >= self.end_idx:
            return None
        
        return self.list[self.idx+1]
        
    def next(self) -> Optional[any]:
        self.move()
        return self.current
        


def classify_token_type(steam: List_steam) -> Optional[any]:
    """
    create the tokens from given text
    """
    # scanning for options
    
    
        



def get_args_token():
    """
    tokenize the args passed by sys.argv
    in these 3 category: word, option, flag
    """
    list_steam = List_steam(sys.argv, 1)
    token = []
    
    while list_steam.eof:
        token.append(
            classify_token_type(
                list_steam
            )
        )
    
    return token
    
    