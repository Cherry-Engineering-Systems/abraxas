#!/bin/bash
set -e

# --- Configuration ---
PROJECT_ROOT="/root/.openclaw/workspace/projects/abraxas"
LOG_FILE="$PROJECT_ROOT/scripts/sync_log.txt"

echo "[$(date)] Starting Sovereign Sync..." >> "$LOG_FILE"

# 1. Pull latest from Remote
echo "Pulling latest from GitHub..." >> "$LOG_FILE"
cd "$PROJECT_ROOT"
git pull origin main

# 2. Update Skills (assuming container-based deployment)
echo "Updating containers and rebuilding skills..." >> "$LOG_FILE"
docker compose up -d --build

# 3. Signal the Agent to reload Constitution
# In a real MCP environment, we would call a specific tool. 
# For now, we write a signal file that the agent checks.
echo "SIGNAL: CONSTITUTION_UPDATE_REQUIRED" > "$PROJECT_ROOT/.sync_signal"

echo "[$(date)] Sovereign Sync Complete. Agent notified via .sync_signal." >> "$LOG_FILE"
echo "------------------------------------------------------------" >> "$LOG_FILE"
