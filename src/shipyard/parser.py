"""
Shipyard command-line parser.

This module implements the core parsing pipeline for the Shipyard CLI.
It converts raw command-line arguments into normalized tokens and exposes
a stream interface for consuming those tokens according to a command
grammar.

Responsibilities
----------------
- Tokenize raw CLI arguments.
- Normalize options and flags.
- Provide sequential token traversal.
- Support grammar-driven command parsing.

This module performs lexical and stream management only. Command
validation and execution are delegated to the registered grammar.
"""


from __future__ import annotations

from enum import IntEnum
from typing import Any, TypedDict, TypeAlias
from dataclasses import dataclass, field
import sys

from .utils import ListStream
from .command import Command

class TokenType(IntEnum):
    """
    Categories of tokens recognized from command-line input.
    """
    word = 0
    option = 1
    flag = 2


class Token(TypedDict):
    """
    Normalized token produced during lexical analysis.
    """
    type: TokenType
    name: str
    value: str | None


class GrammarRegistry(TypedDict):
    """
    Grammar definition for a command scope.

    Defines the valid subcommands, options, flags, and whether the
    current command consumes positional arguments.
    """
    words: dict[str, Any]
    options: dict[str, Any]
    flags: dict[str, Any]
    accepts_arguments: bool


@dataclass(slots=True, frozen=True)
class ParseResult:
    """
    Normalized command input produced by ParserStream.

    Commands consume this object to interpret positional arguments,
    options, and flags.
    """
    arguments: list[str] = field(default_factory=list)
    flags: set[str] = field(default_factory=set)
    options: dict[str, str] = field(default_factory=dict)


TokenList: TypeAlias = list[Token]




def strip_prefix(flag: str) -> str:
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


def classify_token_type(stream: ListStream) -> ParseResult:
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
        if "=" in stream.current:
            key, value = stream.current.split("=", 1)
            val = {
                "type": TokenType.option,
                "name": strip_prefix(key),
                "value": value,
            }
        
        elif stream.peek is not None and not stream.peek.startswith("-"):
            val = {
                "type": TokenType.option,
                "name": strip_prefix(stream.current),
                "value": stream.peek,
            }
            stream.move()

        else:
            val = {
                "type": TokenType.flag,
                "name": None,
                "value": strip_prefix(stream.current),
            }
        
    else:
        val = {
            "type": TokenType.word,
            "name": None,
            "value": stream.current,
        }
    
    stream.next()
    return val



def tokenize(argv: list[str]) -> TokenList:
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
    
    _TOKEN_TABLE = {
        TokenType.word: "words",
        TokenType.option: "options",
        TokenType.flag: "flags",
    }
    
    def __init__(self, token_list: TokenList):
        self.token_list = ListStream(token_list)
    
    def _search(self, grammar: GrammarRegistry):
        word = []
        flag = []
        option = {}
        
        while self.token_list.current:
            token = self.token_list.current
            if token.type == TokenType.word:
                word.append(token.name)
                
            elif token.type == TokenType.flag:
                flag.append(token.name)
            
            else:
                option[token.name] = token.value

            self.token_list.move()
        
        return ParseResult(word, flag, option)
    
    def _error(self):
        pass
    
    # there wont be any case where it will return both command and parseresult 
    # so its either command object or parseresult.
    
    def parse(self, grammar: GrammarRegistry) -> Command | ParseResult:
        """
        If the current grammar has child commands, search for the next
        token as a subcommand. If it has no child commands, consume the 
        remaining input according to the grammar.
        """
        if grammar.accepts_arguments:
            return self._search(grammar)
        
        token = self.token_list.current
        registry = grammar[self._TOKEN_TABLE[token.type]]
        
        if registry is None:
            raise 
        
        if not token.name in registry:
            raise
        
        return registry[token.name]
    
    def raise_error(self):
        pass


def create_parser() -> ParserStream:
    """
    its take user input from sys.args its tokenize it 
    and return a parser_stream obj
    """
    argv = sys.argv
    tokens = tokenize(argv)
    return ParserStream(tokens)