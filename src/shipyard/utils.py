from __future__ import annotations
from typing import Any, List


    
class ListStream:
    """
    Sequential stream interface for traversing a list.

    Provides cursor-based navigation with lookahead support.
    """

    def __init__(self, list: List, s_idx: int = 0):
        """
        Initialize a stream over a list.

        Args:
            list: Sequence to traverse.
            s_idx: Starting index within the sequence.
        """
        self.list = list
        self.idx = s_idx
        self.end_idx = len(list)

    @property
    def eof(self) -> bool:
        """
        Return whether the stream has reached the end.
        """
        return self.idx >= self.end_idx

    @property
    def current(self):
        """
        Return the current item, or ``None`` if the stream is exhausted.
        """
        if self.eof:
            return None
        return self.list[self.idx]

    @property
    def peek(self) -> Any | None:
        """
        Return the next item without advancing the stream.
        """
        if self.idx + 1 >= self.end_idx:
            return None
        return self.list[self.idx + 1]

    def move(self, count: int = 1) -> None:
        """
        Advance the stream by the given number of elements.
        """
        self.idx += count

    def next(self) -> Any | None:
        """
        Advance the stream and return the new current item.
        """
        self.move()
        return self.current
    
    def __str__(self) -> str:
        lines = ["ListStream"]
        
        for num, item in enumerate(self.list):
            connector = "└──" if num == self.end_idx else "├──"
            end = "  <- curr" if num == self.idx else ""
            lines.append(f"{connector} {item} {end}")
            
        if self.eof:
            lines.append("└──  <eof>  <── curr")
        
        return "\n".join(lines)
    
    def __repr__(self):
        return self.__str__()
        
