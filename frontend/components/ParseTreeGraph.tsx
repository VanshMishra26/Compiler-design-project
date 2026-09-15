"use client";

import { Background, Controls, ReactFlow } from "@xyflow/react";
import type { ASTNode, StepTrace } from "../lib/types";
import { astToFlow } from "../lib/treeLayout";

export function ParseTreeGraph({
  ast,
  steps,
  currentStepIndex,
  selectedAstNodeId,
  onSelect
}: {
  ast: ASTNode | null;
  steps: StepTrace[];
  currentStepIndex: number;
  selectedAstNodeId: string | null;
  onSelect: (id: string) => void;
}) {
  if (!ast) return <div className="p-4 text-sm text-ink/55">Compile to view the parse tree.</div>;

  const visibleIds = new Set<string>();
  steps.slice(0, currentStepIndex + 1).forEach((step) => {
    const snapshot = step.snapshot as { producedNodeId?: string | null };
    if (snapshot?.producedNodeId) visibleIds.add(snapshot.producedNodeId);
  });
  if (visibleIds.size === 0) collectIds(ast, visibleIds);

  const { nodes, edges } = astToFlow(ast, visibleIds);
  const styledNodes = nodes.map((node) => ({
    ...node,
    data: { label: `${node.data.subtitle}: ${node.data.label}` },
    style: {
      border: node.id === selectedAstNodeId ? "2px solid #e8755f" : "1px solid rgba(23,32,38,0.18)",
      padding: 10,
      background: "#fff",
      color: "#172026",
      minWidth: 130,
      fontSize: 12
    }
  }));

  return (
    <ReactFlow nodes={styledNodes} edges={edges} fitView onNodeClick={(_, node) => onSelect(node.id)}>
      <Background color="#d7dbd1" />
      <Controls />
    </ReactFlow>
  );
}

function collectIds(node: ASTNode, ids: Set<string>) {
  ids.add(node.id);
  node.children.forEach((child) => collectIds(child, ids));
}
