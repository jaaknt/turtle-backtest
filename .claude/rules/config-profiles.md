---
paths:
  - "config/**"
  - "turtlex/config/**"
  - "db/migrations/**"
  - "scripts/**"
---

# Configuration Profiles

**Profiles (Spring Boot style).** `config/settings.toml` holds a complete set of defaults pointing at
localhost. `ACTIVE_PROFILE=<name>` deep-merges `config/settings-<name>.toml` over it, so an overlay
only names the keys it changes. Adding a profile needs no code change.

A profile names **the machine you are running on**, not a database to connect to.
`config/settings-hetzner.toml` is what the VPS runs under — `ACTIVE_PROFILE=hetzner` lives in its
`~/.config/turtle-backtest/secrets.env`, the `EnvironmentFile` every unit loads, so the units
themselves stay environment-agnostic. It inherits the localhost database unchanged, because Postgres
runs on that box, and its only effect is switching job-run logging on. Dev machines leave
`ACTIVE_PROFILE` unset.
`config/settings-hetzner-db.toml` is the **one profile that names a database rather than a machine**:
`ACTIVE_PROFILE=hetzner-db` points a dev machine at the VPS Postgres over Tailscale as `app_user`,
for studies needing history deeper than the local 5-year mirror. That is the same role the CLIs use
locally, so `DB_APP_PASSWORD` is already the right secret and the call site needs no password
mapping — `ACTIVE_PROFILE=hetzner-db uv run …`. ⚠ **The profile is not read-only.** It connected as
the SELECT-only `claude` role until 2026-08-29; under `app_user` anything run through it can write to
the VPS's `turtle` schema, so a `--persist` run or a stray write now reaches production instead of
failing. The studies only read, but nothing enforces that — check the `Database connection:` banner
every run logs at INFO. After a VPS reboot Postgres binds before the Tailscale address exists, so
connections time out until `systemctl restart postgresql` runs there.

Every database parameter comes from `config/settings.toml` and its profile overlay — there is no
environment variable that changes hosts. `ACTIVE_PROFILE` selects which overlay applies; the only
env vars read are the two secrets. A profile with no matching file raises `ValueError` rather than
silently falling back — a typo must not point a run at the wrong database. The check is in
`load_config_data()`, not `Settings.from_toml`, so Alembic inherits it.

`[job_runs] enabled` is a flat key, **off in the base file** and switched on by the `hetzner` profile,
so the VPS records runs and dev machines do not. Unlike the database section, a missing `[job_runs]`,
a non-table value, or an unknown key means disabled rather than an exception — telemetry config must
never be able to take a job down.
