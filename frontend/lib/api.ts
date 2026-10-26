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

export async function compileUpload(file: File): Promise<FullPipelineResponse> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE}/api/compile/upload`, {
    method: "POST",
    body: form
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail ?? `Upload request failed: ${response.status}`);
  }

  return response.json();
}
