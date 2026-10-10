# Database Migrations

Alembic standalone mode with raw SQL (the usual `current` / `history` / `upgrade head` /
`downgrade -1` / `revision -m` commands apply). Migrations live in `db/migrations/versions/`, the
version table is `public.alembic_version`, and the target database comes from the same
`load_config_data()` the app uses — `db/migrations/env.py` reads `config/settings.toml` plus any
`ACTIVE_PROFILE` overlay, so Alembic and the CLIs can never disagree about which database they mean.
Only `hetzner-db` redirects the database, so Alembic targets localhost unless that profile is
active. **Do not run Alembic under `hetzner-db`** — it would target the VPS, and it connects as the
`alembic` role with `DB_ALEMBIC_PASSWORD` regardless of the profile's `user`, so nothing about the
profile stops a migration landing on production.
