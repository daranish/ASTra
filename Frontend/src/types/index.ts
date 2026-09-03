/* ── TypeScript Interfaces for ASTra Frontend ─────────────── */

// ── Repository ───────────────────────────────────────────────
export interface Repo {
  url: string;
  name: string;          // derived display name, e.g. "pallets/flask"
  ingestionId: string;
  status: RepoStatus;
  filesTotal?: number;
  filesDone?: number;
  chunksTotal?: number;
  chunksIndexed?: number;
  error?: string;
}

export type RepoStatus =
  | "queued"
  | "cloning"
  | "parsing"
  | "embedding"
  | "indexing"
  | "completed"
  | "failed";

// ── Chat Messages ────────────────────────────────────────────
export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  isStreaming?: boolean;
  timestamp: number;
}

// ── Source Citation ───────────────────────────────────────────
export interface Source {
  file_path: string | null;
  language: string | null;
  symbol_name: string | null;
  symbol_kind: string | null;
  parent: string | null;
  start_line: number | null;
  end_line: number | null;
  score: number | null;
  snippet: string | null;
}

// ── SSE Events from /query/stream ────────────────────────────
export interface SourcesEvent {
  type: "sources";
  data: Source[];
}

export interface ChunkEvent {
  type: "chunk";
  data: string;
}

export interface DoneEvent {
  type: "done";
}

export interface ErrorEvent {
  type: "error";
  message: string;
}

export type StreamEvent = SourcesEvent | ChunkEvent | DoneEvent | ErrorEvent;

// ── Ingest API ───────────────────────────────────────────────
export interface IngestResponse {
  ingestion_id: string;
  repo_url: string;
  status: string;
}

export interface IngestStatusResponse {
  ingestion_id: string;
  repo_url: string;
  status: string;
  started_at: number;
  finished_at: number | null;
  files_total: number;
  files_done: number;
  chunks_total: number;
  chunks_indexed: number;
  error: string | null;
}

// ── Health ────────────────────────────────────────────────────
export interface HealthResponse {
  status: string;
  qdrant: boolean;
  has_openrouter_key: boolean;
  details: Record<string, string>;
}
