#!/usr/bin/env bash
# E6 Worker Launch Script (Template/Harness)
# DO NOT EXECUTE UNTIL UPSTREAM SCIENTIFIC AUTHORIZATION IS GIVEN.
#
# This script sets up a supervised, disconnection-resilient execution
# environment for E6 using 8 parallel worker shards.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/env_setup.sh"

N_WORKERS=${1:-8}
LOG_DIR="${MURU_ROOT}/results/e6/logs"
mkdir -p "${LOG_DIR}"

echo "=========================================================="
echo "MURU E6 Cloud Execution Launcher"
echo "Host: $(uname -m), $(nproc) vCPUs, $(free -h | awk '/^Mem:/{print $2}') RAM"
echo "Workers: ${N_WORKERS}"
echo "Log Directory: ${LOG_DIR}"
echo "=========================================================="

# 1. Run Preflight Check
python "${SCRIPT_DIR}/preflight_e6.py"

echo ""
echo "NOTICE: E6 launch script prepared in dry-run/template state."
echo "When scientifically authorized, the execution harness will partition"
echo "the E6 safety opportunities across ${N_WORKERS} worker processes in the background."
echo "=========================================================="
