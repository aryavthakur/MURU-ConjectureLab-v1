"""T4: structure / parser / featurization acceptance over the frozen candidate all-model intersection only.

Candidate intersection = rows of artifacts/comparator_feasibility/overlap_support_per_compound.csv (commit 21fae1a)
with muru_supported & fiora_supported & mspred_supported & not in MSnLib v1.0 & absent from MassSpecGym 1.5.
Inputs per compound come only from the frozen population identity columns (key, scaffold_group, mh, smiles).
No model forward pass, no measured spectrum, mu, peak array, MURU residual or MURU error is read or computed.

Outputs the final frozen common population (sorted by key) with its SHA-256, and every exclusion with its reason.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
from rdkit.Chem import MolToSmiles

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from muru.wur_v2 import identity as ID   # noqa: E402
import modal_app as MA                    # noqa: E402

OUT = ROOT / "artifacts/comparator_benchmark/population"
AUDIT = ROOT / "artifacts/comparator_feasibility/overlap_support_per_compound.csv"
AUDIT_SHA256 = "bf31cb0270c25a62c390e8cfee4896a053369ef06bd0ae5c8cb6193df5fdfa7c"
POP = ROOT / "artifacts/wur_v2_confirmation_v2/freeze/validation_population.csv"
RUNGS = (20, 60)
C = Path(__file__).resolve().parent / "container"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    assert sha256_file(AUDIT) == AUDIT_SHA256
    a = pd.read_csv(AUDIT)
    cand = a[a.muru_supported & a.fiora_supported & a.mspred_supported & ~a.in_msnlib_v1_0 & (a.in_msg_any == False)]  # noqa: E712
    assert len(cand) == 1327 and cand.scaffold_group.nunique() == 1254, (len(cand), cand.scaffold_group.nunique())
    pop = pd.read_csv(POP, usecols=["key", "scaffold_group", "mh", "smiles"]).set_index("key")
    c = pop.loc[sorted(cand.key)].reset_index()
    c["model_smiles"] = [MolToSmiles(ID.parent_mol(s)) for s in c.smiles]
    assert all(ID.parent_connectivity_key(s) == k for s, k in zip(c.model_smiles, c.key))

    fiora_csv = pd.DataFrame([{"Name": f"{r.key}_NCE{n}", "SMILES": r.model_smiles, "Precursor_type": "[M+H]+",
                               "CE": n, "Instrument_type": "HCD"} for r in c.itertuples() for n in RUNGS])
    ms_rows = []
    for r in c.itertuples():
        for n in RUNGS:
            for cond, ce in (("ev_primary", n * r.mh / 500.0), ("raw_nce_sensitivity", float(n))):
                ms_rows.append({"spec": f"{r.key}_NCE{n}_{cond}", "smiles": r.model_smiles, "ionization": "[M+H]+",
                                "precursor": r.mh, "collision_energies": str([repr(ce)]), "instrument": "Orbitrap"})
    ms_tsv = pd.DataFrame(ms_rows)

    OUT.mkdir(parents=True, exist_ok=True)
    with MA.app.run():
        rf = MA.fiora_run.remote(
            "PYTHONPATH=/opt/fiora_v0.1.2_patched python $WORK/t4_fiora.py /opt/fiora_v0.1.2_patched $WORK/in.csv $WORK/t4.json",
            {"in.csv": fiora_csv.to_csv(index=False).encode(), "t4_fiora.py": (C / "t4_fiora.py").read_bytes()}, ["t4.json"])
        ri = MA.mspred_run.remote(
            "/opt/ms-pred/.venv/bin/python $WORK/t4_mspred.py iceberg $WORK/in.tsv $WORK/t4.json",
            {"in.tsv": ms_tsv.to_csv(sep="\t", index=False).encode(), "t4_mspred.py": (C / "t4_mspred.py").read_bytes()}, ["t4.json"])
        rg = MA.mspred_run.remote(
            "/opt/ms-pred/.venv/bin/python $WORK/t4_mspred.py glacier $WORK/in.tsv $WORK/t4.json",
            {"in.tsv": ms_tsv.drop(columns=["precursor"]).to_csv(sep="\t", index=False).encode(),
             "t4_mspred.py": (C / "t4_mspred.py").read_bytes()}, ["t4.json"])
    res = {}
    for model, r in (("fiora_os_v0_1_0", rf), ("iceberg_2_1", ri), ("glacier", rg)):
        if r["returncode"] != 0:
            raise RuntimeError(f"{model}\n{r['stdout']}\n{r['stderr']}")
        res[model] = json.loads(r["outputs"]["t4.json"])
        (OUT / f"t4_{model}_raw.json").write_text(json.dumps(res[model]))
        print(model, r["stdout"].strip().splitlines()[-1])

    # per compound verdict
    fails: dict[str, list[str]] = {}
    for rec in res["fiora_os_v0_1_0"]:
        if not rec["ok"]:
            fails.setdefault(rec["Name"].rsplit("_NCE", 1)[0], []).append(f"FIORA-OS v0.1.0: {rec.get('error')}")
    for model, label in (("iceberg_2_1", "ICEBERG 2.1"), ("glacier", "GLACIER")):
        for rec in res[model]:
            if not rec["ok"]:
                fails.setdefault(rec["spec"].split("_NCE")[0], []).append(f"{label} [{rec['spec']}]: {rec.get('error')}")
    excl = pd.DataFrame([{"key": k, "scaffold_group": pop.loc[k, "scaffold_group"], "reasons": " | ".join(v)}
                         for k, v in sorted(fails.items())], columns=["key", "scaffold_group", "reasons"])
    final = c[~c.key.isin(fails)].sort_values("key").reset_index(drop=True)
    final_cols = final[["key", "scaffold_group", "mh", "model_smiles"]]
    final_cols.to_csv(OUT / "common_population.csv", index=False, float_format="%.17g")
    excl.to_csv(OUT / "t4_exclusions.csv", index=False)
    key_list = "\n".join(final.key)
    summary = {
        "candidate_source": {"file": str(AUDIT.relative_to(ROOT)), "sha256": AUDIT_SHA256, "n": 1327, "groups": 1254},
        "t4_input_rows": {"fiora": len(fiora_csv), "iceberg": len(ms_tsv), "glacier": len(ms_tsv)},
        "t4_accepted_rows": {m: int(sum(r["ok"] for r in v)) for m, v in res.items()},
        "n_excluded_compounds": int(len(excl)),
        "final_population": {"n_compounds": int(len(final)), "n_scaffold_groups": int(final.scaffold_group.nunique()),
                             "largest_group": int(final.scaffold_group.value_counts().max()),
                             "key_list_sha256": hashlib.sha256(key_list.encode()).hexdigest(),
                             "key_list_definition": "sorted parent InChIKey first blocks, newline-joined, no trailing newline",
                             "csv_sha256": sha256_file(OUT / "common_population.csv")},
    }
    (OUT / "common_population_keys.txt").write_text(key_list)
    (OUT / "t4_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
