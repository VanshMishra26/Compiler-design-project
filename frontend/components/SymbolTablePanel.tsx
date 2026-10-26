"use client";

import type { SemanticResult } from "../lib/types";

export function SymbolTablePanel({ data }: { data: SemanticResult | null }) {
  if (!data) return <div className="p-6 text-overline uppercase text-muted">Compile to view semantic data.</div>;
  return (
    <div className="h-full overflow-auto bg-background p-6">
      <table className="w-full border-collapse border-2 border-primary text-left text-sm">
        <thead className="bg-primary text-tertiary">
          <tr>
            <th className="px-3 py-2 text-overline uppercase">Name</th>
            <th className="px-3 py-2 text-overline uppercase">Type</th>
            <th className="px-3 py-2 text-overline uppercase">Kind</th>
            <th className="px-3 py-2 text-overline uppercase">Scope</th>
            <th className="px-3 py-2 text-overline uppercase">Line</th>
          </tr>
        </thead>
        <tbody>
          {data.symbolTable.map((entry, index) => (
            <tr key={`${entry.scopeId}-${entry.name}-${index}`} className="border-b border-border-subtle bg-background hover:bg-surface">
              <td className="px-3 py-3 font-bold">{entry.name}</td>
              <td className="px-3 py-3 font-mono text-sm">{entry.type}</td>
              <td className="px-3 py-3 uppercase tracking-[0.04em]">{entry.kind}</td>
              <td className="px-3 py-3 text-muted">{entry.scopeId}</td>
              <td className="px-3 py-3">{entry.line}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
