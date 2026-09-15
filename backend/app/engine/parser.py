from .ast_nodes import ASTNode
from .errors import CompilerError
from .tokens import Token, TokenType


TYPES = {"int", "float", "bool", "void"}


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0
        self.node_counter = 0
        self.steps: list[dict] = []

    def parse(self) -> tuple[ASTNode, list[dict]]:
        ast = self.parse_program()
        self.consume(TokenType.EOF, "EOF")
        return ast, self.steps

    def parse_program(self) -> ASTNode:
        self.enter("program")
        children = []
        start = self.peek()
        while not self.check(TokenType.EOF):
            children.append(self.parse_declaration())
        return self.node("Program", "Program", start, children)

    def parse_declaration(self) -> ASTNode:
        self.enter("declaration")
        type_token = self.consume_type()
        name = self.consume(TokenType.IDENT)
        if self.match_value("("):
            params = self.parse_params()
            self.consume_value(")")
            body = self.parse_block()
            param_nodes = [
                self.node("Param", p["name"], type_token, attrs={"type": p["type"], "name": p["name"]})
                for p in params
            ]
            return self.node(
                "FuncDecl",
                f"{type_token.value} {name.value}()",
                type_token,
                [*param_nodes, body],
                {"returnType": type_token.value, "name": name.value, "params": params},
            )
        return self.finish_var_decl(type_token, name)

    def finish_var_decl(self, type_token: Token, name: Token) -> ASTNode:
        children = []
        if self.match_value("="):
            children.append(self.parse_expression())
        self.consume_value(";")
        return self.node(
            "VarDecl",
            f"{type_token.value} {name.value}",
            type_token,
            children,
            {"type": type_token.value, "name": name.value},
        )

    def parse_params(self) -> list[dict]:
        self.enter("params")
        params = []
        if self.check_value(")"):
            return params
        while True:
            type_token = self.consume_type()
            name = self.consume(TokenType.IDENT)
            params.append({"type": type_token.value, "name": name.value, "line": name.line})
            if not self.match_value(","):
                break
        return params

    def parse_block(self) -> ASTNode:
        self.enter("block")
        start = self.consume_value("{")
        statements = []
        while not self.check_value("}") and not self.check(TokenType.EOF):
            statements.append(self.parse_statement())
        self.consume_value("}")
        return self.node("Block", "block", start, statements)

    def parse_statement(self) -> ASTNode:
        self.enter("statement")
        if self.is_type_keyword():
            type_token = self.advance()
            name = self.consume(TokenType.IDENT)
            return self.finish_var_decl(type_token, name)
        if self.match_keyword("if"):
            return self.parse_if(self.previous())
        if self.match_keyword("while"):
            return self.parse_while(self.previous())
        if self.match_keyword("return"):
            return self.parse_return(self.previous())
        if self.check_value("{"):
            return self.parse_block()
        return self.parse_expr_stmt()

    def parse_if(self, start: Token) -> ASTNode:
        self.enter("ifStmt")
        self.consume_value("(")
        condition = self.parse_expression()
        self.consume_value(")")
        then_branch = self.parse_statement()
        children = [condition, then_branch]
        if self.match_keyword("else"):
            children.append(self.parse_statement())
        return self.node("IfStmt", "if", start, children)

    def parse_while(self, start: Token) -> ASTNode:
        self.enter("whileStmt")
        self.consume_value("(")
        condition = self.parse_expression()
        self.consume_value(")")
        body = self.parse_statement()
        return self.node("WhileStmt", "while", start, [condition, body])

    def parse_return(self, start: Token) -> ASTNode:
        self.enter("returnStmt")
        children = []
        if not self.check_value(";"):
            children.append(self.parse_expression())
        self.consume_value(";")
        return self.node("ReturnStmt", "return", start, children)

    def parse_expr_stmt(self) -> ASTNode:
        self.enter("exprStmt")
        expr = self.parse_expression()
        self.consume_value(";")
        return self.node("ExprStmt", "expr", expr_token(expr), [expr])

    def parse_expression(self) -> ASTNode:
        self.enter("expression")
        return self.parse_assignment()

    def parse_assignment(self) -> ASTNode:
        self.enter("assignment")
        expr = self.parse_logic_or()
        if self.match_value("="):
            equals = self.previous()
            value = self.parse_assignment()
            if expr.kind != "Identifier":
                raise CompilerError("Invalid assignment target", equals.line, equals.col, "parse")
            return self.node("AssignExpr", f"{expr.attrs['name']} =", equals, [value], {"name": expr.attrs["name"]})
        return expr

    def parse_logic_or(self) -> ASTNode:
        return self.parse_binary(self.parse_logic_and, {"||"}, "logicOr")

    def parse_logic_and(self) -> ASTNode:
        return self.parse_binary(self.parse_equality, {"&&"}, "logicAnd")

    def parse_equality(self) -> ASTNode:
        return self.parse_binary(self.parse_comparison, {"==", "!="}, "equality")

    def parse_comparison(self) -> ASTNode:
        return self.parse_binary(self.parse_term, {"<", ">", "<=", ">="}, "comparison")

    def parse_term(self) -> ASTNode:
        return self.parse_binary(self.parse_factor, {"+", "-"}, "term")

    def parse_factor(self) -> ASTNode:
        return self.parse_binary(self.parse_unary, {"*", "/", "%"}, "factor")

    def parse_binary(self, operand_fn, operators: set[str], rule: str) -> ASTNode:
        self.enter(rule)
        expr = operand_fn()
        while self.peek().value in operators:
            op = self.advance()
            right = operand_fn()
            expr = self.node("BinaryExpr", op.value, op, [expr, right], {"op": op.value})
        return expr

    def parse_unary(self) -> ASTNode:
        self.enter("unary")
        if self.peek().value in {"-", "!"}:
            op = self.advance()
            right = self.parse_unary()
            return self.node("UnaryExpr", op.value, op, [right], {"op": op.value})
        return self.parse_call()

    def parse_call(self) -> ASTNode:
        self.enter("call")
        expr = self.parse_primary()
        if self.match_value("("):
            paren = self.previous()
            args = []
            if not self.check_value(")"):
                while True:
                    args.append(self.parse_expression())
                    if not self.match_value(","):
                        break
            self.consume_value(")")
            if expr.kind != "Identifier":
                raise CompilerError("Can only call functions by name", paren.line, paren.col, "parse")
            return self.node("CallExpr", f"{expr.attrs['name']}()", paren, args, {"callee": expr.attrs["name"]})
        return expr

    def parse_primary(self) -> ASTNode:
        self.enter("primary")
        token = self.peek()
        if self.match(TokenType.NUMBER):
            return self.node("Literal", token.value, token, attrs={"literalType": "int", "value": token.value})
        if self.match(TokenType.FLOAT):
            return self.node("Literal", token.value, token, attrs={"literalType": "float", "value": token.value})
        if self.match(TokenType.BOOL):
            return self.node("Literal", token.value, token, attrs={"literalType": "bool", "value": token.value})
        if self.match(TokenType.IDENT):
            return self.node("Identifier", token.value, token, attrs={"name": token.value})
        if self.match_value("("):
            expr = self.parse_expression()
            self.consume_value(")")
            return expr
        raise CompilerError(f"Expected expression but found '{token.value}'", token.line, token.col, "parse")

    def node(
        self,
        kind: str,
        label: str,
        token: Token,
        children: list[ASTNode] | None = None,
        attrs: dict | None = None,
    ) -> ASTNode:
        self.node_counter += 1
        node = ASTNode(f"n{self.node_counter}", kind, label, token.line, token.col, children or [], attrs or {})
        self.steps.append(
            {
                "index": len(self.steps),
                "description": f"Produced {kind}",
                "highlightRange": None,
                "snapshot": {"producedNodeId": node.id, "ruleApplied": kind, "tokenConsumed": None},
            }
        )
        return node

    def enter(self, rule: str) -> None:
        token = self.peek()
        self.steps.append(
            {
                "index": len(self.steps),
                "description": f"Enter {rule}",
                "highlightRange": (token.startOffset, token.endOffset),
                "snapshot": {"producedNodeId": None, "ruleApplied": rule, "tokenConsumed": None},
            }
        )

    def consume_type(self) -> Token:
        if self.is_type_keyword():
            return self.advance()
        token = self.peek()
        raise CompilerError(f"Expected type but found '{token.value}'", token.line, token.col, "parse")

    def consume(self, token_type: TokenType, value: str | None = None) -> Token:
        token = self.peek()
        if token.type == token_type and (value is None or token.value == value):
            return self.advance()
        expected = value or token_type.value
        raise CompilerError(f"Expected '{expected}' but found '{token.value}'", token.line, token.col, "parse")

    def consume_value(self, value: str) -> Token:
        token = self.peek()
        if token.value == value:
            return self.advance()
        raise CompilerError(f"Expected '{value}' but found '{token.value}'", token.line, token.col, "parse")

    def match(self, token_type: TokenType) -> bool:
        if self.check(token_type):
            self.advance()
            return True
        return False

    def match_value(self, value: str) -> bool:
        if self.check_value(value):
            self.advance()
            return True
        return False

    def match_keyword(self, value: str) -> bool:
        if self.peek().type == TokenType.KEYWORD and self.peek().value == value:
            self.advance()
            return True
        return False

    def check(self, token_type: TokenType) -> bool:
        return self.peek().type == token_type

    def check_value(self, value: str) -> bool:
        return self.peek().value == value

    def is_type_keyword(self) -> bool:
        token = self.peek()
        return token.type == TokenType.KEYWORD and token.value in TYPES

    def advance(self) -> Token:
        token = self.peek()
        if not self.check(TokenType.EOF):
            self.current += 1
        self.steps.append(
            {
                "index": len(self.steps),
                "description": f"Consumed '{token.value}'",
                "highlightRange": (token.startOffset, token.endOffset),
                "snapshot": {"producedNodeId": None, "ruleApplied": "consume", "tokenConsumed": token.to_dict()},
            }
        )
        return token

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]


def expr_token(node: ASTNode) -> Token:
    return Token(TokenType.IDENT, node.label, node.line, node.col, 0, 0)
