#!/usr/bin/env bash
# E2b held-out replay launcher -- same isolation discipline as the E2a resume.
#
# One transient systemd USER UNIT per shard with OOMPolicy=continue, so an OOM
# kill of one worker cannot tear down the others (the failure mode that cost 11
# healthy E2a shards on 2026-08-18; see INTERRUPTION_FORENSICS.json). Units live
# in app.slice under user@1001.service and therefore survive SSH disconnect,
# tmux exit and Claude termination.
#
# MUST NOT run concurrently with E2a: SIMPLIFY_TIMEOUT is a wall-clock budget,
# so CPU contention can change a scientific label. This script refuses to start
# while any e2a-shard-* unit is still running.
set -uo pipefail
REPO="/home/aryav_thakur/MURU-ConjectureLab-v1"
OUT_DIR="${REPO}/results/e2b_heldout/replay_x86"
N_SHARDS="${1:-12}"
STAGGER=12

live=$(systemctl --user list-units 'e2a-shard-*' --no-legend 2>/dev/null | grep -c running)
if [[ "$live" -gt 0 ]]; then
  echo "REFUSING TO START: ${live} e2a-shard units still running." >&2
  echo "E2b must not contend with E2a for CPU -- SIMPLIFY_TIMEOUT is wall-clock." >&2
  exit 2
fi

mkdir -p "$OUT_DIR"
echo "=== E2b replay launch $(date -u +%Y-%m-%dT%H:%M:%SZ) n_shards=${N_SHARDS} ==="
for i in $(seq 0 $((N_SHARDS - 1))); do
  UNIT=$(printf "e2b-shard-%02d" "$i")
  systemctl --user reset-failed "${UNIT}.service" 2>/dev/null
  systemd-run --user --unit="${UNIT}" \
    --description="MURU E2b held-out replay shard ${i}/${N_SHARDS}" \
    --property=OOMPolicy=continue \
    --property=MemoryMax=infinity \
    --property=Restart=no \
    --property=WorkingDirectory="${REPO}" \
    "${REPO}/scripts/e2_rescue_v2/e2b_shard_entry.sh" "$i" "$N_SHARDS" "$OUT_DIR"
  echo "launched ${UNIT}"
  [[ "$i" -lt $((N_SHARDS - 1)) ]] && sleep "$STAGGER"
done
echo "=== launch complete $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
