"""T2b: ICEBERG 2.1 and GLACIER determinism under the declared seed (seed_everything(42) via container/seeded_run.py).

Same 10 non-benchmark example molecules and inputs as t2_t3_smoke.py. Two repetitions per model and condition,
plus a batch-size-1 run of ICEBERG (no batch-composition dependence) for a descriptive comparison. No MURU data.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t2_t3_smoke as T   # noqa: E402

OUT = T.OUT.parent / "t2b_seeded"
SEEDED = "/opt/ms-pred/.venv/bin/python $WORK/seeded_run.py 42 "


def canon(dump):
    return sorted((d["name"], tuple(d["masses_float32"]), tuple(d["intens_float32"])) for d in dump)


def mu_table(dump, mh):
    out = {}
    for d in dump:
        n = d["name"].removeprefix("pred_")
        out[n] = T.MM.spectrum_mu(np.asarray(d["masses_float32"], float), np.asarray(d["intens_float32"], float) ** 2, mh[n])
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ex = T.examples()
    mh = {f"{r.ex}_NCE{n}": r.mh for r in ex.itertuples() for n in T.RUNGS}
    files_common = {"parse.py": T.PARSER, "seeded_run.py": (HERE / "container/seeded_run.py").read_bytes()}
    report = {}
    with T.MA.app.run():
        for model, cmd, with_prec in (("iceberg", T.ICEBERG_CMD, True), ("glacier", T.GLACIER_CMD, False)):
            seeded_cmd = cmd.replace("/opt/ms-pred/.venv/bin/python ", SEEDED, 1)
            for condition in ("ev_primary", "raw_nce_sensitivity"):
                tsv = T.mspred_input(ex, condition, with_prec)
                reps = T.run_pair(T.MA.mspred_run, seeded_cmd + T.DUMP, {"in.tsv": tsv, **files_common},
                                  ["spectra.json", "out/preds.hdf5"])
                dumps = [json.loads(r["outputs"]["spectra.json"]) for r in reps]
                for i, d in enumerate(dumps):
                    (OUT / f"{model}_{condition}_seeded_rep{i + 1}_spectra.json").write_text(json.dumps(d))
                unseeded = json.loads((T.OUT / f"{model}_{condition}_rep1_spectra.json").read_text())
                mu_s, mu_u = mu_table(dumps[0], mh), mu_table(unseeded, mh)
                report[f"{model}_{condition}"] = {
                    "cmd": seeded_cmd,
                    "numeric_identical_seeded_reps": canon(dumps[0]) == canon(dumps[1]),
                    "hdf5_byte_identical_seeded_reps": reps[0]["output_sha256"]["out/preds.hdf5"] == reps[1]["output_sha256"]["out/preds.hdf5"],
                    "max_abs_mu_diff_seeded_vs_unseeded_rep1": float(max(abs(mu_s[k] - mu_u[k]) for k in mu_s)),
                }
            if model == "iceberg":
                tsv = T.mspred_input(ex, "ev_primary", True)
                r1 = T.MA.mspred_run.remote(seeded_cmd.replace("--num-cpu-workers 0", "--num-cpu-workers 0 --batch-size 1") + T.DUMP,
                                            {"in.tsv": tsv, **files_common}, ["spectra.json"])
                assert r1["returncode"] == 0, r1["stderr"]
                d1 = json.loads(r1["outputs"]["spectra.json"])
                seeded = json.loads((OUT / "iceberg_ev_primary_seeded_rep1_spectra.json").read_text())
                m1, ms = mu_table(d1, mh), mu_table(seeded, mh)
                report["iceberg_ev_primary_batch1_descriptive"] = {
                    "max_abs_mu_diff_batch1_vs_seeded_default_batch": float(max(abs(m1[k] - ms[k]) for k in m1)),
                    "per_spectrum_abs_mu_diff": {k: float(abs(m1[k] - ms[k])) for k in sorted(m1)}}
    (OUT / "t2b_report.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "per_spectrum_abs_mu_diff"} for k, v in report.items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
