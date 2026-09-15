import pytest

from app.engine.errors import CompilerError
from app.engine.lexer import tokenize


def values(source: str):
    tokens, _ = tokenize(source)
    return [token.value for token in tokens]


def test_empty_input_returns_eof():
    assert values("") == ["EOF"]


def test_valid_program_offsets():
    tokens, _ = tokenize("int x = 5;")
    assert [token.value for token in tokens] == ["int", "x", "=", "5", ";", "EOF"]
    assert tokens[0].startOffset == 0
    assert tokens[0].endOffset == 3
    assert tokens[3].startOffset == 8


def test_illegal_character():
    with pytest.raises(CompilerError):
        tokenize('int x = "oops";')


def test_float_number():
    assert values("float x = 3.14;") == ["float", "x", "=", "3.14", ";", "EOF"]


def test_keyword_identifier_disambiguation():
    tokens, _ = tokenize("intx = 1;")
    assert tokens[0].type.value == "IDENT"
    assert tokens[0].value == "intx"
