"use client";

import { AlertTriangle } from "lucide-react";
import type { FullPipelineResponse } from "../lib/types";

export function ErrorBanner({ result }: { result: FullPipelineResponse | null }) {
  const failed = result ? (Object.values(result).find((phase) => phase.error) ?? null) : null;
  if (!failed?.error) return null;

  return (
    <div className="flex items-center gap-3 border-b border-coral/30 bg-coral/10 px-4 py-3 text-sm text-ink">
      <AlertTriangle className="h-5 w-5 shrink-0 text-coral" aria-hidden />
      <strong className="font-semibold">{failed.error.phase}</strong>
      <span>{failed.error.message}</span>
      <span className="ml-auto text-xs text-ink/65">
        line {failed.error.line}, col {failed.error.column}
      </span>
    </div>
  );
}
