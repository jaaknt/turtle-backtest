"""Tests for turtlex/common/version.py resolve_version."""

import subprocess
from collections.abc import Iterator

import pytest
from pytest_mock import MockerFixture

from turtlex import __version__
from turtlex.common import version as version_module
from turtlex.common.version import resolve_version


@pytest.fixture(autouse=True)
def clear_version_cache() -> Iterator[None]:
    """Clear the @cache around every test, so one test's mock never leaks into the next."""
    resolve_version.cache_clear()
    yield
    resolve_version.cache_clear()


def _completed(returncode: int = 0, stdout: str = "abc1234\n") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["git"], returncode=returncode, stdout=stdout, stderr="")


def test_appends_the_short_git_sha(mocker: MockerFixture) -> None:
    mocker.patch.object(version_module.subprocess, "run", return_value=_completed())

    assert resolve_version() == f"{__version__}+abc1234"


def test_falls_back_to_bare_version_when_git_is_missing(mocker: MockerFixture) -> None:
    mocker.patch.object(version_module.subprocess, "run", side_effect=FileNotFoundError("no git"))

    assert resolve_version() == __version__


def test_falls_back_to_bare_version_when_git_fails(mocker: MockerFixture) -> None:
    # An installed wheel has no .git, so rev-parse exits non-zero
    mocker.patch.object(version_module.subprocess, "run", return_value=_completed(returncode=128, stdout=""))

    assert resolve_version() == __version__


def test_falls_back_to_bare_version_on_timeout(mocker: MockerFixture) -> None:
    mocker.patch.object(version_module.subprocess, "run", side_effect=subprocess.TimeoutExpired(cmd="git", timeout=5))

    assert resolve_version() == __version__


def test_runs_git_at_most_once_per_process(mocker: MockerFixture) -> None:
    run = mocker.patch.object(version_module.subprocess, "run", return_value=_completed())

    resolve_version()
    resolve_version()
    resolve_version()

    run.assert_called_once()


def test_resolves_against_the_repo_not_the_cwd(mocker: MockerFixture) -> None:
    run = mocker.patch.object(version_module.subprocess, "run", return_value=_completed())

    resolve_version()

    assert run.call_args.kwargs["cwd"] == version_module._REPO_ROOT
    assert (version_module._REPO_ROOT / "pyproject.toml").is_file()
