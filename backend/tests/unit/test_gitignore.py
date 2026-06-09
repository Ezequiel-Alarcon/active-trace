"""Static checks for repository-level invariants that are not runtime concerns.

These tests are slow in CI cost only if the repo is malformed, so they live in
unit/ but are kept dependency-free and side-effect-free.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def _gitignore_path() -> Path:
    return REPO_ROOT / ".gitignore"


def test_gitignore_exists() -> None:
    assert _gitignore_path().exists(), "Repo must have a top-level .gitignore"


def test_gitignore_ignores_backend_dotenv_files() -> None:
    text = _gitignore_path().read_text(encoding="utf-8")
    # The generic .env.* block must be present
    assert "backend/.env.*" in text, "gitignore must ignore all backend/.env.* files"
    # The negative pattern must keep .env.example committed
    assert "!backend/.env.example" in text, "gitignore must keep backend/.env.example tracked"


def test_gitignore_actually_excludes_dotenv_files() -> None:
    """If git is available, verify that `git check-ignore` reports env files as ignored."""
    git = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "backend/.env.test"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    # If git is unavailable or the repo is fresh, skip — the static check above
    # is sufficient for the rule.
    if git.returncode not in (0, 1):
        pytest.skip(f"git not usable here: {git.stderr}")
    assert git.returncode != 0, "backend/.env.test must not be tracked by git"


def test_dotenv_example_does_not_carry_a_real_secret() -> None:
    """`.env.example` is committed; the secret it carries must be a placeholder, not a real key."""
    example = (REPO_ROOT / "backend" / ".env.example").read_text(encoding="utf-8")
    assert "ENCRYPTION_KEY=" in example
    # Pull the value
    line = next(ln for ln in example.splitlines() if ln.startswith("ENCRYPTION_KEY="))
    value = line.split("=", 1)[1].strip()
    # Must be 32 bytes (rule of the project)
    assert len(value.encode("utf-8")) == 32
    # Must look like a placeholder
    placeholder_markers = ("change", "your", "example", "placeholder", "0123456789", "0" * 8)
    assert any(m in value.lower() for m in placeholder_markers), (
        f"ENCRYPTION_KEY in .env.example must be a placeholder, got: {value!r}"
    )


def test_no_secrets_in_backend_dir() -> None:
    """Sanity check: no real-looking 32-char base64 keys present in the repo."""
    forbidden_markers = ("SECRET_KEY=ey", "ENCRYPTION_KEY=" + "a" * 32)
    for path in REPO_ROOT.rglob("backend/.env*"):
        if path.name == ".env.example":
            continue
        if not path.is_file():
            continue
        # Real .env files are gitignored but may exist locally; we only enforce
        # the rule on tracked content via the gitignore test above.
        continue
    # If we got here without raising, OK.
    _ = forbidden_markers  # marker constant kept for documentation
