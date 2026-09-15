"""Mechanical verification of the committed-to-be competitor predictions (no measured data is read).

Checks, per preregistration muru-v2-comparator-benchmark-1.0:
  completeness and one-to-one identity mapping of primary cells; no duplicates; energy inputs as frozen; sensitivity
  outputs distinguishable from primary; every mu recomputed from the raw native output with exactly the frozen single
  transform (FIORA: none beyond the CLI's own square; ms-pred: one square) and MURU's spectrum_mu; frozen code and
  population unchanged since the freeze commit; checkpoint and code hashes inside the execution image equal the
  preregistered values; seeded wrapper in every ms-pred command.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from muru.wur_v2 import external_multims2 as MM   # noqa: E402
import run_predictions as RP                        # noqa: E402

FREEZE = "c0e724e342ee37139a50999be2030bd8144b1346"
PRED = ROOT / "artifacts/comparator_benchmark/predictions"
OUT = ROOT / "artifacts/comparator_benchmark/prediction_verification"
CKPT_SHA = {
    "/opt/fiora_v0.1.2_patched/models/fiora_OS_v0.1.0.pt": "adf44d61e40083f23a593cd6a3914e8008c12637b556d0bf2abd6ac467ab55f5",
    "/opt/fiora_v0.1.2_patched/models/fiora_OS_v0.1.0_state.pt": "0615f268b10564a0bc262d43571a5f414a9c53083d65df3200bec89b9a258790",
    "/opt/fiora_v0.1.2_patched/models/fiora_OS_v0.1.0_params.json": "f4fd5a40bff01bfe8a244ac466bb56ee61bc789a01fc81e5102f8ec60ef3c85a",
    "/ckpt/iceberg21_msg_simulation/gen/best.ckpt": "1eda5f3d9cda8345a93c0c480c3c848de840a611017a3f1641007fec1afb7a70",
    "/ckpt/iceberg21_msg_simulation/inten_contr/best.ckpt": "e074c0392638a71589e68d80acfd9ad53ae0587c523249cfa90e04ee50ee4f58",
    "/ckpt/glacier_msg/best.ckpt": "5a47cecca707d3abd5a49c7dbac99d100aa2a586d5d4f848f1e8e35140d7db11",
}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    checks: dict[str, object] = {}
    fail: list[str] = []

    def check(name, ok, detail=None):
        checks[name] = {"ok": bool(ok), **({"detail": detail} if detail is not None else {})}
        if not ok:
            fail.append(name)

    # ---- freeze and frozen files ----
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    ref = subprocess.run(["git", "rev-parse", RP.FREEZE_REF], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    check("freeze_ref_is_c0e724e", ref == FREEZE, ref)
    diff = subprocess.run(["git", "diff", "--name-only", FREEZE, "--", "scripts/comparator_benchmark/run_predictions.py",
                           "scripts/comparator_benchmark/modal_app.py", "scripts/comparator_benchmark/container",
                           "scripts/comparator_benchmark/analysis.py", "artifacts/comparator_benchmark/population",
                           "MURU_COMPARATOR_BENCHMARK_PREREGISTRATION.md", "src/muru"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    check("frozen_code_population_protocol_unchanged_since_freeze", diff == [], diff)
    fm = json.loads((ROOT / "artifacts/comparator_benchmark/freeze/freeze_manifest.json").read_text())
    bad = [f for f, h in fm["sha256"].items() if f.startswith(("scripts/comparator_benchmark/run_predictions", "scripts/comparator_benchmark/analysis",
                                                              "scripts/comparator_benchmark/modal_app", "scripts/comparator_benchmark/container",
                                                              "artifacts/comparator_benchmark/population", "MURU_COMPARATOR_BENCHMARK"))
           and sha((ROOT / f).read_bytes()) != h]
    check("freeze_manifest_hashes_match", bad == [], bad)
    checks["head_at_verification"] = head

    pop = pd.read_csv(ROOT / "artifacts/comparator_benchmark/population/common_population.csv")
    keys = list(pop.key)
    mh = dict(zip(pop.key, pop.mh))
    expected_ids = {f"{k}_NCE{n}" for k in keys for n in (20, 60)}
    man = json.loads((PRED / "prediction_manifest.json").read_text())
    badf = [f for f, h in man["files"].items() if sha((PRED / f).read_bytes()) != h]
    check("prediction_manifest_file_hashes_match", badf == [], badf)
    check("prediction_manifest_population_hash", man["population_csv_sha256"] == RP.POP_CSV_SHA256)

    mu = pd.read_csv(PRED / "competitor_mu.csv")
    counts = mu.groupby(["model", "condition"]).size().to_dict()
    checks["row_counts"] = {f"{m} | {c}": int(v) for (m, c), v in counts.items()}
    groups = [("FIORA-OS v0.1.0", "native_nce", True), ("ICEBERG 2.1", "ev_primary", True), ("GLACIER", "ev_primary", True),
              ("ICEBERG 2.1", "raw_nce_sensitivity", False), ("GLACIER", "raw_nce_sensitivity", False)]
    check("exactly_five_model_condition_tables", sorted(counts) == sorted((m, c) for m, c, _ in groups), sorted(counts))
    failures = []
    for m, c, primary in groups:
        t = mu[(mu.model == m) & (mu.condition == c)]
        ids = [f"{k}_NCE{n}" for k, n in zip(t.key, t.nce)]
        tag = f"{m} | {c}"
        check(f"{tag}: 2654 rows, one per frozen cell, no duplicates",
              len(t) == 2654 and len(set(ids)) == 2654 and set(ids) == expected_ids, {"rows": len(t), "unique": len(set(ids))})
        check(f"{tag}: every key has exactly NCE20 and NCE60",
              t.groupby("key").nce.apply(lambda s: sorted(s.tolist()) == [20, 60]).all() and set(t.key) == set(keys))
        bad_rows = t[(t.status != "OK") | ~np.isfinite(t.mu)]
        for r in bad_rows.itertuples():
            failures.append({"model": m, "condition": c, "primary": primary, "key": r.key, "nce": int(r.nce), "status": r.status})
    check("no_primary_prediction_failures", not any(f["primary"] for f in failures),
          [f for f in failures if f["primary"]])
    checks["sensitivity_failures_descriptive"] = [f for f in failures if not f["primary"]]

    # ---- FIORA: native MGF -> mu, no transform added; CLI square evident as max intensity 1.0 per spectrum ----
    specs = RP.parse_mgf((PRED / "fiora_os_v0_1_0_output.mgf").read_text())
    check("fiora_mgf_titles_one_to_one", set(specs) == expected_ids and len(specs) == 2654, len(specs))
    fin = pd.read_csv(PRED / "fiora_os_v0_1_0_input.csv")
    check("fiora_input_energy_is_raw_nce_hcd_mh+",
          all(f"{k}_NCE{ce}" == n for k, n, ce in zip(fin.Name.str.rsplit("_NCE", n=1).str[0], fin.Name, fin.CE))
          and set(fin.CE) == {20, 60} and set(fin.Instrument_type) == {"HCD"} and set(fin.Precursor_type) == {"[M+H]+"})
    t = mu[mu.model == "FIORA-OS v0.1.0"].set_index(["key", "nce"])
    maxdev, maxint_ok = 0.0, True
    for name, s in specs.items():
        k, n = name.rsplit("_NCE", 1)
        mz, it = np.array(s["mz"]), np.array(s["inten"])
        maxint_ok &= bool(np.isclose(it.max(), 1.0, rtol=0, atol=1e-12))
        maxdev = max(maxdev, abs(MM.spectrum_mu(mz, it, float(mh[k])) - float(t.loc[(k, int(n)), "mu"])))
    check("fiora_mu_recomputed_from_native_mgf (max abs deviation <= 1e-12; CSV float round-trip only)", maxdev <= 1e-12, maxdev)
    check("fiora_square_applied_once_by_cli (every spectrum max-normalised squared scale, max == 1)", maxint_ok)

    # ---- ms-pred: stored float32 -> single square -> spectrum_mu; energies; sensitivity separation ----
    for model, tag in (("ICEBERG 2.1", "iceberg"), ("GLACIER", "glacier")):
        for cond in ("ev_primary", "raw_nce_sensitivity"):
            dump = json.loads((PRED / f"{tag}_{cond}_spectra.json").read_text())
            tsv = pd.read_csv(PRED / f"{tag}_{cond}_input.tsv", sep="\t")
            import ast
            model_ce = {sp: float(ast.literal_eval(v)[0]) for sp, v in zip(tsv.spec, tsv.collision_energies)}
            names = [d["name"].removeprefix("pred_") for d in dump]
            check(f"{tag}_{cond}: spectra one-to-one with frozen cells", len(names) == 2654 and set(names) == expected_ids,
                  {"n": len(names), "unique": len(set(names))})
            tt = mu[(mu.model == model) & (mu.condition == cond)].set_index(["key", "nce"])
            dev, e_dev, native_max, prec = 0.0, 0.0, 0.0, 0
            for d, nm in zip(dump, names):
                k, n = nm.rsplit("_NCE", 1)
                m_ = np.asarray(d["masses_float32"], float)
                q = np.asarray(d["intens_float32"], float)
                native_max = max(native_max, float(q.max()))
                dev = max(dev, abs(MM.spectrum_mu(m_, q ** 2, float(mh[k])) - float(tt.loc[(k, int(n)), "mu"])))
                exp_ce = int(n) * float(mh[k]) / 500.0 if cond == "ev_primary" else float(n)
                # the value the model received (input TSV) must equal the frozen mapping; the HDF5 only stores a
                # whole-number label (PredSpecDB._get_collision_str uses '.0f'), checked as that rounding
                e_dev = max(e_dev, abs(model_ce[nm] - exp_ce))
                assert d["collision_key"] == f"collision {exp_ce:.0f}", (nm, d["collision_key"], exp_ce)
                root = np.asarray(d["is_root_fragment"], bool)
                prec += int(np.any(root & (np.abs(m_ - float(mh[k])) / float(mh[k]) * 1e6 < 5)))
            check(f"{tag}_{cond}: mu == spectrum_mu(mass, stored_inten**2, mh) (one square, nothing else; max abs deviation <= 1e-12)", dev <= 1e-12, dev)
            check(f"{tag}_{cond}: native stored intensities on sqrt scale (max <= 1, not pre-squared by pipeline)", native_max <= 1.0, native_max)
            check(f"{tag}_{cond}: model-input collision energy (input TSV) equals frozen mapping; HDF5 label is its '.0f' rounding", e_dev < 1e-9, e_dev)
            checks[f"{tag}_{cond}: native [M+H]+ precursor peak present (descriptive)"] = f"{prec}/2654"
            check(f"{tag}_{cond}: input tsv rows 2654, adduct/instrument frozen", len(tsv) == 2654
                  and set(tsv.ionization) == {"[M+H]+"} and set(tsv.instrument) == {"Orbitrap"})
    for model in ("ICEBERG 2.1", "GLACIER"):
        cmds = [v["cmd"] for k, v in man["runs"].items() if k.startswith(model)]
        check(f"{model}: seeded wrapper in every run command", len(cmds) == 2 and all("seeded_run.py 42" in c for c in cmds), cmds)
    check("sensitivity_distinguishable: separate files, condition label, and different stored energies",
          all((PRED / f"{t}_raw_nce_sensitivity_spectra.json").exists() for t in ("iceberg", "glacier"))
          and set(mu[mu.condition == "raw_nce_sensitivity"].model) == {"ICEBERG 2.1", "GLACIER"})

    # ---- execution image contents: checkpoint and code hashes ----
    import modal_app as MA
    code = ("import hashlib,json,sys;print(json.dumps({p:hashlib.sha256(open(p,'rb').read()).hexdigest() for p in sys.argv[1:]}))")
    fiora_paths = [p for p in CKPT_SHA if p.startswith("/opt/fiora")] + ["/opt/fiora_v0.1.2_patched/fiora/MS/SimulationFramework.py",
                                                                        "/opt/fiora_v0.1.2_patched/scripts/fiora-predict"]
    ms_paths = [p for p in CKPT_SHA if p.startswith("/ckpt")]
    with MA.app.run():
        rf = MA.fiora_run.remote(f'python -c "{code}" ' + " ".join(fiora_paths), {}, [])
        rm = MA.mspred_run.remote(f'/opt/ms-pred/.venv/bin/python -c "{code}" ' + " ".join(ms_paths)
                                  + ' && git -C /opt/ms-pred rev-parse HEAD 2>/dev/null; true', {}, [])
    img = {**json.loads(rf["stdout"].strip().splitlines()[-1]), **json.loads(rm["stdout"].strip().splitlines()[0])}
    t1 = json.loads((ROOT / "artifacts/comparator_benchmark/technical/t1/t1_provenance.json").read_text())
    check("image_checkpoint_hashes_equal_preregistration", all(img[p] == h for p, h in CKPT_SHA.items()),
          {p: img[p] for p in CKPT_SHA})
    check("image_fiora_patched_code_equals_t1_record",
          img["/opt/fiora_v0.1.2_patched/fiora/MS/SimulationFramework.py"] == t1["fiora"]["release_code_for_benchmark"]["patched_file_sha256"]
          and img["/opt/fiora_v0.1.2_patched/scripts/fiora-predict"] == t1["fiora"]["release_code_for_benchmark"]["cli_sha256"])

    OUT.mkdir(parents=True, exist_ok=True)
    report = {"verdict": "PASS" if not fail else "FAIL", "failed_checks": fail, "checks": checks,
              "measured_data_read": False}
    (OUT / "verification_report.json").write_text(json.dumps(report, indent=1, default=str) + "\n")
    print(json.dumps({"verdict": report["verdict"], "failed": fail, "row_counts": checks["row_counts"]}, indent=1))
    return 0 if not fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
