from copy import deepcopy

from .ast_nodes import ASTNode
from .errors import CompilerError


NUMERIC = {"int", "float"}


class SemanticAnalyzer:
    def __init__(self, ast: ASTNode):
        self.ast = deepcopy(ast)
        self.scopes: list[dict[str, dict]] = []
        self.scope_ids: list[str] = []
        self.scope_counter = 0
        self.symbols: list[dict] = []
        self.warnings: list[str] = []
        self.steps: list[dict] = []
        self.current_function_return = "void"

    def analyze(self) -> tuple[dict, list[dict], list[str], list[dict]]:
        self.push_scope("global")
        self.visit(self.ast)
        self.pop_scope()
        return self.ast.to_dict(), self.symbols, self.warnings, self.steps

    def visit(self, node: ASTNode) -> str:
        method = getattr(self, f"visit_{node.kind}", self.visit_default)
        return method(node)

    def visit_default(self, node: ASTNode) -> str:
        inferred = "void"
        for child in node.children:
            inferred = self.visit(child)
        node.attrs["inferredType"] = inferred
        return inferred

    def visit_Program(self, node: ASTNode) -> str:
        for child in node.children:
            if child.kind == "FuncDecl":
                self.declare(child.attrs["name"], child.attrs["returnType"], "func", child.line)
        for child in node.children:
            self.visit(child)
        node.attrs["inferredType"] = "void"
        return "void"

    def visit_FuncDecl(self, node: ASTNode) -> str:
        previous = self.current_function_return
        self.current_function_return = node.attrs["returnType"]
        self.push_scope(f"func_{node.attrs['name']}")
        for param in node.attrs["params"]:
            self.declare(param["name"], param["type"], "var", param["line"])
        self.visit(node.children[-1])
        self.pop_scope()
        self.current_function_return = previous
        node.attrs["inferredType"] = node.attrs["returnType"]
        return node.attrs["returnType"]

    def visit_Block(self, node: ASTNode) -> str:
        self.push_scope("block")
        for child in node.children:
            self.visit(child)
        self.pop_scope()
        node.attrs["inferredType"] = "void"
        return "void"

    def visit_VarDecl(self, node: ASTNode) -> str:
        declared_type = node.attrs["type"]
        self.declare(node.attrs["name"], declared_type, "var", node.line)
        if node.children:
            init_type = self.visit(node.children[0])
            self.ensure_assignable(declared_type, init_type, node)
        node.attrs["inferredType"] = declared_type
        return declared_type

    def visit_Identifier(self, node: ASTNode) -> str:
        symbol = self.resolve(node.attrs["name"], node)
        node.attrs["inferredType"] = symbol["type"]
        self.step(f"Resolved {node.attrs['name']} as {symbol['type']}", node, {"symbol": symbol})
        return symbol["type"]

    def visit_Literal(self, node: ASTNode) -> str:
        node.attrs["inferredType"] = node.attrs["literalType"]
        return node.attrs["literalType"]

    def visit_AssignExpr(self, node: ASTNode) -> str:
        symbol = self.resolve(node.attrs["name"], node)
        value_type = self.visit(node.children[0])
        self.ensure_assignable(symbol["type"], value_type, node)
        node.attrs["inferredType"] = symbol["type"]
        self.step(f"Type-checked assignment to {node.attrs['name']}", node, {"targetType": symbol["type"], "valueType": value_type})
        return symbol["type"]

    def visit_BinaryExpr(self, node: ASTNode) -> str:
        left = self.visit(node.children[0])
        right = self.visit(node.children[1])
        op = node.attrs["op"]
        if op in {"+", "-", "*", "/", "%"}:
            if left not in NUMERIC or right not in NUMERIC:
                raise CompilerError(f"Operator '{op}' requires numeric operands", node.line, node.col, "semantic")
            inferred = "float" if "float" in {left, right} else "int"
        elif op in {"<", ">", "<=", ">="}:
            if left not in NUMERIC or right not in NUMERIC:
                raise CompilerError(f"Operator '{op}' requires numeric operands", node.line, node.col, "semantic")
            inferred = "bool"
        elif op in {"==", "!="}:
            if not self.compatible(left, right):
                raise CompilerError(f"Cannot compare {left} and {right}", node.line, node.col, "semantic")
            inferred = "bool"
        else:
            if left != "bool" or right != "bool":
                raise CompilerError(f"Operator '{op}' requires bool operands", node.line, node.col, "semantic")
            inferred = "bool"
        node.attrs["inferredType"] = inferred
        self.step(f"Type-checked {op}", node, {"left": left, "right": right, "result": inferred})
        return inferred

    def visit_UnaryExpr(self, node: ASTNode) -> str:
        operand = self.visit(node.children[0])
        op = node.attrs["op"]
        if op == "-" and operand not in NUMERIC:
            raise CompilerError("Unary '-' requires a numeric operand", node.line, node.col, "semantic")
        if op == "!" and operand != "bool":
            raise CompilerError("Unary '!' requires a bool operand", node.line, node.col, "semantic")
        inferred = operand if op == "-" else "bool"
        node.attrs["inferredType"] = inferred
        return inferred

    def visit_CallExpr(self, node: ASTNode) -> str:
        symbol = self.resolve(node.attrs["callee"], node, expected_kind="func")
        func_decl = self.find_function(node.attrs["callee"])
        expected = func_decl.attrs["params"] if func_decl else []
        if len(node.children) != len(expected):
            raise CompilerError(
                f"Function '{node.attrs['callee']}' expects {len(expected)} args but got {len(node.children)}",
                node.line,
                node.col,
                "semantic",
            )
        for arg, param in zip(node.children, expected):
            arg_type = self.visit(arg)
            self.ensure_assignable(param["type"], arg_type, node)
        node.attrs["inferredType"] = symbol["type"]
        self.step(f"Checked call to {node.attrs['callee']}", node, {"returnType": symbol["type"]})
        return symbol["type"]

    def visit_IfStmt(self, node: ASTNode) -> str:
        condition = self.visit(node.children[0])
        if condition != "bool":
            raise CompilerError("if condition must be bool", node.line, node.col, "semantic")
        self.visit(node.children[1])
        if len(node.children) > 2:
            self.visit(node.children[2])
        node.attrs["inferredType"] = "void"
        return "void"

    def visit_WhileStmt(self, node: ASTNode) -> str:
        condition = self.visit(node.children[0])
        if condition != "bool":
            raise CompilerError("while condition must be bool", node.line, node.col, "semantic")
        self.visit(node.children[1])
        node.attrs["inferredType"] = "void"
        return "void"

    def visit_ReturnStmt(self, node: ASTNode) -> str:
        value_type = "void"
        if node.children:
            value_type = self.visit(node.children[0])
        self.ensure_assignable(self.current_function_return, value_type, node)
        node.attrs["inferredType"] = value_type
        return value_type

    def declare(self, name: str, type_: str, kind: str, line: int) -> None:
        current = self.scopes[-1]
        if name in current:
            raise CompilerError(f"Redeclaration of '{name}'", line, 1, "semantic")
        symbol = {"name": name, "type": type_, "kind": kind, "scopeId": self.scope_ids[-1], "line": line}
        current[name] = symbol
        self.symbols.append(symbol)
        self.step(f"Inserted {kind} '{name}' into {self.scope_ids[-1]}", None, symbol)

    def resolve(self, name: str, node: ASTNode, expected_kind: str | None = None) -> dict:
        for scope in reversed(self.scopes):
            if name in scope and (expected_kind is None or scope[name]["kind"] == expected_kind):
                return scope[name]
        raise CompilerError(f"Undeclared identifier '{name}'", node.line, node.col, "semantic")

    def ensure_assignable(self, target: str, value: str, node: ASTNode) -> None:
        if not self.compatible(target, value):
            raise CompilerError(f"Cannot assign {value} to {target}", node.line, node.col, "semantic")

    def compatible(self, target: str, value: str) -> bool:
        return target == value or (target == "float" and value == "int")

    def find_function(self, name: str) -> ASTNode | None:
        for child in self.ast.children:
            if child.kind == "FuncDecl" and child.attrs["name"] == name:
                return child
        return None

    def push_scope(self, prefix: str) -> None:
        self.scope_counter += 1
        self.scopes.append({})
        self.scope_ids.append(f"{prefix}_{self.scope_counter}")

    def pop_scope(self) -> None:
        self.scopes.pop()
        self.scope_ids.pop()

    def step(self, description: str, node: ASTNode | None, snapshot: dict) -> None:
        self.steps.append(
            {
                "index": len(self.steps),
                "description": description,
                "highlightRange": None,
                "snapshot": {"nodeId": node.id if node else None, **snapshot},
            }
        )
