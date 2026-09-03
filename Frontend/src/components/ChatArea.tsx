"use client";

import { useRef, useEffect } from "react";
import type { Message, Repo } from "@/types";
import MessageBubble from "./MessageBubble";
import SuggestionChips from "./SuggestionChips";
import ChatInput from "./ChatInput";

interface ChatAreaProps {
  messages: Message[];
  selectedRepo: Repo | null;
  isStreaming: boolean;
  onSendMessage: (question: string) => void;
  onToggleSidebar: () => void;
}

export default function ChatArea({
  messages,
  selectedRepo,
  isStreaming,
  onSendMessage,
  onToggleSidebar,
}: ChatAreaProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const showSuggestions = messages.length === 0 && selectedRepo;

  return (
    <div className="flex-1 flex flex-col h-screen bg-dark-slate overflow-hidden">
      {/* ── Top bar ─────────────────────────────────────── */}
      <header className="flex items-center gap-3 px-4 py-3 border-b border-subtle-slate bg-dark-slate/80 backdrop-blur-sm">
        {/* Mobile hamburger */}
        <button
          onClick={onToggleSidebar}
          className="lg:hidden p-2 -ml-1 rounded-lg hover:bg-slate-panel text-muted-gray hover:text-almost-white transition-colors"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>

        {selectedRepo ? (
          <div className="flex items-center gap-2.5">
            <div className="w-2 h-2 rounded-full bg-success" />
            <div>
              <p className="text-sm font-medium text-almost-white">
                {selectedRepo.name}
              </p>
              <p className="text-[10px] text-muted-gray">
                Ready · {selectedRepo.chunksTotal || 0} chunks indexed
              </p>
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-gray">
            Select a repository to start
          </p>
        )}
      </header>

      {/* ── Messages area ───────────────────────────────── */}
      <div className="flex-1 overflow-y-auto">
        {!selectedRepo ? (
          /* No repo selected */
          <div className="flex items-center justify-center h-full px-4">
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-slate-panel border border-subtle-slate flex items-center justify-center">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-muted-gray/50">
                  <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-almost-white mb-2">
                Welcome to ASTra
              </h3>
              <p className="text-sm text-muted-gray max-w-sm">
                Add a GitHub repository and start asking questions about the codebase. ASTra will analyze the code and provide cited answers.
              </p>
            </div>
          </div>
        ) : showSuggestions ? (
          /* Suggestion chips */
          <SuggestionChips
            onSelect={onSendMessage}
            repoName={selectedRepo.name}
          />
        ) : (
          /* Message list */
          <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* ── Input bar ───────────────────────────────────── */}
      <ChatInput
        onSend={onSendMessage}
        disabled={!selectedRepo || isStreaming}
        placeholder={
          !selectedRepo
            ? "Select a repository first…"
            : isStreaming
            ? "Waiting for response…"
            : `Ask about ${selectedRepo.name}…`
        }
      />
    </div>
  );
}
