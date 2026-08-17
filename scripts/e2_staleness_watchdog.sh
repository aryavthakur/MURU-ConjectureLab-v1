#!/usr/bin/env bash
# Execution-recovery-only orchestration wrapper (see E2_EXECUTION_DEVIATION.md).
# e2_shard_supervisor.sh restarts a shard when its process DIES, but does
# nothing if a shard's process stays alive while making no progress -- a
# hang, not a death (this is exactly what the original shard 2 did for
# 6.5+ hours before this rescue). This watchdog closes that gap: if a
# shard's log file goes stale (no new completed-world line) for longer than
# any legitimately observed single-world wall time, it SIGKILLs that
# shard's current process. e2_shard_supervisor.sh sees that as an ordinary
# death and restarts it from the run's own checkpoint, same as any other
# kill. STALE_SECONDS is set well above the largest wall time ever observed
# in this run's own logs (~7305s / ~122min) to avoid killing legitimately
# slow worlds.
#
# Usage: e2_staleness_watchdog.sh <out-dir> [STALE_SECONDS]
set -uo pipefail

OUT_DIR="$1"
STALE_SECONDS="${2:-10800}"  # 3 hours, default
POLL_SECONDS=300

WATCHDOG_LOG="${OUT_DIR}/staleness_watchdog.log"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$WATCHDOG_LOG"; }

log "watchdog started: out_dir=${OUT_DIR} stale_seconds=${STALE_SECONDS} poll_seconds=${POLL_SECONDS}"

while true; do
  now=$(date +%s)
  for i in 0 1 2; do
    log_path="${OUT_DIR}/log_shard_00${i}.txt"
    [[ -f "$log_path" ]] || continue
    mtime=$(stat -f "%m" "$log_path" 2>/dev/null || stat -c "%Y" "$log_path" 2>/dev/null)
    [[ -z "$mtime" ]] && continue
    age=$((now - mtime))
    if [[ "$age" -gt "$STALE_SECONDS" ]]; then
      pid=$(ps -eo pid,pcpu,command | grep "e2_run_shard.py --shard-index ${i} " | grep -v grep | sort -k2 -rn | head -1 | awk '{print $1}')
      if [[ -n "$pid" ]]; then
        log "shard ${i} log stale for ${age}s (>${STALE_SECONDS}s) -- killing PID ${pid} (supervisor will restart from checkpoint)"
        kill -9 "$pid" 2>>"$WATCHDOG_LOG"
      else
        log "shard ${i} log stale for ${age}s but no live e2_run_shard.py process found (already dead / mid-restart)"
      fi
    fi
  done
  sleep "$POLL_SECONDS"
done
