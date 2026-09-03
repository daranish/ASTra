"use client";

interface SuggestionChipsProps {
  onSelect: (question: string) => void;
  repoName?: string;
}

const SUGGESTIONS = [
  {
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
        <line x1="3" y1="9" x2="21" y2="9" />
        <line x1="9" y1="21" x2="9" y2="9" />
      </svg>
    ),
    text: "What is the project structure and architecture?",
    label: "Project Structure",
  },
  {
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    ),
    text: "How does authentication work?",
    label: "Authentication",
  },
  {
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
    ),
    text: "How is error handling implemented?",
    label: "Error Handling",
  },
  {
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="16 18 22 12 16 6" />
        <polyline points="8 6 2 12 8 18" />
      </svg>
    ),
    text: "Explain the main entry point of the application",
    label: "Entry Point",
  },
];

export default function SuggestionChips({ onSelect, repoName }: SuggestionChipsProps) {
  return (
    <div className="flex flex-col items-center justify-center flex-1 px-4 py-12">
      {/* Welcome graphic */}
      <div className="mb-8 text-center">
        <div className="w-16 h-16 mx-auto mb-5 rounded-2xl bg-gradient-to-br from-electric-blue/20 to-bright-blue/10 border border-electric-blue/20 flex items-center justify-center">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-electric-blue">
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-almost-white mb-2">
          Ask about your codebase
        </h2>
        <p className="text-sm text-muted-gray max-w-sm">
          {repoName
            ? `Ask anything about ${repoName}. ASTra will find the answer in the source code.`
            : "Select a repository and ask questions about its code, architecture, and implementation."}
        </p>
      </div>

      {/* Suggestion grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl">
        {SUGGESTIONS.map((suggestion, idx) => (
          <button
            key={idx}
            onClick={() => onSelect(suggestion.text)}
            className="
              group text-left
              px-4 py-3.5 rounded-xl
              bg-slate-panel/60 border border-subtle-slate
              hover:border-electric-blue/30 hover:bg-electric-blue/5
              active:scale-[0.98]
              transition-all duration-200
            "
          >
            <div className="flex items-start gap-3">
              <div className="mt-0.5 text-muted-gray group-hover:text-electric-blue transition-colors">
                {suggestion.icon}
              </div>
              <div>
                <p className="text-xs font-semibold text-almost-white group-hover:text-electric-blue transition-colors">
                  {suggestion.label}
                </p>
                <p className="text-xs text-muted-gray mt-0.5 leading-relaxed">
                  {suggestion.text}
                </p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
