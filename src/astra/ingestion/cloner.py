
from __future__ import annotations

import asyncio
import re
import shutil
import tempfile
import uuid
from pathlib import Path

from astra.config import Settings
from astra.errors import CloneError
from astra.logging import get_logger

log = get_logger(__name__)

# Strict GitHub URL pattern. We reject anything that isn't a github.com repo.
_GH_URL = re.compile(r"^https?://github\.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(\.git)?/?$")


def normalize_repo_url(url: str) -> str:
    m = _GH_URL.match(url.strip())
    if not m:
        raise CloneError(f"Invalid GitHub URL: {url!r}. Expected https://github.com/<owner>/<repo>")
    return f"https://github.com/{m.group('owner')}/{m.group('repo')}"


def canonical_repo_key(url: str) -> str:
    return normalize_repo_url(url)


# def make_temp_clone_dir(prefix: str = "astra_") -> Path:
#     """Create a temporary directory for ephemeral clones (used by the API)."""
#     return Path(tempfile.mkdtemp(prefix=prefix))


async def clone_repo(url: str, settings: Settings) -> tuple[Path, str]:
    canonical = normalize_repo_url(url)
    #cache_root = Path(settings.repo_cache_dir).expanduser().resolve()  # noqa: ASYNC240
    #cache_root.mkdir(parents=True, exist_ok=True)
    #target = cache_root / canonical.removeprefix("https://github.com/").replace("/", "__")

    temp_root = Path(settings.repo_temp_dir).expanduser().resolve()  # noqa: ASYNC240
    temp_root.mkdir(parents=True, exist_ok=True)

    ingestion_id = uuid.uuid4().hex

    target = temp_root / canonical.removeprefix("https://github.com/").replace("/", "__") / ingestion_id

    # if (target / ".git").exists():
    #     log.info("clone_cache_hit", path=str(target))
    #     return target

    git = shutil.which("git")
    if git is None:
        raise CloneError("`git` executable not found on PATH")

    cmd = [
        git,
        "clone",
        "--depth=1",
        "--quiet",
        canonical,
        str(target),
    ]
    log.info("clone_start", url=canonical, ingestion_id=ingestion_id, target=str(target))

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            _, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=settings.ingest_timeout_sec
            )
        except TimeoutError as exc:
            proc.kill()
            raise CloneError(f"git clone timed out after {settings.ingest_timeout_sec}s") from exc
    except FileNotFoundError as exc:
        raise CloneError(f"git executable not runnable: {exc}") from exc

    if proc.returncode != 0:
        msg = stderr.decode("utf-8", errors="replace").strip() if stderr else "unknown"
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        raise CloneError(f"git clone failed (rc={proc.returncode}): {msg}")

    log.info("clone_done", target=str(target), ingestion_id=ingestion_id)
    return target, ingestion_id


__all__ = ["canonical_repo_key", "clone_repo", "make_temp_clone_dir", "normalize_repo_url"]
