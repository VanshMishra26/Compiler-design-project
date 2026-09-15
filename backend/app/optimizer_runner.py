from .pipeline import run_optimize_from_tac, run_parse, run_semantic_from_ast, run_tac_from_ast


def optimize_source(source: str) -> dict:
    parse_result, ast = run_parse(source)
    if ast is None:
        return parse_result
    semantic_result, annotated_ast = run_semantic_from_ast(ast)
    if annotated_ast is None:
        return semantic_result
    tac_result, instructions = run_tac_from_ast(annotated_ast)
    if instructions is None:
        return tac_result
    return run_optimize_from_tac(instructions)
