from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


PhaseName = Literal["lex", "parse", "semantic", "tac", "optimize"]
TokenName = Literal["KEYWORD", "IDENT", "NUMBER", "FLOAT", "BOOL", "STRING", "CHAR", "PREPROCESSOR", "COMMENT", "OP", "PUNCT", "EOF"]
ValueType = str


class CompileRequest(BaseModel):
    source: str


class CompilerErrorPayload(BaseModel):
    message: str
    line: int
    column: int
    phase: str


class StepTrace(BaseModel):
    index: int
    description: str
    highlightRange: tuple[int, int] | None = None
    snapshot: Any = None


class TokenPayload(BaseModel):
    type: TokenName
    value: str
    lexeme: str | None = None
    line: int
    col: int
    column: int | None = None
    end_line: int | None = None
    end_column: int | None = None
    startOffset: int
    endOffset: int
    offset: int | None = None
    skipped: bool = False


class LexResult(BaseModel):
    tokens: list[TokenPayload]
    comments: list[dict] = []
    preprocessor: dict = {}
    lex_errors: list[dict] = []


class ASTNodePayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    kind: str
    label: str
    children: list["ASTNodePayload"] = []
    line: int
    col: int


class ParseResult(BaseModel):
    ast: ASTNodePayload


class SymbolEntry(BaseModel):
    name: str
    type: ValueType
    kind: str
    scopeId: str
    line: int
    scope_level: int | None = None
    size: int | None = None
    offset: int | None = None
    storage: str | None = None
    builtin: bool | None = None


class SemanticResult(BaseModel):
    symbolTable: list[SymbolEntry]
    annotatedAst: ASTNodePayload
    warnings: list[str]


class TACInstruction(BaseModel):
    index: int
    op: str
    arg1: str | None = None
    arg2: str | None = None
    result: str | None = None
    sourceAstNodeId: str


class TACResult(BaseModel):
    instructions: list[TACInstruction]
    tempCount: int


class BasicBlock(BaseModel):
    id: str
    startIndex: int
    endIndex: int
    instructions: list[TACInstruction]


class DAGNode(BaseModel):
    id: str
    label: str
    children: list[str]
    representsInstructionIndices: list[int]


class PeepholeChange(BaseModel):
    originalIndices: list[int]
    replacement: list[TACInstruction]
    reason: str


class OptimizeResult(BaseModel):
    blocks: list[BasicBlock]
    cfg: dict | None = None
    dag: list[DAGNode]
    peepholeChanges: list[PeepholeChange]
    optimizationSteps: list[dict] = []
    optimizedInstructions: list[TACInstruction]


class PhaseResult(BaseModel):
    phase: PhaseName
    success: bool
    data: Any = None
    error: CompilerErrorPayload | None = None
    steps: list[StepTrace] = []


class FullPipelineResponse(BaseModel):
    lex: PhaseResult
    parse: PhaseResult
    semantic: PhaseResult
    tac: PhaseResult
    optimize: PhaseResult
    tokens: list[dict] = []
    comments: list[dict] = []
    preprocessor: dict = {}
    lex_errors: list[dict] = []
    ast: dict | None = None
    parse_errors: list[dict] = []
    symbol_tables: list[dict] = []
    types: dict = {}
    diagnostics: list[dict] = []
    functions: list[dict] = []
    data_section: list[dict] = []
    ast_stats: dict = {}
    filename: str | None = None
    size_bytes: int | None = None
    line_count: int | None = None
    source: str | None = None
