export type PhaseName = "lex" | "parse" | "semantic" | "tac" | "optimize";
export type TokenType = "KEYWORD" | "IDENT" | "NUMBER" | "FLOAT" | "BOOL" | "OP" | "PUNCT" | "EOF";
export type ValueType = "int" | "float" | "bool" | "void";

export interface CompilerErrorPayload {
  message: string;
  line: number;
  column: number;
  phase: string;
}

export interface StepTrace {
  index: number;
  description: string;
  highlightRange: [number, number] | null;
  snapshot: unknown;
}

export interface PhaseResult<T> {
  phase: PhaseName;
  success: boolean;
  data: T | null;
  error: CompilerErrorPayload | null;
  steps: StepTrace[];
}

export interface Token {
  type: TokenType;
  value: string;
  line: number;
  col: number;
  startOffset: number;
  endOffset: number;
}

export interface LexResult {
  tokens: Token[];
}

export interface ASTNode {
  id: string;
  kind: string;
  label: string;
  children: ASTNode[];
  line: number;
  col: number;
  inferredType?: ValueType;
  [key: string]: unknown;
}

export interface ParseResult {
  ast: ASTNode;
}

export interface SymbolEntry {
  name: string;
  type: ValueType;
  kind: "var" | "func";
  scopeId: string;
  line: number;
}

export interface SemanticResult {
  symbolTable: SymbolEntry[];
  annotatedAst: ASTNode;
  warnings: string[];
}

export interface TACInstruction {
  index: number;
  op: string;
  arg1: string | null;
  arg2: string | null;
  result: string | null;
  sourceAstNodeId: string;
}

export interface TACResult {
  instructions: TACInstruction[];
  tempCount: number;
}

export interface BasicBlock {
  id: string;
  startIndex: number;
  endIndex: number;
  instructions: TACInstruction[];
}

export interface DAGNode {
  id: string;
  label: string;
  children: string[];
  representsInstructionIndices: number[];
}

export interface PeepholeChange {
  originalIndices: number[];
  replacement: TACInstruction[];
  reason: string;
}

export interface OptimizeResult {
  blocks: BasicBlock[];
  dag: DAGNode[];
  peepholeChanges: PeepholeChange[];
  optimizedInstructions: TACInstruction[];
}

export interface FullPipelineResponse {
  lex: PhaseResult<LexResult>;
  parse: PhaseResult<ParseResult>;
  semantic: PhaseResult<SemanticResult>;
  tac: PhaseResult<TACResult>;
  optimize: PhaseResult<OptimizeResult>;
}
