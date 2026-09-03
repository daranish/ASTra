
from __future__ import annotations

from pathlib import Path

import pytest

from astra.ingestion.walker import iter_source_files


def test_walker_skips_lock_files(tmp_path: Path, settings):
    (tmp_path / "main.py").write_text("x = 1")
    (tmp_path / "package-lock.json").write_text("{}")
    (tmp_path / "yarn.lock").write_text("")
    (tmp_path / "poetry.lock").write_text("")
    files = iter_source_files(tmp_path, settings)
    names = {f.name for f in files}
    assert "main.py" in names
    assert "package-lock.json" not in names
    assert "yarn.lock" not in names
    assert "poetry.lock" not in names


def test_walker_skips_node_modules(tmp_path: Path, settings):
    (tmp_path / "main.py").write_text("x = 1")
    nm = tmp_path / "node_modules" / "lib"
    nm.mkdir(parents=True)
    (nm / "index.js").write_text("var x;")
    files = iter_source_files(tmp_path, settings)
    names = {f.name for f in files}
    assert "main.py" in names
    assert "index.js" not in names


def test_walker_respects_gitignore(tmp_path: Path, settings):
    (tmp_path / "main.py").write_text("x = 1")
    secret = tmp_path / "secret.py"
    secret.write_text("TOKEN = 'x'")
    (tmp_path / ".gitignore").write_text("secret.py\n")
    files = iter_source_files(tmp_path, settings)
    names = {f.name for f in files}
    assert "main.py" in names
    assert "secret.py" not in names


def test_walker_skips_oversized(tmp_path: Path, settings):
    settings.max_file_size_bytes = 100
    (tmp_path / "small.py").write_text("x = 1")
    (tmp_path / "big.py").write_text("x = 1\n" * 200)
    files = iter_source_files(tmp_path, settings)
    names = {f.name for f in files}
    assert "small.py" in names
    assert "big.py" not in names


def test_walker_raises_on_missing_root(settings):
    from astra.errors import IngestError

    with pytest.raises(IngestError):
        iter_source_files(Path("/nonexistent/path/abc"), settings)
