#!/usr/bin/env bash
#
# Refresh the local Docker Postgres from the Hetzner VPS over Tailscale.
#
# The VPS is the authoritative copy: its systemd timers run the EODHD downloads, so its
# tables move on and the local ones do not. This script pulls them back down. It never
# touches EODHD — running the downloader locally as well would spend API quota twice and
# let the two copies disagree.
#
# What it mirrors — every table is TRUNCATEd and refilled, so upstream deletions propagate:
#   company, company_history, exchange, lightyear_transaction, ticker, ticker_group
#       Every row.
#   daily_bars
#       The last BARS_YEARS years only (5 by default). The truncate is not windowed, so bars
#       older than the cutoff are dropped rather than kept: the local table ends up holding
#       exactly the window. Re-run with a wider BARS_YEARS to pull deep history back down.
#
# Every table is loaded inside a single transaction: a stream that dies mid-copy rolls the
# TRUNCATE back and leaves the table as it was. Row counts are then compared against the
# source, so a silently short stream fails the run rather than passing as a small table.
#
# Both psql processes run inside the `turtledb` container — the WSL host has no Postgres
# client tools — and the data is piped between them there, never through the host.
#
# Caveat: this is a mirror, not a merge. `lightyear_transaction` in particular is wiped and
# refilled from the VPS, so a statement imported locally but never imported on the VPS is
# lost. Import statements on the VPS, or re-run `uv run lightyear-import` locally afterwards.
#
# Usage:
#   scripts/update-local-db.sh                 # 5 years of bars, all other tables in full
#   BARS_YEARS=10 scripts/update-local-db.sh   # widen the daily_bars window
#
# Requires DB_CLAUDE_PASSWORD in the environment (the VPS's read-only role) and a running
# `turtledb` container. See docs/implementation.md for the VPS side.

set -euo pipefail

REMOTE_HOST=${REMOTE_HOST:-hetzner}
REMOTE_USER=${REMOTE_USER:-claude}
REMOTE_DB=${REMOTE_DB:-trading}
CONTAINER=${CONTAINER:-turtledb}
LOCAL_USER=${LOCAL_USER:-postgres}
LOCAL_DB=${LOCAL_DB:-trading}
BARS_YEARS=${BARS_YEARS:-5}

export PGPASSWORD=${DB_CLAUDE_PASSWORD:?DB_CLAUDE_PASSWORD must be set - the read-only role on the VPS}

CUTOFF=$(date -d "${BARS_YEARS} years ago" +%F)

# table[|row filter]. Without a filter the whole table is copied.
TABLES=(
    "company"
    "company_history"
    "exchange"
    "lightyear_transaction"
    "ticker"
    "ticker_group"
    "daily_bars|WHERE date >= '${CUTOFF}'"
)

log() { printf '%s  %s\n' "$(date +%H:%M:%S)" "$*"; }

die() {
    printf '%s  ERROR: %s\n' "$(date +%H:%M:%S)" "$*" >&2
    exit 1
}

remote_query() {
    docker exec -e PGPASSWORD "$CONTAINER" \
        psql -h "$REMOTE_HOST" -U "$REMOTE_USER" -d "$REMOTE_DB" -v ON_ERROR_STOP=1 -qAtc "$1"
}

local_query() {
    docker exec "$CONTAINER" psql -U "$LOCAL_USER" -d "$LOCAL_DB" -v ON_ERROR_STOP=1 -qAtc "$1"
}

# Column order has to agree end to end, because the copy is positional (SELECT * -> COPY FROM).
columns_of() { echo "SELECT string_agg(column_name, ',' ORDER BY ordinal_position)
                    FROM information_schema.columns
                    WHERE table_schema = 'turtle' AND table_name = '$1'"; }

# Stream one table's rows straight from the VPS into the local table. $1 is the source query,
# $2 the statement clearing what is about to be replaced, $3 the qualified target table.
copy_table() {
    docker exec -e PGPASSWORD \
        -e RHOST="$REMOTE_HOST" -e RUSER="$REMOTE_USER" -e RDB="$REMOTE_DB" \
        -e LUSER="$LOCAL_USER" -e LDB="$LOCAL_DB" \
        "$CONTAINER" sh -c '
            set -eu -o pipefail
            psql -h "$RHOST" -U "$RUSER" -d "$RDB" -v ON_ERROR_STOP=1 -q \
                 -c "\copy ($1) TO STDOUT" |
            PGPASSWORD= psql -U "$LUSER" -d "$LDB" -v ON_ERROR_STOP=1 -q --single-transaction \
                 -c "$2" -c "\copy $3 FROM STDIN"
        ' sh "$1" "$2" "$3"
}

log "Source: ${REMOTE_USER}@${REMOTE_HOST}/${REMOTE_DB}  ->  local ${CONTAINER}:${LOCAL_DB}"
log "daily_bars window: ${CUTOFF} onwards (${BARS_YEARS} years)"

docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -q true ||
    die "container '${CONTAINER}' is not running - start it with docker-compose up -d"
[ "$(remote_query 'SELECT 1')" = "1" ] ||
    die "cannot reach ${REMOTE_HOST} - check Tailscale, and that Postgres bound to the tailnet IP after the last reboot"

for entry in "${TABLES[@]}"; do
    table=${entry%%|*}
    remote_cols=$(remote_query "$(columns_of "$table")")
    local_cols=$(local_query "$(columns_of "$table")")
    [ "$remote_cols" = "$local_cols" ] ||
        die "turtle.${table} column mismatch - run 'uv run alembic upgrade head' on the side that is behind
     remote: ${remote_cols}
      local: ${local_cols}"
done

for entry in "${TABLES[@]}"; do
    table=${entry%%|*}
    filter=${entry#*|}
    if [ "$filter" = "$table" ]; then filter=""; fi

    expected=$(remote_query "SELECT count(*) FROM turtle.${table} ${filter}")
    before=$(local_query "SELECT count(*) FROM turtle.${table}")
    log "turtle.${table}: ${before} local rows -> ${expected} from ${REMOTE_HOST}"
    copy_table "SELECT * FROM turtle.${table} ${filter}" "TRUNCATE turtle.${table}" "turtle.${table}"
    actual=$(local_query "SELECT count(*) FROM turtle.${table}")
    [ "$actual" = "$expected" ] || die "turtle.${table}: copied ${actual} rows, expected ${expected}"
    # TRUNCATE leaves no dead tuples to vacuum, but the reloaded table has no statistics either.
    local_query "ANALYZE turtle.${table}" >/dev/null
done

log "Done. Local bars now cover $(local_query "SELECT min(date) || ' to ' || max(date) FROM turtle.daily_bars")"
