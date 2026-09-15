"""T2/T3: load every comparator, test determinism and establish output semantics on non-benchmark molecules only.

Molecules: the 10 structures of FIORA's upstream examples/example_input.csv (identical at v0.1.2 and e19ef82), all
outside the PR #7 frozen and sampled key sets (checked here). Each is predicted as [M+H]+ at NCE 20 and 60 under the
frozen per-model input mappings. Each condition runs twice in separate remote calls.

Reads no MURU outcome data. The only MURU code used is the canonical external_multims2.spectrum_mu and identity.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit.Chem import Descriptors, MolToSmiles

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from muru.wur_v2 import external_multims2 as MM   # noqa: E402
from muru.wur_v2 import identity as ID            # noqa: E402
import modal_app as MA                             # noqa: E402

OUT = ROOT / "artifacts/comparator_benchmark/technical/t2_t3"
PROTON = 1.007276
RUNGS = (20, 60)
FIORA_MODEL = {"v0.1.2": "/opt/fiora_v0.1.2/models/fiora_OS_v0.1.0.pt",
               "v0.1.2_patched": "/opt/fiora_v0.1.2_patched/models/fiora_OS_v0.1.0.pt",
               "head_e19ef82": "/opt/fiora_head/fiora/resources/models/fiora_OS_v0.1.0.pt"}
FIORA_CMD = {"v0.1.2": "cd /opt/fiora_v0.1.2 && PYTHONPATH=/opt/fiora_v0.1.2 python scripts/fiora-predict",
             "v0.1.2_patched": "cd /opt/fiora_v0.1.2_patched && PYTHONPATH=/opt/fiora_v0.1.2_patched python scripts/fiora-predict",
             "head_e19ef82": "cd /opt/fiora_head && PYTHONPATH=/opt/fiora_head python scripts/fiora-predict"}
PARSER = (Path(__file__).resolve().parent / "container/mspred_h5_to_json.py").read_bytes()
ICEBERG_CMD = ("/opt/ms-pred/.venv/bin/python src/ms_pred/iceberg/predict_smis.py --dataset-labels $WORK/in.tsv "
               "--sparse-out --sparse-k 100 --max-nodes 100 --threshold 0.0 --num-cpu-workers 0 "
               "--gen-checkpoint /ckpt/iceberg21_msg_simulation/gen/best.ckpt "
               "--inten-checkpoint /ckpt/iceberg21_msg_simulation/inten_contr/best.ckpt "
               "--save-dir $WORK/out --out-name preds.hdf5")
GLACIER_CMD = ("/opt/ms-pred/.venv/bin/python src/ms_pred/glacier/predict_smis_joint.py --dataset-labels $WORK/in.tsv "
               "--sparse-out --sparse-k 100 --num-cpu-workers 0 --checkpoint /ckpt/glacier_msg/best.ckpt "
               "--save-dir $WORK/out --out-name preds.hdf5")
DUMP = " && /opt/ms-pred/.venv/bin/python $WORK/parse.py $WORK/out/preds.hdf5 $WORK/spectra.json"


def examples() -> pd.DataFrame:
    ex = pd.read_csv(Path.home() / "muru-comparators/repos/fiora_v0.1.2/examples/example_input.csv")
    pop = pd.read_csv(ROOT / "artifacts/wur_v2_confirmation_v2/freeze/validation_population.csv")
    nov = pd.read_csv(ROOT / "artifacts/wur_v2_confirmation_v2/freeze/novelty_bins_per_compound.csv")
    forbidden = set(pop.key) | set(nov.key)
    rows = []
    for _, r in ex.iterrows():
        m = ID.parent_mol(r.SMILES)
        key = ID.parent_connectivity_key(r.SMILES)
        assert key not in forbidden, key
        rows.append({"ex": r.Name, "key": key, "smiles": MolToSmiles(m), "mh": Descriptors.ExactMolWt(m) + PROTON})
    return pd.DataFrame(rows)


def ce_value(model: str, condition: str, nce: int, mh: float) -> float:
    if model == "fiora":
        return float(nce)
    return nce * mh / 500.0 if condition == "ev_primary" else float(nce)


def fiora_input(ex: pd.DataFrame) -> bytes:
    rows = [{"Name": f"{r.ex}_NCE{n}", "SMILES": r.smiles, "Precursor_type": "[M+H]+", "CE": n, "Instrument_type": "HCD"}
            for r in ex.itertuples() for n in RUNGS]
    return pd.DataFrame(rows).to_csv(index=False).encode()


def mspred_input(ex: pd.DataFrame, condition: str, with_precursor: bool) -> bytes:
    rows = []
    for r in ex.itertuples():
        for n in RUNGS:
            row = {"spec": f"{r.ex}_NCE{n}", "smiles": r.smiles, "ionization": "[M+H]+",
                   "collision_energies": str([repr(ce_value("mspred", condition, n, r.mh))]), "instrument": "Orbitrap"}
            if with_precursor:
                row["precursor"] = r.mh
            rows.append(row)
    return pd.DataFrame(rows).to_csv(sep="\t", index=False).encode()


def parse_mgf(text: str) -> list[dict]:
    specs, cur = [], None
    for line in text.splitlines():
        if line == "BEGIN IONS":
            cur = {"meta": {}, "mz": [], "inten": [], "annot": []}
        elif line == "END IONS":
            specs.append(cur)
            cur = None
        elif cur is not None and "=" in line.split(" ")[0]:
            k, v = line.split("=", 1)
            cur["meta"][k] = v
        elif cur is not None and line.strip():
            parts = line.split(" ", 2)
            cur["mz"].append(float(parts[0]))
            cur["inten"].append(float(parts[1]))
            cur["annot"].append(parts[2] if len(parts) > 2 else "")
    return specs


def run_pair(fn, cmd, files, collect):
    reps = [fn.remote(cmd, files, collect) for _ in range(2)]
    for r in reps:
        if r["returncode"] != 0:
            raise RuntimeError(f"{cmd}\nSTDOUT\n{r['stdout']}\nSTDERR\n{r['stderr']}")
    return reps


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ex = examples()
    mh = {f"{r.ex}_NCE{n}": r.mh for r in ex.itertuples() for n in RUNGS}
    report = {"examples": ex.to_dict("records"), "fiora": {}, "iceberg": {}, "glacier": {}}
    with MA.app.run():
        # ---------------- FIORA-OS v0.1.0 under three code variants ----------------
        fin = fiora_input(ex)
        fiora_specs = {}
        for variant in FIORA_CMD:
            cmd = f"{FIORA_CMD[variant]} -i $WORK/in.csv -o $WORK/out.mgf --model {FIORA_MODEL[variant]} --annotation"
            reps = run_pair(MA.fiora_run, cmd, {"in.csv": fin}, ["out.mgf"])
            texts = [r["outputs"]["out.mgf"].decode() for r in reps]
            (OUT / f"fiora_{variant}_rep1.mgf").write_text(texts[0])
            (OUT / f"fiora_{variant}_rep2.mgf").write_text(texts[1])
            specs = {s["meta"]["TITLE"]: s for s in parse_mgf(texts[0])}
            fiora_specs[variant] = specs
            info = {"cmd": cmd, "byte_identical_reps": texts[0] == texts[1],
                    "sha256_rep1": hashlib.sha256(texts[0].encode()).hexdigest(), "n_spectra": len(specs),
                    "platform": reps[0]["platform"], "stdout_tail": reps[0]["stdout"][-1500:], "per_spectrum": {}}
            for name, s in specs.items():
                mz, it = np.array(s["mz"]), np.array(s["inten"])
                prec_mz = float(s["meta"]["PRECURSOR_MZ"])
                prec_idx = [i for i, a in enumerate(s["annot"]) if a.endswith("//[M+H]+") and abs(mz[i] - prec_mz) < 1e-6
                            and a.split("//")[0] == [x for x in s["annot"] if x][0].split("//")[0] or False]
                prec_rows = [i for i in range(len(mz)) if abs(mz[i] - prec_mz) < 1e-6 and s["annot"][i].endswith("//[M+H]+")]
                info["per_spectrum"][name] = {
                    "n_peaks": int(len(mz)), "precursor_mz_header": prec_mz, "mh_muru": mh[name],
                    "precursor_peak_rows": prec_rows,
                    "precursor_intensity": float(it[prec_rows[0]]) if prec_rows else None,
                    "max_intensity": float(it.max()), "sum_intensity": float(it.sum()),
                    "mu_spectrum_mu": MM.spectrum_mu(mz, it, mh[name])}
            report["fiora"][variant] = info
        # sqrt vs linear relation and code-variant equivalence
        rel = {}
        for name in fiora_specs["v0.1.2"]:
            a, b, c = (fiora_specs[v][name] for v in ("v0.1.2", "v0.1.2_patched", "head_e19ef82"))
            ka = sorted(zip(a["mz"], a["annot"], a["inten"]))
            kb = sorted(zip(b["mz"], b["annot"], b["inten"]))
            kc = sorted(zip(c["mz"], c["annot"], c["inten"]))
            ia, ib = np.array([x[2] for x in ka]), np.array([x[2] for x in kb])
            same_peaks_ab = [x[:2] for x in ka] == [x[:2] for x in kb]
            rel[name] = {
                "same_peak_set_unpatched_vs_patched": same_peaks_ab,
                "patched_equals_unpatched_squared_over_max_squared_maxabsdiff":
                    float(np.max(np.abs(ib - ia ** 2 / ia.max() ** 2))) if same_peaks_ab else None,
                "same_peak_set_patched_vs_head": [x[:2] for x in kb] == [x[:2] for x in kc],
                "patched_vs_head_max_abs_intensity_diff":
                    float(np.max(np.abs(ib - np.array([x[2] for x in kc])))) if [x[:2] for x in kb] == [x[:2] for x in kc] else None,
                "patched_vs_head_max_abs_mz_diff": float(np.max(np.abs(np.array([x[0] for x in kb]) - np.array([x[0] for x in kc]))))
                    if len(kb) == len(kc) else None,
                "mu_patched": MM.spectrum_mu(np.array(b["mz"]), np.array(b["inten"]), mh[name]),
                "mu_head": MM.spectrum_mu(np.array(c["mz"]), np.array(c["inten"]), mh[name]),
                "mu_unpatched_sqrt_scale_NOT_ENDPOINT": MM.spectrum_mu(np.array(a["mz"]), np.array(a["inten"]), mh[name]),
            }
        report["fiora"]["variant_relations"] = rel

        # ---------------- ICEBERG 2.1 and GLACIER ----------------
        for model, fn_cmd, with_prec in (("iceberg", ICEBERG_CMD, True), ("glacier", GLACIER_CMD, False)):
            for condition in ("ev_primary", "raw_nce_sensitivity"):
                tsv = mspred_input(ex, condition, with_prec)
                reps = run_pair(MA.mspred_run, fn_cmd + DUMP, {"in.tsv": tsv, "parse.py": PARSER},
                                ["spectra.json", "out/preds.hdf5", "out/*.log", "out/args.yaml"])
                dumps = [json.loads(r["outputs"]["spectra.json"]) for r in reps]
                canon = [sorted((d["name"], d["collision_key"], tuple(d["masses_float32"]), tuple(d["intens_float32"]),
                                 tuple(d["is_root_fragment"] or ())) for d in dd) for dd in dumps]
                (OUT / f"{model}_{condition}_rep1_spectra.json").write_text(json.dumps(dumps[0]))
                (OUT / f"{model}_{condition}_rep2_spectra.json").write_text(json.dumps(dumps[1]))
                (OUT / f"{model}_{condition}_input.tsv").write_bytes(tsv)
                info = {"cmd": fn_cmd, "numeric_identical_reps": canon[0] == canon[1],
                        "hdf5_byte_identical_reps": reps[0]["output_sha256"].get("out/preds.hdf5") == reps[1]["output_sha256"].get("out/preds.hdf5"),
                        "n_spectra": len(dumps[0]), "platform": reps[0]["platform"], "stdout_tail": reps[0]["stdout"][-1500:],
                        "stderr_tail": reps[0]["stderr"][-3000:], "per_spectrum": {}}
                if canon[0] != canon[1]:
                    diffs = []
                    by2 = {(d["name"], d["collision_key"]): d for d in dumps[1]}
                    for d in dumps[0]:
                        e = by2.get((d["name"], d["collision_key"]))
                        if e is None or len(e["intens_float32"]) != len(d["intens_float32"]):
                            diffs.append({"name": d["name"], "length_or_missing": True})
                            continue
                        a = sorted(zip(d["masses_float32"], d["intens_float32"]))
                        b = sorted(zip(e["masses_float32"], e["intens_float32"]))
                        diffs.append({"name": d["name"], "max_abs_mass_diff": float(np.max(np.abs(np.array(a)[:, 0] - np.array(b)[:, 0]))),
                                      "max_abs_inten_diff": float(np.max(np.abs(np.array(a)[:, 1] - np.array(b)[:, 1])))})
                    info["rep_differences"] = diffs
                for d in dumps[0]:
                    d["name"] = d["name"].removeprefix("pred_")   # ms-pred writes spectra as pred_<spec>
                    m = np.array(d["masses_float32"], dtype=np.float64)
                    q = np.array(d["intens_float32"], dtype=np.float64)
                    root = np.array(d["is_root_fragment"] or [False] * len(m))
                    ppm = np.abs(m - mh[d["name"]]) / mh[d["name"]] * 1e6
                    prec_rows = np.where(root & (ppm < 5))[0].tolist()
                    info["per_spectrum"][d["name"]] = {
                        "n_peaks": int(len(m)), "stored_collision_energy": d["stored_collision_energy"],
                        "root_fragment_rows": int(root.sum()), "root_rows_at_mh_5ppm": prec_rows,
                        "root_mh_native_intensity": float(q[prec_rows].sum()) if prec_rows else None,
                        "any_peak_at_mh_5ppm": int((ppm < 5).sum()),
                        "native_min": float(q.min()), "native_max": float(q.max()),
                        "n_nonpositive": int((q <= 0).sum()),
                        "mu_linear_after_single_square": MM.spectrum_mu(m, q ** 2, mh[d["name"]]),
                        "mu_native_sqrt_scale_NOT_ENDPOINT": MM.spectrum_mu(m, q, mh[d["name"]]),
                    }
                report[model][condition] = info
    (OUT / "t2_t3_report.json").write_text(json.dumps(report, indent=1, default=str) + "\n")
    print(json.dumps({k: {c: {kk: vv for kk, vv in v.items() if kk not in ("per_spectrum", "stdout_tail", "stderr_tail", "cmd")}
                          for c, v in d.items() if isinstance(v, dict) and c != "variant_relations"}
                      for k, d in report.items() if k != "examples"}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
