#!/bin/bash
# Abraxas Health Check — verify the system is running properly
set -e

HEALTH_URL="${ABRAXAS_HEALTH_URL:-http://localhost:9901/health}"

echo "========================================="
echo "  Abraxas System Health Check"
echo "========================================="
echo ""

echo "Checking MCP server health at ${HEALTH_URL}..."
echo ""

RESPONSE=$(curl -sf "${HEALTH_URL}" 2>&1) || {
    echo "  Status: UNREACHABLE"
    echo ""
    echo "  The Abraxas MCP server is not running."
    echo "  Start it with: docker compose up -d"
    echo "========================================="
    exit 1
}

STATUS=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','Unknown'))" 2>/dev/null)
DB=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('db','Unknown'))" 2>/dev/null)
SKILLS=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('skills_count','Unknown'))" 2>/dev/null)
FS=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('filesystem','Unknown'))" 2>/dev/null)

echo "  Status:     ${STATUS}"
echo "  Database:   ${DB}"
echo "  Skills:     ${SKILLS} loaded"
echo "  Filesystem: ${FS}"
echo ""

if [ "${STATUS}" = "Sovereign Mode" ]; then
    echo "  ✓ System is healthy and running in Sovereign Mode."
    echo ""
    echo "  MCP Server:  http://localhost:9900/mcp"
    echo "  Health API:  http://localhost:9901/health"
    echo ""
    echo "  Environment configs available:"
    echo "    - OpenCode:   opencode.json"
    echo "    - Claude Code: .mcp.json"
    echo "    - VSCode:      .vscode/settings.json"
else
    echo "  ⚠ System is in Simulation Mode — limited functionality."
    echo "    Check database connection and skill loading."
fi

echo "========================================="
