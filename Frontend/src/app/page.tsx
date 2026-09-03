"use client";

import { useState, useCallback, useRef } from "react";
import type { Message, Repo, Source } from "@/types";
import { streamQuery } from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import ChatArea from "@/components/ChatArea";

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export default function Home() {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<Repo | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Keep a ref so we can abort in-flight streams
  const abortRef = useRef<AbortController | null>(null);

  // Track messages per repo for session persistence
  const messagesByRepo = useRef<Map<string, Message[]>>(new Map());

  const handleSelectRepo = useCallback(
    (repo: Repo) => {
      // Save current messages for previous repo
      if (selectedRepo) {
        messagesByRepo.current.set(selectedRepo.ingestionId, messages);
      }
      // Restore messages for selected repo
      const savedMessages =
        messagesByRepo.current.get(repo.ingestionId) || [];
      setMessages(savedMessages);
      setSelectedRepo(repo);
      setSidebarOpen(false); // Close sidebar on mobile
    },
    [selectedRepo, messages]
  );

  const handleRepoAdded = useCallback((repo: Repo) => {
    setRepos((prev) => {
      // Avoid duplicates
      if (prev.some((r) => r.ingestionId === repo.ingestionId)) return prev;
      return [...prev, repo];
    });
    // Auto-select if first repo
    setSelectedRepo((current) => {
      if (!current) {
        setMessages([]);
        return repo;
      }
      return current;
    });
  }, []);

  const handleSendMessage = useCallback(
    async (question: string) => {
      if (!selectedRepo || isStreaming) return;

      // Abort any previous stream
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      const userMsg: Message = {
        id: generateId(),
        role: "user",
        content: question,
        timestamp: Date.now(),
      };

      const assistantId = generateId();
      const assistantMsg: Message = {
        id: assistantId,
        role: "assistant",
        content: "",
        sources: [],
        isStreaming: true,
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);

      try {
        await streamQuery(
          selectedRepo.url,
          selectedRepo.ingestionId,
          question,
          {
            onSources: (sources: Source[]) => {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, sources } : m
                )
              );
            },
            onChunk: (text: string) => {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? { ...m, content: m.content + text }
                    : m
                )
              );
            },
            onDone: () => {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? { ...m, isStreaming: false }
                    : m
                )
              );
              setIsStreaming(false);
            },
            onError: (errorMsg: string) => {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? {
                        ...m,
                        content:
                          m.content ||
                          `⚠️ Error: ${errorMsg}`,
                        isStreaming: false,
                      }
                    : m
                )
              );
              setIsStreaming(false);
            },
          },
          controller.signal
        );
      } catch (err) {
        if ((err as Error).name === "AbortError") return;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content:
                    m.content ||
                    `⚠️ Failed to get response: ${
                      (err as Error).message
                    }`,
                  isStreaming: false,
                }
              : m
          )
        );
        setIsStreaming(false);
      }
    },
    [selectedRepo, isStreaming]
  );

  return (
    <div className="flex h-screen overflow-hidden bg-deep-graphite">
      <Sidebar
        repos={repos}
        selectedRepo={selectedRepo}
        onSelectRepo={handleSelectRepo}
        onRepoAdded={handleRepoAdded}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />
      <ChatArea
        messages={messages}
        selectedRepo={selectedRepo}
        isStreaming={isStreaming}
        onSendMessage={handleSendMessage}
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
      />
    </div>
  );
}
