import type { ASTNode, DAGNode } from "./types";

type FlowNode = { id: string; position: { x: number; y: number }; data: { label: string; subtitle?: string }; type?: string };
type FlowEdge = { id: string; source: string; target: string };

export function astToFlow(root: ASTNode, visibleIds?: Set<string>): { nodes: FlowNode[]; edges: FlowEdge[] } {
  const nodes: FlowNode[] = [];
  const edges: FlowEdge[] = [];
  let cursor = 0;

  function walk(node: ASTNode, depth: number): number {
    const childXs = node.children.map((child) => walk(child, depth + 1));
    const x = childXs.length ? (Math.min(...childXs) + Math.max(...childXs)) / 2 : cursor++ * 190;
    if (!visibleIds || visibleIds.has(node.id)) {
      nodes.push({
        id: node.id,
        position: { x, y: depth * 105 },
        data: { label: node.label, subtitle: node.kind }
      });
    }
    for (const child of node.children) {
      if (!visibleIds || (visibleIds.has(node.id) && visibleIds.has(child.id))) {
        edges.push({ id: `${node.id}-${child.id}`, source: node.id, target: child.id });
      }
    }
    return x;
  }

  walk(root, 0);
  return { nodes, edges };
}

export function dagToFlow(dag: DAGNode[]): { nodes: FlowNode[]; edges: FlowEdge[] } {
  const nodes = dag.map((node, index) => ({
    id: node.id,
    position: { x: (index % 5) * 170, y: Math.floor(index / 5) * 105 },
    data: { label: node.label, subtitle: node.representsInstructionIndices.join(", ") || "leaf" }
  }));
  const edges = dag.flatMap((node) => node.children.map((child) => ({ id: `${child}-${node.id}`, source: child, target: node.id })));
  return { nodes, edges };
}
