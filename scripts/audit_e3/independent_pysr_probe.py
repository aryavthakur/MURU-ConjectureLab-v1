"""INDEPENDENT dynamic PySR-absence probe, written fresh for this audit
(does not reuse hostile_audit_e3.py's check_c_pysr()). Runs one real world
through the actual E3 worker in a fresh subprocess and inspects
sys.modules for pysr, gplearn, juliacall, symbolicregression, operon, deap
-- a broader substring net than the original check's pysr-only grep.
"""
import subprocess
import sys

E3_SCRIPTS = "/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-v2-e3-identifiability-b23a7b/scripts/e3_identifiability"
FROZEN_SRC = "/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/heldout-analysis-restoration/src"

PROBE = f"""
import sys
sys.path.insert(0, {E3_SCRIPTS!r})
sys.path.insert(0, {FROZEN_SRC!r})
import run_e3
rec = run_e3.run_one_world({{
    "world_id": "V2C|E3|mass_exponential_descriptor|c0.55|noise0.02|grid6|r007",
    "cell_id": "x", "family": "mass_exponential_descriptor", "c": 0.55,
    "noise_sd": 0.02, "grid_points": 6, "replicate": 7,
}})
print("STATUS:", rec["status"])
suspicious = [m for m in sys.modules if any(tok in m.lower() for tok in
              ["pysr", "gplearn", "julia", "symbolicregression", "operon", "deap"])]
print("SUSPICIOUS MODULES LOADED:", suspicious)
print("TOTAL MODULES LOADED:", len(sys.modules))
"""

if __name__ == "__main__":
    proc = subprocess.run([sys.executable, "-c", PROBE], capture_output=True, text=True, timeout=120)
    print(proc.stdout)
    if proc.returncode != 0:
        print("STDERR:", proc.stderr[-3000:])
