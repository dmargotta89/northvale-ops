"""Locate repo data and sample files from an editable install."""

from __future__ import annotations

from pathlib import Path


def find_repo_file(*parts: str) -> Path:
    """Return the first existing file walking upward from this package.

    Editable installs keep sources in the checkout, so ``data/`` and
    ``samples/`` at the repository root stay reachable without copying
    them into the wheel. A matching file in the current directory is used
    only when the checkout copy is absent.
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent.joinpath(*parts)
        if candidate.is_file():
            return candidate
    cwd_candidate = Path.cwd().joinpath(*parts)
    if cwd_candidate.is_file():
        return cwd_candidate
    relative = Path(*parts)
    raise FileNotFoundError(f"Could not find {relative.as_posix()} from the Northvale package or cwd.")
