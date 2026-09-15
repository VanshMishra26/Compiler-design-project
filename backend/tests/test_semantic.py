import pytest

from app.engine.errors import CompilerError
from app.engine.lexer import tokenize
from app.engine.parser import Parser
from app.engine.semantic import SemanticAnalyzer


def analyze(source: str):
    tokens, _ = tokenize(source)
    ast, _ = Parser(tokens).parse()
    analyzer = SemanticAnalyzer(ast)
    return analyzer.analyze()


def test_undeclared_var_caught():
    with pytest.raises(CompilerError):
        analyze("void main() { x = 1; }")


def test_redeclaration_caught():
    with pytest.raises(CompilerError):
        analyze("void main() { int x; int x; }")


def test_type_mismatch_caught():
    with pytest.raises(CompilerError):
        analyze("void main() { int x = true; }")


def test_nested_scope_symbols_have_different_scope_ids():
    _, symbols, _, _ = analyze("void main() { int x = 1; { int y = x; } }")
    entries = {symbol["name"]: symbol for symbol in symbols}
    assert entries["x"]["scopeId"] != entries["y"]["scopeId"]
