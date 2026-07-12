"""Runs the bruno/eodhd Bruno collection against the real EODHD API via the bru CLI.

Opt-in only: excluded from the default `uv run pytest` run (see the `bruno` marker
in pyproject.toml). Run explicitly with `uv run pytest -m bruno`.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

BRUNO_DIR = Path(__file__).parent.parent.parent / "bruno" / "eodhd"
REQUEST_FILES = sorted(p.name for p in BRUNO_DIR.glob("*.yml") if p.name != "opencollection.yml")

pytestmark = [
    pytest.mark.bruno,
    pytest.mark.skipif(shutil.which("bru") is None, reason="bru CLI not installed (npm install -g @usebruno/cli)"),
    pytest.mark.skipif(not (BRUNO_DIR / ".env").exists(), reason="bruno/eodhd/.env with EODHD_API_KEY not found"),
]


@pytest.mark.parametrize("request_file", REQUEST_FILES)
def test_bruno_positive_request(request_file: str) -> None:
    """Runs a single positive-tagged Bruno request and asserts its bru CLI assertions pass."""
    result = subprocess.run(
        ["bru", "run", request_file, "--tests-only"],
        cwd=BRUNO_DIR,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
