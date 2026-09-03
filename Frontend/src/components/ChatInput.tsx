"use client";

import { useState, useRef, useEffect } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
  placeholder?: string;
}

export default function ChatInput({ onSend, disabled, placeholder }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [value]);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-subtle-slate bg-dark-slate/80 backdrop-blur-sm px-4 py-3">
      <div className="max-w-4xl mx-auto">
        <div
          className={`
            flex items-end gap-2
            bg-slate-panel border rounded-2xl
            px-4 py-2.5
            transition-all duration-300
            ${
              disabled
                ? "border-subtle-slate opacity-60"
                : "border-subtle-slate focus-within:border-electric-blue/40 focus-within:shadow-[0_0_15px_rgba(76,141,255,0.08)]"
            }
          `}
        >
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder || "Ask about your codebase…"}
            disabled={disabled}
            rows={1}
            className="
              flex-1 bg-transparent resize-none
              text-sm text-almost-white
              placeholder:text-muted-gray/50
              focus:outline-none
              min-h-[24px] max-h-[160px]
              py-1
              disabled:cursor-not-allowed
            "
          />

          <button
            onClick={handleSubmit}
            disabled={!value.trim() || disabled}
            className="
              flex-shrink-0
              w-8 h-8 rounded-lg
              flex items-center justify-center
              transition-all duration-200
              disabled:opacity-30 disabled:cursor-not-allowed
              bg-electric-blue hover:bg-bright-blue
              active:scale-90
              text-white
            "
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>

        <p className="text-[10px] text-muted-gray/40 text-center mt-2">
          ASTra can make mistakes. Verify important code analysis.
        </p>
      </div>
    </div>
  );
}
