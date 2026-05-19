#!/bin/bash

# Abraxas v4.6 Sovereign E2E Test Suite
# This script stands up a temporary test environment, runs the test runner, 
# and then tears down the environment.

echo "--- [Sovereign E2E Test Suite] ---"
echo "Initializing test environment..."

# 1. Stand up the test stack
docker compose -f docker-compose.test.yml up --build -d

echo "Waiting for MCP Server and ArangoDB to stabilize..."
sleep 15

# 2. Execute the test runner
echo "Running Pytest suite..."
docker logs -f abraxas-test-runner

# Capture the exit code of the test runner
EXIT_CODE=$(docker inspect abraxas-test-runner --format='{{.State.ExitCode}}')

# 3. Cleanup
echo "Tearing down test environment..."
docker compose -f docker-compose.test.yml down -v

if [ "$EXIT_CODE" -eq 0 ]; then
    echo "✅ ALL SOVEREIGN TESTS PASSED"
else
    echo "❌ TEST SUITE FAILED (Exit Code: $EXIT_CODE)"
    exit 1
fi
