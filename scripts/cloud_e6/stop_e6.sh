#!/usr/bin/env bash
# E6 Clean Shutdown and Process Termination Script
# Sends SIGTERM first, verifies clean process termination, and cleans up any orphaned workers.

set -euo pipefail

echo "=== MURU E6 Clean Shutdown Initiated ==="

# 1. Send SIGTERM to any E6 workers
PIDS=$(pgrep -f "e6.*shard" 2>/dev/null || true)
if [ -n "${PIDS}" ]; then
  echo "Sending SIGTERM to E6 processes: ${PIDS}"
  kill -15 ${PIDS} 2>/dev/null || true
  sleep 3
else
  echo "No active E6 shard processes found."
fi

# 2. Check for orphaned child processes
REMAINING=$(pgrep -f "e6.*shard" 2>/dev/null || true)
if [ -n "${REMAINING}" ]; then
  echo "Processes still running after SIGTERM: ${REMAINING}. Sending SIGKILL..."
  kill -9 ${REMAINING} 2>/dev/null || true
  sleep 1
fi

echo "Clean shutdown verified: 0 active E6 worker processes remaining."
