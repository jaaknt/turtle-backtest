"""Helpers shared by the research report writers in ``scripts/``."""

from collections.abc import Sequence
from datetime import datetime
from zoneinfo import ZoneInfo

REPORT_TIMEZONE = ZoneInfo("Europe/Tallinn")


def run_timestamp() -> str:
    """Return the current Tallinn wall-clock time for a report's ``Run date:`` header.

    Studies are re-run from more than one host, so the stamp is pinned to Tallinn rather
    than taken from the host's local zone — otherwise two results written on the same day
    cannot be ordered against each other. The zone name is spelled out in the output so a
    committed result is unambiguous without knowing where it was produced.

    Returns:
        Timestamp formatted as ``YYYY-MM-DD HH:MM:SS Tallinn time``.
    """
    return datetime.now(REPORT_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S Tallinn time")


def config_table(rows: Sequence[tuple[str, str]]) -> str:
    """Render a study's run configuration as the standard `| Parameter | Value |` table.

    Every cohort study writes the same table so its settings can be diffed against another
    study's at a glance. Values that depart from the shared cohort setup — a dropped filter,
    an ungated run, a non-standard algorithm set — are bolded by the caller.

    Args:
        rows: ``(parameter, value)`` pairs, rendered in the order given

    Returns:
        The markdown table, header row included, terminated by a newline.
    """
    lines = ["| Parameter | Value |", "|---|---|"]
    lines.extend(f"| {param} | {value} |" for param, value in rows)
    return "\n".join(lines) + "\n"
