from .ast_nodes import ASTNode
from .errors import CompilerError
from .tokens import Token, TokenType


TYPES = {"char", "short", "int", "long", "float", "double", "bool", "void", "struct", "union", "enum"}
QUALIFIERS = {"static", "const", "extern", "auto", "register", "restrict", "volatile", "signed", "unsigned", "inline", "typedef"}


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
        while self.match_value("*"):
            type_token = Token(type_token.type, f"{type_token.value}*", type_token.line, type_token.col, type_token.startOffset, self.previous().endOffset)
        if self.match_value(";"):
            return self.node("TypeDecl", type_token.value, type_token)
        name = self.consume(TokenType.IDENT)
        if self.match_value("("):
            params = self.parse_params()
            self.consume_value(")")
            if self.match_value(";"):
                return self.node(
                    "FuncDecl",
                    f"{type_token.value} {name.value}()",
                    type_token,
                    [],
                    {"returnType": type_token.value, "name": name.value, "params": params, "prototype": True},
                )
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
        declarations = [self.parse_var_declarator(type_token, name)]
        while self.match_value(","):
            decl_type = type_token
            while self.match_value("*"):
                decl_type = Token(decl_type.type, f"{decl_type.value}*", decl_type.line, decl_type.col, decl_type.startOffset, self.previous().endOffset)
            declarations.append(self.parse_var_declarator(decl_type, self.consume(TokenType.IDENT)))
        self.consume_value(";")
        if len(declarations) == 1:
            return declarations[0]
        return self.node("VarDeclList", "declarations", type_token, declarations)

    def parse_var_declarator(self, type_token: Token, name: Token) -> ASTNode:
        children = []
        declared_type = type_token.value
        dimensions = []
        while self.check_value("["):
            self.consume_value("[")
            if not self.check_value("]"):
                dimensions.append(self.parse_expression().label)
            self.consume_value("]")
            declared_type = f"{declared_type}[]"
        if self.match_value("="):
            if self.check_value("{"):
                children.append(self.parse_initializer_list())
            else:
                children.append(self.parse_expression())
        return self.node(
            "VarDecl",
            f"{declared_type} {name.value}",
            type_token,
            children,
            {"type": declared_type, "name": name.value, "dimensions": dimensions},
        )

    def parse_params(self) -> list[dict]:
        self.enter("params")
        params = []
        if self.check_value(")"):
            return params
        if self.check(TokenType.KEYWORD) and self.peek().value == "void" and self.tokens[self.current + 1].value == ")":
            self.advance()
            return params
        while True:
            if self.match_value("..."):
                params.append({"type": "varargs", "name": "...", "line": self.previous().line})
                break
            type_token = self.consume_type()
            while self.match_value("*"):
                type_token = Token(type_token.type, f"{type_token.value}*", type_token.line, type_token.col, type_token.startOffset, type_token.endOffset)
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
        if self.is_type_keyword() or self.looks_like_typedef_name():
            type_token = self.consume_type()
            while self.match_value("*"):
                type_token = Token(type_token.type, f"{type_token.value}*", type_token.line, type_token.col, type_token.startOffset, self.previous().endOffset)
            name = self.consume(TokenType.IDENT)
            return self.finish_var_decl(type_token, name)
        if self.match_value(";"):
            return self.node("EmptyStmt", "empty", self.previous())
        if self.match_keyword("if"):
            return self.parse_if(self.previous())
        if self.match_keyword("while"):
            return self.parse_while(self.previous())
        if self.match_keyword("for"):
            return self.parse_for(self.previous())
        if self.match_keyword("do"):
            return self.parse_do_while(self.previous())
        if self.match_keyword("switch"):
            return self.parse_switch(self.previous())
        if self.match_keyword("case"):
            return self.parse_case(self.previous())
        if self.match_keyword("default"):
            return self.parse_default(self.previous())
        if self.match_keyword("break"):
            start = self.previous()
            self.consume_value(";")
            return self.node("BreakStmt", "break", start)
        if self.match_keyword("continue"):
            start = self.previous()
            self.consume_value(";")
            return self.node("ContinueStmt", "continue", start)
        if self.match_keyword("return"):
            return self.parse_return(self.previous())
        if self.match_keyword("goto"):
            start = self.previous()
            label = self.consume(TokenType.IDENT)
            self.consume_value(";")
            return self.node("GotoStmt", f"goto {label.value}", start, attrs={"labelName": label.value})
        if self.check(TokenType.IDENT) and self.tokens[self.current + 1].value == ":":
            label = self.advance()
            self.advance()
            return self.node("LabelStmt", f"{label.value}:", label, [self.parse_statement()], {"labelName": label.value})
        if self.check_value("{"):
            return self.parse_block()
        return self.parse_expr_stmt()

    def parse_for(self, start: Token) -> ASTNode:
        self.consume_value("(")
        children = []
        if not self.check_value(";"):
            if self.is_type_keyword() or self.looks_like_typedef_name():
                type_token = self.consume_type()
                while self.match_value("*"):
                    type_token = Token(type_token.type, f"{type_token.value}*", type_token.line, type_token.col, type_token.startOffset, self.previous().endOffset)
                name = self.consume(TokenType.IDENT)
                children.append(self.finish_var_decl(type_token, name))
            else:
                children.append(self.parse_expression())
                self.consume_value(";")
        else:
            self.consume_value(";")
        if not self.check_value(";"):
            children.append(self.parse_expression())
        self.consume_value(";")
        if not self.check_value(")"):
            children.append(self.parse_expression())
        self.consume_value(")")
        children.append(self.parse_statement())
        return self.node("ForStmt", "for", start, children)

    def parse_do_while(self, start: Token) -> ASTNode:
        body = self.parse_statement()
        self.consume(TokenType.KEYWORD, "while")
        self.consume_value("(")
        condition = self.parse_expression()
        self.consume_value(")")
        self.consume_value(";")
        return self.node("DoWhileStmt", "do while", start, [body, condition])

    def parse_switch(self, start: Token) -> ASTNode:
        self.consume_value("(")
        condition = self.parse_expression()
        self.consume_value(")")
        body = self.parse_statement()
        return self.node("SwitchStmt", "switch", start, [condition, body])

    def parse_case(self, start: Token) -> ASTNode:
        value = self.parse_expression()
        self.consume_value(":")
        statements = []
        while not self.check(TokenType.EOF) and not self.check_value("}") and not self.check_keyword_value("case") and not self.check_keyword_value("default"):
            statements.append(self.parse_statement())
        return self.node("CaseStmt", "case", start, [value, *statements])

    def parse_default(self, start: Token) -> ASTNode:
        self.consume_value(":")
        statements = []
        while not self.check(TokenType.EOF) and not self.check_value("}") and not self.check_keyword_value("case") and not self.check_keyword_value("default"):
            statements.append(self.parse_statement())
        return self.node("DefaultStmt", "default", start, statements)

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
        if self.peek().value in {"=", "+=", "-=", "*=", "/=", "%=", "<<=", ">>=", "&=", "|=", "^="}:
            equals = self.advance()
            value = self.parse_assignment()
            op = equals.value
            name = expr.attrs.get("name", expr.label)
            if expr.kind == "Identifier":
                return self.node("AssignExpr", f"{name} {op}", equals, [value], {"name": name, "op": op})
            return self.node("AssignExpr", f"{expr.label} {op}", equals, [expr, value], {"name": name, "op": op, "targetKind": expr.kind})
        return expr

    def parse_logic_or(self) -> ASTNode:
        return self.parse_binary(self.parse_logic_and, {"||"}, "logicOr")

    def parse_logic_and(self) -> ASTNode:
        return self.parse_binary(self.parse_bit_or, {"&&"}, "logicAnd")

    def parse_bit_or(self) -> ASTNode:
        return self.parse_binary(self.parse_bit_xor, {"|"}, "bitOr")

    def parse_bit_xor(self) -> ASTNode:
        return self.parse_binary(self.parse_bit_and, {"^"}, "bitXor")

    def parse_bit_and(self) -> ASTNode:
        return self.parse_binary(self.parse_equality, {"&"}, "bitAnd")

    def parse_equality(self) -> ASTNode:
        return self.parse_binary(self.parse_comparison, {"==", "!="}, "equality")

    def parse_comparison(self) -> ASTNode:
        return self.parse_binary(self.parse_shift, {"<", ">", "<=", ">="}, "comparison")

    def parse_shift(self) -> ASTNode:
        return self.parse_binary(self.parse_term, {"<<", ">>"}, "shift")

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
        if self.peek().value in {"-", "!", "~", "*", "&", "++", "--", "sizeof"}:
            op = self.advance()
            right = self.parse_unary()
            return self.node("UnaryExpr", op.value, op, [right], {"op": op.value})
        return self.parse_call()

    def parse_call(self) -> ASTNode:
        self.enter("call")
        expr = self.parse_primary()
        while True:
            if self.match_value("("):
                paren = self.previous()
                args = []
                if not self.check_value(")"):
                    while True:
                        args.append(self.parse_expression())
                        if not self.match_value(","):
                            break
                self.consume_value(")")
                callee = expr.attrs.get("name", expr.label)
                expr = self.node("CallExpr", f"{callee}()", paren, args, {"callee": callee})
            elif self.match_value("["):
                bracket = self.previous()
                index = self.parse_expression()
                self.consume_value("]")
                expr = self.node("IndexExpr", "[]", bracket, [expr, index])
            elif self.match_value(".") or self.match_value("->"):
                op = self.previous()
                field = self.consume(TokenType.IDENT)
                expr = self.node("MemberExpr", f"{expr.label}{op.value}{field.value}", op, [expr], {"field": field.value, "op": op.value})
            elif self.match_value("++") or self.match_value("--"):
                op = self.previous()
                expr = self.node("PostfixExpr", op.value, op, [expr], {"op": op.value})
            else:
                break
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
        if self.match(TokenType.STRING):
            return self.node("Literal", token.value, token, attrs={"literalType": "char*", "value": token.value})
        if self.match(TokenType.CHAR):
            return self.node("Literal", token.value, token, attrs={"literalType": "char", "value": token.value})
        if token.value == "NULL":
            self.advance()
            return self.node("Literal", token.value, token, attrs={"literalType": "void*", "value": "NULL"})
        if self.match(TokenType.IDENT):
            return self.node("Identifier", token.value, token, attrs={"name": token.value})
        if self.match_value("("):
            expr = self.parse_expression()
            self.consume_value(")")
            return expr
        raise CompilerError(f"Expected expression but found '{token.value}'", token.line, token.col, "parse")

    def parse_initializer_list(self) -> ASTNode:
        start = self.consume_value("{")
        children = []
        while not self.check_value("}") and not self.check(TokenType.EOF):
            if self.check_value("{"):
                children.append(self.parse_initializer_list())
            else:
                children.append(self.parse_expression())
            self.match_value(",")
        self.consume_value("}")
        return self.node("InitializerList", "initializer", start, children)

    def skip_balanced(self, open_value: str, close_value: str) -> None:
        self.consume_value(open_value)
        depth = 1
        while depth and not self.check(TokenType.EOF):
            if self.check_value(open_value):
                depth += 1
            elif self.check_value(close_value):
                depth -= 1
            self.advance()

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
        while self.peek().type == TokenType.KEYWORD and self.peek().value in QUALIFIERS:
            self.advance()
        if self.is_type_keyword():
            token = self.advance()
            if token.value in {"struct", "union", "enum"}:
                end = token
                if self.check(TokenType.IDENT):
                    end = self.advance()
                    value = f"{token.value} {end.value}"
                else:
                    value = token.value
                if self.check_value("{"):
                    self.skip_balanced("{", "}")
                return Token(token.type, value, token.line, token.col, token.startOffset, end.endOffset)
            return token
        if self.peek().type == TokenType.IDENT and self.looks_like_typedef_name():
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

    def check_keyword_value(self, value: str) -> bool:
        return self.peek().type == TokenType.KEYWORD and self.peek().value == value

    def check(self, token_type: TokenType) -> bool:
        return self.peek().type == token_type

    def check_value(self, value: str) -> bool:
        return self.peek().value == value

    def is_type_keyword(self) -> bool:
        token = self.peek()
        return token.type == TokenType.KEYWORD and (token.value in TYPES or token.value in QUALIFIERS)

    def looks_like_typedef_name(self) -> bool:
        token = self.peek()
        if token.type != TokenType.IDENT:
            return False
        next_token = self.tokens[self.current + 1]
        return next_token.type == TokenType.IDENT or next_token.value == "*"

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
