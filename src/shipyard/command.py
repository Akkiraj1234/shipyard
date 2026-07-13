from abc import ABC, abstractmethod
from .parser import GrammarRegistry, ParseResult

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