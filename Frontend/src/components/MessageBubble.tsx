"use client";

import React, { useCallback, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import type { Message } from "@/types";
import SourceChip from "./SourceChip";

interface MessageBubbleProps {
  message: Message;
}

/* ── Custom syntax highlighter theme overrides ────────────── */
const codeTheme = {
  ...oneDark,
  'pre[class*="language-"]': {
    ...oneDark['pre[class*="language-"]'],
    background: "#0B0F14",
    margin: 0,
    borderRadius: 0,
    padding: "1em",
    fontSize: "0.82rem",
    lineHeight: "1.6",
  },
  'code[class*="language-"]': {
    ...oneDark['code[class*="language-"]'],
    background: "transparent",
    fontFamily: "'JetBrains Mono', ui-monospace, monospace",
    fontSize: "0.82rem",
  },
};

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex animate-fade-in ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      <div
        className={`
          max-w-[80%] lg:max-w-[70%]
          ${
            isUser
              ? "bg-electric-blue text-white rounded-2xl rounded-br-md px-4 py-3"
              : "space-y-3"
          }
        `}
      >
        {isUser ? (
          /* ── User message ───────────────────────────────── */
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {message.content}
          </p>
        ) : (
          /* ── Assistant message ───────────────────────────── */
          <>
            {/* AI label */}
            <div className="flex items-center gap-2 mb-1">
              <div className="w-6 h-6 rounded-md bg-gradient-to-br from-electric-blue to-bright-blue flex items-center justify-center">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
                  <path d="M12 2L2 7l10 5 10-5-10-5z" />
                  <path d="M2 17l10 5 10-5" />
                </svg>
              </div>
              <span className="text-xs font-semibold text-muted-gray uppercase tracking-wider">
                ASTra
              </span>
              {message.isStreaming && (
                <div className="flex gap-1 ml-1">
                  <span className="w-1 h-1 rounded-full bg-electric-blue animate-pulse-dot" style={{ animationDelay: "0s" }} />
                  <span className="w-1 h-1 rounded-full bg-electric-blue animate-pulse-dot" style={{ animationDelay: "0.2s" }} />
                  <span className="w-1 h-1 rounded-full bg-electric-blue animate-pulse-dot" style={{ animationDelay: "0.4s" }} />
                </div>
              )}
            </div>

            {/* Markdown content */}
            <div
              className={`
                bg-slate-panel border border-subtle-slate rounded-2xl rounded-tl-md
                px-5 py-4
                ${message.isStreaming ? "streaming-cursor" : ""}
              `}
            >
              <div className="markdown-body text-sm text-almost-white">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code({ className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || "");
                      const codeString = String(children).replace(/\n$/, "");

                      if (match) {
                        return (
                          <CodeBlock language={match[1]} code={codeString} />
                        );
                      }

                      return (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    },
                    pre({ children }) {
                      return <>{children}</>;
                    },
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            </div>

            {/* Sources */}
            {message.sources && message.sources.length > 0 && !message.isStreaming && (
              <div className="animate-fade-in">
                <p className="text-[11px] font-semibold text-muted-gray uppercase tracking-wider mb-2 ml-1">
                  Sources
                </p>
                <div className="flex flex-wrap gap-2">
                  {message.sources.map((source, idx) => (
                    <SourceChip key={idx} source={source} />
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

/* ── Code block with language label + copy button ─────────── */
function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  }, [code]);

  return (
    <div className="code-block-wrapper">
      <div className="code-block-header">
        <span>{language}</span>
        <button onClick={handleCopy} className="copy-button">
          {copied ? (
            <span className="flex items-center gap-1 text-success">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              Copied
            </span>
          ) : (
            <span className="flex items-center gap-1">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
              </svg>
              Copy
            </span>
          )}
        </button>
      </div>
      <SyntaxHighlighter
        style={codeTheme}
        language={language}
        PreTag="pre"
        customStyle={{
          margin: 0,
          borderRadius: "0 0 8px 8px",
          border: "1px solid #26313D",
          borderTop: "none",
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}
