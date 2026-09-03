"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import type { Repo, RepoStatus } from "@/types";
import { ingestRepo, pollIngestionStatus } from "@/lib/api";

interface AddRepoModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRepoAdded: (repo: Repo) => void;
}

/** Extract a short display name from a GitHub URL. */
function repoDisplayName(url: string): string {
  try {
    const parts = url.replace(/\.git$/, "").split("/");
    const repo = parts.pop() || "";
    const owner = parts.pop() || "";
    return owner ? `${owner}/${repo}` : repo;
  } catch {
    return url;
  }
}

export default function AddRepoModal({
  isOpen,
  onClose,
  onRepoAdded,
}: AddRepoModalProps) {
  const [url, setUrl] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ingesting, setIngesting] = useState<{
    id: string;
    status: string;
    filesTotal: number;
    filesDone: number;
  } | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen && !isSubmitting) onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isOpen, isSubmitting, onClose]);

  const handleSubmit = useCallback(async () => {
    const trimmed = url.trim();
    if (!trimmed) return;

    setError(null);
    setIsSubmitting(true);

    try {
      const res = await ingestRepo(trimmed);
      setIngesting({
        id: res.ingestion_id,
        status: res.status,
        filesTotal: 0,
        filesDone: 0,
      });

      // Start polling
      pollRef.current = setInterval(async () => {
        try {
          const status = await pollIngestionStatus(res.ingestion_id);
          setIngesting({
            id: res.ingestion_id,
            status: status.status,
            filesTotal: status.files_total,
            filesDone: status.files_done,
          });

          if (status.status === "completed") {
            if (pollRef.current) clearInterval(pollRef.current);
            const repo: Repo = {
              url: trimmed,
              name: repoDisplayName(trimmed),
              ingestionId: res.ingestion_id,
              status: "completed",
              filesTotal: status.files_total,
              filesDone: status.files_done,
              chunksTotal: status.chunks_total,
              chunksIndexed: status.chunks_indexed,
            };
            onRepoAdded(repo);
            setUrl("");
            setIngesting(null);
            setIsSubmitting(false);
          } else if (status.status === "failed") {
            if (pollRef.current) clearInterval(pollRef.current);
            setError(status.error || "Ingestion failed");
            setIngesting(null);
            setIsSubmitting(false);
          }
        } catch (err) {
          console.error("Poll error:", err);
        }
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setIsSubmitting(false);
    }
  }, [url, onRepoAdded]);

  const statusText = ingesting
    ? {
        queued: "Queued…",
        cloning: "Cloning repository…",
        parsing: "Parsing source files…",
        embedding: "Creating embeddings…",
        indexing: "Indexing vectors…",
      }[ingesting.status] || ingesting.status
    : "";

  const progress =
    ingesting && ingesting.filesTotal > 0
      ? Math.round((ingesting.filesDone / ingesting.filesTotal) * 100)
      : 0;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={!isSubmitting ? onClose : undefined}
      />

      {/* Modal panel */}
      <div className="relative w-full max-w-md animate-slide-up">
        <div className="bg-slate-panel/90 backdrop-blur-xl border border-subtle-slate rounded-2xl shadow-2xl shadow-black/40 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-6 pt-6 pb-2">
            <div>
              <h2 className="text-lg font-semibold text-almost-white">
                Add Repository
              </h2>
              <p className="text-xs text-muted-gray mt-0.5">
                Paste a GitHub URL to analyze
              </p>
            </div>
            {!isSubmitting && (
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg hover:bg-subtle-slate/60 text-muted-gray hover:text-almost-white transition-colors"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>

          {/* Body */}
          <div className="px-6 py-4 space-y-4">
            <div className="relative">
              <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-gray">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
                </svg>
              </div>
              <input
                ref={inputRef}
                type="url"
                value={url}
                onChange={(e) => {
                  setUrl(e.target.value);
                  setError(null);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !isSubmitting) handleSubmit();
                }}
                placeholder="https://github.com/owner/repo"
                disabled={isSubmitting}
                className="
                  w-full pl-10 pr-4 py-3 rounded-xl
                  bg-deep-graphite border border-subtle-slate
                  text-almost-white text-sm
                  placeholder:text-muted-gray/50
                  focus:outline-none focus:border-electric-blue/50 focus:ring-1 focus:ring-electric-blue/20
                  disabled:opacity-50
                  transition-all duration-200
                "
              />
            </div>

            {/* Error */}
            {error && (
              <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg bg-error/10 border border-error/20">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-error mt-0.5 flex-shrink-0">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="15" y1="9" x2="9" y2="15" />
                  <line x1="9" y1="9" x2="15" y2="15" />
                </svg>
                <p className="text-xs text-error">{error}</p>
              </div>
            )}

            {/* Progress */}
            {ingesting && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-gray">{statusText}</span>
                  {ingesting.filesTotal > 0 && (
                    <span className="text-muted-gray">
                      {ingesting.filesDone}/{ingesting.filesTotal} files
                    </span>
                  )}
                </div>
                <div className="h-1.5 bg-subtle-slate rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-electric-blue to-bright-blue rounded-full transition-all duration-700 ease-out"
                    style={{ width: `${Math.max(progress, 5)}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 pb-6 flex gap-3">
            {!isSubmitting && (
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2.5 rounded-xl border border-subtle-slate text-muted-gray text-sm font-medium hover:bg-subtle-slate/40 hover:text-almost-white transition-all"
              >
                Cancel
              </button>
            )}
            <button
              onClick={handleSubmit}
              disabled={!url.trim() || isSubmitting}
              className="
                flex-1 px-4 py-2.5 rounded-xl
                bg-electric-blue text-white text-sm font-semibold
                hover:bg-bright-blue
                disabled:opacity-40 disabled:cursor-not-allowed
                active:scale-[0.98]
                transition-all duration-200
                flex items-center justify-center gap-2
              "
            >
              {isSubmitting ? (
                <>
                  <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="60" strokeLinecap="round" className="opacity-30" />
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="15 45" strokeLinecap="round" />
                  </svg>
                  Ingesting…
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  Ingest Repository
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
