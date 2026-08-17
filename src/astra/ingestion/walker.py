
from __future__ import annotations

from pathlib import Path

from astra.config import Settings
from astra.errors import IngestError
from astra.logging import get_logger

log = get_logger(__name__)

# Common directories to skip. The git clone already excludes .git; these are
# additional ignores that make sense for code analysis.
_SKIP_DIRS: frozenset[str] = frozenset(
    {
        "node_modules",
        ".next",
        "dist",
        "build",
        "out",
        "target",
        "vendor",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".tox",
        ".gradle",
        "Pods",
        ".idea",
        ".vscode",
        "coverage",
        ".nyc_output",
        "ephemeral",
    }
)

# File names to skip entirely.
_SKIP_FILES: frozenset[str] = frozenset(
    {
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "poetry.lock",
        "Cargo.lock",
        "Gemfile.lock",
        "composer.lock",
        "Pipfile.lock",
    }
)


def _read_gitignore(root: Path) -> list[str]:
    gi = root / ".gitignore"
    if not gi.is_file():
        return []
    return [
        line.strip()
        for line in gi.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def _gitignore_matches(rel: str, patterns: list[str]) -> bool:

    import fnmatch

    for pat in patterns:
        if pat.endswith("/"):
            if any(part == pat[:-1] for part in rel.split("/")):
                return True
            continue
        if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(Path(rel).name, pat):
            return True
        if "/" not in pat and any(part == pat for part in rel.split("/")):
            return True
    return False


def iter_source_files(root: Path, settings: Settings) -> list[Path]:
    if not root.exists():
        raise IngestError(f"Clone root does not exist: {root}")
    if not root.is_dir():
        raise IngestError(f"Clone root is not a directory: {root}")

    gitignore_patterns = _read_gitignore(root)
    out: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        # Directory skip
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.name in _SKIP_FILES:
            continue
        rel = path.relative_to(root).as_posix()
        if _gitignore_matches(rel, gitignore_patterns):
            continue
        # Size filter (cheap stat)
        try:
            if path.stat().st_size > settings.max_file_size_bytes:
                log.debug("skip_oversized", file=rel, size=path.stat().st_size)
                continue
        except OSError:
            continue
        out.append(path)

    out.sort()
    log.info("files_enumerated", count=len(out), root=str(root))
    return out


__all__ = ["iter_source_files"]
