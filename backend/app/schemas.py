from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


PhaseName = Literal["lex", "parse", "semantic", "tac", "optimize"]
TokenName = Literal["KEYWORD", "IDENT", "NUMBER", "FLOAT", "BOOL", "OP", "PUNCT", "EOF"]
ValueType = Literal["int", "float", "bool", "void"]


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
    line: int
    col: int
    startOffset: int
    endOffset: int


class LexResult(BaseModel):
    tokens: list[TokenPayload]


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
    kind: Literal["var", "func"]
    scopeId: str
    line: int


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
    dag: list[DAGNode]
    peepholeChanges: list[PeepholeChange]
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
