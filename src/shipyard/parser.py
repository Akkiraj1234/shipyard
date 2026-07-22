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

import sys
from typing import TYPE_CHECKING

from .types import (
    GrammarRegistry, 
    ParseResult, 
    Token, 
    TokenList, 
    TokenType 
)
from .utils import ListStream
from .error import ShipyardParserError

if TYPE_CHECKING:
    from .core import Command




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



class ParserStream(ListStream):
    
    def __init__(self, items: TokenList):
        super().__init__(items, s_idx = 0)
        self.grammar_registry = None
        
    
    def parse(self, grammar: GrammarRegistry) -> ParseResult:
        """
        If the current grammar has child commands, search for the next
        token as a subcommand. If it has no child commands, consume the 
        remaining input according to the grammar.
        """
        self.grammar_registry = grammar
        
        if self.grammar_registry is None:
            raise ShipyardParserError(self, "Invalid grammar registry for token stream.")
        
        if self.current is None:
            return ParseResult()
        
        if (
            self.grammar_registry.has_child and
            self.current["type"] == TokenType.word and 
            bool(self.grammar_registry.words)
        ):
            child = self.current["value"]
            
            if child not in self.grammar_registry.words:
                raise ShipyardParserError(self, f"invalid subcommand {child}")
            
            self.move()
            return ParseResult(child = child)
        
        parse_arg = self._parse_arguments()
        return parse_arg
    
    def _parse_arguments(self) -> ParseResult:
        word: list[str] = []
        flag: set[str] = set()
        option: dict[str, str] = {}
        
        while self.current:
            token = self.current           
            
            if token["type"] == TokenType.word:
                if token["value"] not in self.grammar_registry.words:
                    raise ValueError(f"{token['value']} is not a valid argument")

                word.append(token["value"])

            elif token["type"] == TokenType.flag:
                if token["value"] not in self.grammar_registry.flags:
                    raise ValueError(f"{token['value']} is not a valid flag")
                flag.add(token["value"])

            elif token["name"] is not None and token["value"] is not None:
                if token["name"] not in self.grammar_registry.options:
                    raise ValueError(f"{token['name']} is not a valid option")
                
                option[token["name"]] = token["value"]
                
            self.move()
            
        return ParseResult(None, word, option, flag)


def create_parser(argv: list[str] | None = None) -> ParserStream:
    """
    its take user input from sys.args its tokenize it 
    and return a parser_stream obj
    """
    argv = sys.argv if argv is None else argv
    tokens = tokenize(argv)
    return ParserStream(tokens)
