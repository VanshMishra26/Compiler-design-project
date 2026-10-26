from copy import deepcopy

from .ast_nodes import ASTNode
from .errors import CompilerError


NUMERIC = {"char", "short", "int", "long", "float", "double", "size_t"}
BUILTINS = {
    "printf": "int",
    "scanf": "int",
    "puts": "int",
    "putchar": "int",
    "getchar": "int",
    "malloc": "void*",
    "calloc": "void*",
    "realloc": "void*",
    "free": "void",
    "memcpy": "void*",
    "memset": "void*",
    "strlen": "long",
    "strcmp": "int",
    "strcpy": "char*",
    "strncpy": "char*",
    "strcat": "char*",
    "abs": "int",
    "exit": "void",
    "rand": "int",
    "srand": "void",
    "atoi": "int",
    "sqrt": "double",
    "pow": "double",
}


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
        for name, return_type in BUILTINS.items():
            self.declare(name, return_type, "func", 1, builtin=True)
        self.declare("size_t", "typedef", "typedef", 1, builtin=True)
        self.declare("FILE", "typedef", "typedef", 1, builtin=True)
        self.declare("NULL", "void*", "var", 1, builtin=True)
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
        if node.attrs.get("prototype"):
            node.attrs["inferredType"] = node.attrs["returnType"]
            return node.attrs["returnType"]
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

    def visit_VarDeclList(self, node: ASTNode) -> str:
        inferred = "void"
        for child in node.children:
            inferred = self.visit(child)
        node.attrs["inferredType"] = inferred
        return inferred

    def visit_TypeDecl(self, node: ASTNode) -> str:
        node.attrs["inferredType"] = "type"
        return "type"

    def visit_Identifier(self, node: ASTNode) -> str:
        symbol = self.resolve(node.attrs["name"], node)
        node.attrs["inferredType"] = symbol["type"]
        self.step(f"Resolved {node.attrs['name']} as {symbol['type']}", node, {"symbol": symbol})
        return symbol["type"]

    def visit_Literal(self, node: ASTNode) -> str:
        node.attrs["inferredType"] = node.attrs["literalType"]
        return node.attrs["literalType"]

    def visit_AssignExpr(self, node: ASTNode) -> str:
        if node.attrs.get("targetKind"):
            target_type = self.visit(node.children[0])
            value_type = self.visit(node.children[1])
            target_name = node.children[0].label
        else:
            symbol = self.resolve(node.attrs["name"], node)
            target_type = symbol["type"]
            value_type = self.visit(node.children[0])
            target_name = node.attrs["name"]
        op = node.attrs.get("op", "=")
        if op != "=":
            self.ensure_numeric_assignment(target_type, value_type, node, op)
        else:
            self.ensure_assignable(target_type, value_type, node)
        node.attrs["inferredType"] = target_type
        self.step(f"Type-checked assignment to {target_name}", node, {"targetType": target_type, "valueType": value_type})
        return target_type

    def visit_BinaryExpr(self, node: ASTNode) -> str:
        left = self.visit(node.children[0])
        right = self.visit(node.children[1])
        op = node.attrs["op"]
        if op in {"+", "-", "*", "/", "%", "<<", ">>", "&", "|", "^"}:
            if left not in NUMERIC or right not in NUMERIC:
                raise CompilerError(f"Operator '{op}' requires numeric operands", node.line, node.col, "semantic")
            inferred = "double" if "double" in {left, right} else "float" if "float" in {left, right} else "int"
        elif op in {"<", ">", "<=", ">="}:
            if left not in NUMERIC or right not in NUMERIC:
                raise CompilerError(f"Operator '{op}' requires numeric operands", node.line, node.col, "semantic")
            inferred = "bool"
        elif op in {"==", "!="}:
            if not self.compatible(left, right):
                raise CompilerError(f"Cannot compare {left} and {right}", node.line, node.col, "semantic")
            inferred = "bool"
        else:
            if left not in {"bool", *NUMERIC} or right not in {"bool", *NUMERIC}:
                raise CompilerError(f"Operator '{op}' requires bool operands", node.line, node.col, "semantic")
            inferred = "bool"
        node.attrs["inferredType"] = inferred
        self.step(f"Type-checked {op}", node, {"left": left, "right": right, "result": inferred})
        return inferred

    def visit_UnaryExpr(self, node: ASTNode) -> str:
        operand = self.visit(node.children[0])
        op = node.attrs["op"]
        if op in {"-", "~"} and operand not in NUMERIC:
            raise CompilerError("Unary '-' requires a numeric operand", node.line, node.col, "semantic")
        if op == "!" and operand not in {"bool", *NUMERIC}:
            raise CompilerError("Unary '!' requires a bool operand", node.line, node.col, "semantic")
        inferred = "long" if op == "sizeof" else f"{operand}*" if op == "&" else operand[:-1] if op == "*" and operand.endswith("*") else operand if op in {"-", "~", "++", "--"} else "bool"
        node.attrs["inferredType"] = inferred
        return inferred

    def visit_CallExpr(self, node: ASTNode) -> str:
        symbol = self.resolve(node.attrs["callee"], node, expected_kind="func")
        func_decl = self.find_function(node.attrs["callee"])
        expected = func_decl.attrs["params"] if func_decl else []
        if func_decl and len(node.children) != len(expected):
            raise CompilerError(
                f"Function '{node.attrs['callee']}' expects {len(expected)} args but got {len(node.children)}",
                node.line,
                node.col,
                "semantic",
            )
        if func_decl:
            for arg, param in zip(node.children, expected):
                arg_type = self.visit(arg)
                self.ensure_assignable(param["type"], arg_type, node)
        else:
            for arg in node.children:
                self.visit(arg)
        node.attrs["inferredType"] = symbol["type"]
        self.step(f"Checked call to {node.attrs['callee']}", node, {"returnType": symbol["type"]})
        return symbol["type"]

    def visit_IfStmt(self, node: ASTNode) -> str:
        condition = self.visit(node.children[0])
        if condition not in {"bool", *NUMERIC}:
            raise CompilerError("if condition must be bool", node.line, node.col, "semantic")
        self.visit(node.children[1])
        if len(node.children) > 2:
            self.visit(node.children[2])
        node.attrs["inferredType"] = "void"
        return "void"

    def visit_WhileStmt(self, node: ASTNode) -> str:
        condition = self.visit(node.children[0])
        if condition not in {"bool", *NUMERIC}:
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

    def visit_ForStmt(self, node: ASTNode) -> str:
        for child in node.children:
            self.visit(child)
        node.attrs["inferredType"] = "void"
        return "void"

    def visit_DoWhileStmt(self, node: ASTNode) -> str:
        for child in node.children:
            self.visit(child)
        node.attrs["inferredType"] = "void"
        return "void"

    def visit_SwitchStmt(self, node: ASTNode) -> str:
        for child in node.children:
            self.visit(child)
        node.attrs["inferredType"] = "void"
        return "void"

    def visit_IndexExpr(self, node: ASTNode) -> str:
        base = self.visit(node.children[0])
        self.visit(node.children[1])
        inferred = base[:-2] if base.endswith("[]") else base[:-1] if base.endswith("*") else "int"
        node.attrs["inferredType"] = inferred
        return inferred

    def visit_MemberExpr(self, node: ASTNode) -> str:
        self.visit(node.children[0])
        node.attrs["inferredType"] = "int"
        return "int"

    def visit_PostfixExpr(self, node: ASTNode) -> str:
        inferred = self.visit(node.children[0])
        node.attrs["inferredType"] = inferred
        return inferred

    def visit_BreakStmt(self, node: ASTNode) -> str:
        node.attrs["inferredType"] = "void"
        return "void"

    def visit_ContinueStmt(self, node: ASTNode) -> str:
        node.attrs["inferredType"] = "void"
        return "void"

    def visit_GotoStmt(self, node: ASTNode) -> str:
        node.attrs["inferredType"] = "void"
        return "void"

    def visit_LabelStmt(self, node: ASTNode) -> str:
        for child in node.children:
            self.visit(child)
        node.attrs["inferredType"] = "void"
        return "void"

    def visit_InitializerList(self, node: ASTNode) -> str:
        for child in node.children:
            self.visit(child)
        node.attrs["inferredType"] = "aggregate"
        return "aggregate"

    def visit_CaseStmt(self, node: ASTNode) -> str:
        for child in node.children:
            self.visit(child)
        node.attrs["inferredType"] = "void"
        return "void"

    def visit_DefaultStmt(self, node: ASTNode) -> str:
        for child in node.children:
            self.visit(child)
        node.attrs["inferredType"] = "void"
        return "void"

    def declare(self, name: str, type_: str, kind: str, line: int, builtin: bool = False) -> None:
        current = self.scopes[-1]
        if name in current:
            raise CompilerError(f"Redeclaration of '{name}'", line, 1, "semantic")
        symbol = {"name": name, "type": type_, "kind": kind, "scopeId": self.scope_ids[-1], "line": line, "scope_level": len(self.scopes) - 1, "size": self.sizeof(type_), "offset": 0, "storage": "builtin" if builtin else "auto", "builtin": builtin}
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

    def ensure_numeric_assignment(self, target: str, value: str, node: ASTNode, op: str) -> None:
        if target.rstrip("[]*") not in NUMERIC or value.rstrip("[]*") not in NUMERIC:
            raise CompilerError(f"Operator '{op}' requires numeric operands", node.line, node.col, "semantic")

    def compatible(self, target: str, value: str) -> bool:
        if target == value or value == "aggregate":
            return True
        if target in {"float", "double"} and value in NUMERIC:
            return True
        if target in NUMERIC and value in NUMERIC:
            if target != value:
                self.warnings.append(f"Implicit conversion from {value} to {target}")
            return True
        if target.endswith("*") and value in {"void*", "NULL"}:
            return True
        return False

    def sizeof(self, type_: str) -> int:
        base = type_.replace("const ", "").strip()
        if base.endswith("*"):
            return 8
        return {"char": 1, "short": 2, "int": 4, "bool": 1, "long": 8, "size_t": 8, "float": 4, "double": 8, "void": 0}.get(base, 8)

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
