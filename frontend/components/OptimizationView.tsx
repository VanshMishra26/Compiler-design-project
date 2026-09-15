"use client";

import { Background, Controls, ReactFlow } from "@xyflow/react";
import type { OptimizeResult, TACResult } from "../lib/types";
import { dagToFlow } from "../lib/treeLayout";
import { usePipelineStore } from "../store/pipelineStore";
import { formatInstruction } from "./TACView";

export function OptimizationView({ data, original }: { data: OptimizeResult | null; original: TACResult | null }) {
  const { showOptimized, setShowOptimized } = usePipelineStore();
  if (!data || !original) return <div className="p-4 text-sm text-ink/55">Compile to view optimization output.</div>;
  const display = showOptimized ? data.optimizedInstructions : original.instructions;
  const { nodes, edges } = dagToFlow(data.dag);

  return (
    <div className="grid h-full grid-cols-[45%_55%] overflow-hidden">
      <div className="overflow-auto border-r border-ink/10 p-4">
        <label className="mb-3 flex items-center gap-2 text-sm font-medium">
          <input type="checkbox" checked={showOptimized} onChange={(event) => setShowOptimized(event.target.checked)} className="accent-coral" />
          Show optimized
        </label>
        <div className="mb-4 space-y-2">
          {data.blocks.map((block) => (
            <div key={block.id} className="rounded border border-ink/10 bg-white px-3 py-2 text-xs">
              <strong>{block.id}</strong> lines {block.startIndex}-{block.endIndex}
            </div>
          ))}
        </div>
        <div className="font-mono text-sm">
          {display.map((instruction) => (
            <div key={`${instruction.index}-${formatInstruction(instruction)}`} className="mb-1 rounded bg-white px-3 py-2">
              <span className="mr-3 text-ink/40">{instruction.index}</span>
              {formatInstruction(instruction)}
            </div>
          ))}
        </div>
        <div className="mt-4 space-y-2 text-xs">
          {data.peepholeChanges.map((change, index) => (
            <div key={index} className="rounded border border-amber/40 bg-amber/15 p-2">
              {change.reason}
            </div>
          ))}
        </div>
      </div>
      <ReactFlow
        nodes={nodes.map((node) => ({
          ...node,
          data: { label: node.data.subtitle ? `${node.data.label} (${node.data.subtitle})` : node.data.label },
          style: { border: "1px solid rgba(23,32,38,0.18)", background: "#fff", padding: 10, minWidth: 90, fontSize: 12 }
        }))}
        edges={edges}
        fitView
      >
        <Background color="#d7dbd1" />
        <Controls />
      </ReactFlow>
    </div>
  );
}
