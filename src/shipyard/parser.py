"""
Tokenize and validate command-line input for Shipyard.

The parser converts ``argv`` values into normalized word, option, and flag
tokens, then exposes a cursor-based stream for consuming them against a
command's :class:`~shipyard.types.GrammarRegistry`. Command discovery and
execution remain the responsibility of the command layer (see ADR-0001).

``ParserStream.parse()`` raises :class:`~shipyard.error.UnknownCommandError`
when a child command is not registered, and
:class:`~shipyard.error.InvalidInputError` when an argument, option, or flag
is not accepted by the active grammar.
"""

from __future__ import annotations
import sys

from .utils import ListStream
from .types import (
    GrammarRegistry, 
    ParseResult, 
    Token, 
    TokenList, 
    TokenType 
)
from .error import (
    InvalidInputError, 
    ShipyardParserError, 
    UnknownCommandError
)



def strip_prefix(flag: str) -> str:
    """
    Return an option or flag name without its leading hyphen prefix.

    For example, ``--force`` becomes ``force`` and ``-f`` becomes ``f``.
    Values without a prefix are returned unchanged.
    """

    if flag.startswith("--"):
        return flag[2:]

    if flag.startswith("-"):
        return flag[1:]

    return flag


def classify_token_type(stream: ListStream) -> Token:
    """
    Classify and consume the stream's current command-line value.

    Positional values become word tokens. ``--option value`` and
    ``--option=value`` become option tokens, while a prefixed value without an
    associated value becomes a flag token. This lexical step does not validate
    command names or whether a token is accepted by a grammar.
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
                "name": strip_prefix(stream.current),
                "value": None
            }
        
    else:
        val = {
            "type": TokenType.word,
            "name": stream.current,
            "value": None,
        }
    
    stream.next()
    return val


def tokenize(argv: list[str]) -> TokenList:
    """
    Return normalized tokens for an ``argv``-style argument list.

    The first value is treated as the executable name and is not tokenized.
    Remaining values are classified as words, options, or flags. Syntax is
    normalized here; grammar validation occurs in :meth:`ParserStream.parse`.
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
    """
    A cursor over normalized command-line tokens.

    The stream inherits traversal operations from :class:`ListStream` and
    retains its position between calls to :meth:`parse`. This lets the command
    executor resolve one child command at a time before validating the input
    accepted by the resolved command.
    """
    
    def __init__(self, items: TokenList):
        super().__init__(items, s_idx = 0)
        self.grammar_registry = None
        
    
    def parse(self, grammar: GrammarRegistry | None) -> ParseResult:
        """
        Consume input according to ``grammar`` and return its parse result.

        A grammar with child commands consumes one word token and returns it in
        :attr:`ParseResult.child`. Otherwise, all remaining tokens are
        validated and returned as positional arguments, options, and flags.

        Raises:
            ShipyardParserError: If ``grammar`` is ``None`` instead of a
                :class:`GrammarRegistry`.
            UnknownCommandError: If the next child-command token is not
                registered in ``grammar.words``.
            InvalidInputError: If a positional argument, option, or flag is
                not accepted by the grammar.
        """
        self.grammar_registry = grammar
        
        if self.grammar_registry is None:
            raise ShipyardParserError(
                self,
                "cannot parse command-line input without a grammar registry",
                hint="Pass a GrammarRegistry that describes the current command.",
            )
        
        if self.current is None:
            return ParseResult()
        
        if (
            self.grammar_registry.has_child and
            self.current["type"] == TokenType.word
        ):
            child = self.current["name"]
            
            if child not in self.grammar_registry.words:
                raise UnknownCommandError(
                    self, child, self.grammar_registry.words
                )
            
            self.move()
            return ParseResult(child = child)
        
        parse_arg = self._parse_arguments()
        return parse_arg
    
    def _parse_arguments(self) -> ParseResult:
        """
        Validate and consume all remaining tokens for the active grammar.

        Returns:
            ParseResult: A parse result containing accepted positional arguments, 
            options, and flags.

        Raises:
            InvalidInputError: If a remaining token is not declared by the
                active grammar.
        """
        word: list[str] = []
        flag: set[str] = set()
        option: dict[str, str] = {}
        
        while self.current:
            token = self.current           
            
            if token["type"] == TokenType.word:
                if token["name"] not in self.grammar_registry.words:
                    raise InvalidInputError(
                        self, "argument", token["name"],
                        self.grammar_registry.words,
                    )

                word.append(token["name"])

            elif token["type"] == TokenType.flag:
                if token["name"] not in self.grammar_registry.flags:
                    raise InvalidInputError(
                        self, "flag", token["name"],
                        self.grammar_registry.flags,
                    )
                flag.add(token["name"])

            elif token["name"] is not None and token["value"] is not None:
                if token["name"] not in self.grammar_registry.options:
                    raise InvalidInputError(
                        self, "option", token["name"],
                        self.grammar_registry.options,
                    )
                
                option[token["name"]] = token["value"]
                
            self.move()
            
        return ParseResult(None, word, option, flag)


def create_parser(argv: list[str] | None = None) -> ParserStream:
    """
    Create a parser stream from an ``argv``-style list.

    Args:
        argv: The complete argument vector, including the executable name. If
            omitted, uses :data:`sys.argv`.

    Returns:
        A stream positioned at the first command-line argument.
    """
    argv = sys.argv if argv is None else argv
    tokens = tokenize(argv)
    return ParserStream(tokens)
