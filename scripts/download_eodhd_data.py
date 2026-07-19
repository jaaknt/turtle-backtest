#!/usr/bin/env python3
"""Compatibility wrapper — the implementation lives in turtlex/cli/download_eodhd_data.py.

Prefer the console script installed via [project.scripts]: ``uv run download-eodhd-data``.
"""

import sys

from turtlex.cli.download_eodhd_data import main

if __name__ == "__main__":
    sys.exit(main())
