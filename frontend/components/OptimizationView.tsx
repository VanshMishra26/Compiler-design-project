"use client";

import { Background, Controls, ReactFlow } from "@xyflow/react";
import type { OptimizeResult, TACResult } from "../lib/types";
import { dagToFlow } from "../lib/treeLayout";
import { usePipelineStore } from "../store/pipelineStore";
import { formatInstruction } from "./TACView";

export function OptimizationView({ data, original }: { data: OptimizeResult | null; original: TACResult | null }) {
  const { showOptimized, setShowOptimized } = usePipelineStore();
  if (!data || !original) return <div className="p-6 text-overline uppercase text-muted">Compile to view optimization output.</div>;
  const display = showOptimized ? data.optimizedInstructions : original.instructions;
  const { nodes, edges } = dagToFlow(data.dag);

  return (
    <div className="grid h-full grid-cols-[45%_55%] overflow-hidden bg-background">
      <div className="overflow-auto border-r-2 border-primary p-6">
        <label className="mb-4 flex items-center gap-3 text-sm font-bold uppercase tracking-[0.06em]">
          <input type="checkbox" checked={showOptimized} onChange={(event) => setShowOptimized(event.target.checked)} className="h-[18px] w-[18px] accent-primary" />
          Show optimized
        </label>
        <div className="mb-4 space-y-2">
          {data.blocks.map((block) => (
            <div key={block.id} className="border-2 border-border-medium bg-background px-3 py-2 text-caption uppercase hover:border-primary">
              <strong>{block.id}</strong> lines {block.startIndex}-{block.endIndex}
            </div>
          ))}
        </div>
        <div className="font-mono text-sm">
          {display.map((instruction) => (
            <div key={`${instruction.index}-${formatInstruction(instruction)}`} className="mb-2 border-2 border-border-subtle bg-background px-3 py-2 hover:border-primary hover:bg-surface">
              <span className="mr-3 text-faint">{instruction.index}</span>
              {formatInstruction(instruction)}
            </div>
          ))}
        </div>
        <div className="mt-4 space-y-2 text-xs">
          {data.peepholeChanges.map((change, index) => (
            <div key={index} className="border-l-4 border-secondary bg-surface p-3 text-sm italic">
              {change.reason}
            </div>
          ))}
        </div>
      </div>
      <ReactFlow
        nodes={nodes.map((node) => ({
          ...node,
          data: { label: node.data.subtitle ? `${node.data.label} (${node.data.subtitle})` : node.data.label },
          style: {
            border: "2px solid var(--vb-primary)",
            borderRadius: 0,
            boxShadow: "none",
            background: "var(--vb-background)",
            padding: 10,
            minWidth: 90,
            fontSize: 12,
            fontFamily: "Work Sans, -apple-system, Segoe UI, Helvetica, sans-serif",
            fontWeight: 700,
            textTransform: "uppercase"
          }
        }))}
        edges={edges}
        fitView
      >
        <Background color="var(--vb-border-subtle)" />
        <Controls />
      </ReactFlow>
    </div>
  );
}
