# Desktop Setup and Droplet Fresh-Start Runbook

This guide is for a first-time setup when you are new to the tooling and want to:

1. Prepare your desktop/laptop for development.
2. Clean an existing DigitalOcean droplet so this project can deploy from scratch.
3. Build/run the backend and open the Godot project.

This runbook does not replace the deployment checklist. Use it first, then continue with:

- [DigitalOcean first deployment checklist](digitalocean_first_deploy_checklist.md)

## 0. Important safety rules

- Do not delete anything on the droplet until you know whether the current project has data you need.
- Docker volumes often contain databases and uploads. Removing volumes is permanent.
- If unsure, take a DigitalOcean snapshot before wiping.
- Run destructive commands only after reading their "What this deletes" note.

## 1. Desktop setup

Choose the section for your operating system.

### 1.1 Windows desktop

Install:

- [ ] Git for Windows
- [ ] Docker Desktop
- [ ] Godot 4.x
- [ ] Visual Studio Code or Cursor
- [ ] Android Studio, if you want Android exports

Recommended install order:

1. Install Git for Windows.
2. Install Docker Desktop.
3. Reboot if Docker asks.
4. Install Godot 4.x.
5. Install Android Studio only when you are ready for Android builds.

Verify in PowerShell:

```powershell
git --version
docker --version
docker compose version
```

Clone the repo:

```powershell
git clone <repo-url> GameTesting
cd GameTesting
git checkout cursor/brutal-architecture-review-92ee
```

### 1.2 macOS desktop

Install:

- [ ] Xcode command line tools
- [ ] Git
- [ ] Docker Desktop
- [ ] Godot 4.x
- [ ] Android Studio, if you want Android exports

Commands:

```bash
xcode-select --install
git --version
docker --version
docker compose version
```

Clone the repo:

```bash
git clone <repo-url> GameTesting
cd GameTesting
git checkout cursor/brutal-architecture-review-92ee
```

### 1.3 Linux desktop

Install:

- [ ] Git
- [ ] Docker Engine
- [ ] Docker Compose plugin
- [ ] Godot 4.x
- [ ] Android Studio or Android command-line tools, if you want Android exports

Ubuntu commands:

```bash
sudo apt update
sudo apt install -y git ca-certificates curl
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
newgrp docker
docker --version
docker compose version
```

Clone the repo:

```bash
git clone <repo-url> GameTesting
cd GameTesting
git checkout cursor/brutal-architecture-review-92ee
```

## 2. Desktop: run backend tests locally

From the repo root:

```bash
python3 -m unittest discover backend/tests
```

If Python dependencies are missing locally, build and test inside Docker instead:

```bash
cp infra/.env.example infra/.env
```

Edit `infra/.env` for local development:

```dotenv
POSTGRES_DB=game
POSTGRES_USER=game
POSTGRES_PASSWORD=local_dev_database_password
VT_ENVIRONMENT=local
VT_DEBUG=true
VT_JWT_SECRET=local-development-jwt-secret-at-least-32-characters
HTTP_PORT=80
HTTPS_PORT=443
```

Then run:

```bash
docker compose --env-file infra/.env -f infra/docker-compose.yml build backend
docker compose --env-file infra/.env -f infra/docker-compose.yml run --rm backend \
  python -m unittest discover backend/tests
```

## 3. Desktop: open the Godot project

Current status:

- The Godot project is a scaffold.
- The backend vertical slice is functional through API endpoints.
- Full playable 3D UI scenes are not implemented yet.

Open Godot:

1. Launch Godot 4.x.
2. Click **Import**.
3. Select `godot_project/project.godot`.
4. Open the project.

Check project settings:

- Rendering method should be mobile.
- `ApiClient` should appear as an autoload.

For local API testing from Godot:

- Editor-local `http://localhost` or `http://127.0.0.1` is allowed.
- Non-editor/mobile builds must use HTTPS.

## 4. Desktop: Android export preparation

Only do this when you are ready to test Android builds.

Install:

- [ ] Android Studio
- [ ] Android SDK
- [ ] Android build tools
- [ ] OpenJDK/JDK supported by Godot 4.x
- [ ] Godot Android export templates

In Godot:

1. Open **Editor > Manage Export Templates**.
2. Download/install templates for your Godot version.
3. Open **Editor Settings > Export > Android**.
4. Set Android SDK path.
5. Set Java/JDK path.
6. Create an Android export preset.

Do not worry about this for backend deployment.

## 5. Droplet: identify existing project before wiping

SSH into the droplet:

```bash
ssh root@YOUR_DROPLET_IP
```

or:

```bash
ssh YOUR_USER@YOUR_DROPLET_IP
```

Check what is running:

```bash
docker ps
docker ps -a
docker volume ls
sudo ss -tulpn | grep -E ':80|:443|:5432' || true
pwd
ls
```

If the old project uses Docker Compose, find it:

```bash
sudo find / -name docker-compose.yml -o -name compose.yml 2>/dev/null
```

Read the output carefully. Look for old project directories such as:

- `/root/<project>`
- `/home/<user>/<project>`
- `/opt/<project>`
- `/var/www/<project>`

## 6. Droplet: backup before wiping

If you might need the old project, take at least one backup.

### 6.1 Best safety option: DigitalOcean snapshot

In the DigitalOcean dashboard:

1. Power off the droplet if possible.
2. Create a snapshot.
3. Wait until it completes.

This is the safest beginner option.

### 6.2 Quick Docker inventory backup

This does not back up data by itself, but records what existed:

```bash
mkdir -p ~/pre-wipe-inventory
docker ps -a > ~/pre-wipe-inventory/docker-containers.txt
docker volume ls > ~/pre-wipe-inventory/docker-volumes.txt
docker network ls > ~/pre-wipe-inventory/docker-networks.txt
sudo ss -tulpn > ~/pre-wipe-inventory/listening-ports.txt
```

If the old project has a database, export it according to that project's docs before removing volumes.

## 7. Droplet wipe options

Choose one option.

### Option A: safest clean slate - rebuild the droplet

Use this if you do not need anything from the old droplet.

In DigitalOcean:

1. Snapshot first if you want a rollback point.
2. Destroy the old droplet or rebuild it with Ubuntu LTS.
3. Create/use a fresh SSH key.
4. Continue with the DigitalOcean first deployment checklist.

This avoids hidden old containers, ports, files, cron jobs, and volumes.

### Option B: wipe only old Docker resources

Use this if you want to keep the same droplet.

What this deletes:

- Docker containers.
- Docker networks not in use.
- Docker images.
- Docker volumes only if you run the volume removal command.

Stop existing containers:

```bash
docker stop $(docker ps -q) 2>/dev/null || true
```

Remove stopped containers:

```bash
docker rm $(docker ps -aq) 2>/dev/null || true
```

Remove unused Docker networks/images/build cache:

```bash
docker system prune -a
```

Only if you are absolutely sure old data is not needed, remove old volumes:

```bash
docker volume ls
```

Then remove specific old volumes by name:

```bash
docker volume rm OLD_VOLUME_NAME
```

Avoid this beginner-dangerous command unless you are certain:

```bash
docker system prune -a --volumes
```

### Option C: wipe old project files only

Use this if the old app was not Docker-based or if Docker has already been cleaned.

Find old project directories:

```bash
ls /root
ls /home
ls /opt
ls /var/www
```

Remove only directories you recognize as old and backed up:

```bash
rm -rf /path/to/old-project
```

Do not delete system directories.

## 8. Droplet: verify ports are free

Before starting this project:

```bash
sudo ss -tulpn | grep -E ':80|:443' || true
```

Expected before this project starts:

- Nothing should be listening on 80.
- Nothing should be listening on 443.

If something is still using those ports, stop/remove that service before continuing.

## 9. Droplet: install fresh prerequisites

```bash
sudo apt update
sudo apt install -y git ca-certificates curl dnsutils openssl
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
newgrp docker
docker --version
docker compose version
```

Firewall:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
```

## 10. Droplet: clone this project fresh

Choose a standard location:

```bash
mkdir -p ~/apps
cd ~/apps
git clone <repo-url> GameTesting
cd GameTesting
git checkout cursor/brutal-architecture-review-92ee
```

After PR merge, use `main` instead:

```bash
git checkout main
```

## 11. Droplet: continue with first deployment checklist

Now follow:

```text
docs/deployment/digitalocean_first_deploy_checklist.md
```

Minimum order:

1. Configure DNS.
2. Create `infra/.env`.
3. Add TLS cert files to `infra/certs`.
4. Build backend.
5. Start PostgreSQL.
6. Run migrations.
7. Start backend.
8. Start Nginx.
9. Run vertical-slice smoke test.
10. Run backup and verify both DB dump and JSON save backup.

## 12. If something goes wrong

Check containers:

```bash
docker compose --env-file infra/.env -f infra/docker-compose.yml ps
```

Check logs:

```bash
docker compose --env-file infra/.env -f infra/docker-compose.yml logs --tail=100 postgres
docker compose --env-file infra/.env -f infra/docker-compose.yml logs --tail=100 backend
docker compose --env-file infra/.env -f infra/docker-compose.yml logs --tail=100 nginx
```

Common causes:

- Port 80/443 already in use.
- Missing TLS files.
- `POSTGRES_USER=game` while `VT_ENVIRONMENT=production`.
- JWT secret too short or placeholder-like.
- Forgot `--env-file infra/.env`.
- DNS not pointing to the droplet.
- Certbot standalone failed because port 80 was occupied.

## 13. What I would do in your position

If the old droplet project is not important:

1. Snapshot the droplet in DigitalOcean.
2. Rebuild or recreate the droplet with fresh Ubuntu LTS.
3. Install Git/Docker.
4. Clone this repo.
5. Follow the DigitalOcean first deployment checklist.

If the old project might matter:

1. Snapshot the droplet.
2. Inventory Docker containers/volumes.
3. Back up old databases/uploads.
4. Stop old containers.
5. Free ports 80/443.
6. Deploy this project.
