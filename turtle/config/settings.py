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
            "DB_APP_PASSWORD": ("database", "password"),
            "EODHD_API_KEY": ("app", "eodhd", "api_key"),
        }
        missing = [var for var in required_env_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        db_env = os.getenv("DB_ENV") or "local"
        db_section = data["database"].get(db_env)
        if db_section is None:
            valid = [k for k in data["database"] if k != "pool"]
            raise ValueError(f"Unknown DB_ENV={db_env!r}. Valid options: {valid}")
        db_config = DatabaseConfig(
            **db_section,
            pool=data["database"].get("pool", {}),
            password=os.environ["DB_APP_PASSWORD"],
        )

        data["app"]["eodhd"]["api_key"] = os.environ["EODHD_API_KEY"]

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
