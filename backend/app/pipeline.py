from typing import Any

from .engine.errors import CompilerError
from .engine.lexer import tokenize, tokenize_detailed
from .engine.optimizer import Optimizer
from .engine.parser import Parser
from .engine.semantic import SemanticAnalyzer
from .engine.tac import TACGenerator


def error_result(phase: str, error: CompilerError, steps: list[dict] | None = None) -> dict:
    return {"phase": phase, "success": False, "data": None, "error": error.to_payload(), "steps": steps or []}


def success_result(phase: str, data: Any, steps: list[dict]) -> dict:
    return {"phase": phase, "success": True, "data": data, "error": None, "steps": steps}


def run_lex(source: str) -> dict:
    output = tokenize_detailed(source)
    if output.errors:
        return success_result(
            "lex",
            {
                "tokens": [token.to_dict() for token in output.tokens if not token.skipped],
                "comments": output.comments,
                "preprocessor": output.preprocessor,
                "lex_errors": output.errors,
            },
            output.steps,
        )
    try:
        tokens = [token for token in output.tokens if not token.skipped]
        steps = output.steps
        return success_result(
            "lex",
            {
                "tokens": [token.to_dict() for token in tokens],
                "comments": output.comments,
                "preprocessor": output.preprocessor,
                "lex_errors": [],
            },
            steps,
        )
    except CompilerError as error:
        return error_result("lex", error)


def lex_or_raise(source: str):
    output = tokenize_detailed(source)
    if output.errors:
        first = output.errors[0]
        raise CompilerError(first["message"], first["line"], first["column"], "lex")
    return [token for token in output.tokens if not token.skipped], output.steps


def run_parse(source: str) -> tuple[dict, object | None]:
    try:
        tokens, _ = lex_or_raise(source)
        parser = Parser(tokens)
        ast, steps = parser.parse()
        return success_result("parse", {"ast": ast.to_dict()}, steps), ast
    except CompilerError as error:
        return error_result("parse", error), None


def run_semantic_from_ast(ast) -> tuple[dict, object | None]:
    try:
        analyzer = SemanticAnalyzer(ast)
        annotated_ast, symbols, warnings, steps = analyzer.analyze()
        return (
            success_result(
                "semantic",
                {"symbolTable": symbols, "annotatedAst": annotated_ast, "warnings": warnings},
                steps,
            ),
            analyzer.ast,
        )
    except CompilerError as error:
        return error_result("semantic", error), None


def run_tac_from_ast(ast) -> tuple[dict, list[dict] | None]:
    try:
        generator = TACGenerator(ast)
        instructions, temp_count, steps = generator.generate()
        return success_result("tac", {"instructions": instructions, "tempCount": temp_count}, steps), instructions
    except CompilerError as error:
        return error_result("tac", error), None


def run_optimize_from_tac(instructions: list[dict]) -> dict:
    optimizer = Optimizer(instructions)
    data, steps = optimizer.optimize()
    return success_result("optimize", data, steps)


def run_full_pipeline(source: str) -> dict:
    lex_result = run_lex(source)
    empty_tac = {"phase": "tac", "success": False, "data": None, "error": None, "steps": []}
    empty_optimize = {"phase": "optimize", "success": False, "data": None, "error": None, "steps": []}

    if not lex_result["success"]:
        return enrich_full_response(source, {
            "lex": lex_result,
            "parse": {"phase": "parse", "success": False, "data": None, "error": None, "steps": []},
            "semantic": {"phase": "semantic", "success": False, "data": None, "error": None, "steps": []},
            "tac": empty_tac,
            "optimize": empty_optimize,
        })

    parse_result, ast = run_parse(source)
    if not parse_result["success"] or ast is None:
        return enrich_full_response(source, {
            "lex": lex_result,
            "parse": parse_result,
            "semantic": {"phase": "semantic", "success": False, "data": None, "error": None, "steps": []},
            "tac": empty_tac,
            "optimize": empty_optimize,
        })

    semantic_result, annotated_ast = run_semantic_from_ast(ast)
    if not semantic_result["success"] or annotated_ast is None:
        return enrich_full_response(source, {"lex": lex_result, "parse": parse_result, "semantic": semantic_result, "tac": empty_tac, "optimize": empty_optimize})

    tac_result, instructions = run_tac_from_ast(annotated_ast)
    if not tac_result["success"] or instructions is None:
        return enrich_full_response(source, {"lex": lex_result, "parse": parse_result, "semantic": semantic_result, "tac": tac_result, "optimize": empty_optimize})

    optimize_result = run_optimize_from_tac(instructions)
    return enrich_full_response(source, {"lex": lex_result, "parse": parse_result, "semantic": semantic_result, "tac": tac_result, "optimize": optimize_result})


def enrich_full_response(source: str, result: dict) -> dict:
    lex_data = result["lex"].get("data") or {}
    parse_data = result["parse"].get("data") or {}
    semantic_data = result["semantic"].get("data") or {}
    tac_data = result["tac"].get("data") or {}
    optimize_data = result["optimize"].get("data") or {}
    tokens = lex_data.get("tokens", [])
    diagnostics = []
    diagnostics.extend(lex_data.get("lex_errors", []))
    for phase in ["parse", "semantic", "tac"]:
        error = result[phase].get("error")
        if error:
            diagnostics.append({"severity": "error", "code": phase.upper(), "message": error["message"], "line": error["line"], "column": error["column"]})
    diagnostics.extend({"severity": "warning", "code": "SEMANTIC_WARNING", "message": warning, "line": 1, "column": 1} for warning in semantic_data.get("warnings", []))
    ast = parse_data.get("ast")
    ast_stats = ast_statistics(ast)
    instructions = tac_data.get("instructions", [])
    function_name = infer_function_name(ast) or "global"
    result.update(
        {
            "tokens": tokens,
            "comments": lex_data.get("comments", []),
            "preprocessor": lex_data.get("preprocessor", {"includes": [], "defines": [], "conditionals": [], "diagnostics": []}),
            "lex_errors": lex_data.get("lex_errors", []),
            "ast": ast,
            "parse_errors": [d for d in diagnostics if d.get("code") == "PARSE"],
            "symbol_tables": group_symbols(semantic_data.get("symbolTable", [])),
            "types": {"structs": [], "unions": [], "enums": [], "typedefs": []},
            "diagnostics": diagnostics,
            "functions": [
                {
                    "name": function_name,
                    "tac": instructions,
                    "basic_blocks": optimize_data.get("blocks", []),
                    "cfg": optimize_data.get("cfg", {"nodes": [], "edges": []}),
                    "dag": optimize_data.get("dag", []),
                    "optimization_steps": optimize_data.get("optimizationSteps", []),
                    "optimized_tac": optimize_data.get("optimizedInstructions", []),
                }
            ],
            "data_section": [],
            "ast_stats": ast_stats,
            "line_count": source.count("\n") + (1 if source else 0),
        }
    )
    return result


def infer_function_name(ast: dict | None) -> str | None:
    if not ast:
        return None
    for child in ast.get("children", []):
        if child.get("kind") == "FuncDecl":
            return str(child.get("name") or child.get("label") or "function").split()[0]
    return None


def group_symbols(symbols: list[dict]) -> list[dict]:
    scopes: dict[str, list[dict]] = {}
    for symbol in symbols:
        scopes.setdefault(symbol.get("scopeId", "global"), []).append(symbol)
    return [{"id": scope_id, "symbols": entries} for scope_id, entries in scopes.items()]


def ast_statistics(ast: dict | None) -> dict:
    if not ast:
        return {"node_count": 0, "depth": 0}

    def walk(node: dict, depth: int) -> tuple[int, int]:
        total = 1
        max_depth = depth
        for child in node.get("children", []):
            child_total, child_depth = walk(child, depth + 1)
            total += child_total
            max_depth = max(max_depth, child_depth)
        return total, max_depth

    node_count, depth = walk(ast, 1)
    return {"node_count": node_count, "depth": depth}
