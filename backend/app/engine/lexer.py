from .errors import CompilerError
from .tokens import Token, TokenType


KEYWORDS = {"int", "float", "bool", "void", "if", "else", "while", "return"}
BOOLS = {"true", "false"}
TWO_CHAR_OPS = {"==", "!=", "<=", ">=", "&&", "||"}
ONE_CHAR_OPS = {"=", "+", "-", "*", "/", "%", "<", ">", "!"}
PUNCT = {";", ",", "(", ")", "{", "}"}


def tokenize(source: str) -> tuple[list[Token], list[dict]]:
    tokens: list[Token] = []
    steps: list[dict] = []
    i = 0
    line = 1
    col = 1

    def emit(token_type: TokenType, value: str, start: int, end: int, token_line: int, token_col: int) -> None:
        token = Token(token_type, value, token_line, token_col, start, end)
        tokens.append(token)
        steps.append(
            {
                "index": len(steps),
                "description": f"Matched {token_type.value.lower()} '{value}'",
                "highlightRange": (start, end),
                "snapshot": {"tokenSoFar": token.to_dict(), "dfaState": f"ACCEPT_{token_type.value}"},
            }
        )

    while i < len(source):
        ch = source[i]

        if ch in " \t\r":
            i += 1
            col += 1
            continue
        if ch == "\n":
            i += 1
            line += 1
            col = 1
            continue
        if source.startswith("//", i):
            while i < len(source) and source[i] != "\n":
                i += 1
                col += 1
            continue

        start = i
        token_line = line
        token_col = col

        # DFA-equivalent maximal munch over identifier/keyword states.
        if ch.isalpha() or ch == "_":
            while i < len(source) and (source[i].isalnum() or source[i] == "_"):
                i += 1
                col += 1
            value = source[start:i]
            if value in BOOLS:
                emit(TokenType.BOOL, value, start, i, token_line, token_col)
            elif value in KEYWORDS:
                emit(TokenType.KEYWORD, value, start, i, token_line, token_col)
            else:
                emit(TokenType.IDENT, value, start, i, token_line, token_col)
            continue

        if ch.isdigit():
            while i < len(source) and source[i].isdigit():
                i += 1
                col += 1
            token_type = TokenType.NUMBER
            if i < len(source) and source[i] == ".":
                token_type = TokenType.FLOAT
                i += 1
                col += 1
                if i >= len(source) or not source[i].isdigit():
                    raise CompilerError("Expected digit after decimal point", line, col, "lex")
                while i < len(source) and source[i].isdigit():
                    i += 1
                    col += 1
            emit(token_type, source[start:i], start, i, token_line, token_col)
            continue

        two = source[i : i + 2]
        if two in TWO_CHAR_OPS:
            i += 2
            col += 2
            emit(TokenType.OP, two, start, i, token_line, token_col)
            continue
        if ch in ONE_CHAR_OPS:
            i += 1
            col += 1
            emit(TokenType.OP, ch, start, i, token_line, token_col)
            continue
        if ch in PUNCT:
            i += 1
            col += 1
            emit(TokenType.PUNCT, ch, start, i, token_line, token_col)
            continue

        raise CompilerError(f"Illegal character '{ch}'", line, col, "lex")

    eof = Token(TokenType.EOF, "EOF", line, col, len(source), len(source))
    tokens.append(eof)
    steps.append(
        {
            "index": len(steps),
            "description": "Reached end of file",
            "highlightRange": (len(source), len(source)),
            "snapshot": {"tokenSoFar": eof.to_dict(), "dfaState": "ACCEPT_EOF"},
        }
    )
    return tokens, steps
