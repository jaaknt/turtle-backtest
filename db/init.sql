\getenv alembic_password DB_ALEMBIC_PASSWORD
\getenv db_password DB_PASSWORD

-- Create trading database
CREATE DATABASE trading
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

\connect trading

-- alembic: full access for migrations
CREATE USER alembic WITH PASSWORD :'alembic_password';
GRANT ALL PRIVILEGES ON DATABASE trading TO alembic;

CREATE SCHEMA IF NOT EXISTS turtle AUTHORIZATION alembic;
GRANT ALL ON SCHEMA turtle TO alembic;
ALTER DEFAULT PRIVILEGES IN SCHEMA turtle GRANT ALL ON TABLES TO alembic;
ALTER DEFAULT PRIVILEGES IN SCHEMA turtle GRANT ALL ON SEQUENCES TO alembic;
ALTER DEFAULT PRIVILEGES IN SCHEMA turtle GRANT ALL ON FUNCTIONS TO alembic;

-- trading_ro: readonly access to turtle schema
CREATE USER trading_ro WITH PASSWORD :'db_password';
GRANT CONNECT ON DATABASE trading TO trading_ro;
GRANT USAGE ON SCHEMA turtle TO trading_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA turtle TO trading_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA turtle GRANT SELECT ON TABLES TO trading_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA turtle GRANT SELECT ON SEQUENCES TO trading_ro;
