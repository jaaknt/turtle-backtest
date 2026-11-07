#!/bin/bash
set -e

# Fail before creating anything: docker compose turns an unset variable into an empty string, and
# CREATE USER ... PASSWORD '' succeeds but leaves a role that can never log in.
: "${DB_WEB_PASSWORD:?DB_WEB_PASSWORD must be set (turtle_web role, docs/specs/web.md Step 0)}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE trading
        WITH
        OWNER = postgres
        ENCODING = 'UTF8'
        LC_COLLATE = 'en_US.UTF-8'
        LC_CTYPE = 'en_US.UTF-8'
        TEMPLATE = template0;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "trading" <<-EOSQL
    -- alembic: full access for migrations
    CREATE USER alembic WITH PASSWORD '${DB_ALEMBIC_PASSWORD}';
    GRANT ALL PRIVILEGES ON DATABASE trading TO alembic;

    CREATE SCHEMA IF NOT EXISTS turtle AUTHORIZATION alembic;
    GRANT ALL ON SCHEMA turtle TO alembic;
    ALTER DEFAULT PRIVILEGES IN SCHEMA turtle GRANT ALL ON TABLES TO alembic;
    ALTER DEFAULT PRIVILEGES IN SCHEMA turtle GRANT ALL ON SEQUENCES TO alembic;
    ALTER DEFAULT PRIVILEGES IN SCHEMA turtle GRANT ALL ON FUNCTIONS TO alembic;
    
    GRANT ALL ON SCHEMA public TO alembic;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO alembic;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO alembic;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO alembic;

    -- app_user: read/write access to turtle schema (application user)
    CREATE USER app_user WITH PASSWORD '${DB_APP_PASSWORD}';
    GRANT CONNECT ON DATABASE trading TO app_user;
    GRANT USAGE ON SCHEMA turtle TO app_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA turtle TO app_user;
    GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA turtle TO app_user;
    -- FOR ROLE alembic: ensures tables created by alembic migrations inherit these grants
    ALTER DEFAULT PRIVILEGES FOR ROLE alembic IN SCHEMA turtle GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
    ALTER DEFAULT PRIVILEGES FOR ROLE alembic IN SCHEMA turtle GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO app_user;

    -- claude: readonly access to turtle schema
    CREATE USER claude WITH PASSWORD '${DB_CLAUDE_PASSWORD}';
    GRANT CONNECT ON DATABASE trading TO claude;
    GRANT USAGE ON SCHEMA turtle TO claude;
    GRANT SELECT ON ALL TABLES IN SCHEMA turtle TO claude;
    -- FOR ROLE alembic: ensures tables created by alembic migrations inherit these grants
    ALTER DEFAULT PRIVILEGES FOR ROLE alembic IN SCHEMA turtle GRANT SELECT ON TABLES TO claude;
    ALTER DEFAULT PRIVILEGES FOR ROLE alembic IN SCHEMA turtle GRANT SELECT ON SEQUENCES TO claude;

    -- turtle_web: readonly network service, the turtle-web dashboard (docs/specs/web.md, Step 0)
    -- \getenv binds the password as a psql variable, so a quote in it cannot break the statement
    \getenv web_password DB_WEB_PASSWORD
    CREATE USER turtle_web WITH PASSWORD :'web_password';
    GRANT CONNECT ON DATABASE trading TO turtle_web;
    GRANT USAGE ON SCHEMA turtle TO turtle_web;
    GRANT SELECT ON ALL TABLES IN SCHEMA turtle TO turtle_web;
    -- FOR ROLE alembic: ensures tables created by alembic migrations inherit this grant
    ALTER DEFAULT PRIVILEGES FOR ROLE alembic IN SCHEMA turtle GRANT SELECT ON TABLES TO turtle_web;
    -- GRANT SELECT is the barrier; these are guard rails for a long-running network service.
    -- The session default turns an accidental write into an explicit error, but a session can
    -- override it, so never grant this role more than SELECT.
    ALTER ROLE turtle_web SET default_transaction_read_only = on;
    ALTER ROLE turtle_web SET statement_timeout = '10s';
    ALTER ROLE turtle_web SET idle_in_transaction_session_timeout = '30s';
    -- JIT compilation was 352 ms of a 1,472 ms query here; every dashboard query returns few rows
    ALTER ROLE turtle_web SET jit = off;
EOSQL
