#!/usr/bin/env bash
# STAGE B: the single world held back from the Stage A resume,
# V2C|E2|mass_power|c_low|n_default|r000 -- the world in flight on shard 0 when
# the kernel OOM killer fired at 03:11:34Z with that process at 33.4 GiB.
#
# It runs ALONE, after Stage A, in its own unit and its own output directory,
# following the E2_EXECUTION_DEVIATION.md section 13 precedent. Running it while
# other shards are live would put the host under memory pressure and inflate
# their wall-clock -- and SIMPLIFY_TIMEOUT is a wall-clock budget, so that could
# manufacture timeout verdicts in innocent worlds. Hence the hard guard below.
#
# This is NOT a poison declaration. The world is computed in full under
# identical frozen definitions, with the SAME seeds (world_ordinal is a pure
# function of world identity, so holding it out changed nothing), the SAME
# classify cache, and the SAME 5s SIMPLIFY_TIMEOUT. Only its scheduling differs.
set -uo pipefail
REPO="/home/aryav_thakur/MURU-ConjectureLab-v1"
MAIN_DIR="${REPO}/results/e2/run_x86_e2a_v1"
OUT_DIR="${MAIN_DIR}/stage_b_isolated"
ORDER="${MAIN_DIR}/WORLD_ORDER_1_ISOLATED.json"
CACHE_DB="/home/aryav_thakur/e2_x86_cache/classify_cache.sqlite3"

live=$(systemctl --user list-units 'e2a-shard-*' --no-legend 2>/dev/null | grep -c running)
if [[ "$live" -gt 0 ]]; then
  echo "REFUSING TO START: ${live} Stage A shard units still running." >&2
  echo "Stage B must run alone -- memory pressure perturbs the wall-clock SIMPLIFY_TIMEOUT." >&2
  exit 2
fi

mkdir -p "$OUT_DIR"
# --shard-index 0 --n-shards 1 is the ONLY combination that passes the runner's
# `world_ordinal % n_shards == shard_index` filter unconditionally; section 13
# records a live mistake where --shard-index 6 --n-shards 1 silently completed
# with 0 worlds attempted. A distinct OUTPUT DIRECTORY, not a distinct shard
# index, is what keeps this run separate.
systemctl --user reset-failed e2a-stage-b.service 2>/dev/null
systemd-run --user --unit=e2a-stage-b \
  --description="MURU x86 E2a Stage B -- isolated world mass_power|c_low|n_default|r000" \
  --property=OOMPolicy=continue \
  --property=MemoryMax=infinity \
  --property=Restart=no \
  --property=WorkingDirectory="${REPO}" \
  "${REPO}/scripts/e2_rescue_v2/e2a_shard_entry.sh" \
    0 1 "$OUT_DIR" "$ORDER" "$CACHE_DB" "stage_b_nohup" --max-restarts 3
echo "launched e2a-stage-b -> ${OUT_DIR}"
