"""Benchmark step 1 (NOT RUN during protocol construction): competitor predictions for the frozen common population.

Refuses to run unless the preregistration freeze ref exists and the population files match their frozen hashes.
Produces, per model and energy condition, the native prediction output (hashed) and a per-(key, NCE) mu table
computed with MURU's canonical external_multims2.spectrum_mu. Reads no measured spectrum or mu.

Frozen transforms (preregistration sections 5-6):
  FIORA-OS v0.1.0 : peaks exactly as written by the minimally patched v0.1.2 CLI (the CLI itself squares the
                    compiled_probsSQRT output back to linear intensity, once); mu = spectrum_mu(mz, I, mh).
  ICEBERG 2.1     : stored float32 masses and intensities of preds.hdf5; I = inten ** 2 applied here, once;
  GLACIER           mu = spectrum_mu(mass, I, mh).
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

PREREG_ID = "muru-v2-comparator-benchmark-1.0"
FREEZE_REF = f"refs/muru-freeze/{PREREG_ID}"
POP_DIR = ROOT / "artifacts/comparator_benchmark/population"
POP_CSV_SHA256 = "5526441961102c41b128993b7e0af686e6bb63a10299e002cd230c2f0d0276fe"
POP_KEYS_SHA256 = "dbdba9ca7edd4c6532b1e88b556f6fadcb582dd14d5c50a78f05c5bf04a52514"
OUT = ROOT / "artifacts/comparator_benchmark/predictions"
RUNGS = (20, 60)
C = Path(__file__).resolve().parent / "container"

FIORA_CMD = ("cd /opt/fiora_v0.1.2_patched && PYTHONPATH=/opt/fiora_v0.1.2_patched python scripts/fiora-predict "
             "-i $WORK/in.csv -o $WORK/out.mgf --model /opt/fiora_v0.1.2_patched/models/fiora_OS_v0.1.0.pt --annotation")
ICEBERG_CMD = ("/opt/ms-pred/.venv/bin/python $WORK/seeded_run.py 42 src/ms_pred/iceberg/predict_smis.py --dataset-labels $WORK/in.tsv "
               "--sparse-out --sparse-k 100 --max-nodes 100 --threshold 0.0 --num-cpu-workers 0 "
               "--gen-checkpoint /ckpt/iceberg21_msg_simulation/gen/best.ckpt "
               "--inten-checkpoint /ckpt/iceberg21_msg_simulation/inten_contr/best.ckpt "
               "--save-dir $WORK/out --out-name preds.hdf5")
GLACIER_CMD = ("/opt/ms-pred/.venv/bin/python $WORK/seeded_run.py 42 src/ms_pred/glacier/predict_smis_joint.py --dataset-labels $WORK/in.tsv "
               "--sparse-out --sparse-k 100 --num-cpu-workers 0 --checkpoint /ckpt/glacier_msg/best.ckpt "
               "--save-dir $WORK/out --out-name preds.hdf5")
DUMP = " && /opt/ms-pred/.venv/bin/python $WORK/parse.py $WORK/out/preds.hdf5 $WORK/spectra.json"


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def check_frozen() -> pd.DataFrame:
    r = subprocess.run(["git", "rev-parse", "--verify", FREEZE_REF], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"refusing: {FREEZE_REF} does not exist (preregistration not frozen)")
    csv_p, keys_p = POP_DIR / "common_population.csv", POP_DIR / "common_population_keys.txt"
    assert sha256(csv_p.read_bytes()) == POP_CSV_SHA256 and sha256(keys_p.read_bytes()) == POP_KEYS_SHA256
    pop = pd.read_csv(csv_p)
    assert "\n".join(pop.key) == keys_p.read_text()
    return pop


def ce(condition: str, nce: int, mh: float) -> float:
    return nce * mh / 500.0 if condition == "ev_primary" else float(nce)


def parse_mgf(text: str) -> dict:
    specs, cur = {}, None
    for line in text.splitlines():
        if line == "BEGIN IONS":
            cur = {"meta": {}, "mz": [], "inten": []}
        elif line == "END IONS":
            specs[cur["meta"]["TITLE"]] = cur
            cur = None
        elif cur is not None and "=" in line.split(" ")[0]:
            k, v = line.split("=", 1)
            cur["meta"][k] = v
        elif cur is not None and line.strip():
            parts = line.split(" ", 2)
            cur["mz"].append(float(parts[0]))
            cur["inten"].append(float(parts[1]))
    return specs


def mu_rows(pop, get_spec, model, condition):
    rows = []
    for r in pop.itertuples():
        for n in RUNGS:
            spec = get_spec(r.key, n)
            if spec is None:
                rows.append({"key": r.key, "nce": n, "mu": np.nan, "n_peaks": 0, "status": "NO_SPECTRUM"})
                continue
            mz, inten, prec = spec
            mu = MM.spectrum_mu(mz, inten, float(r.mh))
            rows.append({"key": r.key, "nce": n, "mu": mu, "n_peaks": int(mz.size), "precursor_peak_emitted": bool(prec),
                         "status": "OK" if np.isfinite(mu) else "EMPTY_OR_NONPOSITIVE"})
    return pd.DataFrame(rows).assign(model=model, condition=condition)


def main() -> int:
    pop = check_frozen()
    OUT.mkdir(parents=True, exist_ok=True)
    import modal_app as MA
    manifest = {"prereg_id": PREREG_ID, "population_csv_sha256": POP_CSV_SHA256, "files": {}, "runs": {}}
    tables = []
    with MA.app.run():
        # FIORA-OS v0.1.0
        fin = pd.DataFrame([{"Name": f"{r.key}_NCE{n}", "SMILES": r.model_smiles, "Precursor_type": "[M+H]+", "CE": n,
                             "Instrument_type": "HCD"} for r in pop.itertuples() for n in RUNGS]).to_csv(index=False).encode()
        res = MA.fiora_run.remote(FIORA_CMD, {"in.csv": fin}, ["out.mgf"])
        assert res["returncode"] == 0, res["stderr"]
        mgf = res["outputs"]["out.mgf"]
        (OUT / "fiora_os_v0_1_0_input.csv").write_bytes(fin)
        (OUT / "fiora_os_v0_1_0_output.mgf").write_bytes(mgf)
        specs = parse_mgf(mgf.decode())

        def get_fiora(k, n):
            s = specs.get(f"{k}_NCE{n}")
            if s is None:
                return None
            mz, it = np.array(s["mz"]), np.array(s["inten"])
            prec = bool(np.any(np.abs(mz - float(s["meta"]["PRECURSOR_MZ"])) < 1e-6))   # descriptive only
            return mz, it, prec
        tables.append(mu_rows(pop, get_fiora, "FIORA-OS v0.1.0", "native_nce"))
        manifest["runs"]["FIORA-OS v0.1.0"] = {"cmd": FIORA_CMD, "platform": res["platform"]}
        # ICEBERG 2.1 and GLACIER, primary and sensitivity conditions run as separate invocations
        for model, cmd, with_prec in (("ICEBERG 2.1", ICEBERG_CMD, True), ("GLACIER", GLACIER_CMD, False)):
            for condition in ("ev_primary", "raw_nce_sensitivity"):
                rows = []
                for r in pop.itertuples():
                    for n in RUNGS:
                        row = {"spec": f"{r.key}_NCE{n}", "smiles": r.model_smiles, "ionization": "[M+H]+",
                               "collision_energies": str([repr(ce(condition, n, float(r.mh)))]), "instrument": "Orbitrap"}
                        if with_prec:
                            row["precursor"] = float(r.mh)
                        rows.append(row)
                tsv = pd.DataFrame(rows).to_csv(sep="\t", index=False).encode()
                res = MA.mspred_run.remote(cmd + DUMP, {"in.tsv": tsv, "parse.py": (C / "mspred_h5_to_json.py").read_bytes(),
                                                          "seeded_run.py": (C / "seeded_run.py").read_bytes()},
                                           ["spectra.json", "out/preds.hdf5"])
                assert res["returncode"] == 0, res["stderr"]
                tag = f"{model.split()[0].lower()}_{condition}"
                (OUT / f"{tag}_input.tsv").write_bytes(tsv)
                (OUT / f"{tag}_preds.hdf5").write_bytes(res["outputs"]["out/preds.hdf5"])
                (OUT / f"{tag}_spectra.json").write_bytes(res["outputs"]["spectra.json"])
                dump = {d["name"].removeprefix("pred_"): d for d in json.loads(res["outputs"]["spectra.json"])}

                def get(k, n, dump=dump):
                    d = dump.get(f"{k}_NCE{n}")
                    if d is None:
                        return None
                    m = np.asarray(d["masses_float32"], dtype=np.float64)
                    root = np.asarray(d["is_root_fragment"] or [False] * len(m), dtype=bool)
                    mh = float(pop.set_index("key").loc[k, "mh"])
                    prec = bool(np.any(root & (np.abs(m - mh) / mh * 1e6 < 5)))   # descriptive only
                    return m, np.asarray(d["intens_float32"], dtype=np.float64) ** 2, prec   # the single frozen inverse
                tables.append(mu_rows(pop, get, model, condition))
                manifest["runs"][f"{model} {condition}"] = {"cmd": cmd, "platform": res["platform"]}
    mu = pd.concat(tables, ignore_index=True)
    mu.to_csv(OUT / "competitor_mu.csv", index=False, float_format="%.17g")
    for p in sorted(OUT.glob("*")):
        if p.name != "prediction_manifest.json":
            manifest["files"][p.name] = sha256(p.read_bytes())
    manifest["precursor_peak_emitted_fraction"] = {f"{m} | {c}": float(g.precursor_peak_emitted.mean())
                                                   for (m, c), g in mu.groupby(["model", "condition"])}
    manifest["status_counts"] = {f"{m} | {c}": g.status.value_counts().to_dict() for (m, c), g in mu.groupby(["model", "condition"])}
    (OUT / "prediction_manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(json.dumps(manifest["status_counts"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
