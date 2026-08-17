import logging
import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine

from turtlex.config.model import AppConfig, DatabaseConfig, JobRunsConfig

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "./config/settings.toml"


def _deep_merge(base: dict[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively merge `overlay` into `base`, in place, and return `base`.

    Nested tables merge key by key so a profile can override [database] host without
    restating port/dbname/user; every other value type replaces wholesale.

    Args:
        base: Mapping to merge into; mutated
        overlay: Mapping whose values win on conflict

    Returns:
        The mutated `base`, for convenience
    """
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def _read_toml(path: Path) -> dict[str, Any]:
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_config_data(file_path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load the base TOML and layer the ACTIVE_PROFILE overlay on top of it.

    Args:
        file_path: Path to the base TOML. The overlay is derived from it by inserting
            `-<profile>` before the suffix, so ./config/settings.toml with
            ACTIVE_PROFILE=hetzner reads ./config/settings-hetzner.toml.

    Returns:
        The merged configuration mapping.

    Raises:
        FileNotFoundError: If the base file does not exist.
        ValueError: If ACTIVE_PROFILE is set but names no existing profile file.
    """
    base_path = Path(file_path)
    if not base_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    data = _read_toml(base_path)

    # An empty ACTIVE_PROFILE reads as "no profile", so a shell or EnvironmentFile that exports
    # the name without a value gets the base configuration rather than an error.
    profile = os.getenv("ACTIVE_PROFILE")
    if not profile:
        logger.info("Active profile: none (base configuration only)")
        return data

    overlay_path = base_path.with_name(f"{base_path.stem}-{profile}{base_path.suffix}")
    # Deliberately stricter than Spring Boot, which ignores a profile it cannot match: a typo'd
    # ACTIVE_PROFILE must not silently fall back to the localhost defaults and point a
    # production-shaped run at the wrong database.
    if not overlay_path.exists():
        raise ValueError(f"ACTIVE_PROFILE={profile!r} but no profile file at {overlay_path}")

    logger.info(f"Active profile: {profile} ({overlay_path})")
    return _deep_merge(data, _read_toml(overlay_path))


@dataclass
class Settings:
    """Main application settings"""

    app: AppConfig
    database: DatabaseConfig
    engine: Engine
    job_runs: JobRunsConfig = field(default_factory=JobRunsConfig)

    @classmethod
    def from_toml(cls, file_path: str = DEFAULT_CONFIG_PATH) -> Settings:
        """Load settings from the base TOML plus any ACTIVE_PROFILE overlay"""
        load_dotenv()
        data = load_config_data(file_path)

        # Require secrets from environment variables — never fall back to TOML values
        required_env_vars = {
            "DB_APP_PASSWORD": ("database", "password"),
            "EODHD_API_KEY": ("app", "eodhd", "api_key"),
        }
        missing = [var for var in required_env_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        # [database.pool] nests under [database], so the splat carries it through as a dict and
        # DatabaseConfig.__post_init__ turns it into a DatabasePoolConfig.
        db_config = DatabaseConfig(**data["database"], password=os.environ["DB_APP_PASSWORD"])
        logger.info(f"Database connection: {db_config.host}:{db_config.port}/{db_config.dbname}")

        # Deliberately more lenient than the [database] read above, which raises on a malformed
        # section. Telemetry config must not be able to take a job down, so a missing [job_runs]
        # TOML section, a non-table value, and an unrecognized key all mean "disabled" rather than
        # an exception. Splatting the section with ** would instead raise TypeError on the
        # realistic edit -- someone adding a key to the VPS TOML, or a rolled-back deploy meeting
        # a newer config.
        job_runs_section = data.get("job_runs", {})
        if not isinstance(job_runs_section, dict):
            logger.warning("[job_runs] is not a table — job-run logging disabled")
            job_runs_section = {}
        unknown_keys = set(job_runs_section) - {f.name for f in fields(JobRunsConfig)}
        if unknown_keys:
            logger.warning("Ignoring unknown [job_runs] keys: %s", ", ".join(sorted(unknown_keys)))
        # bool() rather than the raw value: a quoted "false" in TOML is a truthy string, which
        # would silently switch logging on.
        job_runs_config = JobRunsConfig(enabled=bool(job_runs_section.get("enabled", False)))

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
