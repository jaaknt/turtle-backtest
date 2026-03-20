from turtle.config.model import AppConfig, DatabaseConfig, DatabasePoolConfig
from turtle.config.settings import Settings

import pytest
from pytest_mock import MockerFixture


class TestDatabasePoolConfig:
    def test_defaults(self) -> None:
        pool = DatabasePoolConfig()
        assert pool.min_size == 4
        assert pool.max_size == 20
        assert pool.max_idle == 300
        assert pool.max_lifetime == 3600
        assert pool.timeout == 30

    def test_custom_values(self) -> None:
        pool = DatabasePoolConfig(min_size=2, max_size=10, timeout=60)
        assert pool.min_size == 2
        assert pool.max_size == 10
        assert pool.timeout == 60


class TestDatabaseConfig:
    @pytest.fixture
    def db_config(self) -> DatabaseConfig:
        return DatabaseConfig(host="localhost", port=5432, dbname="trading", user="postgres", password="secret")

    def test_connection_string(self, db_config: DatabaseConfig) -> None:
        conn = db_config.connection_string
        assert "host=localhost" in conn
        assert "port=5432" in conn
        assert "dbname=trading" in conn
        assert "user=postgres" in conn
        assert "password=secret" in conn

    def test_sqlalchemy_url(self, db_config: DatabaseConfig) -> None:
        url = db_config.sqlalchemy_url
        assert url == "postgresql+psycopg://postgres:secret@localhost:5432/trading"

    def test_pool_initialised_from_dict(self) -> None:
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            dbname="trading",
            user="postgres",
            password="secret",
            pool={"min_size": 2, "max_size": 5},  # type: ignore[arg-type]
        )
        assert isinstance(config.pool, DatabasePoolConfig)
        assert config.pool.min_size == 2
        assert config.pool.max_size == 5


class TestAppConfig:
    def test_required_fields(self) -> None:
        config = AppConfig(name="test-app", debug=False)
        assert config.name == "test-app"
        assert config.debug is False

    def test_default_api_key_placeholders(self) -> None:
        config = AppConfig(name="test-app", debug=False)
        assert config.eodhd["api_key"] == "**REPLACE_ME**"

    def test_custom_api_keys(self) -> None:
        config = AppConfig(
            name="test-app",
            debug=False,
            eodhd={"api_key": "eodhd_123"},
        )
        assert config.eodhd["api_key"] == "eodhd_123"


class TestSettingsFromToml:
    def test_raises_when_config_file_missing(self, required_env_vars: None) -> None:
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            Settings.from_toml("nonexistent/path/settings.toml")

    def test_raises_when_env_vars_missing(self, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture) -> None:
        mocker.patch("turtle.config.settings.load_dotenv")  # prevent .env file from restoring vars
        for var in ("DB_PASSWORD", "EODHD_API_KEY"):
            monkeypatch.delenv(var, raising=False)
        with pytest.raises(ValueError, match="Missing required environment variables"):
            Settings.from_toml()

    def test_raises_listing_all_missing_vars(self, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture) -> None:
        mocker.patch("turtle.config.settings.load_dotenv")  # prevent .env file from restoring vars
        for var in ("DB_PASSWORD", "EODHD_API_KEY"):
            monkeypatch.delenv(var, raising=False)
        with pytest.raises(ValueError) as exc_info:
            Settings.from_toml()
        message = str(exc_info.value)
        assert "DB_PASSWORD" in message
        assert "EODHD_API_KEY" in message

    def test_loads_env_vars_into_config(self, required_env_vars: None, mocker: MockerFixture) -> None:
        mocker.patch("turtle.config.settings.create_engine", return_value=mocker.Mock())
        settings = Settings.from_toml()
        assert settings.database.password == "test_password"
        assert settings.app.eodhd["api_key"] == "test_eodhd_key"

    def test_database_config_populated(self, required_env_vars: None, mocker: MockerFixture) -> None:
        mocker.patch("turtle.config.settings.create_engine", return_value=mocker.Mock())
        settings = Settings.from_toml()
        assert settings.database.host == "localhost"
        assert settings.database.port == 5432
        assert settings.database.dbname == "trading"
        assert settings.database.user == "postgres"

    def test_pool_config_populated(self, required_env_vars: None, mocker: MockerFixture) -> None:
        mocker.patch("turtle.config.settings.create_engine", return_value=mocker.Mock())
        settings = Settings.from_toml()
        assert settings.database.pool.min_size == 10
        assert settings.database.pool.max_size == 30
        assert settings.database.pool.timeout == 30

    def test_app_config_populated(self, required_env_vars: None, mocker: MockerFixture) -> None:
        mocker.patch("turtle.config.settings.create_engine", return_value=mocker.Mock())
        settings = Settings.from_toml()
        assert settings.app.name == "turtle-backtest"
        assert settings.app.debug is True
