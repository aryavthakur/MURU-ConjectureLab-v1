#!/usr/bin/env bash
# Execution-recovery-only orchestration wrapper for the Rescue-v2 LAZY runner.
# Structurally identical to scripts/e2_shard_supervisor.sh (which hardcodes the
# older exhaustive scripts/e2_run_shard.py); this variant launches
# scripts/e2_rescue_v2/e2_run_shard_lazy.py instead. Not part of the frozen
# scientific pipeline: it never touches which worlds get computed or how -- it
# only restarts the shard if the OS kills it. The runner's own _already_done()
# checkpoint makes a restart resume, not repeat, completed worlds.
#
# Usage: e2_shard_supervisor_lazy.sh <python-bin> <shard-index> <n-shards> \
#            <out-dir> <world-order-file> <cache-db> [--max-restarts N]
set -uo pipefail

PYTHON_BIN="$1"; SHARD_INDEX="$2"; N_SHARDS="$3"; OUT_DIR="$4"
WORLD_ORDER="$5"; CACHE_DB="$6"; shift 6
MAX_RESTARTS=20
while [[ $# -gt 0 ]]; do
  case "$1" in
    --max-restarts) MAX_RESTARTS="$2"; shift 2 ;;
    *) shift ;;
  esac
done

SHARD_TAG=$(printf "%03d" "$SHARD_INDEX")
SUP_LOG="${OUT_DIR}/supervisor_shard_${SHARD_TAG}.log"
LOG_PATH="${OUT_DIR}/log_shard_${SHARD_TAG}.txt"
mkdir -p "$OUT_DIR"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$SUP_LOG"; }

ARGS=(scripts/e2_rescue_v2/e2_run_shard_lazy.py
      --shard-index "$SHARD_INDEX" --n-shards "$N_SHARDS" --out-dir "$OUT_DIR"
      --world-order-file "$WORLD_ORDER" --cache-db "$CACHE_DB")

attempt=0
while true; do
  attempt=$((attempt + 1))
  log "attempt ${attempt}/${MAX_RESTARTS}: launching ${PYTHON_BIN} ${ARGS[*]}"
  "$PYTHON_BIN" "${ARGS[@]}"
  exit_code=$?
  log "attempt ${attempt} exited with code ${exit_code}"
  if [[ -f "$LOG_PATH" ]] && tail -1 "$LOG_PATH" | grep -q "shard ${SHARD_INDEX} COMPLETE"; then
    log "shard ${SHARD_INDEX} COMPLETE confirmed -- supervisor exiting cleanly"
    exit 0
  fi
  if [[ "$attempt" -ge "$MAX_RESTARTS" ]]; then
    log "reached max restarts (${MAX_RESTARTS}) without a COMPLETE marker -- giving up, needs human attention"
    exit 1
  fi
  log "no COMPLETE marker yet -- restarting (already-done worlds are skipped via the run's own checkpoint)"
  sleep 2
done
