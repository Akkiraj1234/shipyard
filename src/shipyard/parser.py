from typing import Any, List, TypeAlias, Dict, Optional, TypedDict
from enum import IntEnum
import sys
from .utils import ListStream, TokenType

# Tokenization helpers for the Shipyard CLI parser.
#
# This module handles the first parsing step: turning raw values from `sys.argv`
# into structured tokens that the command grammar can understand later.
#
# Example input:
#     roadmap done SHP-001 --message "Finished parser" --force
#
# Example token flow:
#     WORD
#     WORD
#     WORD
#     OPTION
#     FLAG
#
# This tokenizer only understands CLI shapes such as positional values, options,
# and flags. It does not decide whether a command is valid; that responsibility
# belongs to the grammar layer that consumes these tokens one step at a time.

class TokenType(IntEnum):
    """
    Token categories produced from CLI input.

    `word` represents a positional argument, `option` represents a key-value
    argument, and `flag` represents a switch without an attached value.
    """
    word = 0
    option = 1
    flag = 2

class Token(TypedDict):
    type: TokenType
    key: Optional[str]
    value: Optional[str]


TokenList: TypeAlias = List[Token]

class ParserRegistry(TypedDict):
    words: Dict[str, Any]
    options: Dict[str, Any]
    flags: Dict[str, Any]


    
def remove_flag_prefix(flag: str) -> str:
    """
    Remove a leading CLI prefix from an option or flag name.

    This normalizes tokens like `--force` and `-f` into plain names so the
    parser can work with consistent values internally.
    """

    if flag.startswith("--"):
        return flag[2:]

    if flag.startswith("-"):
        return flag[1:]

    return flag


def classify_token_type(stream: ListStream) -> Token:
    """
    Convert the current CLI value into a token dictionary.

    The tokenizer supports three common input shapes:
        word
        --option value
        --option=value
        --flag

    A positional value becomes a `word` token. A prefixed argument followed by
    a separate value, or containing `=`, becomes an `option` token. A prefixed
    argument with no value becomes a `flag` token.

    This function only classifies syntax. It does not validate command names,
    argument meaning, or command order.
    """
    if stream.current.startswith("-"):
        # option
        if "=" in stream.current:
            key, value = stream.current.split("=", 1)
            val = {
                "type": TokenType.option,
                "key": remove_flag_prefix(key),
                "value": value,
            }
        
        # option
        elif stream.peek is not None and not stream.peek.startswith("-"):
            val = {
                "type": TokenType.option,
                "key": remove_flag_prefix(stream.current),
                "value": stream.peek,
            }
            stream.move()

        # flag
        else:
            val = {
                "type": TokenType.flag,
                "key": None,
                "value": remove_flag_prefix(stream.current),
            }
    
    # word
    else:
        val = {
            "type": TokenType.word,
            "key": None,
            "value": stream.current,
        }
    
    stream.next()
    return val


def tokenize(argv: List[str]) -> TokenList:
    """
    Tokenize command-line arguments from `sys.argv`.

    The returned list contains normalized token dictionaries grouped into the
    three supported categories: word, option, and flag.
    """
    list_steam = ListStream(argv, 1)
    token = []
    
    while not list_steam.eof:
        token.append(
            classify_token_type(
                list_steam
            )
        )
    
    return token


class ParserStream:
    def __init__(self, token_list: TokenList):
        pass
    
    def parse(self, registry: ParserRegistry,  num: int = 1) -> any:
        pass
    




def parser() -> ParserStream:
    """
    its take user input from sys.args its tokenize it 
    and return a parser_stream obj
    """
    argv = sys.argv
    tokens = tokenize(argv)
    return ParserStream(tokens)
    
    
    
    
    

