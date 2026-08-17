#!/usr/bin/env python
"""Rolling 30-min throughput report for the current 6-shard execution
regime. Appends a timestamped snapshot to a history file (so 60min/3hr
windows can be computed on subsequent runs) and prints the full report.
Deliberately does NOT use lifetime-average throughput -- only the rolling
windows computed from this history file, which only covers the current
(post-throughput-investigation) execution regime.

Reads across every isolated output directory a stuck-world workaround has
created (S13, S15), not just results/e2/run/ -- each is a genuine,
disjoint contributor to the 540-world population, not yet merged. The 5
quarantined worlds (results/e2/run_poison_world/, results/e2/run_stuck_worlds/)
are read-only failure records, not population progress, and are excluded
from every count here.
"""
import glob
import json
import os
import statistics
import subprocess
import sys
import time

RESULTS_ROOT = "/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/exp-v2-e2-pareto-observability/results/e2"
MAIN_DIR = f"{RESULTS_ROOT}/run"
ISOLATED_DIRS = [
    f"{RESULTS_ROOT}/run_shard1_healthy",
    f"{RESULTS_ROOT}/run_shard3_healthy",
    f"{RESULTS_ROOT}/run_shard4_healthy",
    f"{RESULTS_ROOT}/run_shard5_healthy",
]
ALL_PROGRESS_DIRS = [MAIN_DIR] + ISOLATED_DIRS
HISTORY_PATH = "/tmp/e2_rescue_snapshot/rolling_progress_history.jsonl"
N_SHARDS = 6
TOTAL_WORLDS = 540

QUARANTINED_WORLD_IDS = {
    "V2C|E2|mass_affine_descriptor|c_low|n_noiseless|r000",   # shard 0, S13
    "V2C|E2|mass_power|c_low|n_strong|r007",                  # shard 1, S15
    "V2C|E2|mass_power|c_high|n_default|r003",                # shard 3, S15
    "V2C|E2|mass_saturating_descriptor|c_mid|n_strong|r010",  # shard 4, S15
    "V2C|E2|mass_affine_descriptor|c_low|n_noiseless|r011",   # shard 5, S15
}


def load_world_rows():
    rows = []
    for d in ALL_PROGRESS_DIRS:
        for path in sorted(glob.glob(f"{d}/worlds_shard_*.jsonl")):
            for line in open(path):
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def per_output_file_counts():
    """Informational only -- see true_shard_assignment() for the
    authoritative per-shard remaining count. Shard-index filenames 1 and 2
    under results/e2/run/ carry a few leftover entries from the earlier
    3-shard era's different assignment, so counting by file alone
    misattributes a few worlds to the wrong shard label."""
    counts = {}
    for d in ALL_PROGRESS_DIRS:
        for path in sorted(glob.glob(f"{d}/worlds_shard_*.jsonl")):
            label = f"{os.path.basename(d)}/{os.path.basename(path)}"
            counts[label] = sum(1 for _ in open(path))
    return counts


def classifier_timeout_count():
    total = 0
    for d in ALL_PROGRESS_DIRS:
        for path in glob.glob(f"{d}/candidates_shard_*.jsonl"):
            with open(path) as f:
                for line in f:
                    if '"canonicalization_status": "SIMPLIFY_TIMEOUT"' in line:
                        total += 1
    return total


def supervisor_restart_count():
    """Total attempts beyond the first, across every supervisor log in
    every progress directory (each isolated-directory supervisor counts
    the same as a main-directory one)."""
    total_attempts = 0
    n_supervisor_logs = 0
    for d in ALL_PROGRESS_DIRS:
        for path in glob.glob(f"{d}/supervisor_shard_*.log"):
            n_supervisor_logs += 1
            for line in open(path):
                if "launching" in line:
                    total_attempts += 1
    return total_attempts - n_supervisor_logs


def true_shard_assignment():
    """The real world_ordinal % N_SHARDS assignment (90 worlds/shard),
    independent of which on-disk file/directory a world's record happens
    to have landed in. This is the authoritative source for remaining and
    active-world computation; the underlying checkpoint (_already_done,
    global per output directory) was already verified duplicate-free
    independent of this reporting convenience."""
    sys.path.insert(0, "/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/exp-v2-e2-pareto-observability/src")
    from muru.v2_calibration import e2_worlds as e2w

    all_worlds = list(e2w.iter_worlds())
    assignment = {i: [] for i in range(N_SHARDS)}
    for a in all_worlds:
        i = e2w.world_ordinal(*a) % N_SHARDS
        assignment[i].append(e2w.world_id(*a))
    return assignment


def active_world_ids(done, assignment):
    """Best-effort: the first not-yet-done, not-quarantined world (in
    deterministic order) for each shard is very likely what it's currently
    computing, since run_shard.py processes its assigned worlds strictly
    in order."""
    active = {}
    for i in range(N_SHARDS):
        my_worlds = [w for w in assignment[i] if w not in QUARANTINED_WORLD_IDS]
        for wid in my_worlds:
            if wid not in done:
                active[str(i)] = wid
                break
        else:
            active[str(i)] = "(shard complete)"
    return active


def sys_stats():
    up = subprocess.run(["uptime"], capture_output=True, text=True).stdout
    load = up.split("load averages:")[-1].strip()
    top = subprocess.run(["top", "-l", "1", "-n", "0", "-s", "0"], capture_output=True, text=True).stdout
    cpu_line = next((l for l in top.splitlines() if "CPU usage" in l), "")
    mem_line = next((l for l in top.splitlines() if "PhysMem" in l), "")
    return load, cpu_line.strip(), mem_line.strip()


def main():
    now = time.time()
    rows = load_world_rows()
    total_done = len(rows)
    done_ids = {r["world_id"] for r in rows}

    assignment = true_shard_assignment()
    true_remaining_per_shard = {
        i: sum(1 for w in assignment[i] if w not in QUARANTINED_WORLD_IDS and w not in done_ids)
        for i in range(N_SHARDS)
    }
    true_remaining_total = sum(true_remaining_per_shard.values())
    n_quarantined = len(QUARANTINED_WORLD_IDS)

    # sanity: total_done + remaining + quarantined should equal 540
    assert total_done + true_remaining_total + n_quarantined == TOTAL_WORLDS, (
        f"population accounting mismatch: {total_done} + {true_remaining_total} + {n_quarantined} != {TOTAL_WORLDS}"
    )

    # append snapshot to history
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "a") as f:
        f.write(json.dumps({"t": now, "total_done": total_done}) + "\n")

    # rolling windows from history
    history = [json.loads(l) for l in open(HISTORY_PATH) if l.strip()]

    def total_at_or_before(cutoff):
        candidates = [h for h in history if h["t"] <= cutoff]
        return candidates[-1]["total_done"] if candidates else None

    done_60m_ago = total_at_or_before(now - 3600)
    done_3h_ago = total_at_or_before(now - 3 * 3600)
    completed_60m = total_done - done_60m_ago if done_60m_ago is not None else None
    completed_3h = total_done - done_3h_ago if done_3h_ago is not None else None
    rate_60m = completed_60m if completed_60m is not None else None
    rate_3h = (completed_3h / 3) if completed_3h is not None else None

    wall_seconds = [r["wall_seconds"] for r in rows if r.get("wall_seconds") is not None]
    median_rt = statistics.median(wall_seconds) if wall_seconds else None
    p90_rt = statistics.quantiles(wall_seconds, n=10)[8] if len(wall_seconds) >= 10 else (max(wall_seconds) if wall_seconds else None)

    timeout_count = classifier_timeout_count()
    restarts = supervisor_restart_count()
    active = active_world_ids(done_ids, assignment)
    load, cpu_line, mem_line = sys_stats()

    print(f"=== E2 rolling report @ {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))} (6-shard regime) ===")
    print(f"completed total: {total_done}/540 (+{n_quarantined} quarantined PENDING_EXECUTION_DIAGNOSIS, not counted here)")
    print(f"completed in last 60 min: {completed_60m if completed_60m is not None else 'n/a (< 60min of history)'}")
    print(f"completed in last 3 hours: {completed_3h if completed_3h is not None else 'n/a (< 3hr of history)'}")
    print(f"worlds/hour (60min window): {rate_60m if rate_60m is not None else 'n/a'}")
    print(f"worlds/hour (3hr window, avg): {round(rate_3h, 2) if rate_3h is not None else 'n/a'}")
    print(f"remaining ordinary worlds: {true_remaining_total} (+{n_quarantined} quarantined, not counted)")
    print(f"remaining per shard (true ordinal%6 assignment): " + ", ".join(f"{i}: {true_remaining_per_shard[i]}" for i in range(N_SHARDS)))
    print(f"active (in-progress, best-effort) world IDs: {active}")
    print(f"median completed-world runtime: {round(median_rt, 1) if median_rt else 'n/a'}s")
    print(f"p90 completed-world runtime: {round(p90_rt, 1) if p90_rt else 'n/a'}s")
    print(f"classifier SIMPLIFY_TIMEOUT count (cumulative): {timeout_count}")
    print(f"supervisor restart count (cumulative, excl. initial launch): {restarts}")
    print(f"load average: {load}")
    print(f"{cpu_line}")
    print(f"{mem_line}")
    if rate_3h and rate_3h > 0:
        eta_hours = true_remaining_total / rate_3h
        print(f"ETA (from rolling 3hr rate only): ~{round(eta_hours, 1)} hours (~{time.strftime('%Y-%m-%d %H:%M', time.localtime(now + eta_hours*3600))})")
    else:
        print("ETA: insufficient rolling-window history yet")
    print("=== end report ===")


if __name__ == "__main__":
    main()
