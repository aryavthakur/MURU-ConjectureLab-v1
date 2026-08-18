#!/usr/bin/env bash
# Per-shard entrypoint for the x86 E2a RESUME (2026-08-18 OOM interruption).
# Orchestration-only: it sets the frozen environment and execs the unmodified
# supervisor. It never touches which worlds are computed or how.
#
# Usage: e2a_shard_entry.sh <shard-index> <n-shards> <out-dir> <world-order> <cache-db> <log-tag> [--max-restarts N]
set -uo pipefail
REPO="/home/aryav_thakur/MURU-ConjectureLab-v1"
cd "$REPO" || exit 90

SHARD_INDEX="$1"; N_SHARDS="$2"; OUT_DIR="$3"; WORLD_ORDER="$4"; CACHE_DB="$5"; LOG_TAG="$6"; shift 6

# Frozen environment, from the single canonical definition on this host.
# env_setup.sh expands ${PYTHONPATH} unguarded, so under `set -u` it aborts
# with "PYTHONPATH: unbound variable" whenever PYTHONPATH is not already in
# the environment. That is true under systemd (a clean environment) but was
# NOT true in the interactive tmux shell the original run was launched from,
# which is why this only surfaced here. Seed the variable and relax -u for
# the duration of the source rather than editing the canonical env file.
: "${PYTHONPATH:=}"
export PYTHONPATH
set +u
# shellcheck disable=SC1091
source "$REPO/scripts/cloud_e6/env_setup.sh" >/dev/null 2>&1
set -u

# Fail loudly rather than silently running with a wrong environment.
for _v in JULIA_NUM_THREADS OMP_NUM_THREADS MKL_NUM_THREADS OPENBLAS_NUM_THREADS \
          PYTHON_JULIAPKG_EXE PYTHON_JULIAPKG_PROJECT; do
  if [[ -z "${!_v:-}" ]]; then
    echo "FATAL: ${_v} not set after sourcing env_setup.sh" >&2
    exit 91
  fi
done

mkdir -p "$OUT_DIR"
exec >>"${OUT_DIR}/${LOG_TAG}_shard_${SHARD_INDEX}.log" 2>&1
echo "=== entry $(date -u +%Y-%m-%dT%H:%M:%SZ) shard=${SHARD_INDEX}/${N_SHARDS} order=${WORLD_ORDER} ==="
echo "python=$(python -V 2>&1) julia=$(julia --version 2>&1) JULIA_NUM_THREADS=${JULIA_NUM_THREADS} OMP_NUM_THREADS=${OMP_NUM_THREADS}"

exec bash "$REPO/scripts/e2_rescue_v2/e2_shard_supervisor_lazy.sh" \
  /home/aryav_thakur/venv/bin/python \
  "$SHARD_INDEX" "$N_SHARDS" "$OUT_DIR" "$WORLD_ORDER" "$CACHE_DB" "$@"
