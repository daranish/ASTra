"use client";

import type { Source } from "@/types";
import { useState } from "react";

interface SourceChipProps {
  source: Source;
}

export default function SourceChip({ source }: SourceChipProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  const fileName = source.file_path?.split("/").pop() || "unknown";
  const lineRange =
    source.start_line && source.end_line
      ? `L${source.start_line}-${source.end_line}`
      : "";

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <div
        className="
          inline-flex items-center gap-1.5
          px-3 py-1.5 rounded-lg
          bg-deep-graphite border border-subtle-slate
          text-xs font-medium text-muted-gray
          hover:border-electric-blue/40 hover:text-electric-blue
          cursor-default
          transition-all duration-200
          group
        "
      >
        {/* File icon */}
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className="flex-shrink-0 text-muted-gray group-hover:text-electric-blue transition-colors"
        >
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
          <polyline points="14 2 14 8 20 8" />
        </svg>

        <span className="truncate max-w-[120px]">{fileName}</span>

        {lineRange && (
          <span className="text-muted-gray/60 text-[10px]">{lineRange}</span>
        )}
      </div>

      {/* Tooltip */}
      {showTooltip && source.snippet && (
        <div className="absolute bottom-full left-0 mb-2 z-50 w-80 animate-fade-in">
          <div className="bg-slate-panel border border-subtle-slate rounded-xl shadow-2xl shadow-black/40 overflow-hidden">
            {/* Tooltip header */}
            <div className="px-3 py-2 border-b border-subtle-slate flex items-center gap-2">
              <span className="text-[10px] font-mono text-muted-gray truncate flex-1">
                {source.file_path || ""}
              </span>
              {source.symbol_kind && (
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-electric-blue/10 text-electric-blue font-medium uppercase">
                  {source.symbol_kind}
                </span>
              )}
            </div>
            {/* Tooltip snippet */}
            <div className="px-3 py-2 max-h-32 overflow-y-auto">
              <pre className="text-[11px] font-mono text-muted-gray whitespace-pre-wrap leading-relaxed">
                {source.snippet}
              </pre>
            </div>
            {/* Score bar */}
            {source.score !== null && source.score !== undefined && (
              <div className="px-3 py-1.5 border-t border-subtle-slate flex items-center gap-2">
                <span className="text-[9px] text-muted-gray/60">Relevance</span>
                <div className="flex-1 h-1 bg-subtle-slate rounded-full overflow-hidden">
                  <div
                    className="h-full bg-electric-blue rounded-full"
                    style={{ width: `${Math.round(source.score * 100)}%` }}
                  />
                </div>
                <span className="text-[9px] text-muted-gray/60">
                  {Math.round(source.score * 100)}%
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
