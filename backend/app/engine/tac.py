from .ast_nodes import ASTNode


class TACGenerator:
    def __init__(self, ast: ASTNode):
        self.ast = ast
        self.instructions: list[dict] = []
        self.steps: list[dict] = []
        self.temp_counter = 0
        self.label_counter = 0

    def generate(self) -> tuple[list[dict], int, list[dict]]:
        self.visit(self.ast)
        return self.instructions, self.temp_counter, self.steps

    def emit(self, op: str, arg1: str | None, arg2: str | None, result: str | None, node: ASTNode) -> dict:
        instruction = {
            "index": len(self.instructions),
            "op": op,
            "arg1": arg1,
            "arg2": arg2,
            "result": result,
            "sourceAstNodeId": node.id,
        }
        self.instructions.append(instruction)
        self.steps.append(
            {
                "index": len(self.steps),
                "description": f"Emitted {self.format_instruction(instruction)}",
                "highlightRange": None,
                "snapshot": {"instruction": instruction},
            }
        )
        return instruction

    def visit(self, node: ASTNode) -> str | None:
        method = getattr(self, f"visit_{node.kind}", self.visit_default)
        return method(node)

    def visit_default(self, node: ASTNode) -> str | None:
        value = None
        for child in node.children:
            value = self.visit(child)
        return value

    def visit_FuncDecl(self, node: ASTNode) -> str | None:
        self.emit("label", None, None, node.attrs["name"], node)
        return self.visit(node.children[-1])

    def visit_VarDecl(self, node: ASTNode) -> str | None:
        if node.children:
            value = self.visit(node.children[0])
            self.emit("=", value, None, node.attrs["name"], node)
        return node.attrs["name"]

    def visit_Literal(self, node: ASTNode) -> str:
        return str(node.attrs["value"])

    def visit_Identifier(self, node: ASTNode) -> str:
        return node.attrs["name"]

    def visit_AssignExpr(self, node: ASTNode) -> str:
        value = self.visit(node.children[0])
        self.emit("=", value, None, node.attrs["name"], node)
        return node.attrs["name"]

    def visit_BinaryExpr(self, node: ASTNode) -> str:
        left = self.visit(node.children[0])
        right = self.visit(node.children[1])
        temp = self.new_temp()
        self.emit(node.attrs["op"], left, right, temp, node)
        return temp

    def visit_UnaryExpr(self, node: ASTNode) -> str:
        operand = self.visit(node.children[0])
        temp = self.new_temp()
        self.emit(f"u{node.attrs['op']}", operand, None, temp, node)
        return temp

    def visit_CallExpr(self, node: ASTNode) -> str:
        for arg in node.children:
            self.emit("param", self.visit(arg), None, None, node)
        temp = self.new_temp()
        self.emit("call", node.attrs["callee"], str(len(node.children)), temp, node)
        return temp

    def visit_IfStmt(self, node: ASTNode) -> None:
        condition = self.visit(node.children[0])
        else_label = self.new_label()
        end_label = self.new_label()
        self.emit("ifFalse", condition, None, else_label, node)
        self.visit(node.children[1])
        if len(node.children) > 2:
            self.emit("goto", None, None, end_label, node)
            self.emit("label", None, None, else_label, node)
            self.visit(node.children[2])
            self.emit("label", None, None, end_label, node)
        else:
            self.emit("label", None, None, else_label, node)

    def visit_WhileStmt(self, node: ASTNode) -> None:
        top = self.new_label()
        end = self.new_label()
        self.emit("label", None, None, top, node)
        condition = self.visit(node.children[0])
        self.emit("ifFalse", condition, None, end, node)
        self.visit(node.children[1])
        self.emit("goto", None, None, top, node)
        self.emit("label", None, None, end, node)

    def visit_ReturnStmt(self, node: ASTNode) -> None:
        value = self.visit(node.children[0]) if node.children else None
        self.emit("return", value, None, None, node)

    def new_temp(self) -> str:
        temp = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp

    def new_label(self) -> str:
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label

    def format_instruction(self, i: dict) -> str:
        if i["op"] == "label":
            return f"{i['result']}:"
        if i["op"] == "goto":
            return f"goto {i['result']}"
        if i["op"] == "ifFalse":
            return f"ifFalse {i['arg1']} goto {i['result']}"
        if i["op"] == "=":
            return f"{i['result']} = {i['arg1']}"
        if i["op"] == "return":
            return f"return {i['arg1'] or ''}".strip()
        return f"{i['result']} = {i['arg1']} {i['op']} {i['arg2']}"
