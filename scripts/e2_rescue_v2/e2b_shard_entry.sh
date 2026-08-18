#!/usr/bin/env bash
# Per-shard entrypoint for the E2b held-out replay. Sets the frozen environment
# and execs the replay runner. Orchestration-only.
set -uo pipefail
REPO="/home/aryav_thakur/MURU-ConjectureLab-v1"
cd "$REPO" || exit 90
SHARD_INDEX="$1"; N_SHARDS="$2"; OUT_DIR="$3"

# env_setup.sh expands ${PYTHONPATH} unguarded, fatal under `set -u` in the
# clean environment systemd provides. Seed it and relax -u for the source.
: "${PYTHONPATH:=}"
export PYTHONPATH
set +u
# shellcheck disable=SC1091
source "$REPO/scripts/cloud_e6/env_setup.sh" >/dev/null 2>&1
set -u

for _v in JULIA_NUM_THREADS OMP_NUM_THREADS PYTHON_JULIAPKG_EXE PYTHON_JULIAPKG_PROJECT; do
  if [[ -z "${!_v:-}" ]]; then echo "FATAL: ${_v} not set" >&2; exit 91; fi
done

mkdir -p "$OUT_DIR"
exec >>"${OUT_DIR}/e2b_nohup_shard_${SHARD_INDEX}.log" 2>&1
echo "=== e2b entry $(date -u +%Y-%m-%dT%H:%M:%SZ) shard=${SHARD_INDEX}/${N_SHARDS} ==="
echo "python=$(python -V 2>&1) julia=$(julia --version 2>&1)"

exec /home/aryav_thakur/venv/bin/python \
  "$REPO/scripts/e2_rescue_v2/e2b_replay_shard.py" \
  --shard-index "$SHARD_INDEX" --n-shards "$N_SHARDS" --out-dir "$OUT_DIR"
