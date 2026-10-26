from fastapi import APIRouter, File, HTTPException, UploadFile

from ..engine.lexer import tokenize
from ..optimizer_runner import optimize_source
from ..pipeline import run_full_pipeline, run_lex, run_parse, run_semantic_from_ast, run_tac_from_ast
from ..schemas import CompileRequest

router = APIRouter(prefix="/api/compile", tags=["compile"])
MAX_UPLOAD_BYTES = 256 * 1024


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


@router.post("/upload")
async def compile_upload(file: UploadFile = File(...)):
    filename = file.filename or ""
    if not filename.lower().endswith((".c", ".h")):
        raise HTTPException(status_code=400, detail="Only .c and .h files are supported")

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is larger than the 256 KB limit")
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    diagnostics = []
    try:
        source = content.decode("utf-8")
    except UnicodeDecodeError:
        source = content.decode("latin-1")
        diagnostics.append(
            {
                "severity": "info",
                "code": "UPLOAD_ENCODING",
                "message": "File was decoded as latin-1 because UTF-8 decoding failed",
                "line": 1,
                "column": 1,
            }
        )
    if source.startswith("\ufeff"):
        source = source.removeprefix("\ufeff")
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    if not source.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    result = run_full_pipeline(source)
    result["filename"] = filename
    result["size_bytes"] = len(content)
    result["line_count"] = source.count("\n") + (1 if source else 0)
    result["source"] = source
    result.setdefault("diagnostics", []).extend(diagnostics)
    return result
