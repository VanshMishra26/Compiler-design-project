"use client";

import type { FullPipelineResponse, PhaseName } from "../lib/types";

const phases: { key: PhaseName; label: string }[] = [
  { key: "lex", label: "Lexer" },
  { key: "parse", label: "Parser" },
  { key: "semantic", label: "Semantic" },
  { key: "tac", label: "TAC" },
  { key: "optimize", label: "Optimize" }
];

export function PhaseTabs({
  result,
  currentPhase,
  onChange
}: {
  result: FullPipelineResponse | null;
  currentPhase: PhaseName;
  onChange: (phase: PhaseName) => void;
}) {
  return (
    <div className="flex border-b border-ink/10 bg-white">
      {phases.map((phase) => {
        const disabled = Boolean(result && !result[phase.key].data);
        const active = currentPhase === phase.key;
        return (
          <button
            key={phase.key}
            disabled={disabled}
            onClick={() => onChange(phase.key)}
            className={`h-11 border-r border-ink/10 px-4 text-sm font-medium transition ${
              active ? "bg-ink text-white" : "text-ink/70 hover:bg-paper disabled:text-ink/25"
            }`}
          >
            {phase.label}
          </button>
        );
      })}
    </div>
  );
}
