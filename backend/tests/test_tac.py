from app.engine.lexer import tokenize
from app.engine.parser import Parser
from app.engine.semantic import SemanticAnalyzer
from app.engine.tac import TACGenerator


def tac(source: str):
    tokens, _ = tokenize(source)
    ast, _ = Parser(tokens).parse()
    analyzer = SemanticAnalyzer(ast)
    analyzer.analyze()
    instructions, temp_count, _ = TACGenerator(analyzer.ast).generate()
    return instructions, temp_count


def test_if_else_has_two_labels():
    instructions, _ = tac("void main() { int x = 0; if (x == 0) x = 1; else x = 2; }")
    labels = [i for i in instructions if i["op"] == "label" and i["result"].startswith("L")]
    assert len(labels) == 2
    assert any(i["op"] == "ifFalse" for i in instructions)


def test_while_has_back_edge():
    instructions, _ = tac("void main() { int x = 0; while (x < 3) x = x + 1; }")
    top_label = next(i["result"] for i in instructions if i["op"] == "label" and i["result"].startswith("L"))
    assert any(i["op"] == "goto" and i["result"] == top_label for i in instructions)


def test_expression_temp_order():
    instructions, temp_count = tac("void main() { int a; int b; int c; int x = a + b * c; }")
    math = [i for i in instructions if i["op"] in {"*", "+"}]
    assert temp_count == 2
    assert [i["op"] for i in math] == ["*", "+"]
