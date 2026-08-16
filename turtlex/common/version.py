"""Resolve the version of the code a job run is executing."""

import logging
import subprocess
from functools import cache
from pathlib import Path

from turtlex import __version__

logger = logging.getLogger(__name__)

# turtlex/common/version.py -> turtlex/common -> turtlex -> repo root. Derived from __file__
# rather than cwd: systemd sets WorkingDirectory, but nothing guarantees it for an ad-hoc run.
_REPO_ROOT = Path(__file__).resolve().parents[2]


@cache
def resolve_version() -> str:
    """Return the running code version as "<package>+<git-sha>", e.g. "1.0.0+fd66f3b".

    The git SHA is the half that identifies deployed code, since the VPS updates by `git pull`.
    When git is unavailable — no binary, or an installed wheel with no `.git` — the bare package
    version is returned instead. Cached, so the subprocess runs at most once per process.

    Returns:
        str: Package version with the short git SHA appended, or the package version alone
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as e:
        # Missing git binary, or a timeout. Version resolution must never fail a job.
        logger.debug("Could not resolve git SHA: %s", e)
        return __version__

    if result.returncode != 0:
        # No .git — an installed wheel rather than a checkout.
        logger.debug("git rev-parse returned %d: %s", result.returncode, result.stderr.strip())
        return __version__

    return f"{__version__}+{result.stdout.strip()}"
