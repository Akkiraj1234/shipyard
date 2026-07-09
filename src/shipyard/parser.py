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



class ListStream:
    def __init__(self, list: List, s_idx: int = 0):
        self.list = list
        self.idx = s_idx
        self.end_idx = len(list)
    
    @property
    def eof(self) -> bool:
        return self.idx >= self.end_idx
    
    @property
    def current(self):
        if self.eof: return None
        return self.list[self.idx]
    
    @property
    def peek(self) -> Optional[any]:
        if self.idx+1 >= self.end_idx:
            return None
        return self.list[self.idx+1]
    
    def move(self, count: int = 1) -> None:
        self.idx += count
        
    def next(self) -> Optional[any]:
        self.move()
        return self.current
        


def classify_token_type(steam: ListStream) -> Optional[any]:
    """
    create the tokens from given text
    currently its support 
    --flag search
    --option value search
    'any other word' search
    
    need to add
    --option= word search
    ./hello/some.txt full path creation
    """
    # scanning for options
    if steam.current.startswith("-") or steam.current.startswith("--"):
        if "=" in steam.current:
            key, value = items = steam.current.split("=", 1)
            val = {"type": TokenType.option, "key": key, "value": value} 
            
        elif steam.peek and not steam.peek.startswith("-"):
            val = {"type": TokenType.option, "key": steam.current, "value": steam.peek}
            steam.move(1)

        else:
            val = {"type": TokenType.flag, "key": None, "value": steam.current}
    
    else:
        val = {"type": TokenType.word, "key": None, "value": steam.current}
    
    steam.next()
    return val
        



def get_args_token():
    """
    tokenize the args passed by sys.argv
    in these 3 category: word, option, flag
    """
    list_steam = ListStream(sys.argv, 1)
    token = []
    
    while not list_steam.eof:
        token.append(
            classify_token_type(
                list_steam
            )
        )
    
    return token
    
    