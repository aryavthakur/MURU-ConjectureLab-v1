#!/usr/bin/env bash
# Passive progress recorder. Runs in its OWN systemd unit and only ever READS
# (counts completed world records, samples RSS). It never signals, kills, or
# owns any shard process -- so it cannot terminate the run it observes.
set -uo pipefail
OUT_DIR="$1"; INTERVAL="${2:-300}"
REC="${OUT_DIR}/RESUME_PROGRESS.log"
while true; do
  n=$(cat "${OUT_DIR}"/worlds_shard_*.jsonl 2>/dev/null | grep -c . || echo 0)
  live=$(ps -eo args | grep -c '[e]2_run_shard_lazy.py --shard-index' || true)
  maxrss=$(ps -eo rss,args | grep '[e]2_run_shard_lazy.py --shard-index' | sort -rn | head -1 | awk '{printf "%.2f",$1/1048576}')
  mem=$(free -g | awk '/^Mem:/{print $3"/"$2"GiB used"}')
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] completed=${n}/540 live_workers=${live} max_worker_rss=${maxrss}GiB host_mem=${mem}" >> "$REC"
  sleep "$INTERVAL"
done
