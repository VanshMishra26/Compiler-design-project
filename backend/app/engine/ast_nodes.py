from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ASTNode:
    id: str
    kind: str
    label: str
    line: int
    col: int
    children: list["ASTNode"] = field(default_factory=list)
    attrs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
            "children": [child.to_dict() for child in self.children],
            "line": self.line,
            "col": self.col,
        }
        data.update(self.attrs)
        return data
