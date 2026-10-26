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
    <div className="flex bg-background">
      {phases.map((phase) => {
        const disabled = Boolean(result && !result[phase.key].data);
        const active = currentPhase === phase.key;
        return (
          <button
            key={phase.key}
            disabled={disabled}
            onClick={() => onChange(phase.key)}
            className={`h-12 border-r-2 border-primary px-5 text-overline uppercase transition ${
              active
                ? "border-b-[3px] border-b-secondary bg-primary text-tertiary"
                : "bg-background text-muted hover:bg-primary hover:text-tertiary disabled:text-faint disabled:hover:bg-background disabled:hover:text-faint"
            }`}
          >
            {phase.label}
          </button>
        );
      })}
    </div>
  );
}
