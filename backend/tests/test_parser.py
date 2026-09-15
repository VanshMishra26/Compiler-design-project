import pytest

from app.engine.errors import CompilerError
from app.engine.lexer import tokenize
from app.engine.parser import Parser


def parse(source: str):
    tokens, _ = tokenize(source)
    ast, _ = Parser(tokens).parse()
    return ast


def test_variable_declaration():
    ast = parse("int x = 1;")
    assert ast.children[0].kind == "VarDecl"


def test_function_with_params():
    ast = parse("int add(int a, int b) { return a + b; }")
    fn = ast.children[0]
    assert fn.kind == "FuncDecl"
    assert len(fn.attrs["params"]) == 2


def test_if_else_while_and_nested_blocks():
    ast = parse("void main() { int x = 0; while (x < 3) { if (x == 1) x = x + 1; else x = x + 2; } }")
    body = ast.children[0].children[-1]
    assert body.children[1].kind == "WhileStmt"


def test_operator_precedence():
    ast = parse("int x = 1 + 2 * 3;")
    expr = ast.children[0].children[0]
    assert expr.kind == "BinaryExpr"
    assert expr.attrs["op"] == "+"
    assert expr.children[1].attrs["op"] == "*"


@pytest.mark.parametrize("source", ["int x = ;", "void main( { }"])
def test_syntax_errors(source):
    with pytest.raises(CompilerError):
        parse(source)
