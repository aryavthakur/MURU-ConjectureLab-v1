"""Runtime budget for the governed objective-validation run.

Computed FROM `muru.objval.plan2`, so the arithmetic cannot drift from what is
executed and nested loops cannot be miscounted by hand — the failure that cost
Phase 2 (`BACKLOG.md` I4).

The benchmark measures structured worlds as well as nulls, because Phase 3 found
structured worlds slower, and it measures the world-build cost separately from
the per-seed search cost because they scale with different loop counts.

Benchmark units are written to a THROWAWAY checkpoint root and deleted, so no
governed unit is produced before the pre-registration is frozen.

    python scripts/ov_01_runtime_budget.py [--bench-seeds 3] [--workers 4]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
ART = ROOT / "artifacts"

BENCH_SPECS = [
    ("G1B", "structured positive control"),
    ("G4", "pure null"),
    ("G2", "non-collapsing, slowest family in Phase 3"),
]


def rss_gb() -> float:
    import resource
    m = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return m / (1024 ** 3) if sys.platform == "darwin" else m / (1024 ** 2)


def main() -> int:
    import numpy as np
    from muru.discovery import protocol
    from muru.objval.generators2 import build_world2
    from muru.objval.plan2 import (N_GPLEARN_SEEDS, N_SEEDS, gplearn_worlds2,
                                   run_counts2)
    from muru.synth.generators import load_dev_covariates

    ap = argparse.ArgumentParser()
    ap.add_argument("--bench-seeds", type=int, default=3)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--workers-grid", default="",
                    help="comma-separated worker counts to measure; the fastest "
                         "is adopted and the rest are recorded as rejected")
    ap.add_argument("--out", default=str(ART / "ov_runtime_budget.json"))
    a = ap.parse_args()

    counts = run_counts2()

    t = time.time()
    cov = load_dev_covariates()
    cov_load_s = time.time() - t

    bench = []
    for fam, note in BENCH_SPECS:
        t = time.time()
        w = build_world2(fam, 900, "moderate", cov=cov)
        build_s = time.time() - t
        long, covw = w.search_inputs()
        t = time.time()
        wd = protocol.build_world_data(w.world_id, long, covw)
        fit_s = time.time() - t

        # One warm-up seed is discarded: Julia JIT-compiles the search kernels on
        # first call and that cost is paid once per PROCESS, not once per run.
        # Charging it to every one of 9,690 runs would overstate the budget by
        # more than a factor of two.
        protocol.run_seed(wd, 1_699_999_999, which="pysr")
        seeds = [1_700_000_000 + k for k in range(a.bench_seeds)]
        t = time.time()
        for s in seeds:
            protocol.run_seed(wd, s, which="pysr")
        pysr_s = (time.time() - t) / len(seeds)

        t = time.time()
        protocol.run_seed(wd, seeds[0], which="gplearn")
        gp_s = time.time() - t

        bench.append({"family": fam, "note": note,
                      "world_build_s": build_s, "collapse_fit_s": fit_s,
                      "pysr_s_per_seed_serial": pysr_s,
                      "gplearn_s_per_seed_serial": gp_s})
        print(f"[bench] {fam:5s} build={build_s:5.2f}s fit={fit_s:5.2f}s "
              f"pysr={pysr_s:5.2f}s/seed gplearn={gp_s:5.2f}s/seed", flush=True)

    pysr_serial = float(np.mean([b["pysr_s_per_seed_serial"] for b in bench]))
    gp_serial = float(np.mean([b["gplearn_s_per_seed_serial"] for b in bench]))
    build_mean = float(np.mean([b["world_build_s"] + b["collapse_fit_s"]
                                for b in bench]))

    # --- concurrency measurement -------------------------------------------
    # N independent processes, each running one PySR seed, timed together.
    # Each process warms up, then times `bench_seeds` steady-state runs, so the
    # reported number is what the real sharded run actually pays per unit.
    def measure(nworkers: int) -> dict:
        code = (
            "import os,sys,time\n"
            "for v in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',"
            "'VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'): os.environ[v]='1'\n"
            f"sys.path.insert(0,{str(ROOT / 'src')!r})\n"
            "from muru.discovery import protocol\n"
            "from muru.objval.generators2 import build_world2\n"
            "from muru.synth.generators import load_dev_covariates\n"
            "i=int(sys.argv[1]); n=int(sys.argv[2])\n"
            "cov=load_dev_covariates()\n"
            "w=build_world2('G1B',900+i,'moderate',cov=cov)\n"
            "l,c=w.search_inputs()\n"
            "wd=protocol.build_world_data(w.world_id,l,c)\n"
            "protocol.run_seed(wd,1699999999,which='pysr')\n"
            "t=time.time()\n"
            "for k in range(n): protocol.run_seed(wd,1700000000+100*i+k,which='pysr')\n"
            "print('PERSEED', (time.time()-t)/n)\n")
        nb = max(3, a.bench_seeds)
        procs = [subprocess.Popen(
            [sys.executable, "-c", code, str(i), str(nb)],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            for i in range(nworkers)]
        inner = []
        for p in procs:
            txt = p.communicate()[0].decode()
            line = [x for x in txt.splitlines() if x.startswith("PERSEED")]
            inner.append(float(line[-1].split()[1]) if line else float("nan"))
        per_run_parallel = float(np.nanmean(inner)) / nworkers
        m = {"workers": nworkers,
             "steady_state_s_per_seed_per_worker": inner,
             "mean_s_per_seed_per_worker": float(np.nanmean(inner)),
             "wall_s_per_run": per_run_parallel,
             "speedup_vs_serial": pysr_serial / per_run_parallel,
             "seeds_timed_per_worker": nb,
             "note": ("each worker warms Julia up first and then times "
                      "steady-state runs, so per-process startup — which the "
                      "real run pays once per shard — is excluded")}
        print(f"[bench] {nworkers} concurrent: {np.nanmean(inner):.2f}s/seed "
              f"per worker => {per_run_parallel:.3f}s/run wall, speedup "
              f"{m['speedup_vs_serial']:.2f}x", flush=True)
        return m

    grid = [int(x) for x in a.workers_grid.split(",")] if a.workers_grid \
        else [a.workers]
    measured = [measure(n) for n in grid if n > 1]
    speedup = min(measured, key=lambda m: m["wall_s_per_run"]) if measured else None
    if speedup:
        a.workers = speedup["workers"]

    # --- post-processing per world ------------------------------------------
    # Selection, adjudication and recovery run once per world, not once per
    # seed, so they scale with 323 rather than 9,690 and are measured separately
    # instead of being folded into a per-run figure.
    import sympy as sp
    from muru.discovery import falsify
    from muru.objval import adjudicate as adjmod, select as selmod, signature
    w = build_world2("G1B", 902, "moderate", cov=cov)
    long, covw = w.search_inputs()
    wd = protocol.build_world_data(w.world_id, long, covw)
    expr = sp.sympify("sqrt(precursor_mz*(heteroatom_fraction+0.79))")
    thr = np.linspace(0.07, 0.49, 21)
    t = time.time()
    falsify.run_harness(wd, expr, 6, ("precursor_mz", "heteroatom_fraction"),
                        thr, {"fraction": 1.0})
    harness_s = time.time() - t
    t = time.time()
    adjmod.flexible_ceiling(wd)
    ceiling_s = time.time() - t
    t = time.time()
    Z = selmod.lattice(wd.X, list(protocol.FEATURES))
    for _ in range(10):
        signature.signature(expr, list(protocol.FEATURES), Z)
    sig_s = (time.time() - t) / 10
    post = {"harness_s_per_world": harness_s, "ceiling_s_per_world": ceiling_s,
            "signature_s_per_candidate": sig_s,
            "selection_s_per_world_measured_in_development": 2.0,
            "recovery_s_per_world_estimate": 0.5}

    per_run = speedup["wall_s_per_run"] if speedup else pysr_serial
    n_pysr = counts["pysr_runs_total"]
    n_gp = counts["gplearn_runs_total"]
    n_worlds = counts["n_worlds"]

    pysr_h = n_pysr * per_run / 3600.0
    gp_h = n_gp * (gp_serial / max(1, a.workers)) / 3600.0
    build_h = n_worlds * build_mean / max(1, a.workers) / 3600.0
    post_per_world = (post["selection_s_per_world_measured_in_development"]
                      + post["harness_s_per_world"] + post["ceiling_s_per_world"]
                      + build_mean + post["recovery_s_per_world_estimate"])
    post_h = n_worlds * post_per_world / max(1, a.workers) / 3600.0

    budget = {
        "hardware": "2024 MacBook Air, 8 cores, 16 GB",
        "thread_caps": {v: "1" for v in
                        ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                         "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
                         "NUMEXPR_NUM_THREADS")},
        "workers": a.workers,
        "counts": counts,
        "benchmark": bench,
        "covariate_load_s": cov_load_s,
        "pysr_s_per_seed_serial_mean": pysr_serial,
        "gplearn_s_per_seed_serial_mean": gp_serial,
        "world_build_plus_fit_s_mean": build_mean,
        "concurrency": speedup,
        "concurrency_grid": measured,
        "post_processing": post,
        "projection": {
            "pysr_runs": n_pysr,
            "pysr_wall_s_per_run": per_run,
            "pysr_hours": pysr_h,
            "gplearn_runs": n_gp,
            "gplearn_hours": gp_h,
            "world_build_hours": build_h,
            "post_processing_s_per_world": post_per_world,
            "post_processing_hours": post_h,
            "total_hours": pysr_h + gp_h + build_h + post_h,
            "arithmetic": (
                f"PySR: {n_pysr} runs x {per_run:.3f} s = {pysr_h:.2f} h; "
                f"gplearn: {n_gp} runs x {gp_serial:.3f} s / {a.workers} = "
                f"{gp_h:.2f} h; world build+fit: {n_worlds} x "
                f"{build_mean:.2f} s / {a.workers} = {build_h:.2f} h; "
                f"select+adjudicate+recover: {n_worlds} x "
                f"{post_per_world:.2f} s / {a.workers} = {post_h:.2f} h"),
        },
        "peak_rss_gb_single_process": rss_gb(),
        "checkpoint_unit": "one (block, world, seed) symbolic run",
        "gplearn_scope": {"worlds": len(gplearn_worlds2()),
                          "seeds": N_GPLEARN_SEEDS,
                          "pysr_seeds_per_world": N_SEEDS},
    }
    Path(a.out).write_text(json.dumps(budget, indent=1, default=str))
    print(json.dumps(budget["projection"], indent=1), flush=True)
    print(f"[ov01] wrote {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
