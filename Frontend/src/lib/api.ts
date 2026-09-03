import type {
  HealthResponse,
  IngestResponse,
  IngestStatusResponse,
  Source,
  StreamEvent,
} from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ── Health ────────────────────────────────────────────────── */

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_URL}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

/* ── Ingest ────────────────────────────────────────────────── */

export async function ingestRepo(repoUrl: string): Promise<IngestResponse> {
  const res = await fetch(`${API_URL}/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url: repoUrl }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Ingest failed: ${res.status}`);
  }
  return res.json();
}

export async function pollIngestionStatus(
  ingestionId: string
): Promise<IngestStatusResponse> {
  const res = await fetch(`${API_URL}/ingest/${ingestionId}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Status check failed: ${res.status}`);
  }
  return res.json();
}

/* ── Stream Query ─────────────────────────────────────────── */

export async function streamQuery(
  repo: string,
  ingestionId: string,
  question: string,
  callbacks: {
    onSources: (sources: Source[]) => void;
    onChunk: (text: string) => void;
    onDone: () => void;
    onError: (message: string) => void;
  },
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API_URL}/query/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo, ingestion_id: ingestionId, question }),
    signal,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Query failed: ${res.status}`);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Parse SSE lines: each event is "data: {...}\n\n"
      const lines = buffer.split("\n\n");
      // Keep the last incomplete chunk in the buffer
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data: ")) continue;

        const jsonStr = trimmed.slice(6); // strip "data: "
        try {
          const event: StreamEvent = JSON.parse(jsonStr);

          switch (event.type) {
            case "sources":
              callbacks.onSources(event.data);
              break;
            case "chunk":
              callbacks.onChunk(event.data);
              break;
            case "done":
              callbacks.onDone();
              return;
            case "error":
              callbacks.onError(event.message);
              return;
          }
        } catch {
          // Skip malformed JSON
          console.warn("Skipping malformed SSE event:", jsonStr);
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
