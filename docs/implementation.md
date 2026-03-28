# Hetzner VPS Deployment Guide

## Context

turtle-backtest runs locally today. This guide covers moving it to a Hetzner VPS so the database and scheduled jobs persist without a local machine, and the Streamlit UI is optionally accessible remotely.

**Services required:**
- PostgreSQL 17 (primary data store, ~1–2GB of OHLCV data)
- Python 3.13 runtime with `uv`
- Outbound HTTPS to `eodhd.com` for data downloads
- Optional: Streamlit dashboard on port 8501
- Scheduled daily data downloads

---

## Decision Points

### 1. Server Size

| Option | Specs | Cost ~EUR/mo | Notes |
|--------|-------|-------------|-------|
| CX22 | 2 vCPU, 4GB RAM, 40GB SSD | ~4.35 | Minimum viable — tight under load |
| **CX32** | **4 vCPU, 8GB RAM, 80GB SSD** | **~8.35** | **Recommended** |
| CAX21 (ARM) | 2 vCPU, 4GB RAM, 40GB SSD | ~4.35 | Cheaper ARM; psycopg binary wheels may need rebuilding |

**Recommended: CX32** — pandas portfolio backtests are memory-heavy; 4GB RAM is tight.

### 2. PostgreSQL Deployment

| Option | Pros | Cons |
|--------|------|------|
| **Native PostgreSQL 17** | Best perf, no Docker overhead, systemd-native | Manual install steps |
| Docker Compose (same as local) | Identical to dev, easy config | Docker overhead |
| Hetzner Managed Databases | Automated backups, HA | ~€20+/mo, overkill for solo use |

**Recommended: Native PostgreSQL 17.** Alternative: keep Docker Compose if you prefer parity with local — zero behaviour difference.

### 3. Streamlit UI Access

| Option | Pros | Cons |
|--------|------|------|
| SSH tunnel only | Zero exposure, free | Must have SSH session open |
| **Tailscale** | Private network, no open ports, free | Requires Tailscale on client machines |
| nginx + Let's Encrypt TLS | Secure, persistent browser access | Needs a domain name |
| Cloudflare Tunnel | No open ports, free tier | Adds Cloudflare dependency |

**Recommended: Tailscale** for personal use (zero attack surface). Use **nginx + Let's Encrypt** if you need to share access with others.

### 4. Scheduled Tasks

| Option | Pros | Cons |
|--------|------|------|
| **systemd timers** | Native, journald logging, retry logic | Slightly more setup than cron |
| cron | Simple, universal | No built-in failure notifications |
| GitHub Actions scheduled | Runs on GitHub infra | Needs self-hosted runner or SSH deploy action |

**Recommended: systemd timers** — pairs with `journalctl` for log review.

### 5. Secrets Management

| Option | Pros | Cons |
|--------|------|------|
| `.env` file (chmod 600) | Simple, existing pattern | Plaintext on disk |
| **systemd EnvironmentFile** | Per-service, not in project directory | Slightly more config |

**Recommended: systemd EnvironmentFile** at `/etc/turtle-backtest/secrets.env` (chmod 600, owned by app user).

### 6. Data Migration (local → VPS)

| Option | Pros | Cons |
|--------|------|------|
| pg_dump → pg_restore | Fast, exact copy | Requires local DB to be running |
| **Re-download from EODHD** | Clean slate | Uses API quota, slow for large datasets |
| rsync data directory | Raw copy | Risky if PostgreSQL minor versions differ |

**Recommended: Re-download from EODHD**

### 7. Backups

| Option | Pros | Cons |
|--------|------|------|
| **pg_dump → Hetzner Object Storage** | DB-level, point-in-time, S3-compatible | Needs `rclone` setup |
| Hetzner Server Snapshots | Whole-server, one click | ~€0.01/GB/mo |

**Recommended: Daily pg_dump → Hetzner Object Storage** (~€0.023/GB/mo). Weekly Hetzner Server Snapshots as a safety net.

### 8. Code Deployment

| Option | Pros | Cons |
|--------|------|------|
| **git pull** | Simple, version-controlled | Manual pull after each push |
| GitHub Actions CD (SSH deploy) | Automated | More setup |

**Recommended: git pull** for now. Add GitHub Actions CD later if needed.

---

## Estimated Costs (EUR/mo)

| Item | Cost |
|------|------|
| CX32 VPS | ~8.35 |
| Hetzner Object Storage (1GB) | ~0.02 |
| Server Snapshots (weekly) | ~0.50 |
| **Total** | **~9/mo** |

---

## Implementation

### Phase 1: VPS Provisioning

1. Create a **CX32** server in Hetzner Cloud — **Ubuntu 24.04 LTS**
2. Add your SSH public key during creation
3. Assign a Hetzner Firewall:
   - Allow TCP 22 (SSH) from your IP only
   - Allow TCP 8501 (Streamlit) only if NOT using Tailscale
   - Block all else inbound
4. (Optional) Install Tailscale:
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   tailscale up
   ```

### Phase 2: Server Setup

```bash
# As root — create app user
adduser turtle
usermod -aG sudo turtle

# Switch to turtle user for the rest
su - turtle

# Install uv and Python 3.13
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.13

# Install PostgreSQL 17
sudo apt install -y curl ca-certificates
sudo install -d /usr/share/postgresql-common/pgdg
sudo curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc
sudo sh -c 'echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
sudo apt update
sudo apt install -y postgresql-17
sudo systemctl enable --now postgresql

# Clone the repo
git clone https://github.com/jaaknt/turtle-backtest.git ~/turtle-backtest
cd ~/turtle-backtest


# Run the init script manually (docker-compose is not involved on VPS)
export POSTGRES_USER=postgres
export POSTGRES_DB=postgres
export POSTGRES_PASSWORD=<postgres_password>
export DB_ALEMBIC_PASSWORD=<alembic_password>
export DB_APP_PASSWORD=<app_password>
export DB_CLAUDE_PASSWORD=<claude_password>
sudo -E -u postgres bash ./db/init.sh

# Set user postgres password <optonal>
sudo -u postgres psql
\password postgres
<postgres_password>
```

#### Allow access to database from external the Tailscale IP  
```bash
# Find your Tailscale IP
tailscale ip -4 

# Edit postgresql.conf:
sudo vi /etc/postgresql/17/main/postgresql.conf
listen_addresses = 'localhost,100.x.x.x'   # your tailscale IP

# Edit pg_hba.conf:
sudo vi /etc/postgresql/17/main/pg_hba.conf
host    all    all    100.64.0.0/10    scram-sha-256

# restart database
sudo systemctl restart postgresql

```
### Phase 3: Application Deployment

```bash
# Create secrets file
sudo mkdir /etc/turtle-backtest
sudo tee /etc/turtle-backtest/secrets.env <<EOF
DB_APP_PASSWORD=<app_password>
DB_ALEMBIC_PASSWORD=<alembic_password>
EODHD_API_KEY=<api_key>
EOF
sudo chmod 600 /etc/turtle-backtest/secrets.env
sudo chown turtle:turtle /etc/turtle-backtest/secrets.env
# add to current environment
set -a && source /etc/turtle-backtest/secrets.env && set +a

# Install dependencies and apply migrations
source /etc/turtle-backtest/secrets.env
uv sync
uv run alembic upgrade head
```

No changes to `config/settings.toml` required — the app already reads `DB_PASSWORD` and `EODHD_API_KEY` from environment variables.

### Phase 4: Data Migration

```bash
# On your LOCAL machine:
pg_dump -h localhost -U postgres trading | gzip > trading_backup.sql.gz
scp trading_backup.sql.gz turtle@<vps-ip>:~/

# On the VPS:
gunzip -c ~/trading_backup.sql.gz | psql -h 127.0.0.1 -U postgres trading
```

Alternatively, skip migration and re-download fresh data from EODHD:
```bash
uv run python scripts/download_eodhd_data.py --data exchange
uv run python scripts/download_eodhd_data.py --data us_ticker
uv run python scripts/download_eodhd_data.py --data company

# set active group that is needed for stocks history download
PGPASSWORD=$DB_APP_PASSWORD psql -h localhost -p 5432 -U app_user -d trading -f examples/active_symbol_goup_setup.sql

uv run python scripts/download_eodhd_data.py --data history 
```

### Phase 5: Systemd Services

**Daily data download — `/etc/systemd/system/turtle-download.service`:**
```ini
[Unit]
Description=Turtle EODHD Data Download
After=network.target postgresql.service

[Service]
Type=oneshot
User=turtle
WorkingDirectory=/home/turtle/turtle-backtest
EnvironmentFile=/etc/turtle-backtest/secrets.env
ExecStart=/home/turtle/.local/bin/uv run python scripts/download_eodhd_data.py --data history
```

**Timer — `/etc/systemd/system/turtle-download.timer`:**
```ini
[Unit]
Description=Daily EODHD Download

[Timer]
OnCalendar=*-*-* 21:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now turtle-download.timer
```

**Optional — Streamlit UI — `/etc/systemd/system/turtle-ui.service`:**
```ini
[Unit]
Description=Turtle Backtest Streamlit UI
After=postgresql.service

[Service]
User=turtle
WorkingDirectory=/home/turtle/turtle-backtest
EnvironmentFile=/etc/turtle-backtest/secrets.env
ExecStart=/home/turtle/.local/bin/uv run streamlit run app.py --server.port 8501 --server.address 127.0.0.1
Restart=always
```

```bash
sudo systemctl enable --now turtle-ui.service
```

Access via SSH tunnel: `ssh -L 8501:127.0.0.1:8501 turtle@<vps-ip>` then open `http://localhost:8501`.

### Phase 6: Backups

```bash
# Install rclone and configure Hetzner Object Storage (S3-compatible endpoint)
sudo apt install -y rclone
rclone config  # add "hetzner" remote using S3 provider + Hetzner credentials

# Backup service — /etc/systemd/system/turtle-backup.service
```
```ini
[Unit]
Description=Turtle Database Backup

[Service]
Type=oneshot
User=turtle
ExecStart=/bin/bash -c 'pg_dump -U postgres trading | gzip | rclone rcat hetzner:turtle-backups/trading_$(date +%%Y%%m%%d).sql.gz'
```

```bash
# Daily at 02:00 — /etc/systemd/system/turtle-backup.timer
```
```ini
[Unit]
Description=Daily Database Backup

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

### Phase 7: nginx + TLS (only if exposing Streamlit publicly)

```bash
sudo apt install -y nginx certbot python3-certbot-nginx

# /etc/nginx/sites-available/turtle
# server {
#     listen 80;
#     server_name <your-domain>;
#     location / { proxy_pass http://127.0.0.1:8501; }
# }

sudo certbot --nginx -d <your-domain>
```

---

## Verification

```bash
# 1. Confirm signals generate correctly
uv run python scripts/signal_runner.py --start-date 2024-01-01 --end-date 2024-01-02 --mode analyze

# 2. Confirm portfolio backtest runs end-to-end
uv run python scripts/portfolio_runner.py --start-date 2024-01-01 --end-date 2024-01-31 --output-file /tmp/test.html

# 3. Check timer is registered
systemctl list-timers turtle-download.timer

# 4. Review logs after first timer run
journalctl -u turtle-download.service

# 5. Streamlit (via SSH tunnel)
ssh -L 8501:127.0.0.1:8501 turtle@<vps-ip>
# open http://localhost:8501
```
