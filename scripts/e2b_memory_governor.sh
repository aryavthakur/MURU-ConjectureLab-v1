#!/bin/bash
# ADAPTIVE MEMORY GOVERNOR -- execution tooling only.
#
# The E2b frozen classification path has no authoritative timeout and no memory
# cap, so an expression that triggers catastrophic sympy expansion must be
# allowed to run. But the host has 47 GB and no swap, so several such cases
# running at once will OOM the machine and destroy unrelated in-flight work.
#
# This governor culls ONLY when the machine is actually about to die, and always
# culls the single LARGEST sweep child. Consequences:
#   * a culled case is recorded by the sweep as an explicit EXECUTION FAILURE
#     and is NEVER given a classification -- resource limits never become science
#   * a case running ALONE is free to consume nearly the whole machine, which is
#     exactly the "isolate it and let it complete" remedy
# It never touches the sweep parents, the evaluators' logic, or any checkpoint.
THRESHOLD_MB=${1:-6000}
LOG=audit/e2b_definitive_cloud_adjudication_20260818/_memory_governor.log
while true; do
  free_mb=$(free -m | awk '/^Mem:/{print $7}')
  if [ "$free_mb" -lt "$THRESHOLD_MB" ]; then
    read -r rss pid <<<"$(ps -eo rss,pid,args --sort=-rss | grep 'sys.path.insert' | grep -v grep | head -1 | awk '{print $1, $2}')"
    if [ -n "$pid" ] && [ "${rss:-0}" -gt 2000000 ]; then
      echo "$(date -u +%FT%TZ) CULL pid=$pid rss_mb=$((rss/1024)) free_mb=$free_mb" >> "$LOG"
      kill -9 "$pid" 2>/dev/null
      sleep 5
    fi
  fi
  sleep 10
done
