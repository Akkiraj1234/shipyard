from abc import ABC, abstractmethod

from .types import GrammarRegistry, ParseResult
from .parser import ParserStream




class Command(ABC):
    """
    Base class for all Shipyard commands.
    """

    NAME: str
    DESCRIPTION: str

    @property
    @abstractmethod
    def grammar(self) -> GrammarRegistry:
        ...

    @abstractmethod
    def execute(self, result: ParseResult) -> None:
        ...
        

class Command:
    pass


def execute(parserstream: ParserStream, grammar: GrammarRegistry) -> int:
    # while ParserStream
    
    while not parserstream.eof:
        if parserstream.current in grammar.words:
            pass
        
        elif parserstream.current in grammar.options:
            pass
        
        elif parserstream.current in grammar.flags:
            pass
        
        else:
            # tho it might never happen
            raise
