"use client";

import type { TACInstruction, TACResult } from "../lib/types";

export function TACView({
  data,
  selectedAstNodeId,
  onSelectAst
}: {
  data: TACResult | null;
  selectedAstNodeId: string | null;
  onSelectAst: (id: string) => void;
}) {
  if (!data) return <div className="p-6 text-overline uppercase text-muted">Compile to view TAC.</div>;
  return (
    <div className="h-full overflow-auto bg-background p-6 font-mono text-sm">
      {data.instructions.map((instruction) => (
        <button
          key={instruction.index}
          onClick={() => onSelectAst(instruction.sourceAstNodeId)}
          className={`mb-2 flex w-full border-2 px-3 py-2 text-left ${
            selectedAstNodeId === instruction.sourceAstNodeId
              ? "border-secondary bg-[var(--vb-error-surface)]"
              : "border-border-subtle bg-background hover:border-primary hover:bg-surface"
          }`}
        >
          <span className="mr-4 w-8 text-faint">{instruction.index}</span>
          <span>{formatInstruction(instruction)}</span>
        </button>
      ))}
    </div>
  );
}

export function formatInstruction(instruction: TACInstruction): string {
  if (instruction.op === "label") return `${instruction.result}:`;
  if (instruction.op === "goto") return `goto ${instruction.result}`;
  if (instruction.op === "ifFalse") return `ifFalse ${instruction.arg1} goto ${instruction.result}`;
  if (instruction.op === "=") return `${instruction.result} = ${instruction.arg1}`;
  if (instruction.op === "param") return `param ${instruction.arg1}`;
  if (instruction.op === "call") return `${instruction.result} = call ${instruction.arg1}, ${instruction.arg2}`;
  if (instruction.op === "return") return `return ${instruction.arg1 ?? ""}`.trim();
  return `${instruction.result} = ${instruction.arg1} ${instruction.op} ${instruction.arg2}`;
}
