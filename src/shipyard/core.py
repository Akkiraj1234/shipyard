from .types import GrammarRegistry
from .parser import ParserStream



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