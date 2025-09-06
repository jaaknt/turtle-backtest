import os
from dataclasses import dataclass
from pathlib import Path
import tomllib
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool

from turtle.config.model import DatabaseConfig, AppConfig


@dataclass
class Settings:
    """Main application settings"""

    app: AppConfig
    database: DatabaseConfig
    pool: ConnectionPool

    @classmethod
    def from_toml(cls, file_path: str = "./config/settings.toml") -> "Settings":
        # Load environment variables from .env file
        load_dotenv()

        """Load settings from TOML file"""
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(file_path_obj, "rb") as f:
            data = tomllib.load(f)

        # replace sensitive information with environment variables
        data["database"]["password"] = os.getenv("DB_PASSWORD", data["database"]["password"])

        # Create database config
        db_config = DatabaseConfig(**data.get("database", {}))

        # replace sensitive information with environment variables
        data["app"]["eodhd"]["api_key"] = os.getenv("EODHD_API_KEY", "**REPLACE_ME**")
        data["app"]["alpaca"]["api_key"] = os.getenv("ALPACA_API_KEY", "**REPLACE_ME**")
        data["app"]["alpaca"]["secret_key"] = os.getenv("ALPACA_SECRET_KEY", "**REPLACE_ME**")

        # Create app config
        app_config = AppConfig(**data.get("app", {}))

        return cls(
            app=app_config,
            database=db_config,
            pool=ConnectionPool(
                conninfo=db_config.connection_string,
                min_size=db_config.pool.min_size,
                max_size=db_config.pool.max_size,
                max_idle=db_config.pool.max_idle,
                max_lifetime=db_config.pool.max_lifetime,
                timeout=db_config.pool.timeout,
            ),
        )
