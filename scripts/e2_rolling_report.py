#!/usr/bin/env python
"""Rolling 30-min throughput report for the current 6-shard execution
regime. Appends a timestamped snapshot to a history file (so 60min/3hr
windows can be computed on subsequent runs) and prints the full report.
Deliberately does NOT use lifetime-average throughput -- only the rolling
windows computed from this history file, which only covers the current
(post-throughput-investigation) execution regime.
"""
import glob
import json
import os
import statistics
import subprocess
import sys
import time

OUT_DIR = "/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/exp-v2-e2-pareto-observability/results/e2/run"
HISTORY_PATH = "/tmp/e2_rescue_snapshot/rolling_progress_history.jsonl"
N_SHARDS = 6
TOTAL_WORLDS = 540


def load_world_rows():
    rows = []
    for path in sorted(glob.glob(f"{OUT_DIR}/worlds_shard_*.jsonl")):
        for line in open(path):
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def per_shard_counts(rows):
    # shard index isn't in the row; recompute from world_ordinal % N_SHARDS
    # by reading which file each count came from instead -- simpler: count
    # per output file.
    counts = {}
    for path in sorted(glob.glob(f"{OUT_DIR}/worlds_shard_*.jsonl")):
        idx = os.path.basename(path).replace("worlds_shard_", "").replace(".jsonl", "")
        n = sum(1 for _ in open(path))
        counts[idx] = n
    return counts


def classifier_timeout_count():
    total = 0
    for path in glob.glob(f"{OUT_DIR}/candidates_shard_*.jsonl"):
        with open(path) as f:
            for line in f:
                if '"canonicalization_status": "SIMPLIFY_TIMEOUT"' in line:
                    total += 1
    return total


def supervisor_restart_count():
    total_attempts = 0
    completed_shards = 0
    for path in glob.glob(f"{OUT_DIR}/supervisor_shard_*.log"):
        launches = 0
        completed = False
        for line in open(path):
            if "launching" in line:
                launches += 1
            if "COMPLETE confirmed" in line:
                completed = True
        total_attempts += launches
        if completed:
            completed_shards += 1
    # restarts = attempts beyond the first, per shard
    return total_attempts, completed_shards


POISON_WORLD_ID = "V2C|E2|mass_affine_descriptor|c_low|n_noiseless|r000"


def true_shard_assignment():
    """The real world_ordinal % N_SHARDS assignment (90 worlds/shard),
    independent of which on-disk file a world's record happens to have
    landed in -- shard-index filenames 1 and 2 are reused from the earlier
    3-shard era and carry some leftover entries from that scheme's
    different assignment, so counting by file alone misattributes a few
    worlds. This is a reporting-accuracy fix only; the underlying
    checkpoint (`_already_done`, global) was already verified correct
    (zero duplicates) independent of this."""
    sys.path.insert(0, "/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/exp-v2-e2-pareto-observability/src")
    from muru.v2_calibration import e2_worlds as e2w

    all_worlds = list(e2w.iter_worlds())
    assignment = {i: [] for i in range(N_SHARDS)}
    for a in all_worlds:
        i = e2w.world_ordinal(*a) % N_SHARDS
        assignment[i].append(e2w.world_id(*a))
    return assignment


def active_world_ids(done, assignment):
    """Best-effort: the first not-yet-done world (in deterministic order)
    for each shard is very likely what it's currently computing, since
    run_shard.py processes its assigned worlds strictly in order. Shard 0
    excludes the quarantined poison world (see PENDING_EXECUTION_DIAGNOSIS.md)
    -- it is not in shard 0's actual only-worlds-file since S13."""
    active = {}
    for i in range(N_SHARDS):
        my_worlds = [w for w in assignment[i] if w != POISON_WORLD_ID]
        for wid in my_worlds:
            if wid not in done:
                active[str(i)] = wid
                break
        else:
            active[str(i)] = "(shard complete)"
    return active


def sys_stats():
    load = open("/proc/loadavg").read().split()[:3] if os.path.exists("/proc/loadavg") else None
    if load is None:
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
    shard_counts = per_shard_counts(rows)
    remaining = TOTAL_WORLDS - total_done - 1  # -1 for the quarantined poison world, tracked separately

    # append snapshot to history
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "a") as f:
        f.write(json.dumps({"t": now, "total_done": total_done, "per_shard": shard_counts}) + "\n")

    # rolling windows from history
    history = [json.loads(l) for l in open(HISTORY_PATH) if l.strip()]
    def total_at_or_before(cutoff):
        candidates = [h for h in history if h["t"] <= cutoff]
        return candidates[-1]["total_done"] if candidates else None

    done_60m_ago = total_at_or_before(now - 3600)
    done_3h_ago = total_at_or_before(now - 3 * 3600)
    completed_60m = total_done - done_60m_ago if done_60m_ago is not None else None
    completed_3h = total_done - done_3h_ago if done_3h_ago is not None else None
    rate_60m = completed_60m if completed_60m is not None else None  # worlds/hour over last 60m window IS the count
    rate_3h = (completed_3h / 3) if completed_3h is not None else None

    wall_seconds = [r["wall_seconds"] for r in rows if r.get("wall_seconds") is not None]
    median_rt = statistics.median(wall_seconds) if wall_seconds else None
    p90_rt = statistics.quantiles(wall_seconds, n=10)[8] if len(wall_seconds) >= 10 else (max(wall_seconds) if wall_seconds else None)

    timeout_count = classifier_timeout_count()
    total_attempts, completed_shards = supervisor_restart_count()
    restarts = total_attempts - (N_SHARDS - completed_shards + completed_shards)  # attempts beyond 1 per shard launched so far
    # simpler: restarts = total launches - number of shard supervisors that have ever launched
    n_supervisors_launched = len(glob.glob(f"{OUT_DIR}/supervisor_shard_*.log"))
    restarts = total_attempts - n_supervisors_launched

    done_ids = {r["world_id"] for r in rows}
    assignment = true_shard_assignment()
    true_remaining_per_shard = {
        i: sum(1 for w in assignment[i] if w != POISON_WORLD_ID and w not in done_ids)
        for i in range(N_SHARDS)
    }
    active = active_world_ids(done_ids, assignment)
    load, cpu_line, mem_line = sys_stats()

    print(f"=== E2 rolling report @ {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))} (6-shard regime) ===")
    print(f"completed total: {total_done}/540 (+1 quarantined PENDING_EXECUTION_DIAGNOSIS, not counted here)")
    print(f"completed in last 60 min: {completed_60m if completed_60m is not None else 'n/a (< 60min of history)'}")
    print(f"completed in last 3 hours: {completed_3h if completed_3h is not None else 'n/a (< 3hr of history)'}")
    print(f"worlds/hour (60min window): {rate_60m if rate_60m is not None else 'n/a'}")
    print(f"worlds/hour (3hr window, avg): {round(rate_3h, 2) if rate_3h is not None else 'n/a'}")
    true_remaining_total = sum(true_remaining_per_shard.values())
    print(f"remaining ordinary worlds: {true_remaining_total} (+1 quarantined, not counted)")
    print(f"remaining per shard (true ordinal%6 assignment): " + ", ".join(f"{i}: {true_remaining_per_shard[i]}" for i in range(N_SHARDS)))
    print(f"completed per output file (informational; shard-index filenames 1,2 carry some leftover entries from the earlier 3-shard era): {shard_counts}")
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
