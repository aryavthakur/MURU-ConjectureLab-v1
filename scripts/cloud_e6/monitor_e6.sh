#!/usr/bin/env bash
# E6 Cloud Execution Monitor
# Reads telemetry and execution progress without exposing blinded outcomes.

set -euo pipefail

MURU_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RESULT_DIR="${MURU_ROOT}/results/e6"

echo "=== MURU E6 Cloud Execution Monitor ==="
echo "Timestamp: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "Host Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "Memory Usage: $(free -h | awk '/^Mem:/{print \"Used: \" $3 \" / \" $2 \" (Free: \" $4 \")\"}')"
echo ""

# Count active worker processes
WORKER_COUNT=$(pgrep -f "e6.*shard" 2>/dev/null | wc -l || echo 0)
echo "Active E6 Worker Processes: ${WORKER_COUNT}"

# Count completed worlds if directory exists
if [ -d "${RESULT_DIR}" ]; then
  COMPLETED_COUNT=$(find "${RESULT_DIR}" -name "*.jsonl" -exec wc -l {} + 2>/dev/null | awk '/total$/{print $1}' || echo 0)
  echo "Completed Output Records: ${COMPLETED_COUNT}"
else
  echo "Result directory ${RESULT_DIR} not yet created."
fi

echo "========================================"
