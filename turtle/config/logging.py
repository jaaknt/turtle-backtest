"""
Logging configuration module.

This module provides centralized logging configuration for the turtle trading system.
"""

import json
import logging.config
import logging.handlers
import pathlib
from dataclasses import dataclass


@dataclass
class LogConfig:
    """Configuration for logging setup."""

    @classmethod
    def setup(cls, verbose: bool = False) -> None:
        """Setup logging configuration."""
        config_file = pathlib.Path(__file__).parent.parent.parent / "config" / "stdout.json"

        if config_file.exists():
            with open(config_file) as f_in:
                config = json.load(f_in)

            # Adjust log level if verbose
            if verbose:
                if "root" in config:
                    config["root"]["level"] = "DEBUG"
                if "loggers" in config and "root" in config["loggers"]:
                    config["loggers"]["root"]["level"] = "DEBUG"
                if "loggers" in config and "turtle" in config["loggers"]:
                    config["loggers"]["turtle"]["level"] = "DEBUG"
                for handler in config["handlers"].values():
                    if "level" in handler:
                        handler["level"] = "DEBUG"

            logging.config.dictConfig(config)
        else:
            # Fallback to basic config if json config not found
            level = logging.DEBUG if verbose else logging.INFO
            logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")