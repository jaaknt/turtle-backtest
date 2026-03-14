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
        """Load settings from TOML file"""
        load_dotenv()

        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(file_path_obj, "rb") as f:
            data = tomllib.load(f)

        # Require secrets from environment variables — never fall back to TOML values
        required_env_vars = {
            "DB_PASSWORD": ("database", "password"),
            "EODHD_API_KEY": ("app", "eodhd", "api_key"),
            "ALPACA_API_KEY": ("app", "alpaca", "api_key"),
            "ALPACA_SECRET_KEY": ("app", "alpaca", "secret_key"),
        }
        missing = [var for var in required_env_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        data["database"]["password"] = os.environ["DB_PASSWORD"]
        db_config = DatabaseConfig(**data.get("database", {}))

        data["app"]["eodhd"]["api_key"] = os.environ["EODHD_API_KEY"]
        data["app"]["alpaca"]["api_key"] = os.environ["ALPACA_API_KEY"]
        data["app"]["alpaca"]["secret_key"] = os.environ["ALPACA_SECRET_KEY"]

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
