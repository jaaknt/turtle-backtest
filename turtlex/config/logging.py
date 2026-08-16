"""
Logging configuration module.

This module provides centralized logging configuration for the turtle trading system.
"""

import logging
import re
import sys

_FORMAT = "[%(levelname)s] %(asctime)s: %(message)s"
_DATEFMT = "%Y-%m-%dT%H:%M:%S"
# --verbose additionally reports the call site and the UTC offset
_VERBOSE_FORMAT = "[%(levelname)s|%(module)s|%(funcName)s|L%(lineno)d] %(asctime)s: %(message)s"
_VERBOSE_DATEFMT = "%Y-%m-%dT%H:%M:%S%z"

# Pinned even under --verbose: DEBUG on these floods the console
# (matplotlib.font_manager glyph scanning, sqlalchemy.engine SQL echo).
# matplotlib.font_manager is pinned at ERROR to drop the cosmetic
# "findfont: Font family 'Arial' not found" warnings quantstats provokes by
# passing fontname="Arial" explicitly on every title and axis label: the font
# is absent on a stock Ubuntu server, and matplotlib renders fine in DejaVu
# Sans regardless.
_THIRD_PARTY_LEVELS = {
    "httpx": logging.WARNING,
    "httpcore": logging.WARNING,
    "urllib3": logging.INFO,
    "sqlalchemy.engine": logging.WARNING,
    "matplotlib": logging.INFO,
    "matplotlib.font_manager": logging.ERROR,
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


class LastErrorCapture(logging.Handler):
    """Keeps the most recent ERROR-level message emitted while attached to the root logger.

    Lives here rather than beside its caller because handler ownership belongs to this module:
    library code must not mutate the root logger's handlers itself. Job-run logging needs it
    because most CLIs report failure by logging an error and returning 1 rather than raising,
    so there is no exception object to read the message off.

    Attached to the root logger rather than a named one so it sees errors from every module,
    including the ones run_cli logs on behalf of an unexpected exception.
    """

    def __init__(self) -> None:
        super().__init__(logging.ERROR)
        self.last_message: str | None = None

    def emit(self, record: logging.LogRecord) -> None:
        """Store the formatted message of `record`.

        Args:
            record: Log record at ERROR or above
        """
        self.last_message = record.getMessage()

    def attach(self) -> None:
        """Start capturing ERROR records from the root logger."""
        logging.getLogger().addHandler(self)

    def detach(self) -> None:
        """Stop capturing. Safe to call when not attached."""
        logging.getLogger().removeHandler(self)


def setup_logging(verbose: bool = False) -> None:
    """Configure root logging for a CLI entry point.

    Installs a single stdout handler with api_token redaction, replacing any
    handlers already present so repeated calls are idempotent. Third-party
    loggers stay pinned at their own levels even when verbose.

    Call once per process, immediately after parsing arguments and before
    Settings.from_toml(), so the database-connection banner that Settings logs
    at INFO is visible.

    Args:
        verbose: Emit DEBUG records from turtlex modules instead of INFO, and switch to
            the diagnostic line format that names the call site and the UTC offset.
    """
    fmt, datefmt = (_VERBOSE_FORMAT, _VERBOSE_DATEFMT) if verbose else (_FORMAT, _DATEFMT)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    handler.addFilter(ApiTokenFilter())

    root = logging.getLogger()
    for existing in root.handlers[:]:
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if verbose else logging.INFO)

    for name, level in _THIRD_PARTY_LEVELS.items():
        logging.getLogger(name).setLevel(level)
