"use client";

import { motion } from "framer-motion";
import type { LexResult, TokenType } from "../lib/types";

const colors: Record<TokenType, string> = {
  KEYWORD: "bg-primary text-tertiary border-primary",
  IDENT: "bg-background text-ink border-border-medium",
  NUMBER: "bg-background text-secondary border-secondary",
  FLOAT: "bg-background text-secondary border-secondary",
  BOOL: "bg-background text-secondary border-secondary",
  STRING: "bg-surface text-ink border-border-medium",
  CHAR: "bg-surface text-ink border-border-medium",
  PREPROCESSOR: "bg-raised text-ink border-primary",
  COMMENT: "bg-surface text-muted border-border-medium",
  OP: "bg-background text-ink border-primary",
  PUNCT: "bg-background text-muted border-border-medium",
  EOF: "bg-primary text-tertiary border-primary"
};

export function TokenStream({ data, currentStepIndex }: { data: LexResult | null; currentStepIndex: number }) {
  if (!data) return <EmptyState />;
  const visible = data.tokens.slice(0, Math.min(currentStepIndex + 1, data.tokens.length));
  return (
    <div className="h-full overflow-auto bg-background p-6">
      <div className="flex flex-wrap gap-2">
        {visible.map((token, index) => (
          <motion.div
            key={`${token.startOffset}-${token.value}-${index}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.18, ease: [0.2, 0, 0, 1] }}
            className={`border-2 px-3 py-2 text-sm shadow-none ${colors[token.type]}`}
          >
            <div className="font-mono text-sm">{token.value}</div>
            <div className="text-overline uppercase opacity-70">{token.type}</div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function EmptyState() {
  return <div className="p-6 text-overline uppercase text-muted">Compile to view tokens.</div>;
}
