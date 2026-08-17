from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from turtlex.config.model import AppConfig, DatabaseConfig, DatabasePoolConfig
from turtlex.config.settings import Settings, _deep_merge

# A synthetic base file for the tmp_path tests: deliberately unlike config/settings.toml (pool
# min_size 7, no [job_runs]) so an assertion cannot pass by accidentally reading the real file.
BASE_TOML = """\
[app]
name = "turtle-backtest"
debug = true
eodhd.api_key = "X"

[database]
host = "localhost"
port = 5432
dbname = "trading"
user = "app_user"

[database.pool]
min_size = 7
"""


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
        mocker.patch("turtlex.config.settings.load_dotenv")  # prevent .env file from restoring vars
        for var in ("DB_APP_PASSWORD", "EODHD_API_KEY"):
            monkeypatch.delenv(var, raising=False)
        with pytest.raises(ValueError, match="Missing required environment variables"):
            Settings.from_toml()

    def test_raises_listing_all_missing_vars(self, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture) -> None:
        mocker.patch("turtlex.config.settings.load_dotenv")  # prevent .env file from restoring vars
        for var in ("DB_APP_PASSWORD", "EODHD_API_KEY"):
            monkeypatch.delenv(var, raising=False)
        with pytest.raises(ValueError) as exc_info:
            Settings.from_toml()
        message = str(exc_info.value)
        assert "DB_APP_PASSWORD" in message
        assert "EODHD_API_KEY" in message

    def test_loads_env_vars_into_config(self, required_env_vars: None, mocker: MockerFixture) -> None:
        mocker.patch("turtlex.config.settings.create_engine", return_value=mocker.Mock())
        settings = Settings.from_toml()
        assert settings.database.password == "test_password"
        assert settings.app.eodhd["api_key"] == "test_eodhd_key"

    def test_database_config_populated(self, required_env_vars: None, mocker: MockerFixture) -> None:
        mocker.patch("turtlex.config.settings.create_engine", return_value=mocker.Mock())
        settings = Settings.from_toml()
        assert settings.database.host == "localhost"
        assert settings.database.port == 5432
        assert settings.database.dbname == "trading"
        assert settings.database.user == "app_user"

    def test_pool_config_populated(self, required_env_vars: None, mocker: MockerFixture) -> None:
        mocker.patch("turtlex.config.settings.create_engine", return_value=mocker.Mock())
        settings = Settings.from_toml()
        assert settings.database.pool.min_size == 10
        assert settings.database.pool.max_size == 30
        assert settings.database.pool.timeout == 30

    def test_app_config_populated(self, required_env_vars: None, mocker: MockerFixture) -> None:
        mocker.patch("turtlex.config.settings.create_engine", return_value=mocker.Mock())
        settings = Settings.from_toml()
        assert settings.app.name == "turtle-backtest"
        assert settings.app.debug is True

    def test_job_runs_read_from_flat_section(self, required_env_vars: None, mocker: MockerFixture, tmp_path: Path) -> None:
        # Against a fixture, not the committed config: whether logging is on by default is a
        # deployment policy that may change, but reading the flat [job_runs] table must not.
        config = tmp_path / "settings.toml"
        config.write_text(BASE_TOML + "\n[job_runs]\nenabled = true\n")
        mocker.patch("turtlex.config.settings.create_engine", return_value=mocker.Mock())

        settings = Settings.from_toml(str(config))

        assert settings.job_runs.enabled is True
        assert settings.database.pool.min_size == 7  # proves the fixture was read, not config/

    def test_missing_job_runs_section_disables_rather_than_raising(
        self, required_env_vars: None, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        # An old settings.toml on the VPS must record nothing, not break every CLI
        config = tmp_path / "settings.toml"
        config.write_text(BASE_TOML)
        mocker.patch("turtlex.config.settings.create_engine", return_value=mocker.Mock())

        settings = Settings.from_toml(str(config))

        assert settings.job_runs.enabled is False
        assert settings.database.pool.min_size == 7  # proves the fixture was read, not config/


class TestActiveProfile:
    def test_overlay_overrides_base_and_preserves_the_rest(
        self, required_env_vars: None, mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        (tmp_path / "settings.toml").write_text(BASE_TOML)
        (tmp_path / "settings-dev.toml").write_text('[database]\nhost = "dev-host"\n\n[job_runs]\nenabled = true\n')
        monkeypatch.setenv("ACTIVE_PROFILE", "dev")
        mocker.patch("turtlex.config.settings.create_engine", return_value=mocker.Mock())

        settings = Settings.from_toml(str(tmp_path / "settings.toml"))

        assert settings.database.host == "dev-host"
        # Keys the overlay does not mention survive from the base, including the nested pool table
        assert settings.database.port == 5432
        assert settings.database.dbname == "trading"
        assert settings.database.pool.min_size == 7
        assert settings.job_runs.enabled is True

    def test_no_profile_uses_base_only(self, required_env_vars: None, mocker: MockerFixture, tmp_path: Path) -> None:
        (tmp_path / "settings.toml").write_text(BASE_TOML)
        (tmp_path / "settings-dev.toml").write_text('[database]\nhost = "dev-host"\n')
        mocker.patch("turtlex.config.settings.create_engine", return_value=mocker.Mock())

        settings = Settings.from_toml(str(tmp_path / "settings.toml"))

        assert settings.database.host == "localhost"
        assert settings.database.pool.min_size == 7  # proves the fixture was read, not config/

    def test_unknown_profile_raises(self, required_env_vars: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        # A typo must fail loudly rather than falling back to the localhost defaults
        (tmp_path / "settings.toml").write_text(BASE_TOML)
        monkeypatch.setenv("ACTIVE_PROFILE", "nope")

        with pytest.raises(ValueError, match=f"no profile file at {tmp_path / 'settings-nope.toml'}"):
            Settings.from_toml(str(tmp_path / "settings.toml"))

    def test_nested_tables_merge_below_the_first_level(
        self, required_env_vars: None, mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # root -> database -> pool: a profile tuning one pool key must not drop its siblings
        (tmp_path / "settings.toml").write_text(BASE_TOML + "max_size = 30\n")
        (tmp_path / "settings-dev.toml").write_text("[database.pool]\nmin_size = 2\n")
        monkeypatch.setenv("ACTIVE_PROFILE", "dev")
        mocker.patch("turtlex.config.settings.create_engine", return_value=mocker.Mock())

        settings = Settings.from_toml(str(tmp_path / "settings.toml"))

        assert settings.database.pool.min_size == 2
        assert settings.database.pool.max_size == 30


class TestCommittedProfiles:
    """Guards the real config/ files, which the tmp_path tests above deliberately never touch."""

    @pytest.mark.parametrize("profile_path", sorted(Path("config").glob("settings-*.toml")), ids=lambda p: p.stem)
    def test_committed_profile_loads(
        self, profile_path: Path, required_env_vars: None, mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Catches a profile file that is untracked, misnamed, or malformed — none of which the
        # synthetic tmp_path fixtures can see.
        monkeypatch.setenv("ACTIVE_PROFILE", profile_path.stem.removeprefix("settings-"))
        mocker.patch("turtlex.config.settings.create_engine", return_value=mocker.Mock())

        settings = Settings.from_toml()

        assert settings.database.host
        assert settings.database.dbname

    def test_hetzner_profile_enables_job_run_logging(
        self, required_env_vars: None, mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The VPS runs under this profile, set in its secrets.env. It deliberately does NOT
        # redirect the database — Postgres is local to that box — so telemetry is its whole purpose.
        monkeypatch.setenv("ACTIVE_PROFILE", "hetzner")
        mocker.patch("turtlex.config.settings.create_engine", return_value=mocker.Mock())

        settings = Settings.from_toml()

        assert settings.job_runs.enabled is True
        assert settings.database.host == "localhost"


class TestDeepMerge:
    def test_nested_tables_merge_key_by_key(self) -> None:
        base = {"database": {"host": "localhost", "port": 5432}}
        assert _deep_merge(base, {"database": {"host": "hetzner"}}) == {"database": {"host": "hetzner", "port": 5432}}

    def test_scalars_replace(self) -> None:
        assert _deep_merge({"debug": True}, {"debug": False}) == {"debug": False}

    def test_overlay_only_keys_are_added(self) -> None:
        assert _deep_merge({"a": 1}, {"b": {"c": 2}}) == {"a": 1, "b": {"c": 2}}

    def test_scalar_overlay_replaces_a_table(self) -> None:
        assert _deep_merge({"a": {"b": 1}}, {"a": 2}) == {"a": 2}
