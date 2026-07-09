from typing import List, Optional


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