import type { FullPipelineResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function compileFull(source: string): Promise<FullPipelineResponse> {
  const response = await fetch(`${API_BASE}/api/compile/full`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source })
  });

  if (!response.ok) {
    throw new Error(`Compile request failed: ${response.status}`);
  }

  return response.json();
}
