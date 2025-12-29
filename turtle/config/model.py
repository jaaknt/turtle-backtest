from dataclasses import dataclass, field


@dataclass
class DatabasePoolConfig:
    """Database connection pool configuration"""

    min_size: int = 4
    max_size: int = 20
    max_idle: int = 300
    max_lifetime: int = 3600
    timeout: int = 30
    check: str = "SELECT 1"


@dataclass
class DatabaseConfig:
    """PostgreSQL database configuration"""

    host: str
    port: int
    dbname: str
    user: str
    password: str
    sslmode: str = "prefer"
    connect_timeout: int = 10
    application_name: str = "turtle-app"
    pool: DatabasePoolConfig = field(default_factory=DatabasePoolConfig)

    def __post_init__(self) -> None:
        """Initialize nested configurations"""
        if isinstance(self.pool, dict):
            self.pool = DatabasePoolConfig(**self.pool)

    @property
    def connection_string(self) -> str:
        """Generate psycopg connection string"""
        return (
            f"host={self.host} "
            f"port={self.port} "
            f"dbname={self.dbname} "
            f"user={self.user} "
            f"password={self.password} "
            f"sslmode={self.sslmode} "
            f"connect_timeout={self.connect_timeout} "
            f"application_name={self.application_name}"
        )

    @property
    def sqlalchemy_url(self) -> str:
        """Generate SQLAlchemy-compatible database URL for psycopg (version 3)"""
        return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"


@dataclass
class AppConfig:
    """Application specific settings"""

    name: str
    debug: bool
    eodhd: dict[str, str] = field(default_factory=lambda: {"api_key": "**REPLACE_ME**"})
    alpaca: dict[str, str] = field(default_factory=lambda: {"api_key": "**REPLACE_ME**", "secret_key": "**REPLACE_ME**"})
