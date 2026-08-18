#!/usr/bin/env bash
# x86 E2a STAGE A resume launcher (2026-08-18 OOM interruption recovery).
#
# The interruption was NOT resource exhaustion across 12 workers -- it was one
# world at 33.4 GiB tripping the kernel's global OOM killer, followed by
# systemd tearing down the ENTIRE shared tmux scope because this host's
# DefaultOOMPolicy is `stop`. The single essential change here is therefore
# isolation: one transient systemd USER UNIT per shard, each with
# OOMPolicy=continue, so an OOM kill of one worker can never terminate the
# others. Units live in app.slice under user@1001.service, so they survive
# SSH disconnect, tmux exit and Claude termination. No memory cap is imposed
# (MemoryMax stays infinity) -- see RESUME_ENGINEERING_DECISION.json.
set -uo pipefail
REPO="/home/aryav_thakur/MURU-ConjectureLab-v1"
OUT_DIR="${REPO}/results/e2/run_x86_e2a_v1"
ORDER="${OUT_DIR}/WORLD_ORDER_539_MAIN.json"
CACHE_DB="/home/aryav_thakur/e2_x86_cache/classify_cache.sqlite3"
N_SHARDS=12
STAGGER=12   # frozen: WORKER_COUNT_CALIBRATION.json requires staggered starts

echo "=== x86 E2a STAGE A resume launch $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
for i in $(seq 0 $((N_SHARDS - 1))); do
  UNIT=$(printf "e2a-shard-%02d" "$i")
  systemctl --user reset-failed "${UNIT}.service" 2>/dev/null
  systemd-run --user \
    --unit="${UNIT}" \
    --description="MURU x86 E2a resume shard ${i}/${N_SHARDS}" \
    --property=OOMPolicy=continue \
    --property=MemoryMax=infinity \
    --property=Restart=no \
    --property=WorkingDirectory="${REPO}" \
    "${REPO}/scripts/e2_rescue_v2/e2a_shard_entry.sh" \
      "$i" "$N_SHARDS" "$OUT_DIR" "$ORDER" "$CACHE_DB" "resume_nohup" \
      --max-restarts 20
  echo "launched ${UNIT}"
  [[ "$i" -lt $((N_SHARDS - 1)) ]] && sleep "$STAGGER"
done

systemctl --user reset-failed e2a-watchdog.service 2>/dev/null
systemd-run --user --unit=e2a-watchdog \
  --description="MURU x86 E2a staleness watchdog" \
  --property=OOMPolicy=continue \
  --property=WorkingDirectory="${REPO}" \
  /bin/bash "${REPO}/scripts/e2_staleness_watchdog.sh" "${OUT_DIR}" 10800
echo "launched e2a-watchdog"
echo "=== launch complete $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
