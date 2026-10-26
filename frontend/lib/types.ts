export type PhaseName = "lex" | "parse" | "semantic" | "tac" | "optimize";
export type TokenType = "KEYWORD" | "IDENT" | "NUMBER" | "FLOAT" | "BOOL" | "STRING" | "CHAR" | "PREPROCESSOR" | "COMMENT" | "OP" | "PUNCT" | "EOF";
export type ValueType = string;

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
  lexeme?: string;
  line: number;
  col: number;
  column?: number;
  end_line?: number;
  end_column?: number;
  startOffset: number;
  endOffset: number;
  offset?: number;
  skipped?: boolean;
}

export interface LexResult {
  tokens: Token[];
  comments?: Token[];
  preprocessor?: PreprocessorInfo;
  lex_errors?: Diagnostic[];
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
  kind: string;
  scopeId: string;
  line: number;
  scope_level?: number;
  size?: number;
  offset?: number;
  storage?: string;
  builtin?: boolean;
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
  cfg?: CFG;
  dag: DAGNode[];
  peepholeChanges: PeepholeChange[];
  optimizationSteps?: OptimizationStep[];
  optimizedInstructions: TACInstruction[];
}

export interface Diagnostic {
  severity: "error" | "warning" | "info";
  code?: string;
  message: string;
  line: number;
  column: number;
}

export interface PreprocessorInfo {
  includes: Array<Record<string, unknown>>;
  defines: Array<Record<string, unknown>>;
  conditionals: Array<Record<string, unknown>>;
  diagnostics: Diagnostic[];
}

export interface CFG {
  nodes: Array<{ id: string; instructions: TACInstruction[] }>;
  edges: Array<{ from: string; to: string; label: string }>;
}

export interface OptimizationStep {
  pass: string;
  before: TACInstruction[];
  after: TACInstruction[];
  reason: string;
}

export interface FunctionPipeline {
  name: string;
  tac: TACInstruction[];
  basic_blocks: BasicBlock[];
  cfg: CFG;
  dag: DAGNode[];
  optimization_steps: OptimizationStep[];
  optimized_tac: TACInstruction[];
}

export interface FullPipelineResponse {
  lex: PhaseResult<LexResult>;
  parse: PhaseResult<ParseResult>;
  semantic: PhaseResult<SemanticResult>;
  tac: PhaseResult<TACResult>;
  optimize: PhaseResult<OptimizeResult>;
  tokens?: Token[];
  comments?: Token[];
  preprocessor?: PreprocessorInfo;
  lex_errors?: Diagnostic[];
  ast?: ASTNode | null;
  parse_errors?: Diagnostic[];
  symbol_tables?: Array<{ id: string; symbols: SymbolEntry[] }>;
  types?: Record<string, unknown>;
  diagnostics?: Diagnostic[];
  functions?: FunctionPipeline[];
  data_section?: Array<Record<string, unknown>>;
  ast_stats?: { node_count: number; depth: number };
  filename?: string;
  size_bytes?: number;
  line_count?: number;
  source?: string;
}
