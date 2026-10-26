from __future__ import annotations

from dataclasses import dataclass, field

from .errors import CompilerError
from .tokens import Token, TokenType


KEYWORDS = {
    "auto",
    "break",
    "case",
    "char",
    "const",
    "continue",
    "default",
    "do",
    "double",
    "else",
    "enum",
    "extern",
    "float",
    "for",
    "goto",
    "if",
    "inline",
    "int",
    "long",
    "register",
    "restrict",
    "return",
    "short",
    "signed",
    "sizeof",
    "static",
    "struct",
    "switch",
    "typedef",
    "union",
    "unsigned",
    "void",
    "volatile",
    "while",
    "bool",
    "true",
    "false",
    "NULL",
}
BOOLS = {"true", "false"}
THREE_CHAR_OPS = {"<<=", ">>=", "..."}
TWO_CHAR_OPS = {
    "++",
    "--",
    "+=",
    "-=",
    "*=",
    "/=",
    "%=",
    "&=",
    "|=",
    "^=",
    "==",
    "!=",
    "<=",
    ">=",
    "&&",
    "||",
    "<<",
    ">>",
    "->",
}
ONE_CHAR_OPS = {"=", "+", "-", "*", "/", "%", "<", ">", "!", "&", "|", "^", "~", "?", ":", "."}
PUNCT = {";", ",", "(", ")", "{", "}", "[", "]"}
PREPROCESSOR_DIRECTIVES = {"include", "define", "ifdef", "ifndef", "endif", "if", "else", "undef"}


@dataclass
class LexOutput:
    tokens: list[Token]
    steps: list[dict]
    comments: list[dict] = field(default_factory=list)
    preprocessor: dict = field(default_factory=lambda: {"includes": [], "defines": [], "conditionals": [], "diagnostics": []})
    errors: list[dict] = field(default_factory=list)


def tokenize(source: str) -> tuple[list[Token], list[dict]]:
    output = tokenize_detailed(source)
    if output.errors:
        first = output.errors[0]
        raise CompilerError(first["message"], first["line"], first["column"], "lex")
    for token in output.tokens:
        if token.type == TokenType.STRING:
            raise CompilerError(f"Illegal character '{token.value[0]}'", token.line, token.col, "lex")
    return [token for token in output.tokens if not token.skipped], output.steps


def tokenize_detailed(source: str) -> LexOutput:
    scanner = _Scanner(source)
    return scanner.scan()


class _Scanner:
    def __init__(self, source: str):
        self.source = source
        self.tokens: list[Token] = []
        self.steps: list[dict] = []
        self.comments: list[dict] = []
        self.preprocessor = {"includes": [], "defines": [], "conditionals": [], "diagnostics": []}
        self.errors: list[dict] = []
        self.i = 0
        self.line = 1
        self.col = 1
        self.at_line_start = True

    def scan(self) -> LexOutput:
        while not self.done:
            ch = self.peek()

            if ch in " \t\r":
                self.advance()
                continue
            if ch == "\n":
                self.advance()
                self.line += 1
                self.col = 1
                self.at_line_start = True
                continue
            if self.at_line_start and ch == "#":
                self.scan_preprocessor()
                continue
            self.at_line_start = False

            if self.starts("//"):
                self.scan_line_comment()
            elif self.starts("/*"):
                self.scan_block_comment()
            elif ch.isalpha() or ch == "_":
                self.scan_identifier()
            elif ch.isdigit() or (ch == "." and self.peek(1).isdigit()):
                self.scan_number()
            elif ch == '"':
                self.scan_string()
            elif ch == "'":
                self.scan_char()
            else:
                self.scan_operator_or_error()

        eof = Token(TokenType.EOF, "EOF", self.line, self.col, len(self.source), len(self.source), self.line, self.col)
        self.tokens.append(eof)
        self.step(eof, "Reached end of file")
        return LexOutput(self.tokens, self.steps, self.comments, self.preprocessor, self.errors)

    @property
    def done(self) -> bool:
        return self.i >= len(self.source)

    def peek(self, ahead: int = 0) -> str:
        index = self.i + ahead
        return self.source[index] if index < len(self.source) else "\0"

    def starts(self, text: str) -> bool:
        return self.source.startswith(text, self.i)

    def advance(self) -> str:
        ch = self.source[self.i]
        self.i += 1
        self.col += 1
        return ch

    def emit(self, token_type: TokenType, value: str, start: int, line: int, col: int, skipped: bool = False, raw: str | None = None) -> Token:
        token = Token(token_type, value, line, col, start, self.i, self.line, self.col, skipped, raw)
        self.tokens.append(token)
        self.step(token, f"Matched {token_type.value.lower()} '{value}'")
        return token

    def step(self, token: Token, description: str) -> None:
        self.steps.append(
            {
                "index": len(self.steps),
                "description": description,
                "highlightRange": (token.startOffset, token.endOffset),
                "snapshot": {"tokenSoFar": token.to_dict(), "dfaState": f"ACCEPT_{token.type.value}"},
            }
        )

    def error(self, message: str, line: int | None = None, column: int | None = None) -> None:
        self.errors.append({"message": message, "line": line or self.line, "column": column or self.col, "phase": "lex"})

    def scan_identifier(self) -> None:
        start, line, col = self.i, self.line, self.col
        while self.peek().isalnum() or self.peek() == "_":
            self.advance()
        value = self.source[start:self.i]
        if value in BOOLS:
            self.emit(TokenType.BOOL, value, start, line, col)
        elif value in KEYWORDS:
            self.emit(TokenType.KEYWORD, value, start, line, col)
        else:
            self.emit(TokenType.IDENT, value, start, line, col)

    def scan_number(self) -> None:
        start, line, col = self.i, self.line, self.col
        is_float = False
        if self.starts(("0x", "0X")):
            self.advance()
            self.advance()
            while self.peek().isdigit() or self.peek().lower() in "abcdef":
                self.advance()
        elif self.starts(("0b", "0B")):
            self.advance()
            self.advance()
            while self.peek() in "01":
                self.advance()
        else:
            while self.peek().isdigit():
                self.advance()
            if self.peek() == ".":
                is_float = True
                self.advance()
                while self.peek().isdigit():
                    self.advance()
            if self.peek().lower() == "e":
                is_float = True
                self.advance()
                if self.peek() in "+-":
                    self.advance()
                if not self.peek().isdigit():
                    self.error("Malformed exponent in number literal", line, col)
                while self.peek().isdigit():
                    self.advance()
        while self.peek().lower() in "ulfl":
            if self.peek().lower() == "f":
                is_float = True
            self.advance()
        self.emit(TokenType.FLOAT if is_float else TokenType.NUMBER, self.source[start:self.i], start, line, col)

    def scan_string(self) -> None:
        start, line, col = self.i, self.line, self.col
        self.advance()
        while not self.done and self.peek() not in {'"', "\n"}:
            if self.peek() == "\\":
                self.advance()
                if not self.done:
                    self.advance()
            else:
                self.advance()
        if self.done or self.peek() == "\n":
            self.error("Unterminated string literal", line, col)
        else:
            self.advance()
        self.emit(TokenType.STRING, self.source[start:self.i], start, line, col)

    def scan_char(self) -> None:
        start, line, col = self.i, self.line, self.col
        self.advance()
        while not self.done and self.peek() not in {"'", "\n"}:
            if self.peek() == "\\":
                self.advance()
                if not self.done:
                    self.advance()
            else:
                self.advance()
        if self.done or self.peek() == "\n":
            self.error("Unterminated character literal", line, col)
        else:
            self.advance()
        self.emit(TokenType.CHAR, self.source[start:self.i], start, line, col)

    def scan_line_comment(self) -> None:
        start, line, col = self.i, self.line, self.col
        while not self.done and self.peek() != "\n":
            self.advance()
        token = self.emit(TokenType.COMMENT, self.source[start:self.i], start, line, col, skipped=True)
        self.comments.append(token.to_dict())

    def scan_block_comment(self) -> None:
        start, line, col = self.i, self.line, self.col
        self.advance()
        self.advance()
        while not self.done and not self.starts("*/"):
            if self.peek() == "\n":
                self.advance()
                self.line += 1
                self.col = 1
            else:
                self.advance()
        if self.done:
            self.error("Unterminated block comment", line, col)
        else:
            self.advance()
            self.advance()
        token = self.emit(TokenType.COMMENT, self.source[start:self.i], start, line, col, skipped=True)
        self.comments.append(token.to_dict())

    def scan_preprocessor(self) -> None:
        start, line, col = self.i, self.line, self.col
        while not self.done and self.peek() != "\n":
            self.advance()
        raw = self.source[start:self.i]
        parts = raw[1:].strip().split(None, 1)
        directive = parts[0] if parts else ""
        token = self.emit(TokenType.PREPROCESSOR, f"#{directive}", start, line, col, skipped=True, raw=raw)
        if directive == "include":
            self.preprocessor["includes"].append({"line": line, "raw": raw})
        elif directive == "define":
            self.preprocessor["defines"].append({"line": line, "raw": raw})
        elif directive in {"ifdef", "ifndef", "endif", "if", "else", "undef"}:
            self.preprocessor["conditionals"].append({"line": line, "directive": directive, "raw": raw})
        else:
            self.preprocessor["diagnostics"].append({"severity": "info", "line": line, "column": col, "message": f"Unsupported preprocessor directive '{directive}'"})
        self.comments.append(token.to_dict())

    def scan_operator_or_error(self) -> None:
        start, line, col = self.i, self.line, self.col
        three = self.source[self.i : self.i + 3]
        two = self.source[self.i : self.i + 2]
        if three in THREE_CHAR_OPS:
            self.i += 3
            self.col += 3
            self.emit(TokenType.OP if three != "..." else TokenType.PUNCT, three, start, line, col)
        elif two in TWO_CHAR_OPS:
            self.i += 2
            self.col += 2
            self.emit(TokenType.OP, two, start, line, col)
        elif self.peek() in ONE_CHAR_OPS:
            self.advance()
            self.emit(TokenType.OP, self.source[start:self.i], start, line, col)
        elif self.peek() in PUNCT:
            self.advance()
            self.emit(TokenType.PUNCT, self.source[start:self.i], start, line, col)
        else:
            bad = self.advance()
            self.error(f"Illegal character '{bad}'", line, col)

