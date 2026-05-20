#!/bin/bash
set -e

# --- Configuration ---
DB_CONTAINER="arangodb"
DB_NAME="abraxas_db"
DB_PASS="TheBestPassword!"
BACKUP_ROOT="/root/.openclaw/workspace/projects/abraxas/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"
LOG_FILE="$BACKUP_ROOT/backup_log.txt"

# Ensure backup directory exists
mkdir -p "$BACKUP_ROOT"

echo "[$(date)] Starting Sovereign Vault Backup..." >> "$LOG_FILE"

# 1. Create temporary directory inside container for dump
docker exec "$DB_CONTAINER" mkdir -p /backup

# 2. Execute arangodump inside the container
echo "Executing arangodump for $DB_NAME..." >> "$LOG_FILE"
docker exec "$DB_CONTAINER" arangodump \
  --server.database "$DB_NAME" \
  --server.password "$DB_PASS" \
  --output-directory /backup

# 3. Copy the dump from container to host
mkdir -p "$BACKUP_DIR"
echo "Copying dump to host: $BACKUP_DIR" >> "$LOG_FILE"
docker cp "$DB_CONTAINER":/backup "$BACKUP_DIR"

# 4. Compress the backup to save space
cd "$BACKUP_ROOT"
tar -czf "abraxas_vault_$TIMESTAMP.tar.gz" "$TIMESTAMP"
rm -rf "$TIMESTAMP"

# 5. Cleanup container temp dir
docker exec "$DB_CONTAINER" rm -rf /backup

echo "[$(date)] Backup completed successfully: abraxas_vault_$TIMESTAMP.tar.gz" >> "$LOG_FILE"
echo "------------------------------------------------------------" >> "$LOG_FILE"
