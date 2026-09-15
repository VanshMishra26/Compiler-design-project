from typing import Any

from .engine.errors import CompilerError
from .engine.lexer import tokenize
from .engine.optimizer import Optimizer
from .engine.parser import Parser
from .engine.semantic import SemanticAnalyzer
from .engine.tac import TACGenerator


def error_result(phase: str, error: CompilerError, steps: list[dict] | None = None) -> dict:
    return {"phase": phase, "success": False, "data": None, "error": error.to_payload(), "steps": steps or []}


def success_result(phase: str, data: Any, steps: list[dict]) -> dict:
    return {"phase": phase, "success": True, "data": data, "error": None, "steps": steps}


def run_lex(source: str) -> dict:
    try:
        tokens, steps = tokenize(source)
        return success_result("lex", {"tokens": [token.to_dict() for token in tokens]}, steps)
    except CompilerError as error:
        return error_result("lex", error)


def lex_or_raise(source: str):
    return tokenize(source)


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
        return {
            "lex": lex_result,
            "parse": {"phase": "parse", "success": False, "data": None, "error": None, "steps": []},
            "semantic": {"phase": "semantic", "success": False, "data": None, "error": None, "steps": []},
            "tac": empty_tac,
            "optimize": empty_optimize,
        }

    parse_result, ast = run_parse(source)
    if not parse_result["success"] or ast is None:
        return {
            "lex": lex_result,
            "parse": parse_result,
            "semantic": {"phase": "semantic", "success": False, "data": None, "error": None, "steps": []},
            "tac": empty_tac,
            "optimize": empty_optimize,
        }

    semantic_result, annotated_ast = run_semantic_from_ast(ast)
    if not semantic_result["success"] or annotated_ast is None:
        return {"lex": lex_result, "parse": parse_result, "semantic": semantic_result, "tac": empty_tac, "optimize": empty_optimize}

    tac_result, instructions = run_tac_from_ast(annotated_ast)
    if not tac_result["success"] or instructions is None:
        return {"lex": lex_result, "parse": parse_result, "semantic": semantic_result, "tac": tac_result, "optimize": empty_optimize}

    optimize_result = run_optimize_from_tac(instructions)
    return {"lex": lex_result, "parse": parse_result, "semantic": semantic_result, "tac": tac_result, "optimize": optimize_result}
