# MURU E6 Cloud Execution Package

This directory contains the operational tooling and execution scripts for running **E6 (`FALSE_STRUCTURE_SAFETY_COUNTERWEIGHT`)** on the 16-vCPU ARM64 Google Cloud host once upstream scientific authorization is granted.

> **IMPORTANT**: Do NOT execute E6 until all upstream scientific prerequisites (E2b falsification hook and E4a candidate proposal) are formally resolved and licensed.

---

## 1. Package Structure

- `env_setup.sh`: Exports all necessary environment variables, configures Julia and PythonCall paths, caps thread pools (`JULIA_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`), and sets `PYTHONPATH`.
- `preflight_e6.py`: Results-blind preflight test verifying Python dependencies, Julia stack identity, classifier SHA-256 hash, and directory permissions.
- `launch_e6.sh`: Automated worker launcher partitioning safety opportunities across 8 worker shards.
- `monitor_e6.sh`: Telemetry and progress monitoring script (reports load, RAM, active workers, and completed records without exposing blinded outcomes).
- `stop_e6.sh`: Controlled SIGTERM shutdown script that sweeps and terminates any orphaned worker processes.

---

## 2. SSH / Browser Disconnection Resilience

To ensure computation survives laptop closure, network disconnection, or browser termination:

### Starting in a Persistent `tmux` Session
```bash
# 1. Start a persistent tmux session named 'e6_run'
tmux new -s e6_run

# 2. Inside tmux, run the preflight verification
source scripts/cloud_e6/env_setup.sh
python scripts/cloud_e6/preflight_e6.py

# 3. Launch E6 execution (when authorized)
bash scripts/cloud_e6/launch_e6.sh 8

# 4. Detach safely from tmux at any time:
# Press Ctrl+B then D
```

### Reconnecting to the Session
```bash
# Re-attach to the running session from any terminal/SSH connection
tmux attach -t e6_run
```

### Monitoring Outside tmux
```bash
bash scripts/cloud_e6/monitor_e6.sh
```

### Clean Shutdown
```bash
bash scripts/cloud_e6/stop_e6.sh
```

---

## 3. Recommended Operational Parameters

- **Host**: 16 vCPUs, 31 GiB RAM (aarch64)
- **Worker Concurrency**: 8 parallel shards
- **Memory Footprint**: ~12 GiB total (~1.5 GiB peak RSS per search worker)
- **Expected Total Runtime**: ~2.2 hours for 3 candidate changes (~43.5 minutes per candidate change)
- **Results Directory**: `results/e6/`
- **Logs Directory**: `results/e6/logs/`
