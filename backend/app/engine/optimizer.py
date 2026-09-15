ARITHMETIC = {"+", "-", "*", "/", "%"}


class Optimizer:
    def __init__(self, instructions: list[dict]):
        self.instructions = instructions
        self.steps: list[dict] = []

    def optimize(self) -> tuple[dict, list[dict]]:
        blocks = self.basic_blocks()
        dag = self.build_dag(blocks)
        optimized, changes = self.peephole()
        result = {
            "blocks": blocks,
            "dag": dag,
            "peepholeChanges": changes,
            "optimizedInstructions": self.reindex(optimized),
        }
        return result, self.steps

    def basic_blocks(self) -> list[dict]:
        if not self.instructions:
            return []
        leaders = {0}
        labels = {instr["result"]: instr["index"] for instr in self.instructions if instr["op"] == "label"}
        for i, instr in enumerate(self.instructions):
            if instr["op"] == "label":
                leaders.add(i)
            if instr["op"] in {"goto", "ifFalse", "if"}:
                if i + 1 < len(self.instructions):
                    leaders.add(i + 1)
                if instr["result"] in labels:
                    leaders.add(labels[instr["result"]])
        starts = sorted(leaders)
        blocks = []
        for idx, start in enumerate(starts):
            end = (starts[idx + 1] - 1) if idx + 1 < len(starts) else len(self.instructions) - 1
            blocks.append(
                {
                    "id": f"B{idx}",
                    "startIndex": self.instructions[start]["index"],
                    "endIndex": self.instructions[end]["index"],
                    "instructions": self.instructions[start : end + 1],
                }
            )
        self.step("Partitioned TAC into basic blocks", {"blocks": [b["id"] for b in blocks]})
        return blocks

    def build_dag(self, blocks: list[dict]) -> list[dict]:
        nodes: dict[tuple, dict] = {}
        leaf_ids: dict[str, str] = {}
        next_id = 0

        def new_id() -> str:
            nonlocal next_id
            node_id = f"D{next_id}"
            next_id += 1
            return node_id

        def leaf(value: str) -> str:
            if value not in leaf_ids:
                node_id = new_id()
                leaf_ids[value] = node_id
                nodes[("leaf", value)] = {
                    "id": node_id,
                    "label": value,
                    "children": [],
                    "representsInstructionIndices": [],
                }
            return leaf_ids[value]

        for block in blocks:
            for instr in block["instructions"]:
                if instr["op"] in ARITHMETIC and instr["arg1"] is not None and instr["arg2"] is not None:
                    left = leaf(instr["arg1"])
                    right = leaf(instr["arg2"])
                    key = (instr["op"], left, right)
                    if key not in nodes:
                        nodes[key] = {
                            "id": new_id(),
                            "label": instr["op"],
                            "children": [left, right],
                            "representsInstructionIndices": [],
                        }
                    nodes[key]["representsInstructionIndices"].append(instr["index"])
        dag = list(nodes.values())
        self.step("Built value-numbering DAG", {"dagNodes": len(dag)})
        return dag

    def peephole(self) -> tuple[list[dict], list[dict]]:
        optimized = [dict(instr) for instr in self.instructions]
        changes = []
        i = 0
        while i < len(optimized):
            instr = optimized[i]
            if instr["op"] in ARITHMETIC and self.is_number(instr["arg1"]) and self.is_number(instr["arg2"]):
                value = self.fold(instr["op"], instr["arg1"], instr["arg2"])
                replacement = {**instr, "op": "=", "arg1": value, "arg2": None}
                changes.append(
                    {
                        "originalIndices": [instr["index"]],
                        "replacement": [replacement],
                        "reason": f"Constant folded {instr['arg1']} {instr['op']} {instr['arg2']} -> {value}",
                    }
                )
                optimized[i] = replacement
            elif (
                instr["op"] == "="
                and instr["result"]
                and i + 1 < len(optimized)
                and optimized[i + 1]["op"] == "="
                and optimized[i + 1]["arg1"] == instr["result"]
            ):
                replacement = {**optimized[i + 1], "arg1": instr["arg1"]}
                changes.append(
                    {
                        "originalIndices": [instr["index"], optimized[i + 1]["index"]],
                        "replacement": [instr, replacement],
                        "reason": "Eliminated redundant load/store through temporary",
                    }
                )
                optimized[i + 1] = replacement
            elif instr["op"] == "goto" and i + 1 < len(optimized) and optimized[i + 1]["op"] == "label" and instr["result"] == optimized[i + 1]["result"]:
                changes.append({"originalIndices": [instr["index"]], "replacement": [], "reason": "Removed jump to next instruction"})
                optimized.pop(i)
                continue
            i += 1
        self.step("Applied peephole optimizations", {"changes": len(changes)})
        return optimized, changes

    def reindex(self, instructions: list[dict]) -> list[dict]:
        return [{**instr, "index": index} for index, instr in enumerate(instructions)]

    def is_number(self, value: str | None) -> bool:
        if value is None:
            return False
        try:
            float(value)
            return True
        except ValueError:
            return False

    def fold(self, op: str, left: str, right: str) -> str:
        a = float(left) if "." in left else int(left)
        b = float(right) if "." in right else int(right)
        value = {
            "+": a + b,
            "-": a - b,
            "*": a * b,
            "/": a / b,
            "%": a % b,
        }[op]
        return str(int(value)) if isinstance(value, float) and value.is_integer() else str(value)

    def step(self, description: str, snapshot: dict) -> None:
        self.steps.append(
            {
                "index": len(self.steps),
                "description": description,
                "highlightRange": None,
                "snapshot": snapshot,
            }
        )
