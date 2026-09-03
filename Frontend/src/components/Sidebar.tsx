"use client";

import { useState } from "react";
import type { Repo } from "@/types";
import AddRepoModal from "./AddRepoModal";

interface SidebarProps {
  repos: Repo[];
  selectedRepo: Repo | null;
  onSelectRepo: (repo: Repo) => void;
  onRepoAdded: (repo: Repo) => void;
  isOpen: boolean;
  onToggle: () => void;
}

/* ── Status indicator colors ──────────────────────────────── */
function statusDotClass(status: string): string {
  switch (status) {
    case "completed":
      return "bg-success";
    case "failed":
      return "bg-error";
    case "queued":
    case "cloning":
    case "parsing":
    case "embedding":
    case "indexing":
      return "bg-warning animate-pulse";
    default:
      return "bg-muted-gray";
  }
}

function statusLabel(status: string): string {
  switch (status) {
    case "completed":
      return "Ready";
    case "failed":
      return "Failed";
    case "queued":
      return "Queued";
    case "cloning":
      return "Cloning…";
    case "parsing":
      return "Parsing…";
    case "embedding":
      return "Embedding…";
    case "indexing":
      return "Indexing…";
    default:
      return status;
  }
}

export default function Sidebar({
  repos,
  selectedRepo,
  onSelectRepo,
  onRepoAdded,
  isOpen,
  onToggle,
}: SidebarProps) {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <>
      {/* ── Mobile overlay backdrop ──────────────────────── */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 backdrop-blur-sm lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* ── Sidebar panel ────────────────────────────────── */}
      <aside
        className={`
          fixed top-0 left-0 z-40 h-full w-72
          bg-deep-graphite border-r border-subtle-slate
          flex flex-col
          transition-transform duration-300 ease-in-out
          lg:relative lg:translate-x-0
          ${isOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        {/* ── Logo ───────────────────────────────────────── */}
        <div className="flex items-center gap-3 px-5 py-5 border-b border-subtle-slate">
          <div className="relative">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-electric-blue to-bright-blue flex items-center justify-center shadow-lg shadow-electric-blue/20">
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-white"
              >
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
            </div>
            <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-success rounded-full border-2 border-deep-graphite" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-almost-white tracking-tight">
              ASTra
            </h1>
            <p className="text-[10px] text-muted-gray tracking-widest uppercase">
              Code Analyzer
            </p>
          </div>

          {/* Mobile close button */}
          <button
            onClick={onToggle}
            className="ml-auto lg:hidden p-1.5 rounded-md hover:bg-slate-panel text-muted-gray hover:text-almost-white transition-colors"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* ── Repo list section ──────────────────────────── */}
        <div className="flex-1 overflow-y-auto px-3 py-4">
          <p className="text-[11px] font-semibold text-muted-gray uppercase tracking-wider px-2 mb-3">
            Repositories
          </p>

          {repos.length === 0 ? (
            <div className="px-2 py-8 text-center">
              <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-slate-panel border border-subtle-slate flex items-center justify-center">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-muted-gray">
                  <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
              </div>
              <p className="text-xs text-muted-gray mb-1">No repositories yet</p>
              <p className="text-[10px] text-muted-gray/60">Add a GitHub repo to get started</p>
            </div>
          ) : (
            <ul className="space-y-1">
              {repos.map((repo) => {
                const isSelected = selectedRepo?.ingestionId === repo.ingestionId;
                return (
                  <li key={repo.ingestionId}>
                    <button
                      onClick={() => onSelectRepo(repo)}
                      disabled={repo.status !== "completed"}
                      className={`
                        w-full text-left px-3 py-2.5 rounded-lg
                        transition-all duration-200 group
                        ${
                          isSelected
                            ? "bg-electric-blue/10 border border-electric-blue/30"
                            : "hover:bg-slate-panel border border-transparent"
                        }
                        ${repo.status !== "completed" ? "opacity-60 cursor-not-allowed" : "cursor-pointer"}
                      `}
                    >
                      <div className="flex items-center gap-2.5">
                        <span
                          className={`w-2 h-2 rounded-full flex-shrink-0 ${statusDotClass(repo.status)}`}
                        />
                        <div className="min-w-0 flex-1">
                          <p
                            className={`text-sm font-medium truncate ${
                              isSelected ? "text-electric-blue" : "text-almost-white"
                            }`}
                          >
                            {repo.name}
                          </p>
                          <p className="text-[10px] text-muted-gray mt-0.5">
                            {statusLabel(repo.status)}
                            {repo.status !== "completed" &&
                              repo.status !== "failed" &&
                              repo.filesTotal
                              ? ` · ${repo.filesDone || 0}/${repo.filesTotal} files`
                              : ""}
                          </p>
                        </div>
                      </div>

                      {/* Progress bar for active ingestions */}
                      {repo.status !== "completed" &&
                        repo.status !== "failed" &&
                        repo.filesTotal !== undefined &&
                        repo.filesTotal > 0 && (
                          <div className="mt-2 h-1 bg-subtle-slate rounded-full overflow-hidden">
                            <div
                              className="h-full bg-warning rounded-full transition-all duration-500"
                              style={{
                                width: `${Math.round(
                                  ((repo.filesDone || 0) / repo.filesTotal) * 100
                                )}%`,
                              }}
                            />
                          </div>
                        )}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        {/* ── Add repo button ────────────────────────────── */}
        <div className="p-3 border-t border-subtle-slate">
          <button
            onClick={() => setModalOpen(true)}
            className="
              w-full flex items-center justify-center gap-2
              px-4 py-2.5 rounded-lg
              bg-electric-blue/10 border border-electric-blue/20
              text-electric-blue text-sm font-medium
              hover:bg-electric-blue/20 hover:border-electric-blue/40
              active:scale-[0.98]
              transition-all duration-200
            "
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14" />
            </svg>
            Add Repository
          </button>
        </div>
      </aside>

      {/* ── Add Repo Modal ───────────────────────────────── */}
      <AddRepoModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onRepoAdded={(repo) => {
          onRepoAdded(repo);
          setModalOpen(false);
        }}
      />
    </>
  );
}
