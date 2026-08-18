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
  # Discover shard indices dynamically from whichever log_shard_*.txt files
  # actually exist, instead of a hardcoded range. Found live: a hardcoded
  # `for i in 0 1 2` (this script's own earlier version) silently covered
  # only 3 of the 6 shards after the throughput investigation moved to
  # 6-way sharding -- shard 5 sat stuck, alive, and completely unwatched
  # for 6+ hours because its index was simply never in the loop. Globbing
  # the actual log files makes this correct for any shard count, present
  # or future, without needing to keep this script's range in sync by hand.
  for log_path in "${OUT_DIR}"/log_shard_*.txt; do
    [[ -f "$log_path" ]] || continue
    base=$(basename "$log_path")
    idx_str="${base#log_shard_}"
    idx_str="${idx_str%.txt}"
    i=$((10#$idx_str))

    # PORTABILITY FIX (2026-08-18, x86 resume): the original line tried the
    # macOS form `stat -f "%m"` FIRST with a `||` fallback to the GNU form.
    # On Linux `stat -f` is not "format" at all -- it means "report on the
    # FILE SYSTEM" -- so it EXITS 0 while printing a multi-line filesystem
    # block ("  File: ...\n  ID: ...\n ..."). The `||` fallback therefore
    # never fired, $mtime became that block, and `$((now - mtime))` made bash
    # evaluate the bare word `File` as a variable, which under `set -u` aborts
    # the whole watchdog with `line 46: File: unbound variable`. That is
    # exactly how this watchdog died 22 seconds after starting on 2026-08-18
    # at 02:16:37 UTC and stayed dead for the entire x86 E2a run. Try the GNU
    # form first and only fall back to the BSD/macOS form.
    mtime=$(stat -c "%Y" "$log_path" 2>/dev/null || stat -f "%m" "$log_path" 2>/dev/null)
    # Guard against any future non-numeric return rather than trusting it.
    case "$mtime" in (''|*[!0-9]*) log "shard ${i}: could not read a numeric mtime -- skipping"; continue ;; esac
    [[ -z "$mtime" ]] && continue
    age=$((now - mtime))
    if [[ "$age" -gt "$STALE_SECONDS" ]]; then
      # COVERAGE FIX (2026-08-18, x86 resume): this pattern was written for
      # the exhaustive runner `e2_run_shard.py`. Rescue-v2 production runs
      # `e2_rescue_v2/e2_run_shard_lazy.py`, which this literal pattern does
      # NOT match -- so even had the watchdog survived the bug above, it
      # would have found no PID and killed nothing, the same class of silent
      # under-coverage as E2_EXECUTION_DEVIATION.md section 11. Match both.
      pid=$(ps -eo pid,pcpu,command | grep -E "e2_run_shard(_lazy)?\.py --shard-index ${i} " | grep -v grep | sort -k2 -rn | head -1 | awk '{print $1}')
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
