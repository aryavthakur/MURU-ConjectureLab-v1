#!/usr/bin/env python3
"""P1 (ms-pred loader/preprocessing side) evidence script.

Outcome-blind: reads only committed ms-pred source/labels, the MassSpecGym 1.5
identity parquet (scalar metadata), the frozen t1 hyperparameter extract, and
checkpoint pickle *strings* (the checkpoint pickles are never unpickled, no
model is loaded, nothing is predicted).

Intended home: scripts/ce_interface_adjudication/p1_pipeline_evidence.py in the
muru-ce-interface-adjudication worktree. Output path is set by OUT below.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import math
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True  # do not leave __pycache__ inside the upstream ms-pred clone

WT =Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
MSPRED = Path("/Users/aryav/muru-comparators/repos/ms-pred")
CKPT = Path("/Users/aryav/muru-comparators/checkpoints")
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else WT / "artifacts/ce_interface_adjudication/p1/p1_evidence.json"

PARQUET = WT / "artifacts/comparator_feasibility/massspecgym15_identity.parquet"
LABELS = MSPRED / "data/spec_datasets/msg/labels.tsv"
HPARAMS = WT / "artifacts/comparator_benchmark/technical/t1/checkpoint_hyperparameters.jsonl"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_function(path: Path, name: str, ns: dict):
    """Exec a single top-level function's source (no package import, no torch)."""
    src = path.read_text()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            seg = ast.get_source_segment(src, node)
            exec(seg, ns)
            return ns[name], node.lineno, node.end_lineno
    raise KeyError(name)


def main():
    ev: dict = {"inputs": {}}
    for k, p in [("labels_tsv", LABELS), ("msg15_identity_parquet", PARQUET), ("t1_hparams", HPARAMS)]:
        ev["inputs"][k] = {"path": str(p), "sha256": sha256(p)}

    # ---------------- parsers, verbatim from ms-pred ----------------
    ns = {"re": re, "pd": pd, "math": math}
    chem = MSPRED / "src/ms_pred/common/chem_utils.py"
    get_ce, l0, l1 = extract_function(chem, "get_collision_energy", ns)
    to_float, m0, m1 = extract_function(chem, "collision_energy_to_float", ns)
    spec = importlib.util.spec_from_file_location("cmsd", MSPRED / "data_scripts/create_msg_simulation_dataset.py")
    cmsd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cmsd)

    probes = ["collision 30", "collision 27.75", "collision 32.5", "collision 30 eV",
              "collision 30 eV [imputed]", "collision 30%", "collision NCE 30", "collision nan",
              "collision 20,30,40", "collision 1.5e1", "collision -5", "collision",
              "MassSpecGymID0000001_collision 30.json"]
    parser_probe = {}
    for t in probes:
        try:
            parser_probe[t] = get_ce(t)
        except Exception as e:  # noqa
            parser_probe[t] = f"EXC {type(e).__name__}"
    to_float_probe = {}
    for t in ["30", "30 eV", "27.75", "nan", "20,30", "30%"]:
        try:
            to_float_probe[t] = repr(to_float(t))
        except Exception as e:  # noqa
            to_float_probe[t] = f"EXC {type(e).__name__}"
    fmt_probe = {}
    for v in [30.0, 32.5, 21.374848, 27.75, float("nan"), "30 eV", None]:
        fmt_probe[repr(v)] = cmsd.format_collision_energy(v)
    ev["parser_probe"] = {
        "get_collision_energy_lines": f"chem_utils.py:{l0}-{l1}",
        "collision_energy_to_float_lines": f"chem_utils.py:{m0}-{m1}",
        "get_collision_energy": parser_probe,
        "collision_energy_to_float": to_float_probe,
        "create_msg_simulation_dataset.format_collision_energy": fmt_probe,
        "massspec_init_rounding_f'{x:.0f}'": {str(x): f"{x:.0f}" for x in (27.5, 27.75, 28.5, 32.5, 21.374848)},
    }

    # ---------------- committed labels vs MSG 1.5 ----------------
    L = pd.read_csv(LABELS, sep="\t")
    m = pd.read_parquet(PARQUET)
    sim = m[m.simulation_challenge].copy()
    j = L.merge(m, left_on="spec", right_on="identifier", how="left", indicator=True)
    lab_ce = j.collision_energies.str.extract(r"\['([^']*)'\]")[0].astype(float)
    msg_ce = j.collision_energy
    pos = {k: i for i, k in enumerate(m.identifier)}
    ev["committed_labels_vs_msg15"] = {
        "labels_rows": int(len(L)),
        "labels_columns": list(L.columns),
        "labels_unique_specs": int(L.spec.nunique()),
        "labels_instrument_counts": L.instrument.value_counts().to_dict(),
        "labels_adduct_counts": L.ionization.value_counts().to_dict(),
        "labels_unique_ce_strings": int(L.collision_energies.nunique()),
        "msg15_simulation_rows": int(len(sim)),
        "msg15_simulation_ce_nan": int(sim.collision_energy.isna().sum()),
        "join_both": int((j._merge == "both").sum()),
        "all_label_specs_are_sim_rows": bool(j.simulation_challenge.all()),
        "same_spec_set_as_msg15_sim": set(L.spec) == set(sim.identifier),
        "inchikey_equal_frac": float((j.inchikey_x == j.inchikey_y).mean()),
        "instrument_equal_frac": float((j.instrument == j.instrument_type).mean()),
        "adduct_equal_frac": float((j.ionization == j.adduct).mean()),
        "label_ce_string_counts_containing": {
            s: int(j.collision_energies.str.contains(s, regex=False).sum()) for s in ["eV", "imputed", "nan", "%", ",", "."]
        },
        "label_ce_equals_msg15_ce_frac": float(np.isclose(lab_ce, msg_ce).mean()),
        "label_ce_equals_floor_msg15_ce_frac": float(np.isclose(lab_ce, np.floor(msg_ce)).mean()),
        "label_ce_equals_round_half_even_msg15_ce_frac": float(np.isclose(lab_ce, [float(f"{x:.0f}") for x in msg_ce]).mean()),
        "unnamed0_equals_msg15_row_position_frac": float((j["Unnamed: 0"] == j.spec.map(pos)).mean()),
        "msg15_sim_noninteger_ce_rows": int((sim.collision_energy % 1 != 0).sum()),
    }

    # implied NCE for non-integer MSG CE (uses committed labels precursor)
    ni = j[(j.collision_energy % 1) != 0].copy()
    ni["nce_implied"] = ni.collision_energy * 500.0 / ni.precursor
    near = np.abs(ni.nce_implied - ni.nce_implied.round()) < 0.01
    it = j[(j.collision_energy % 1) == 0]
    imp_it = it.collision_energy * 500.0 / it.precursor
    near_int = np.abs(imp_it - imp_it.round()) < 0.01
    xt = pd.crosstab(j.instrument, (j.collision_energy % 1) == 0)
    ev["msg15_noninteger_ce_pattern"] = {
        "noninteger_rows": int(len(ni)),
        "by_instrument": ni.instrument.value_counts().to_dict(),
        "implied_nce_within_0.01_of_integer": int(near.sum()),
        "implied_nce_within_0.01_frac": float(near.mean()),
        "top_implied_nce_values": {str(k): int(v) for k, v in ni.nce_implied.round().value_counts().head(12).items()},
        "integer_rows": int(len(it)),
        "integer_rows_implied_nce_near_integer_frac": float(near_int.mean()),
        "instrument_x_is_integer_ce": {str(r): {str(c): int(xt.loc[r, c]) for c in xt.columns} for r in xt.index},
    }

    # ---------------- create_msg_simulation_dataset key replication ----------------
    sim["label"] = sim.collision_energy.map(cmsd.format_collision_energy)

    def label_key(lbl):
        parsed = ast.literal_eval(lbl)
        return cmsd.collision_key(str(parsed[0]).split()[0])

    sim["label_key"] = sim.label.map(label_key)
    sim["floor_key"] = np.floor(sim.collision_energy).astype(int).astype(str)
    sim["round_key"] = sim.collision_energy.map(lambda x: f"{x:.0f}")
    per_fold = {}
    for fold in ["train", "val", "test"]:
        s = sim[sim.fold == fold]
        mism = int((s.label_key != s.floor_key).sum())
        per_fold[fold] = {"rows": int(len(s)), "label_key_ne_floor_key": mism,
                          "kept_if_base_keys_are_floor": int(len(s) - mism),
                          "label_key_ne_round_key": int((s.label_key != s.round_key).sum())}
    ev["msg_simulation_label_keys"] = {
        "label_examples_noninteger": sim[sim.collision_energy % 1 != 0].label.head(5).tolist(),
        "per_fold": per_fold,
    }

    # ---------------- checkpoint step arithmetic ----------------
    hp = [json.loads(x) for x in open(HPARAMS)]
    steps = {}
    for rec in hp:
        ep, gs = rec["epoch"], rec["global_step"]
        steps[rec["path"]] = {"epoch": ep, "global_step": gs, "global_step_over_epoch_plus_1": gs / (ep + 1)}
    n_train_sim = int((sim.fold == "train").sum())
    n_keep = per_fold["train"]["kept_if_base_keys_are_floor"]
    known = m[m.collision_energy.notna()]
    ev["step_arithmetic"] = {
        "checkpoints": steps,
        "msg15_sim_train_rows": n_train_sim,
        "one_gpu_bs32_steps_if_all_sim_train": math.ceil(n_train_sim / 32),
        "n_range_for_3098_steps_one_gpu_bs32": [3097 * 32 + 1, 3098 * 32],
        "n_range_for_1378_steps_ddp2_bs32": [1377 * 64 + 1, 1378 * 64],
        "kept_train_if_floor_keyed_base": n_keep,
        "ddp2_bs32_steps_for_kept": math.ceil(math.ceil(n_keep / 2) / 32),
        "ddp2_bs32_steps_if_no_ce_drop": math.ceil(math.ceil(n_train_sim / 2) / 32),
        "one_gpu_bs32_steps_for_kept": math.ceil(n_keep / 32),
        "msg15_all_train_rows": int((m.fold == "train").sum()),
        "one_gpu_bs32_steps_if_all_msg_train": math.ceil(int((m.fold == "train").sum()) / 32),
        "msg15_known_ce_train_rows": int((known.fold == "train").sum()),
        "one_gpu_bs32_steps_if_known_ce_train": math.ceil(int((known.fold == "train").sum()) / 32),
    }

    # ---------------- checkpoint pickle strings (no unpickling) ----------------
    ck = {}
    for rel in ["iceberg21_msg_simulation/gen/best.ckpt", "iceberg21_msg_simulation/inten_contr/best.ckpt", "glacier_msg/best.ckpt"]:
        z = zipfile.ZipFile(CKPT / rel)
        pk = [n for n in z.namelist() if n.endswith("data.pkl")][0]
        data = z.read(pk)
        strs = sorted({s.decode() for s in re.findall(rb"[\x20-\x7e]{6,}", data) if b"results/" in s})
        ck[rel] = {"result_path_strings": strs}
    outer = {}
    for rel in ["iceberg21_msg_simulation.zip", "glacier_msg.zip"]:
        p = CKPT / rel
        if p.exists():
            outer[rel] = [[i.filename, list(i.date_time), i.file_size] for i in zipfile.ZipFile(p).infolist()]
    ev["checkpoint_strings"] = ck
    ev["archive_entry_timestamps"] = outer

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(ev, indent=1, default=str) + "\n")
    print(json.dumps(ev, indent=1, default=str))


if __name__ == "__main__":
    main()
