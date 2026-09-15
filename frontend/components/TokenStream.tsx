"use client";

import { motion } from "framer-motion";
import type { LexResult } from "../lib/types";

const colors = {
  KEYWORD: "bg-steel/15 text-steel border-steel/30",
  IDENT: "bg-mint/20 text-ink border-mint/50",
  NUMBER: "bg-amber/25 text-ink border-amber/50",
  FLOAT: "bg-amber/25 text-ink border-amber/50",
  BOOL: "bg-coral/15 text-coral border-coral/35",
  OP: "bg-ink/10 text-ink border-ink/15",
  PUNCT: "bg-white text-ink/70 border-ink/15",
  EOF: "bg-ink text-white border-ink"
};

export function TokenStream({ data, currentStepIndex }: { data: LexResult | null; currentStepIndex: number }) {
  if (!data) return <EmptyState />;
  const visible = data.tokens.slice(0, Math.min(currentStepIndex + 1, data.tokens.length));
  return (
    <div className="h-full overflow-auto p-4">
      <div className="flex flex-wrap gap-2">
        {visible.map((token, index) => (
          <motion.div
            key={`${token.startOffset}-${token.value}-${index}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`rounded border px-3 py-2 text-sm shadow-sm ${colors[token.type]}`}
          >
            <div className="font-semibold">{token.value}</div>
            <div className="text-[11px] opacity-70">{token.type}</div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function EmptyState() {
  return <div className="p-4 text-sm text-ink/55">Compile to view tokens.</div>;
}
