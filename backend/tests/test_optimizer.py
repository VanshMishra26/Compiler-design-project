from app.pipeline import run_full_pipeline


def test_constant_folding():
    result = run_full_pipeline("void main() { int x = 2 + 3; }")
    changes = result["optimize"]["data"]["peepholeChanges"]
    assert any("Constant folded 2 + 3 -> 5" in change["reason"] for change in changes)


def test_duplicate_subexpression_collapses_to_one_dag_node():
    result = run_full_pipeline("void main() { int a; int b; int x = a * b; int y = a * b; }")
    dag = result["optimize"]["data"]["dag"]
    multiply_nodes = [node for node in dag if node["label"] == "*"]
    assert len(multiply_nodes) == 1
    assert sorted(multiply_nodes[0]["representsInstructionIndices"]) == [1, 3]


def test_block_boundaries_around_if_else():
    result = run_full_pipeline("void main() { int x = 0; if (x == 0) x = 1; else x = 2; }")
    blocks = result["optimize"]["data"]["blocks"]
    assert len(blocks) >= 3
