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