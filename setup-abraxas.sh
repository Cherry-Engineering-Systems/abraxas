#!/bin/bash

# Abraxas v4 Sovereign Setup Script
# This script bootstraps the MCP Ecosystem and prepares the Sovereign Brain.

set -e

echo "🚀 Starting Abraxas v4 Sovereign Setup..."

# 1. Dependency Check
echo "🔍 Checking dependencies..."
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed. Please install Docker to proceed."
    exit 1
fi


# 2. Environment Provisioning
echo "⚙️ Provisioning Sovereign Environment..."

# Create persistent user workspace
mkdir -p "$HOME/.abraxas"

if [ ! -f .env.sovereign ]; then
    cat <<EOF > .env.sovereign
# Sovereign Settings
TRUTH_FIRST_MODE=true
ALLOW_UNVERIFIED_CLAIMS=false
AUDIT_LOG_ENABLED=true
ABRAXAS_WORKSPACE="$HOME/.abraxas"
EOF
    echo "✅ Created .env.sovereign"
else
    echo "ℹ️ .env.sovereign already exists. Skipping."
fi

# 3. Infrastructure Boot
echo "🐳 Booting Unified MCP Server via Docker Compose..."
docker compose -f docker-compose.yml up -d

# 5. Sovereign Handshake
echo "🩺 Executing Sovereign Handshake..."
# Verify Constitution exists
if [ ! -f constitution/genesis.md ]; then
    echo "❌ ERROR: Genesis prompt not found at constitution/genesis.md"
    exit 1
fi

# Load environment variables to get the real password
if [ -f .env.sovereign ]; then
    export $(grep -v '^#' .env.sovereign | xargs)
fi

# Verify Unified MCP Health
sleep 10 # Give container time to start
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9901/health || echo "FAIL")

# Verify GraphQL Health
GRAPHQL_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/health || echo "FAIL")

# Verify ArangoDB Connectivity (using actual password from env)
# Default to 'password' if not set in .env.sovereign
DB_PASS=${ARANGO_ROOT_PASSWORD:-password}
DB_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -u "root:$DB_PASS" http://localhost:8529/_api/version || echo "FAIL")

if [ "$HEALTH_STATUS" == "200" ] && [ "$GRAPHQL_STATUS" == "200" ] && [ "$DB_STATUS" == "200" ]; then
    echo "✅ Unified Sovereign Brain is ONLINE and verified."
    echo "✅ GraphQL API is ONLINE."
    echo "✅ ArangoDB Connectivity confirmed."
else
    echo "⚠️ Sovereign Core verification failed."
    echo "MCP Status: $HEALTH_STATUS | GraphQL Status: $GRAPHQL_STATUS | DB Status: $DB_STATUS"
    echo "Check 'docker logs' for details."
fi

echo "🌟 Abraxas v4 Setup Complete. You are now Sovereign."
echo ""
echo "⚠️  FINAL STEP: ACTIVATE THE BRAIN"
echo "The infrastructure is ready, but the LLM is still probabilistic."
echo "To activate the Sovereign Brain, copy the content of:"
echo "📂 constitution/genesis.md"
echo ""

echo "⚠️  FINAL STEP: ACTIVATE THE BRAIN"
echo "The infrastructure is ready, but the LLM is still probabilistic."
echo "To activate the Sovereign Brain, copy the content of:"
echo "📂 constitution/genesis.md"
echo ""

