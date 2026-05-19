#!/bin/bash

# Sovereign Vault Backup Script
# Uses arangodump via Docker to ensure logically consistent snapshots.
# This script sources the root password from .env.sovereign.

# 1. Load Environment Variables
# Assuming the script is run from the project root
ENV_FILE=".env.sovereign"

if [ -f "$ENV_FILE" ]; then
    # Export variables from .env.sovereign, ignoring comments
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo "[ERROR] $ENV_FILE not found. Aborting backup."
    exit 1
fi

# Assign the root password from the environment variable
DB_PASS=${ARANGO_ROOT_PASSWORD}

if [ -z "$DB_PASS" ]; then
    echo "[ERROR] ARANGO_ROOT_PASSWORD not found in $ENV_FILE. Aborting."
    exit 1
fi

# Define backup directory based on timestamp
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_HOST_DIR="$HOME/abraxas_backups/$TIMESTAMP"

echo "[Sovereign Vault] Initiating secure snapshot to $BACKUP_HOST_DIR..."
mkdir -p "$BACKUP_HOST_DIR"

# 2. Perform the dump using a temporary Docker container
# --rm: Remove container after execution
# -v: Map the local backup directory to /dump inside the container
# --network host: Allow the container to reach the running ArangoDB instance on localhost:8529
docker run --rm \
  -v "$BACKUP_HOST_DIR:/dump" \
  --network host \
  arangodb/arangodb \
  arangodump \
  --server.endpoint tcp://localhost:8529 \
  --save-path /dump \
  --root-password "$DB_PASS"

# Check if the docker command succeeded
if [ $? -eq 0 ]; then
    echo "[SUCCESS] Sovereign Vault snapshot complete."
    echo "Backup location: $BACKUP_HOST_DIR"
else
    echo "[FAILURE] ArangoDump failed. Ensure the ArangoDB instance is running on port 8529."
    exit 1
fi
