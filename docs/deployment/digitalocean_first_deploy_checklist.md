# DigitalOcean First Deployment Checklist

Target: DigitalOcean Ubuntu droplet, 2 vCPU, 4GB RAM, 80GB SSD.  
Stack: Docker Compose, FastAPI backend, PostgreSQL, Nginx TLS reverse proxy.  
Goal: first-time deployment of the current vertical slice.

Use this checklist from the repository root unless a command explicitly says otherwise.

If you are starting from your desktop or cleaning a droplet that already has another project on it, read [Desktop Setup and Droplet Fresh-Start Runbook](desktop_and_droplet_fresh_start_runbook.md) first.

## 0. Current deployment constraints

- The stack expects TLS certificates before Nginx can start.
- Use `--env-file infra/.env` with Docker Compose commands from the repo root.
- The backend health check currently verifies liveness via `/health`; it does not yet verify database migration revision.
- The vertical-slice save file is stored at `/app/var/vertical_slice_save.json` inside the backend container.
- PostgreSQL data is persisted in the Docker volume `postgres_data`.
- Vertical-slice JSON save data is persisted in the Docker volume `vertical_slice_saves`.

## 1. Droplet prerequisites

### 1.1 Verify droplet size

- [ ] DigitalOcean droplet has at least:
  - [ ] 2 vCPU
  - [ ] 4GB RAM
  - [ ] 80GB SSD
  - [ ] Ubuntu LTS

Verify:

```bash
nproc
free -h
df -h /
lsb_release -a
```

### 1.2 Update the server

- [ ] System packages updated.
- [ ] Server rebooted if kernel/security updates require it.

```bash
sudo apt update
sudo apt upgrade -y
sudo reboot
```

### 1.3 Install required tools

- [ ] Git installed.
- [ ] Docker installed.
- [ ] Docker Compose plugin installed.
- [ ] Current user can run Docker or you are using `sudo`.

```bash
sudo apt install -y git ca-certificates curl
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
newgrp docker
docker --version
docker compose version
```

### 1.4 Firewall

- [ ] SSH allowed.
- [ ] HTTP allowed for redirect/certificate challenge.
- [ ] HTTPS allowed for game API.
- [ ] PostgreSQL is not publicly exposed.

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
```

Expected:

- `22/tcp` allowed.
- `80/tcp` allowed.
- `443/tcp` allowed.
- No public `5432/tcp` rule.

## 2. DNS prerequisite

- [ ] Domain or subdomain selected, e.g. `api.example.com`.
- [ ] DNS `A` record points to the droplet public IPv4.
- [ ] DNS has propagated before TLS issuance.

Verify:

```bash
dig +short api.example.com
curl -I http://api.example.com
```

Expected:

- `dig` returns the droplet IP.
- `curl` reaches the droplet once Nginx or a temporary challenge server is running.

## 3. Fetch the repository

- [ ] Repository cloned.
- [ ] Correct branch checked out.
- [ ] Working tree clean.

```bash
git clone <repo-url> GameTesting
cd GameTesting
git checkout cursor/brutal-architecture-review-92ee
git status --short --branch
```

For production after merge, use `main` instead of the PR branch.

## 4. Environment variables

### 4.1 Create env file

- [ ] `infra/.env` exists.
- [ ] Values are not copied placeholders.
- [ ] Secrets are long and unique.

```bash
cp infra/.env.example infra/.env
chmod 600 infra/.env
```

Edit:

```bash
nano infra/.env
```

Required values:

```dotenv
POSTGRES_DB=game
POSTGRES_USER=vt_prod_user
POSTGRES_PASSWORD=<long-random-database-password>
VT_ENVIRONMENT=production
VT_DEBUG=false
VT_JWT_SECRET=<long-random-jwt-secret-at-least-32-characters>
HTTP_PORT=80
HTTPS_PORT=443
```

The Docker Compose file sets the vertical-slice save path automatically:

```dotenv
VT_VERTICAL_SLICE_SAVE_PATH=/app/var/vertical_slice_save.json
```

You normally do not need to add this to `infra/.env` unless you are overriding the Compose defaults.

Generate secrets:

```bash
openssl rand -base64 32
openssl rand -base64 48
```

### 4.2 Verify env values

- [ ] `VT_ENVIRONMENT=production`.
- [ ] `VT_DEBUG=false`.
- [ ] `POSTGRES_USER` is not `game` for production.
- [ ] `POSTGRES_PASSWORD` is not empty and does not contain placeholder words.
- [ ] `VT_JWT_SECRET` is at least 32 characters and does not contain placeholder words.

Check without printing secret values:

```bash
set -a
. infra/.env
set +a
test "$VT_ENVIRONMENT" = "production"
test "$VT_DEBUG" = "false"
test "$POSTGRES_USER" != "game"
test ${#POSTGRES_PASSWORD} -ge 16
test ${#VT_JWT_SECRET} -ge 32
```

## 5. TLS/SSL certificates

The Nginx config requires:

```text
infra/certs/fullchain.pem
infra/certs/privkey.pem
```

### 5.1 Create cert directory

```bash
mkdir -p infra/certs
chmod 700 infra/certs
```

### 5.2 Obtain certificates

Option A: use certbot standalone before starting Nginx:

```bash
sudo apt install -y certbot
sudo certbot certonly --standalone -d api.example.com
sudo cp /etc/letsencrypt/live/api.example.com/fullchain.pem infra/certs/fullchain.pem
sudo cp /etc/letsencrypt/live/api.example.com/privkey.pem infra/certs/privkey.pem
sudo chown "$USER":"$USER" infra/certs/fullchain.pem infra/certs/privkey.pem
chmod 600 infra/certs/privkey.pem
```

Option B: copy existing certificate files from your certificate provider:

```bash
cp /path/to/fullchain.pem infra/certs/fullchain.pem
cp /path/to/privkey.pem infra/certs/privkey.pem
chmod 600 infra/certs/privkey.pem
```

### 5.3 Verify certificates

- [ ] Files exist.
- [ ] Private key is not world-readable.
- [ ] Certificate matches domain.

```bash
test -s infra/certs/fullchain.pem
test -s infra/certs/privkey.pem
openssl x509 -in infra/certs/fullchain.pem -noout -subject -issuer -dates
```

## 6. Preflight validation before startup

### 6.1 Validate Docker Compose config

```bash
docker compose --env-file infra/.env -f infra/docker-compose.yml config
```

Expected:

- No missing variable errors.
- Services: `postgres`, `backend`, `nginx`.
- Ports include `80:80` and `443:443`.
- Nginx cert volume maps `./certs` to `/etc/nginx/certs`.
- Backend mounts the named volume `vertical_slice_saves` at `/app/var`.

### 6.2 Build backend image

```bash
docker compose --env-file infra/.env -f infra/docker-compose.yml build backend
```

### 6.3 Run tests on the droplet

Run tests before first startup:

```bash
python3 -m unittest discover backend/tests
```

If Python dependencies are not installed on the host, run tests in a temporary backend container after build:

```bash
docker compose --env-file infra/.env -f infra/docker-compose.yml run --rm backend \
  python -m unittest discover backend/tests
```

## 7. Database startup and migrations

### 7.1 Start PostgreSQL first

```bash
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d postgres
docker compose --env-file infra/.env -f infra/docker-compose.yml ps
```

Verify healthy:

```bash
docker compose --env-file infra/.env -f infra/docker-compose.yml exec postgres \
  pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

### 7.2 Run migrations

Run Alembic migrations before backend startup:

```bash
docker compose --env-file infra/.env -f infra/docker-compose.yml run --rm backend \
  alembic -c backend/alembic.ini upgrade head
```

Verify current migration:

```bash
docker compose --env-file infra/.env -f infra/docker-compose.yml run --rm backend \
  alembic -c backend/alembic.ini current
```

Expected:

- Current revision includes `0001_foundation_schema`.

## 8. Startup order

Use this exact order for first deploy:

1. PostgreSQL
2. Database migrations
3. Backend
4. Nginx
5. Health/API verification
6. Backup verification

Commands:

```bash
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d postgres
docker compose --env-file infra/.env -f infra/docker-compose.yml run --rm backend \
  alembic -c backend/alembic.ini upgrade head
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d backend
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d nginx
docker compose --env-file infra/.env -f infra/docker-compose.yml ps
```

Expected:

- `postgres` is healthy.
- `backend` is healthy.
- `nginx` is running.
- Docker volumes include `postgres_data` and `vertical_slice_saves`.

Verify volumes:

```bash
docker volume ls | grep -E 'postgres_data|vertical_slice_saves'
```

## 9. Service verification

### 9.1 Check container logs

```bash
docker compose --env-file infra/.env -f infra/docker-compose.yml logs --tail=100 postgres
docker compose --env-file infra/.env -f infra/docker-compose.yml logs --tail=100 backend
docker compose --env-file infra/.env -f infra/docker-compose.yml logs --tail=100 nginx
```

Expected:

- No repeated restart loop.
- No Nginx certificate errors.
- No backend production secret validation errors.
- No PostgreSQL authentication errors.

### 9.2 Verify HTTPS

```bash
curl -I https://api.example.com/health
curl -I http://api.example.com/health
```

Expected:

- HTTPS returns `200`.
- HTTP returns redirect to HTTPS.
- Response includes security headers such as `Strict-Transport-Security`.

### 9.3 Verify API metadata

```bash
curl https://api.example.com/api/v1/server-info
curl https://api.example.com/api/v1/content/manifest
```

Expected:

- Server info returns API and content manifest versions.
- Content manifest returns entries for the starter content.

## 10. Vertical-slice smoke test

Replace `api.example.com` with your domain.

### 10.1 Register

```bash
curl -s https://api.example.com/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"first-player@example.com","display_name":"FirstPlayer","password":"safe-password"}'
```

Save the `access_token` and `account.id`.

### 10.2 Create character

```bash
TOKEN='<access-token>'
curl -s https://api.example.com/api/v1/characters \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Ari"}'
```

Save the character `id`.

### 10.3 Enter world

```bash
CHARACTER_ID='<character-id>'
curl -s https://api.example.com/api/v1/world/characters/$CHARACTER_ID \
  -H "Authorization: Bearer $TOKEN"
```

Expected:

- `current_zone_key` is `dawnreef_atoll`.
- `known_spells` includes `glimmer_spark`, `root_snare`, `tide_mend`.

### 10.4 Accept quest

```bash
curl -s -X POST https://api.example.com/api/v1/world/characters/$CHARACTER_ID/quests/lantern_well_first_light/accept \
  -H "Authorization: Bearer $TOKEN"
```

### 10.5 Fight enemy

```bash
curl -s -X POST https://api.example.com/api/v1/world/characters/$CHARACTER_ID/combat/fight \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"enemy_key":"fog_thorn_lurker","spell_key":"root_snare"}'
```

Expected:

- `victory` is `true`.
- `experience_gained` is `100`.
- Character level becomes `2`.
- Quest is completed.
- Inventory contains `sunthread_bandage`.
- Wallet contains `shell_chits`.

### 10.6 Save and logout

```bash
curl -s -X POST https://api.example.com/api/v1/world/characters/$CHARACTER_ID/save \
  -H "Authorization: Bearer $TOKEN"
curl -s -X POST https://api.example.com/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

### 10.7 Login again and verify persistence

```bash
curl -s https://api.example.com/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"first-player@example.com","password":"safe-password"}'
```

Use the new token:

```bash
TOKEN='<new-access-token>'
curl -s https://api.example.com/api/v1/world/characters/$CHARACTER_ID \
  -H "Authorization: Bearer $TOKEN"
```

Expected:

- Level remains `2`.
- XP remains `100`.
- Quest remains completed.
- Inventory and wallet rewards persist.

## 11. Backup configuration

### 11.1 Create backup directory

```bash
mkdir -p backups
chmod 700 backups
```

### 11.2 Run backup

The backup script writes:

- A PostgreSQL dump: `postgres-YYYYMMDDTHHMMSSZ.dump`
- A vertical-slice JSON save copy: `vertical-slice-save-YYYYMMDDTHHMMSSZ.json`

The JSON save backup is skipped if no player save file exists yet.

The backup script reads `POSTGRES_USER` and `POSTGRES_DB` from the shell, so export env first:

```bash
set -a
. infra/.env
set +a
BACKUP_DIR=./backups COMPOSE_FILE=infra/docker-compose.yml infra/scripts/backup_postgres.sh
```

Verify:

```bash
ls -lh backups/
```

Expected:

- A file named like `postgres-YYYYMMDDTHHMMSSZ.dump`.
- File size is greater than zero.
- After the vertical-slice smoke test has created progress, a file named like `vertical-slice-save-YYYYMMDDTHHMMSSZ.json`.

### 11.3 Verify backup integrity

```bash
docker compose --env-file infra/.env -f infra/docker-compose.yml exec -T postgres \
  pg_restore --list < "$(ls -t backups/postgres-*.dump | head -n 1)" >/tmp/latest-backup-list.txt
test -s /tmp/latest-backup-list.txt
```

After the vertical-slice smoke test, verify the JSON save backup:

```bash
latest_save="$(ls -t backups/vertical-slice-save-*.json | head -n 1)"
test -s "$latest_save"
python3 -m json.tool "$latest_save" >/tmp/latest-save-check.json
```

### 11.4 Schedule backups

- [ ] Add a cron job for nightly backups.
- [ ] Copy encrypted backups off the droplet if this becomes a public test.
- [ ] Periodically test restore on a separate database.

Example cron:

```bash
crontab -e
```

Add:

```cron
15 3 * * * cd /path/to/GameTesting && set -a && . infra/.env && set +a && BACKUP_DIR=./backups COMPOSE_FILE=infra/docker-compose.yml infra/scripts/backup_postgres.sh >> backups/backup.log 2>&1
```

## 12. Restart and update procedure

For future deploys:

```bash
git pull
docker compose --env-file infra/.env -f infra/docker-compose.yml build backend
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d postgres
docker compose --env-file infra/.env -f infra/docker-compose.yml run --rm backend \
  alembic -c backend/alembic.ini upgrade head
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d backend nginx
docker compose --env-file infra/.env -f infra/docker-compose.yml ps
```

## 13. Rollback checklist

If deployment fails:

- [ ] Capture logs before changing anything.
- [ ] Stop backend and Nginx, leave PostgreSQL running unless data corruption is suspected.
- [ ] Check Nginx cert files.
- [ ] Check `infra/.env` values.
- [ ] Check migration status.
- [ ] Restore previous Git commit if needed.

Commands:

```bash
docker compose --env-file infra/.env -f infra/docker-compose.yml logs --tail=200 > deploy-failure.log
docker compose --env-file infra/.env -f infra/docker-compose.yml stop nginx backend
git log --oneline -5
git checkout <previous-known-good-commit>
docker compose --env-file infra/.env -f infra/docker-compose.yml build backend
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d backend nginx
```

## 14. Final first-deploy signoff

- [ ] Droplet resources verified.
- [ ] Firewall allows only SSH, HTTP, HTTPS.
- [ ] DNS points to droplet.
- [ ] `infra/.env` exists with production-safe values.
- [ ] TLS cert and key exist under `infra/certs/`.
- [ ] Docker Compose config renders successfully.
- [ ] PostgreSQL starts and is healthy.
- [ ] Alembic migration is at head.
- [ ] Backend starts and is healthy.
- [ ] Nginx starts with TLS.
- [ ] HTTP redirects to HTTPS.
- [ ] `/health` returns 200 over HTTPS.
- [ ] `/api/v1/server-info` works.
- [ ] `/api/v1/content/manifest` works.
- [ ] Vertical-slice smoke test passes.
- [ ] Backup file is created.
- [ ] Backup dump can be listed with `pg_restore --list`.
- [ ] Vertical-slice JSON save backup is created after smoke-test progress exists.
- [ ] Backup schedule is configured.
