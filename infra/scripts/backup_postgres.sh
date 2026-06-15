#!/usr/bin/env sh
set -eu

BACKUP_DIR="${BACKUP_DIR:-./backups}"
COMPOSE_FILE="${COMPOSE_FILE:-infra/docker-compose.yml}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT="${BACKUP_DIR}/postgres-${TIMESTAMP}.dump"

mkdir -p "${BACKUP_DIR}"

docker compose -f "${COMPOSE_FILE}" exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-game}" \
  -d "${POSTGRES_DB:-game}" \
  --format=custom \
  --no-owner \
  --file=- > "${OUTPUT}"

echo "Wrote ${OUTPUT}"
