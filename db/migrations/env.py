import os
import sys
import tomllib
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import URL

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# Load environment variables from .env
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic always connects as the dedicated 'alembic' user with full DDL privileges.
# Read only host/port/dbname from TOML — no app secrets required.
alembic_password = os.environ.get("DB_ALEMBIC_PASSWORD")
if not alembic_password:
    raise ValueError("Missing required environment variable: DB_ALEMBIC_PASSWORD")

with open(project_root / "config/settings.toml", "rb") as _f:
    _toml = tomllib.load(_f)
_db = _toml["database"]

alembic_url = URL.create(
    "postgresql+psycopg",
    username="alembic",
    password=alembic_password,
    host=_db["host"],
    port=_db["port"],
    database=_db["dbname"],
)
config.set_main_option("sqlalchemy.url", alembic_url.render_as_string(hide_password=False))

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

# CRITICAL: No SQLAlchemy models (standalone mode)
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # CRITICAL: Set search_path to turtle schema
        version_table_schema=config.get_main_option("version_table_schema"),
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # Enable TimescaleDB support with search_path
        connect_args={"options": "-csearch_path=turtle,public"},
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=config.get_main_option("version_table_schema"),
            include_schemas=True,
            # Render item for TimescaleDB custom types
            render_as_batch=False,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
