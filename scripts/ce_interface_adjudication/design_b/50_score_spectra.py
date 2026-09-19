"""Design B step 50: score every (analysable compound, NCE, model, mapping) cell with the frozen endpoints.

Reuses the Design A scoring module unchanged (pinned by sha256) for the prediction reader and score_pair, which
calls the frozen similarity layer with its frozen defaults only. Observed side: observed_spectra.json from step 40.
parent_mass = theoretical [M+H]+. A cell with a missing or empty prediction carries a drop reason and no value.
Also scores the reproducibility QC: observed-to-observed cosine between each reproducibility injection and the
analysable injection of the same compound, per NCE cell (descriptive).
"""
import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import design_b_constants as C  # noqa: E402

ROOT = HERE.parents[2]
STUDY_DIR = ROOT / "artifacts/ce_interface_adjudication/design_b"
DESIGN_A_SCORER = HERE.parent / "design_a/40_score_spectra.py"
DESIGN_A_SCORER_SHA256 = "ec0100b5d93ffa2106460c1354a33cf302f00cea93efb92baaa70168a4824bbf"
MODEL_KEYS = (("iceberg_2_1_msg_simulation", "ICEBERG_2_1"), ("glacier_msg", "GLACIER"))
COLUMNS = ["compound_id", "stratum", "scaffold_group", "theoretical_mh", "nce", "model", "mapping", "cosine", "js", "drop_reason"]


def load_scorer():
    got = hashlib.sha256(DESIGN_A_SCORER.read_bytes()).hexdigest()
    if got != DESIGN_A_SCORER_SHA256:
        raise SystemExit(f"refusing: Design A scorer sha256 {got} != pinned {DESIGN_A_SCORER_SHA256}")
    spec = importlib.util.spec_from_file_location("design_a_scorer", DESIGN_A_SCORER)
    S = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(S)
    if S.SS.frozen_config_sha256() != C.SIMILARITY_FROZEN_CONFIG_SHA256:
        raise SystemExit("refusing: similarity frozen config sha256 mismatch")
    return S


def score(S, pop: pd.DataFrame, observed: dict, dumps: dict) -> list:
    rows = []
    for r in pop.sort_values("compound_id").to_dict("records"):
        for nce in C.NCE_GRID:
            cell = observed[r["compound_id"]][str(nce)]
            obs = (cell["mz"], cell["intensity"])
            for key, label in MODEL_KEYS:
                for m in C.MAPPINGS:
                    row = {**{k: r[k] for k in ("compound_id", "stratum", "scaffold_group", "theoretical_mh")},
                           "nce": nce, "model": label, "mapping": m, "cosine": None, "js": None, "drop_reason": ""}
                    e = dumps[(label, m)].get(S.spec_id(r["compound_id"], nce))
                    if e is None:
                        row["drop_reason"] = S.DROP_MISSING_PREDICTION
                    else:
                        try:
                            pred = S.prediction_spectrum(e)
                            row["cosine"], row["js"] = S.score_pair(pred, obs, float(r["theoretical_mh"]))
                        except S.PredictionError as exc:
                            row["drop_reason"] = exc.reason
                    rows.append(row)
    return rows


def main() -> int:
    for ref in (C.FREEZE_REF, C.PROCUREMENT_REF, C.SPECTRA_REF, C.PREDICTIONS_REF):
        if not subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--verify", "--quiet", ref], capture_output=True, text=True).stdout.strip():
            raise SystemExit(f"refusing: {ref} does not resolve")
    S = load_scorer()
    pop = pd.read_csv(STUDY_DIR / "prediction_population/prediction_population.csv")
    observed = json.loads((STUDY_DIR / "observed/observed_spectra.json").read_text())
    dumps = {(label, m): S.load_prediction_dump(STUDY_DIR / "prediction_outputs" / S.dump_filename(key, m))
             for key, label in MODEL_KEYS for m in C.MAPPINGS}
    rows = score(S, pop, observed, dumps)
    out = STUDY_DIR / "scores/cell_scores.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(COLUMNS)
        for r in rows:
            w.writerow([r[c] if c not in ("cosine", "js") else S.format_value(r[c]) for c in COLUMNS])
    repro = json.loads((STUDY_DIR / "observed/reproducibility_spectra.json").read_text())
    qc = []
    mh = pop.set_index("compound_id")["theoretical_mh"]
    for k, cells in sorted(repro.items()):
        if k not in observed:
            continue
        for n, c in sorted(cells.items()):
            qc.append({"compound_id": k, "nce": n, "obs_obs_cosine": S.SS.cosine_similarity_untransformed(
                (c["mz"], c["intensity"]), (observed[k][n]["mz"], observed[k][n]["intensity"]), parent_mass=float(mh[k]),
                pred_inverse_transform="identity", allow_override=True)})  # declared: both sides observed, QC only
    pd.DataFrame(qc).to_csv(STUDY_DIR / "scores/reproducibility_qc.csv", index=False)
    print(hashlib.sha256(out.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
