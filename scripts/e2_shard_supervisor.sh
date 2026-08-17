#!/usr/bin/env bash
# Execution-recovery-only orchestration wrapper (see E2_EXECUTION_DEVIATION.md).
# Not part of the frozen scientific pipeline: it never touches which worlds
# get computed or how -- it only restarts e2_run_shard.py if the OS kills it
# out from under us for reasons outside E2's own code (the diagnosed cause of
# shard 0's original silent death: no traceback, no crash report, no
# error-file entry, reproduced live in an isolated single-world re-run of the
# same first-assigned world). e2_run_shard.py's own `_already_done()`
# checkpoint (unmodified) makes a restart resume, not repeat, completed
# worlds -- this script adds nothing beyond "notice it died, try again".
#
# Usage:
#   e2_shard_supervisor.sh <python-bin> <shard-index> <n-shards> <out-dir> \
#       [--only-worlds-file PATH] [--max-restarts N]
set -uo pipefail

PYTHON_BIN="$1"; shift
SHARD_INDEX="$1"; shift
N_SHARDS="$1"; shift
OUT_DIR="$1"; shift

ONLY_WORLDS_FILE=""
MAX_RESTARTS=20
EXTRA_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --only-worlds-file) ONLY_WORLDS_FILE="$2"; shift 2 ;;
    --max-restarts) MAX_RESTARTS="$2"; shift 2 ;;
    *) EXTRA_ARGS+=("$1"); shift ;;
  esac
done

SHARD_TAG=$(printf "%03d" "$SHARD_INDEX")
SUP_LOG="${OUT_DIR}/supervisor_shard_${SHARD_TAG}.log"
LOG_PATH="${OUT_DIR}/log_shard_${SHARD_TAG}.txt"
mkdir -p "$OUT_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$SUP_LOG"; }

ARGS=(scripts/e2_run_shard.py --shard-index "$SHARD_INDEX" --n-shards "$N_SHARDS" --out-dir "$OUT_DIR")
if [[ -n "$ONLY_WORLDS_FILE" ]]; then
  ARGS+=(--only-worlds-file "$ONLY_WORLDS_FILE")
fi
ARGS+=("${EXTRA_ARGS[@]}")

attempt=0
while true; do
  attempt=$((attempt + 1))
  log "attempt ${attempt}/${MAX_RESTARTS}: launching ${PYTHON_BIN} ${ARGS[*]}"
  "$PYTHON_BIN" "${ARGS[@]}"
  exit_code=$?
  log "attempt ${attempt} exited with code ${exit_code}"

  if [[ -f "$LOG_PATH" ]] && tail -1 "$LOG_PATH" | grep -q "shard ${SHARD_INDEX} COMPLETE"; then
    log "shard ${SHARD_INDEX} COMPLETE confirmed in ${LOG_PATH} -- supervisor exiting cleanly"
    exit 0
  fi

  if [[ "$attempt" -ge "$MAX_RESTARTS" ]]; then
    log "reached max restarts (${MAX_RESTARTS}) without a COMPLETE marker -- giving up, needs human attention"
    exit 1
  fi

  log "no COMPLETE marker yet -- restarting (already-done worlds are skipped via the run's own checkpoint)"
  sleep 2
done
