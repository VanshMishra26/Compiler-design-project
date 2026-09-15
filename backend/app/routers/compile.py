from fastapi import APIRouter

from ..engine.lexer import tokenize
from ..optimizer_runner import optimize_source
from ..pipeline import run_full_pipeline, run_lex, run_parse, run_semantic_from_ast, run_tac_from_ast
from ..schemas import CompileRequest

router = APIRouter(prefix="/api/compile", tags=["compile"])


@router.post("/lex")
def compile_lex(request: CompileRequest):
    return run_lex(request.source)


@router.post("/parse")
def compile_parse(request: CompileRequest):
    result, _ = run_parse(request.source)
    return result


@router.post("/semantic")
def compile_semantic(request: CompileRequest):
    parse_result, ast = run_parse(request.source)
    if ast is None:
        return parse_result
    result, _ = run_semantic_from_ast(ast)
    return result


@router.post("/tac")
def compile_tac(request: CompileRequest):
    parse_result, ast = run_parse(request.source)
    if ast is None:
        return parse_result
    semantic_result, annotated_ast = run_semantic_from_ast(ast)
    if annotated_ast is None:
        return semantic_result
    result, _ = run_tac_from_ast(annotated_ast)
    return result


@router.post("/optimize")
def compile_optimize(request: CompileRequest):
    return optimize_source(request.source)


@router.post("/full")
def compile_full(request: CompileRequest):
    return run_full_pipeline(request.source)
