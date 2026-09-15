from dataclasses import dataclass
from enum import Enum


class TokenType(str, Enum):
    KEYWORD = "KEYWORD"
    IDENT = "IDENT"
    NUMBER = "NUMBER"
    FLOAT = "FLOAT"
    BOOL = "BOOL"
    OP = "OP"
    PUNCT = "PUNCT"
    EOF = "EOF"


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    line: int
    col: int
    startOffset: int
    endOffset: int

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "value": self.value,
            "line": self.line,
            "col": self.col,
            "startOffset": self.startOffset,
            "endOffset": self.endOffset,
        }
