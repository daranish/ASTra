
from __future__ import annotations

from typing import Any

SYSTEM_PROMPT = """You are ASTra, an expert code analyst. You answer questions about a \
software repository using ONLY the code snippets provided as context.

Rules:
1. Ground every claim in the provided snippets. If a snippet doesn't contain \
the answer, say so explicitly rather than guessing.
2. Always cite your sources using the format [file_path:start_line-end_line] \
immediately after each claim. Multiple citations are allowed.
3. Prefer concrete code references (function names, class names, file paths) \
over vague language.
4. If the question is ambiguous, ask for clarification rather than inventing an answer.
5. Keep answers focused and well-structured. Use markdown for code blocks.

You must not use any knowledge that isn't in the provided snippets."""


def build_context_block(chunks: list[dict[str, Any]], max_chars: int = 60_000) -> str:

    lines: list[str] = []
    used = 0
    for i, c in enumerate(chunks, start=1):
        block = (
            f"[{i}] {c.get('file_path', '?')}:{c.get('start_line', '?')}-"
            f"{c.get('end_line', '?')} | {c.get('symbol_kind', '?')} "
            f"{c.get('symbol_name', '?')}\n"
            f"```{c.get('language', '')}\n{c.get('content', '').rstrip()}\n```\n"
        )
        if used + len(block) > max_chars and i > 1:
            lines.append(f"\n... ({len(chunks) - i + 1} more snippets omitted for brevity)")
            break
        lines.append(block)
        used += len(block)
    return "\n".join(lines)


def build_user_prompt(question: str, context_block: str) -> str:
    return (
        f"## Repository code context\n\n{context_block}\n\n## Question\n\n{question}\n\n## Answer\n"
    )


__all__ = ["SYSTEM_PROMPT", "build_context_block", "build_user_prompt"]
