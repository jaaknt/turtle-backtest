"""
Logging configuration module.

This module provides centralized logging configuration for the turtle trading system.
"""

import logging
import re
import sys

_FORMAT = "[%(levelname)s|%(module)s|%(funcName)s|L%(lineno)d] %(asctime)s: %(message)s"
_DATEFMT = "%Y-%m-%dT%H:%M:%S%z"

# Pinned even under --verbose: DEBUG on these floods the console
# (matplotlib.font_manager glyph scanning, sqlalchemy.engine SQL echo).
_THIRD_PARTY_LEVELS = {
    "httpx": logging.WARNING,
    "httpcore": logging.WARNING,
    "urllib3": logging.INFO,
    "sqlalchemy.engine": logging.WARNING,
    "matplotlib": logging.INFO,
    "asyncio": logging.INFO,
}


class ApiTokenFilter(logging.Filter):
    """Redact api_token query parameter from httpx request log messages.

    httpx logs via format-string args (e.g. "HTTP Request: %s %s ..."),
    so the URL lives in record.args, not record.msg.

    Must be attached to the handler rather than a logger: httpx logs from
    httpx._client propagate to root without passing through filters attached
    to the parent httpx logger.
    """

    _PATTERN = re.compile(r"api_token=[^&\s\"]+")

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact any api_token value in the record, in place.

        Args:
            record: Log record to scrub; both msg and args are rewritten

        Returns:
            Always True — the record is redacted, never dropped
        """
        record.msg = self._PATTERN.sub("api_token=***", str(record.msg))
        if record.args:
            args = record.args if isinstance(record.args, tuple) else (record.args,)
            record.args = tuple(self._PATTERN.sub("api_token=***", s) if "api_token=" in (s := str(arg)) else arg for arg in args)
        return True


def setup_logging(verbose: bool = False) -> None:
    """Configure root logging for a CLI entry point.

    Installs a single stdout handler with api_token redaction, replacing any
    handlers already present so repeated calls are idempotent. Third-party
    loggers stay pinned at their own levels even when verbose.

    Call once per process, immediately after parsing arguments and before
    Settings.from_toml(), so the database-connection banner that Settings logs
    at INFO is visible.

    Args:
        verbose: Emit DEBUG records from turtlex modules instead of INFO.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    handler.addFilter(ApiTokenFilter())

    root = logging.getLogger()
    for existing in root.handlers[:]:
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if verbose else logging.INFO)

    for name, level in _THIRD_PARTY_LEVELS.items():
        logging.getLogger(name).setLevel(level)
