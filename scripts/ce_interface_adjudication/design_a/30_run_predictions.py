"""Design A step 30: collision-energy interface adjudication prediction harness.

Study: "MURU CE interface adjudication Design A" (study id muru-ce-interface-adjudication-design-a).
Question: which collision-energy input convention do the two public ms-pred checkpoints encode.

Two modes:

  emit-inputs  Build, for each model in {iceberg_2_1_msg_simulation, glacier_msg} and each frozen mapping in
               {K1, K2, K3}, a deterministic ms-pred `--dataset-labels` TSV covering every (compound, NCE) cell,
               plus a manifest recording every file's sha256, the exact command line that execution would run,
               the checkpoint identities with their expected sha256, and the resolved environment variables.
               This mode contacts no model, loads no checkpoint and imports neither torch nor modal.

  execute      Refuses unless ALL of: MURU_CE_ADJUDICATION_EXECUTE=1 is set in the environment, the freeze ref
               refs/muru-freeze/muru-ce-interface-adjudication-design-a resolves in git, and every emitted input
               file still matches its manifest sha256. Each refusal is a hard SystemExit naming the missing
               precondition. This path is inert until the preregistration is frozen and execution authorized.

The three frozen mappings (preregistration section 3; no others, no fitted factors, no offsets, no interpolation,
no per-instrument or per-model variants):

  K1: CE_input = float(NCE)
  K2: CE_input = float(NCE) * theoretical_mh / 500.0     IEEE-754 binary64, no rounding
  K3: CE_input = float(math.floor(K2))                   floor toward negative infinity, returned as a float

The mapping applies to the collision energy ONLY. The `precursor` column (ICEBERG) always carries the unmodified
theoretical_mh, because it is the precursor m/z input, not a collision-energy input.

Execution conventions are inherited verbatim from the frozen comparator harness
scripts/comparator_benchmark/run_predictions.py and scripts/comparator_benchmark/modal_app.py; every inherited
convention, and everything deliberately NOT inherited, is documented with file:line in
artifacts/ce_interface_adjudication/design_a/notes/prediction_harness_provenance.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

STUDY_ID = "muru-ce-interface-adjudication-design-a"
FREEZE_REF = f"refs/muru-freeze/{STUDY_ID}"
EXECUTE_ENV_VAR = "MURU_CE_ADJUDICATION_EXECUTE"

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STUDY_DIR = ROOT / "artifacts/ce_interface_adjudication/design_a"
POP_DIR = STUDY_DIR / "population"
IN_DIR = STUDY_DIR / "prediction_inputs"
OUT_DIR = STUDY_DIR / "prediction_outputs"
MANIFEST_NAME = "prediction_input_manifest.json"

# Frozen energy rungs of the Design A population (MassBank Eawag EQ [M+H]+ HCD, NCE 30 and 60).
NCE_RUNGS = (30, 60)

# Container helpers inherited unchanged from the comparator harness.
COMPARATOR_CONTAINER = ROOT / "scripts/comparator_benchmark/container"

# Checkpoint identities, sha256 values as recorded in artifacts/comparator_benchmark/technical/t1/t1_provenance.json.
COMPARATORS_HOME = Path(os.environ.get("MURU_COMPARATORS_HOME", str(Path.home() / "muru-comparators")))

# Command lines: inherited byte-for-byte from run_predictions.py:40-48 (ICEBERG), :45-47 (GLACIER), :48 (DUMP).
ICEBERG_CMD = ("/opt/ms-pred/.venv/bin/python $WORK/seeded_run.py 42 src/ms_pred/iceberg/predict_smis.py --dataset-labels $WORK/in.tsv "
               "--sparse-out --sparse-k 100 --max-nodes 100 --threshold 0.0 --num-cpu-workers 0 "
               "--gen-checkpoint /ckpt/iceberg21_msg_simulation/gen/best.ckpt "
               "--inten-checkpoint /ckpt/iceberg21_msg_simulation/inten_contr/best.ckpt "
               "--save-dir $WORK/out --out-name preds.hdf5")
GLACIER_CMD = ("/opt/ms-pred/.venv/bin/python $WORK/seeded_run.py 42 src/ms_pred/glacier/predict_smis_joint.py --dataset-labels $WORK/in.tsv "
               "--sparse-out --sparse-k 100 --num-cpu-workers 0 --checkpoint /ckpt/glacier_msg/best.ckpt "
               "--save-dir $WORK/out --out-name preds.hdf5")
DUMP = " && /opt/ms-pred/.venv/bin/python $WORK/parse.py $WORK/out/preds.hdf5 $WORK/spectra.json"

# Resolved environment of the ms-pred container function, modal_app.py:88-89.
MSPRED_ENV = {"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD": "1"}

# Fixed input tokens, run_predictions.py:135-138.
IONIZATION = "[M+H]+"
INSTRUMENT = "Orbitrap"

MODELS = {
    "iceberg_2_1_msg_simulation": {
        "display_name": "ICEBERG 2.1 msg_simulation",
        "entry_script": "src/ms_pred/iceberg/predict_smis.py",
        "command": ICEBERG_CMD,
        # predict_smis.prepare_entry reads entry["precursor"]; predict_smis_joint.prepare_entry does not.
        "emit_precursor": True,
        "checkpoints": {
            "/ckpt/iceberg21_msg_simulation/gen/best.ckpt": {
                "host_path": str(COMPARATORS_HOME / "checkpoints/iceberg21_msg_simulation/gen/best.ckpt"),
                "sha256": "1eda5f3d9cda8345a93c0c480c3c848de840a611017a3f1641007fec1afb7a70",
                "bytes": 41561644,
            },
            "/ckpt/iceberg21_msg_simulation/inten_contr/best.ckpt": {
                "host_path": str(COMPARATORS_HOME / "checkpoints/iceberg21_msg_simulation/inten_contr/best.ckpt"),
                "sha256": "e074c0392638a71589e68d80acfd9ad53ae0587c523249cfa90e04ee50ee4f58",
                "bytes": 40604948,
            },
        },
    },
    "glacier_msg": {
        "display_name": "GLACIER MassSpecGym",
        "entry_script": "src/ms_pred/glacier/predict_smis_joint.py",
        "command": GLACIER_CMD,
        "emit_precursor": False,
        "checkpoints": {
            "/ckpt/glacier_msg/best.ckpt": {
                "host_path": str(COMPARATORS_HOME / "checkpoints/glacier_msg/best.ckpt"),
                "sha256": "5a47cecca707d3abd5a49c7dbac99d100aa2a586d5d4f848f1e8e35140d7db11",
                "bytes": 181602423,
            },
        },
    },
}

MS_PRED_COMMIT = "ed8311f22958cb37f055b663b5f56c5c77a2ee33"
MS_PRED_REPO = str(COMPARATORS_HOME / "repos/ms-pred")


# ----------------------------------------------------------------------------------------------------------------
# The three frozen mappings
# ----------------------------------------------------------------------------------------------------------------

def k1(nce: int | float, theoretical_mh: float) -> float:
    """K1: the raw NCE number, unconverted."""
    return float(nce)


def k2(nce: int | float, theoretical_mh: float) -> float:
    """K2: the Thermo normalised-collision-energy conversion at the 500 Da reference, binary64, no rounding."""
    return float(nce) * float(theoretical_mh) / 500.0


def k3(nce: int | float, theoretical_mh: float) -> float:
    """K3: K2 floored toward negative infinity, returned as a float."""
    return float(math.floor(k2(nce, theoretical_mh)))


MAPPINGS = {
    "K1": k1,
    "K2": k2,
    "K3": k3,
}

MAPPING_DEFINITIONS = {
    "K1": "CE_input = float(NCE)",
    "K2": "CE_input = float(NCE) * theoretical_mh / 500.0 (IEEE-754 binary64, no rounding)",
    "K3": "CE_input = float(math.floor(K2)) (floor toward negative infinity)",
}


def format_collision_energies(ce_value: float) -> str:
    """The exact collision_energies cell the comparator harness writes: run_predictions.py:136.

    `str([repr(ce(...))])` -> a Python list literal holding one single-quoted decimal string, e.g. "['19.9998']".
    ms-pred parses it with ast.literal_eval then common.collision_energy_to_float, which does
    float(s.split()[0]) for a str. repr() of a binary64 is the shortest round-tripping decimal, so the
    container recovers the identical double.
    """
    return str([repr(float(ce_value))])


# ----------------------------------------------------------------------------------------------------------------
# Population
# ----------------------------------------------------------------------------------------------------------------

REQUIRED_COMPOUND_COLUMNS = ("compound_id", "representative_smiles", "theoretical_mh")


def load_population(compounds_csv: Path, fold: str = "all") -> pd.DataFrame:
    if not compounds_csv.exists():
        raise SystemExit(f"refusing: population file not found: {compounds_csv}")
    pop = pd.read_csv(compounds_csv)
    missing = [c for c in REQUIRED_COMPOUND_COLUMNS if c not in pop.columns]
    if missing:
        raise SystemExit(f"refusing: {compounds_csv} is missing required column(s): {', '.join(missing)}")
    if fold != "all":
        if "fold" not in pop.columns:
            raise SystemExit(f"refusing: --fold {fold} requested but {compounds_csv} has no 'fold' column")
        pop = pop[pop["fold"].astype(str) == fold]
        if pop.empty:
            raise SystemExit(f"refusing: no compounds in fold {fold!r} of {compounds_csv}")
    if pop["compound_id"].duplicated().any():
        dups = sorted(pop.loc[pop["compound_id"].duplicated(), "compound_id"].astype(str).unique())
        raise SystemExit(f"refusing: duplicate compound_id in {compounds_csv}: {dups[:10]}")
    # Deterministic order: lexicographic by compound_id, independent of the file's own row order.
    pop = pop.sort_values("compound_id", kind="mergesort").reset_index(drop=True)
    return pop


def spec_id(compound_id: str, nce: int) -> str:
    """Stable per-cell spec id. Mirrors the comparator's f"{key}_NCE{n}" (run_predictions.py:111,135)."""
    return f"{compound_id}_NCE{nce}"


def build_rows(pop: pd.DataFrame, mapping: str, emit_precursor: bool) -> list[dict]:
    """One row per (compound, NCE) cell, in (compound_id asc, nce asc) order.

    Column order reproduces run_predictions.py:135-138 exactly:
    spec, smiles, ionization, collision_energies, instrument [, precursor].
    """
    fn = MAPPINGS[mapping]
    rows: list[dict] = []
    for r in pop.itertuples(index=False):
        mh = float(r.theoretical_mh)
        for nce in NCE_RUNGS:
            row = {
                "spec": spec_id(str(r.compound_id), nce),
                "smiles": str(r.representative_smiles),
                "ionization": IONIZATION,
                "collision_energies": format_collision_energies(fn(nce, mh)),
                "instrument": INSTRUMENT,
            }
            if emit_precursor:
                row["precursor"] = mh
            rows.append(row)
    return rows


def rows_to_tsv_bytes(rows: list[dict]) -> bytes:
    """Serialization inherited from run_predictions.py:140: pandas to_csv(sep='\\t', index=False)."""
    return pd.DataFrame(rows).to_csv(sep="\t", index=False).encode()


def input_filename(model: str, mapping: str) -> str:
    return f"{model}__{mapping}__in.tsv"


# ----------------------------------------------------------------------------------------------------------------
# Hashing and git
# ----------------------------------------------------------------------------------------------------------------

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_out(repo: Path, *args: str) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    except OSError:
        return None
    return r.stdout.strip() if r.returncode == 0 else None


# ----------------------------------------------------------------------------------------------------------------
# emit-inputs
# ----------------------------------------------------------------------------------------------------------------

def build_manifest(pop: pd.DataFrame, files: dict[str, dict], compounds_csv: Path,
                   records_csv: Path, fold: str) -> dict:
    records = None
    if records_csv.exists():
        rec = pd.read_csv(records_csv)
        records = {
            "path": str(records_csv.relative_to(ROOT)),
            "sha256": sha256_file(records_csv),
            "n_rows": int(len(rec)),
            "observed_nce_values": sorted({float(x) for x in rec["nce"]}) if "nce" in rec.columns else None,
            "observed_instruments": sorted({str(x) for x in rec["instrument"]}) if "instrument" in rec.columns else None,
        }
    return {
        "study_id": STUDY_ID,
        "freeze_ref": FREEZE_REF,
        "artifact": "prediction inputs for the CE interface adjudication, Design A step 30",
        "generator": {
            "path": str(Path(__file__).resolve().relative_to(ROOT)),
            "sha256": sha256_file(Path(__file__).resolve()),
        },
        "inherited_from": {
            "harness": "scripts/comparator_benchmark/run_predictions.py",
            "container_env": "scripts/comparator_benchmark/modal_app.py",
            "provenance_record": "artifacts/comparator_benchmark/technical/t1/t1_provenance.json",
            "notes": "artifacts/ce_interface_adjudication/design_a/notes/prediction_harness_provenance.md",
        },
        "population": {
            "compounds_csv": str(compounds_csv.relative_to(ROOT)) if compounds_csv.is_relative_to(ROOT) else str(compounds_csv),
            "compounds_csv_sha256": sha256_file(compounds_csv),
            "n_compounds": int(len(pop)),
            "fold_filter": fold,
            "nce_rungs": list(NCE_RUNGS),
            "n_cells_per_model_mapping": int(len(pop) * len(NCE_RUNGS)),
            "records_csv": records,
        },
        "mappings": MAPPING_DEFINITIONS,
        "fixed_tokens": {"ionization": IONIZATION, "instrument": INSTRUMENT,
                         "collision_energies_format": "str([repr(float(ce))]), e.g. \"['19.9998']\""},
        "seeded_run": {
            "wrapper": "scripts/comparator_benchmark/container/seeded_run.py",
            "wrapper_sha256": sha256_file(COMPARATOR_CONTAINER / "seeded_run.py")
            if (COMPARATOR_CONTAINER / "seeded_run.py").exists() else None,
            "seed": 42,
        },
        "hdf5_dump": {
            "parser": "scripts/comparator_benchmark/container/mspred_h5_to_json.py",
            "parser_sha256": sha256_file(COMPARATOR_CONTAINER / "mspred_h5_to_json.py")
            if (COMPARATOR_CONTAINER / "mspred_h5_to_json.py").exists() else None,
            "appended_command": DUMP,
        },
        "ms_pred": {"repository": "https://github.com/coleygroup/ms-pred", "commit": MS_PRED_COMMIT,
                    "local_clone": MS_PRED_REPO},
        "environment": MSPRED_ENV,
        "models": {
            name: {
                "display_name": m["display_name"],
                "entry_script": m["entry_script"],
                "command": m["command"] + DUMP,
                "emit_precursor_column": m["emit_precursor"],
                "checkpoints": m["checkpoints"],
            }
            for name, m in MODELS.items()
        },
        "files": files,
    }


def emit_inputs(compounds_csv: Path, records_csv: Path, out_dir: Path, fold: str = "all") -> dict:
    """Write one TSV per (model, mapping) plus the manifest. Contacts no model."""
    pop = load_population(compounds_csv, fold=fold)
    out_dir.mkdir(parents=True, exist_ok=True)
    files: dict[str, dict] = {}
    seen_specs: set[tuple[str, str, str]] = set()
    for model in sorted(MODELS):
        spec_cfg = MODELS[model]
        for mapping in sorted(MAPPINGS):
            rows = build_rows(pop, mapping, spec_cfg["emit_precursor"])
            for row in rows:
                cell = (model, mapping, row["spec"])
                if cell in seen_specs:
                    raise SystemExit(f"refusing: duplicate cell {cell}")
                seen_specs.add(cell)
            payload = rows_to_tsv_bytes(rows)
            name = input_filename(model, mapping)
            (out_dir / name).write_bytes(payload)
            files[name] = {
                "model": model,
                "mapping": mapping,
                "sha256": sha256_bytes(payload),
                "bytes": len(payload),
                "n_rows": len(rows),
                "command": spec_cfg["command"] + DUMP,
                "uploaded_as": "in.tsv",
            }
    manifest = build_manifest(pop, files, compounds_csv, records_csv, fold)
    (out_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=1, sort_keys=False) + "\n")
    return manifest


# ----------------------------------------------------------------------------------------------------------------
# execute-mode preconditions (each refusal is a hard SystemExit naming the missing precondition)
# ----------------------------------------------------------------------------------------------------------------

def require_execute_env(env: dict | None = None) -> None:
    env = os.environ if env is None else env
    value = env.get(EXECUTE_ENV_VAR)
    if value != "1":
        raise SystemExit(
            f"refusing to execute: missing precondition 1 of 3, environment variable {EXECUTE_ENV_VAR}=1 "
            f"(observed: {value!r}). Execution of the two public checkpoints is not authorized without it."
        )


def require_freeze_ref(repo: Path | None = None) -> str:
    repo = ROOT if repo is None else repo
    sha = git_out(repo, "rev-parse", "--verify", FREEZE_REF)
    if not sha:
        raise SystemExit(
            f"refusing to execute: missing precondition 2 of 3, the study freeze ref {FREEZE_REF} does not "
            f"resolve in {repo}. The preregistration is not frozen, so no prediction may be generated."
        )
    return sha


def require_manifest_match(in_dir: Path | None = None) -> dict:
    in_dir = IN_DIR if in_dir is None else in_dir
    manifest_path = in_dir / MANIFEST_NAME
    if not manifest_path.exists():
        raise SystemExit(
            f"refusing to execute: missing precondition 3 of 3, no input manifest at {manifest_path}. "
            f"Run `emit-inputs` first."
        )
    manifest = json.loads(manifest_path.read_text())
    problems: list[str] = []
    for name, rec in manifest["files"].items():
        p = in_dir / name
        if not p.exists():
            problems.append(f"{name}: missing")
            continue
        got = sha256_file(p)
        if got != rec["sha256"]:
            problems.append(f"{name}: sha256 {got} != manifest {rec['sha256']}")
    expected = {input_filename(m, k) for m in MODELS for k in MAPPINGS}
    for name in sorted(expected - set(manifest["files"])):
        problems.append(f"{name}: absent from the manifest")
    if problems:
        raise SystemExit(
            "refusing to execute: missing precondition 3 of 3, input files do not match the manifest:\n  "
            + "\n  ".join(problems)
        )
    return manifest


def verify_checkpoints(manifest: dict) -> dict[str, str]:
    """Hash the checkpoint files on disk without loading them. Pure file IO, no torch."""
    observed: dict[str, str] = {}
    problems: list[str] = []
    for model, cfg in manifest["models"].items():
        for container_path, rec in cfg["checkpoints"].items():
            host = Path(rec["host_path"])
            if not host.exists():
                problems.append(f"{model} {container_path}: {host} not found")
                continue
            got = sha256_file(host)
            observed[container_path] = got
            if got != rec["sha256"]:
                problems.append(f"{model} {container_path}: sha256 {got} != expected {rec['sha256']}")
    if problems:
        raise SystemExit("refusing to execute: checkpoint identity check failed:\n  " + "\n  ".join(problems))
    return observed


# ----------------------------------------------------------------------------------------------------------------
# Provenance capture written next to the execute-mode outputs (modelled on t1_provenance.py)
# ----------------------------------------------------------------------------------------------------------------

def collect_provenance(manifest: dict, observed_checkpoint_sha: dict[str, str],
                       freeze_sha: str, container_env_freeze: str | None = None) -> dict:
    """Environment, package versions, checkpoint hashes, git HEAD and ms-pred commit at execution time.

    Structured after artifacts/comparator_benchmark/technical/t1/t1_provenance.json. Reads files only.
    """
    import platform
    from datetime import datetime, timezone

    ms_pred_repo = Path(MS_PRED_REPO)
    return {
        "study_id": STUDY_ID,
        "recorded_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "freeze_ref": FREEZE_REF,
        "freeze_ref_sha": freeze_sha,
        "muru_repo": {
            "git_head": git_out(ROOT, "rev-parse", "HEAD"),
            "git_branch": git_out(ROOT, "rev-parse", "--abbrev-ref", "HEAD"),
            "git_status_porcelain": git_out(ROOT, "status", "--porcelain"),
        },
        "driver_platform": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "execution_platform": (
            "Modal, Linux x86_64 (gVisor), CPU only; image `mspred_image` defined in "
            "scripts/comparator_benchmark/modal_app.py and reused unchanged"
        ),
        "ms_pred": {
            "repository": "https://github.com/coleygroup/ms-pred",
            "commit_expected": MS_PRED_COMMIT,
            "commit_observed": git_out(ms_pred_repo, "rev-parse", "HEAD"),
            "commit_date_observed": git_out(ms_pred_repo, "log", "-1", "--format=%cI"),
            "install": "uv sync --extra cpu, UV_EXCLUDE_NEWER=2026-09-04T05:12:22Z",
        },
        "checkpoints": {
            model: {
                container_path: {
                    "host_path": rec["host_path"],
                    "sha256_expected": rec["sha256"],
                    "sha256_observed": observed_checkpoint_sha.get(container_path),
                    "bytes_expected": rec["bytes"],
                }
                for container_path, rec in cfg["checkpoints"].items()
            }
            for model, cfg in manifest["models"].items()
        },
        "environment": MSPRED_ENV,
        "container_package_freeze": container_env_freeze,
        "reference_environment_freeze": {
            "path": "artifacts/comparator_benchmark/technical/t1/mspred_env_freeze.txt",
            "sha256": "a7ff2fcea09a4541748b85aae63bf13fc579fe8e7ed796251abc0d47f9782b78",
        },
        "input_manifest": {
            "path": str((IN_DIR / MANIFEST_NAME).relative_to(ROOT)),
            "sha256": sha256_file(IN_DIR / MANIFEST_NAME) if (IN_DIR / MANIFEST_NAME).exists() else None,
            "generator_sha256": manifest["generator"]["sha256"],
        },
        "mappings": MAPPING_DEFINITIONS,
        "commands": {model: cfg["command"] for model, cfg in manifest["models"].items()},
    }


# ----------------------------------------------------------------------------------------------------------------
# execute (inert until every precondition above is satisfied)
# ----------------------------------------------------------------------------------------------------------------

def execute(in_dir: Path | None = None, out_dir: Path | None = None) -> int:
    in_dir = IN_DIR if in_dir is None else in_dir
    out_dir = OUT_DIR if out_dir is None else out_dir

    # Gate order is load-bearing: nothing is imported, hashed or launched before the authorization checks pass.
    require_execute_env()
    freeze_sha = require_freeze_ref()
    manifest = require_manifest_match(in_dir)
    observed_ckpt = verify_checkpoints(manifest)

    sys.path.insert(0, str(ROOT / "scripts/comparator_benchmark"))
    import modal_app as MA   # noqa: PLC0415  (deliberately late: keeps emit-inputs free of modal and torch)

    out_dir.mkdir(parents=True, exist_ok=True)
    seeded = (COMPARATOR_CONTAINER / "seeded_run.py").read_bytes()
    parser = (COMPARATOR_CONTAINER / "mspred_h5_to_json.py").read_bytes()
    run_record: dict[str, dict] = {}
    container_freeze = None
    with MA.app.run():
        for name, rec in sorted(manifest["files"].items()):
            tsv = (in_dir / name).read_bytes()
            res = MA.mspred_run.remote(
                rec["command"],
                {"in.tsv": tsv, "parse.py": parser, "seeded_run.py": seeded},
                ["spectra.json", "out/preds.hdf5"],
            )
            if res["returncode"] != 0:
                raise SystemExit(f"execution failed for {name} (returncode {res['returncode']}):\n{res['stderr']}")
            tag = f"{rec['model']}__{rec['mapping']}"
            (out_dir / f"{tag}_preds.hdf5").write_bytes(res["outputs"]["out/preds.hdf5"])
            (out_dir / f"{tag}_spectra.json").write_bytes(res["outputs"]["spectra.json"])
            run_record[tag] = {
                "input_file": name,
                "input_sha256": rec["sha256"],
                "command": rec["command"],
                "platform": res["platform"],
                "machine": res["machine"],
                "output_sha256": res["output_sha256"],
            }
        container_freeze = MA.mspred_env.remote()
    prov = collect_provenance(manifest, observed_ckpt, freeze_sha, container_env_freeze=container_freeze)
    prov["runs"] = run_record
    prov["outputs"] = {p.name: sha256_file(p) for p in sorted(out_dir.glob("*")) if p.name != "execution_provenance.json"}
    (out_dir / "execution_provenance.json").write_text(json.dumps(prov, indent=1) + "\n")
    print(json.dumps({"runs": sorted(run_record), "out_dir": str(out_dir)}, indent=1))
    return 0


# ----------------------------------------------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=["emit-inputs", "execute"])
    ap.add_argument("--compounds-csv", type=Path, default=POP_DIR / "design_a_compounds.csv")
    ap.add_argument("--records-csv", type=Path, default=POP_DIR / "design_a_records.csv")
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="emit-inputs: where the TSVs and manifest are written (default the study prediction_inputs dir)")
    ap.add_argument("--fold", default="all", help="restrict to a fold of the population's 'fold' column")
    args = ap.parse_args(argv)

    if args.mode == "emit-inputs":
        out_dir = args.out_dir if args.out_dir is not None else IN_DIR
        manifest = emit_inputs(args.compounds_csv, args.records_csv, out_dir, fold=args.fold)
        print(json.dumps({
            "out_dir": str(out_dir),
            "n_compounds": manifest["population"]["n_compounds"],
            "nce_rungs": manifest["population"]["nce_rungs"],
            "files": {k: v["sha256"] for k, v in manifest["files"].items()},
        }, indent=1))
        return 0

    in_dir = args.out_dir if args.out_dir is not None else IN_DIR
    return execute(in_dir=in_dir)


if __name__ == "__main__":
    raise SystemExit(main())
