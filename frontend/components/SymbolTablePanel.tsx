"use client";

import type { SemanticResult } from "../lib/types";

export function SymbolTablePanel({ data }: { data: SemanticResult | null }) {
  if (!data) return <div className="p-4 text-sm text-ink/55">Compile to view semantic data.</div>;
  return (
    <div className="h-full overflow-auto p-4">
      <table className="w-full border-collapse text-left text-sm">
        <thead className="bg-ink text-white">
          <tr>
            <th className="px-3 py-2">Name</th>
            <th className="px-3 py-2">Type</th>
            <th className="px-3 py-2">Kind</th>
            <th className="px-3 py-2">Scope</th>
            <th className="px-3 py-2">Line</th>
          </tr>
        </thead>
        <tbody>
          {data.symbolTable.map((entry, index) => (
            <tr key={`${entry.scopeId}-${entry.name}-${index}`} className="border-b border-ink/10 bg-white">
              <td className="px-3 py-2 font-medium">{entry.name}</td>
              <td className="px-3 py-2">{entry.type}</td>
              <td className="px-3 py-2">{entry.kind}</td>
              <td className="px-3 py-2 text-ink/65">{entry.scopeId}</td>
              <td className="px-3 py-2">{entry.line}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
