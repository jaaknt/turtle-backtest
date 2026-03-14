import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from turtle.config.model import AppConfig, DatabaseConfig

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine


@dataclass
class Settings:
    """Main application settings"""

    app: AppConfig
    database: DatabaseConfig
    engine: Engine

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

        app_config = AppConfig(**data.get("app", {}))
        pool_config = db_config.pool

        engine = create_engine(
            db_config.sqlalchemy_url,
            pool_size=pool_config.min_size,
            max_overflow=pool_config.max_size - pool_config.min_size,
            pool_recycle=pool_config.max_lifetime,
            pool_timeout=pool_config.timeout,
            pool_pre_ping=True,
        )

        return cls(
            app=app_config,
            database=db_config,
            engine=engine,
        )
