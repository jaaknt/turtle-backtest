import logging
import os
import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine

from turtlex.config.model import AppConfig, DatabaseConfig, JobRunsConfig

logger = logging.getLogger(__name__)


@dataclass
class Settings:
    """Main application settings"""

    app: AppConfig
    database: DatabaseConfig
    engine: Engine
    job_runs: JobRunsConfig = field(default_factory=JobRunsConfig)

    @classmethod
    def from_toml(cls, file_path: str = "./config/settings.toml") -> Settings:
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
        logger.info(f"Database connection: DB_ENV={db_env} ({db_config.host}:{db_config.port}/{db_config.dbname})")

        # Deliberately more lenient than the [database.<env>] lookup above, which raises on an
        # unknown DB_ENV. Telemetry config must not be able to take a job down, so a missing
        # [job_runs] TOML section, a missing entry for this DB_ENV, a non-table value, and an
        # unrecognized key all mean "disabled" rather than an exception. Splatting the section
        # with ** would instead raise TypeError on the realistic edit -- someone adding a key to
        # the VPS TOML, or a rolled-back deploy meeting a newer config.
        job_runs_section = data.get("job_runs", {})
        job_runs_env = job_runs_section.get(db_env, {}) if isinstance(job_runs_section, dict) else {}
        if not isinstance(job_runs_env, dict):
            logger.warning("[job_runs.%s] is not a table — job-run logging disabled", db_env)
            job_runs_env = {}
        unknown_keys = set(job_runs_env) - {f.name for f in fields(JobRunsConfig)}
        if unknown_keys:
            logger.warning("Ignoring unknown [job_runs.%s] keys: %s", db_env, ", ".join(sorted(unknown_keys)))
        # bool() rather than the raw value: a quoted "false" in TOML is a truthy string, which
        # would silently switch logging on.
        job_runs_config = JobRunsConfig(enabled=bool(job_runs_env.get("enabled", False)))

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
            job_runs=job_runs_config,
        )
