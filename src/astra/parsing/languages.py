
from __future__ import annotations

from pathlib import Path

# Map file extension → language identifier accepted by tree-sitter-language-pack.
EXTENSION_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".java": "java",
    ".rs": "rust",
    ".rb": "ruby",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".cs": "c_sharp",
    ".php": "php",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".swift": "swift",
    ".scala": "scala",
    ".m": "objc",
    ".mm": "objc",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
}

# Languages where the pack's structure extraction is reliable and useful.
# Anything else falls through to sliding-window chunking.
EXTRACTED_LANGUAGES: frozenset[str] = frozenset(
    {
        "python",
        "javascript",
        "typescript",
        "go",
        "java",
        "rust",
        "ruby",
        "c",
        "cpp",
        "c_sharp",
        "php",
        "kotlin",
        "swift",
        "scala",
        "objc",
        "bash",
    }
)


_PACK_KIND_TO_OURS: dict[str, str] = {
    "Function": "function",
    "Method": "method",
    "Class": "class",
    "Struct": "class",
    "Interface": "class",
    "Enum": "class",
    "Module": "module",
    "Trait": "class",
    "Impl": "class",
    "Namespace": "module",
}


def detect_language(path: Path) -> str | None:
    return EXTENSION_LANGUAGE.get(path.suffix.lower())


def is_extractable(language: str) -> bool:
    return language in EXTRACTED_LANGUAGES


def pack_kind_to_ours(pack_kind_name: str) -> str | None:
    return _PACK_KIND_TO_OURS.get(pack_kind_name)
