#!/usr/bin/env sh
set -eu

BACKUP_DIR="${BACKUP_DIR:-./backups}"
COMPOSE_FILE="${COMPOSE_FILE:-infra/docker-compose.yml}"
VERTICAL_SLICE_SAVE_PATH="${VERTICAL_SLICE_SAVE_PATH:-/app/var/vertical_slice_save.json}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
POSTGRES_OUTPUT="${BACKUP_DIR}/postgres-${TIMESTAMP}.dump"
SAVE_OUTPUT="${BACKUP_DIR}/vertical-slice-save-${TIMESTAMP}.json"

mkdir -p "${BACKUP_DIR}"

docker compose -f "${COMPOSE_FILE}" exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-game}" \
  -d "${POSTGRES_DB:-game}" \
  --format=custom \
  --no-owner > "${POSTGRES_OUTPUT}"

if [ ! -s "${POSTGRES_OUTPUT}" ]; then
  echo "PostgreSQL backup is empty: ${POSTGRES_OUTPUT}" >&2
  exit 1
fi

if docker compose -f "${COMPOSE_FILE}" exec -T backend test -s "${VERTICAL_SLICE_SAVE_PATH}"; then
  docker compose -f "${COMPOSE_FILE}" exec -T backend \
    python -c "from pathlib import Path; print(Path('${VERTICAL_SLICE_SAVE_PATH}').read_text(encoding='utf-8'), end='')" \
    > "${SAVE_OUTPUT}"
  echo "Wrote ${SAVE_OUTPUT}"
else
  echo "No vertical-slice save file found at ${VERTICAL_SLICE_SAVE_PATH}; skipping JSON save backup"
fi

echo "Wrote ${POSTGRES_OUTPUT}"
