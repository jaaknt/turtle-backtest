#!/usr/bin/env python3
"""Compatibility wrapper — the implementation lives in turtlex/cli/signal_runner.py.

Prefer the console script installed via [project.scripts]: ``uv run signal-runner``.
"""

import sys

from turtlex.cli.signal_runner import main

if __name__ == "__main__":
    sys.exit(main())
