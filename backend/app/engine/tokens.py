from dataclasses import dataclass
from enum import Enum


class TokenType(str, Enum):
    KEYWORD = "KEYWORD"
    IDENT = "IDENT"
    NUMBER = "NUMBER"
    FLOAT = "FLOAT"
    BOOL = "BOOL"
    STRING = "STRING"
    CHAR = "CHAR"
    PREPROCESSOR = "PREPROCESSOR"
    COMMENT = "COMMENT"
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
    end_line: int | None = None
    end_col: int | None = None
    skipped: bool = False
    raw: str | None = None

    def to_dict(self) -> dict:
        end_line = self.end_line if self.end_line is not None else self.line
        end_col = self.end_col if self.end_col is not None else self.col + len(self.value)
        data = {
            "type": self.type.value,
            "value": self.value,
            "lexeme": self.value,
            "line": self.line,
            "col": self.col,
            "column": self.col,
            "end_line": end_line,
            "end_column": end_col,
            "startOffset": self.startOffset,
            "endOffset": self.endOffset,
            "offset": self.startOffset,
            "skipped": self.skipped,
        }
        if self.raw is not None:
            data["raw"] = self.raw
        return data
