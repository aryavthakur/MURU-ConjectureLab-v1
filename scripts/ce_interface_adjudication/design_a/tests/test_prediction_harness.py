"""Tests for the Design A CE interface adjudication prediction harness.

Nothing here runs a model, loads a checkpoint or touches the network. The fixture is a synthetic 5-compound
population, chosen so that the K2/K3 boundary cases are unambiguous:

  FIXT_02  theoretical_mh = 500.0     K1 and K2 must be bit-identical at both rungs
  FIXT_03  theoretical_mh = 333.33    K2 at NCE 30 is 19.9998, just below 20, so floor(K2) = 19 is unambiguous
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

HARNESS = Path(__file__).resolve().parents[1] / "30_run_predictions.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("design_a_30_run_predictions", HARNESS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = _load_module()


FIXTURE_ROWS = [
    # compound_id, representative_smiles, formula, theoretical_mh, scaffold_group
    ("FIXT_01", "CCO", "C2H6O", 47.049, "SG_A"),
    ("FIXT_02", "c1ccccc1", "C6H6", 500.0, "SG_B"),          # K1 == K2 exactly
    ("FIXT_03", "CC(=O)Oc1ccccc1C(=O)O", "C9H8O4", 333.33, "SG_C"),   # K2(30) = 19.9998 -> floor 19
    ("FIXT_04", "CN1C=NC2=C1C(=O)N(C)C(=O)N2C", "C8H10N4O2", 250.05, "SG_C"),
    ("FIXT_05", "OCC1OC(O)C(O)C(O)C1O", "C6H12O6", 995.556, "SG_D"),
]


@pytest.fixture()
def population(tmp_path: Path) -> Path:
    p = tmp_path / "design_a_compounds.csv"
    lines = ["compound_id,representative_smiles,formula,theoretical_mh,scaffold_group"]
    # deliberately shuffled relative to sorted compound_id order, to prove the harness sorts
    for cid, smi, form, mh, sg in [FIXTURE_ROWS[3], FIXTURE_ROWS[0], FIXTURE_ROWS[4], FIXTURE_ROWS[2], FIXTURE_ROWS[1]]:
        lines.append(f"{cid},{smi},{form},{mh!r},{sg}")
    p.write_text("\n".join(lines) + "\n")
    return p


@pytest.fixture()
def emitted(tmp_path: Path, population: Path):
    out = tmp_path / "prediction_inputs"
    manifest = H.emit_inputs(population, tmp_path / "design_a_records.csv", out)
    return out, manifest


# ------------------------------------------------------------------------------------------------------
# 1. The three frozen mappings
# ------------------------------------------------------------------------------------------------------

def test_k1_is_the_raw_nce():
    for nce in (30, 60):
        for mh in (47.049, 500.0, 995.556):
            assert H.k1(nce, mh) == float(nce)
            assert isinstance(H.k1(nce, mh), float)


def test_k2_is_exact_binary64_product_quotient():
    for nce in (30, 60):
        for mh in (47.049, 333.33, 250.05, 995.556):
            assert H.k2(nce, mh) == float(nce) * mh / 500.0
    # explicit literals, computed independently of the harness expression
    assert H.k2(30, 333.33) == 19.9998
    assert H.k2(60, 333.33) == 39.9996
    assert H.k2(30, 250.05) == 15.003
    assert H.k2(30, 995.556) == 59.73336


def test_k2_just_below_an_integer_makes_k3_unambiguous():
    v = H.k2(30, 333.33)
    assert v < 20.0 and v > 19.99, v
    assert H.k3(30, 333.33) == 19.0
    assert isinstance(H.k3(30, 333.33), float)
    # a second, tighter case
    assert H.k2(30, 166.65) == 9.999
    assert H.k3(30, 166.65) == 9.0


def test_k3_floors_toward_negative_infinity_and_returns_float():
    for nce in (30, 60):
        for mh in (47.049, 333.33, 250.05, 500.0, 995.556):
            expected = float(math.floor(float(nce) * mh / 500.0))
            got = H.k3(nce, mh)
            assert got == expected
            assert type(got) is float


def test_k1_and_k2_bit_identical_at_mh_exactly_500():
    for nce in (30, 60):
        a, b = H.k1(nce, 500.0), H.k2(nce, 500.0)
        assert a == b
        # bit-level identity, not just numeric equality
        import struct
        assert struct.pack(">d", a) == struct.pack(">d", b)
        assert repr(a) == repr(b)
        assert H.format_collision_energies(a) == H.format_collision_energies(b)


def test_exactly_three_mappings_are_declared():
    assert sorted(H.MAPPINGS) == ["K1", "K2", "K3"]
    assert sorted(H.MAPPING_DEFINITIONS) == ["K1", "K2", "K3"]


# ------------------------------------------------------------------------------------------------------
# 2. collision_energies formatting, byte for byte against the comparator convention
# ------------------------------------------------------------------------------------------------------

def _comparator_formatting(value: float) -> str:
    """The frozen comparator expression, scripts/comparator_benchmark/run_predictions.py:136."""
    return str([repr(value)])


@pytest.mark.parametrize("value", [30.0, 60.0, 19.9998, 39.9996, 9.999, 15.003, 59.73336, 19.0, 9.0])
def test_collision_energies_field_matches_comparator_byte_for_byte(value):
    assert H.format_collision_energies(value) == _comparator_formatting(value)


def test_collision_energies_field_shape_and_container_roundtrip():
    s = H.format_collision_energies(19.9998)
    assert s == "['19.9998']"
    parsed = ast.literal_eval(s)                      # ms-pred predict_smis.prepare_entry
    assert isinstance(parsed, list) and len(parsed) == 1 and isinstance(parsed[0], str)
    assert float(parsed[0].split()[0]) == 19.9998     # common.collision_energy_to_float


def test_emitted_field_matches_the_comparator_expression_for_every_cell(emitted):
    out, manifest = emitted
    import csv
    for name, rec in manifest["files"].items():
        with open(out / name, newline="") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                cid, nce = row["spec"].rsplit("_NCE", 1)
                mh = dict((c[0], c[3]) for c in FIXTURE_ROWS)[cid]
                expected = _comparator_formatting(H.MAPPINGS[rec["mapping"]](int(nce), mh))
                assert row["collision_energies"] == expected


# ------------------------------------------------------------------------------------------------------
# 3. Cell coverage, uniqueness, determinism
# ------------------------------------------------------------------------------------------------------

def test_one_file_per_model_mapping(emitted):
    out, manifest = emitted
    assert sorted(manifest["files"]) == sorted(
        H.input_filename(m, k) for m in H.MODELS for k in H.MAPPINGS
    )
    assert len(manifest["files"]) == 2 * 3


def test_every_cell_appears_exactly_once_with_unique_spec_ids(emitted):
    out, manifest = emitted
    import csv
    expected_specs = {f"{cid}_NCE{n}" for cid, *_ in FIXTURE_ROWS for n in H.NCE_RUNGS}
    assert len(expected_specs) == 5 * 2
    for name, rec in manifest["files"].items():
        with open(out / name, newline="") as f:
            specs = [row["spec"] for row in csv.DictReader(f, delimiter="\t")]
        assert len(specs) == len(set(specs)) == 10, name
        assert set(specs) == expected_specs, name
        assert rec["n_rows"] == 10


def test_row_order_is_deterministic_and_sorted(emitted):
    out, manifest = emitted
    import csv
    expected = [f"{cid}_NCE{n}" for cid in sorted(c[0] for c in FIXTURE_ROWS) for n in H.NCE_RUNGS]
    for name in manifest["files"]:
        with open(out / name, newline="") as f:
            specs = [row["spec"] for row in csv.DictReader(f, delimiter="\t")]
        assert specs == expected, name


def test_column_set_and_order_match_the_comparator(emitted):
    out, manifest = emitted
    for name, rec in manifest["files"].items():
        header = (out / name).read_bytes().split(b"\n")[0].decode()
        cols = header.split("\t")
        if H.MODELS[rec["model"]]["emit_precursor"]:
            assert cols == ["spec", "smiles", "ionization", "collision_energies", "instrument", "precursor"]
        else:
            assert cols == ["spec", "smiles", "ionization", "collision_energies", "instrument"]


def test_fixed_tokens(emitted):
    out, manifest = emitted
    import csv
    for name in manifest["files"]:
        with open(out / name, newline="") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                assert row["ionization"] == "[M+H]+"
                assert row["instrument"] == "Orbitrap"


def test_repeated_runs_are_byte_identical(tmp_path: Path, population: Path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    H.emit_inputs(population, tmp_path / "records.csv", a)
    H.emit_inputs(population, tmp_path / "records.csv", b)
    names = sorted(p.name for p in a.glob("*.tsv"))
    assert names
    for n in names:
        assert (a / n).read_bytes() == (b / n).read_bytes(), n
    # the manifest carries no timestamp, so it is byte-identical too
    assert (a / H.MANIFEST_NAME).read_bytes() == (b / H.MANIFEST_NAME).read_bytes()


def test_input_row_order_independent_of_population_file_order(tmp_path: Path, population: Path):
    shuffled = tmp_path / "shuffled.csv"
    head, *rows = population.read_text().strip().split("\n")
    shuffled.write_text("\n".join([head] + list(reversed(rows))) + "\n")
    a, b = tmp_path / "a", tmp_path / "b"
    H.emit_inputs(population, tmp_path / "r.csv", a)
    H.emit_inputs(shuffled, tmp_path / "r.csv", b)
    for p in sorted(a.glob("*.tsv")):
        assert p.read_bytes() == (b / p.name).read_bytes(), p.name


def test_precursor_column_is_unmapped_theoretical_mh(emitted):
    out, manifest = emitted
    import csv
    for name, rec in manifest["files"].items():
        if not H.MODELS[rec["model"]]["emit_precursor"]:
            continue
        with open(out / name, newline="") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                cid = row["spec"].rsplit("_NCE", 1)[0]
                mh = dict((c[0], c[3]) for c in FIXTURE_ROWS)[cid]
                assert float(row["precursor"]) == mh, (name, cid)


# ------------------------------------------------------------------------------------------------------
# 4. Manifest content
# ------------------------------------------------------------------------------------------------------

def test_manifest_records_hashes_commands_checkpoints_and_env(emitted):
    out, manifest = emitted
    on_disk = json.loads((out / H.MANIFEST_NAME).read_text())
    assert on_disk == manifest
    for name, rec in manifest["files"].items():
        assert rec["sha256"] == hashlib.sha256((out / name).read_bytes()).hexdigest()
        assert "--dataset-labels $WORK/in.tsv" in rec["command"]
        assert rec["command"].endswith(H.DUMP)
    assert manifest["environment"] == {"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
                                       "TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD": "1"}
    assert manifest["seeded_run"]["seed"] == 42
    ice = manifest["models"]["iceberg_2_1_msg_simulation"]["checkpoints"]
    assert ice["/ckpt/iceberg21_msg_simulation/gen/best.ckpt"]["sha256"] == \
        "1eda5f3d9cda8345a93c0c480c3c848de840a611017a3f1641007fec1afb7a70"
    assert ice["/ckpt/iceberg21_msg_simulation/inten_contr/best.ckpt"]["sha256"] == \
        "e074c0392638a71589e68d80acfd9ad53ae0587c523249cfa90e04ee50ee4f58"
    gla = manifest["models"]["glacier_msg"]["checkpoints"]
    assert gla["/ckpt/glacier_msg/best.ckpt"]["sha256"] == \
        "5a47cecca707d3abd5a49c7dbac99d100aa2a586d5d4f848f1e8e35140d7db11"
    assert manifest["ms_pred"]["commit"] == "ed8311f22958cb37f055b663b5f56c5c77a2ee33"
    assert manifest["population"]["nce_rungs"] == [30, 60]
    assert manifest["population"]["n_compounds"] == 5


def test_no_fiora_and_no_raw_nce_sensitivity_leak_into_the_harness(emitted):
    """The comparator harness's FIORA model, its mu endpoint and its raw-NCE sensitivity condition are not inherited."""
    out, manifest = emitted
    # the parts of the manifest the study controls (paths under a pytest tmp dir are excluded by construction)
    blob = json.dumps({"models": manifest["models"], "mappings": manifest["mappings"],
                       "files": manifest["files"], "fixed_tokens": manifest["fixed_tokens"]}).lower()
    for forbidden in ("fiora", "raw_nce", "ev_primary", "spectrum_mu", "competitor_mu", "mgf"):
        assert forbidden not in blob, forbidden
    src = HARNESS.read_text().lower()
    for forbidden in ("fiora_cmd", "parse_mgf", "mu_rows", "spectrum_mu", "external_multims2", "raw_nce_sensitivity"):
        assert forbidden not in src, forbidden
    assert sorted(manifest["models"]) == ["glacier_msg", "iceberg_2_1_msg_simulation"]


# ------------------------------------------------------------------------------------------------------
# 5. Execute-mode refusals, one precondition per test
# ------------------------------------------------------------------------------------------------------

def test_execute_refuses_without_the_environment_variable(monkeypatch, emitted):
    monkeypatch.delenv(H.EXECUTE_ENV_VAR, raising=False)
    with pytest.raises(SystemExit) as e:
        H.require_execute_env()
    assert H.EXECUTE_ENV_VAR in str(e.value)
    assert "precondition 1 of 3" in str(e.value)
    # the CLI entry point stops at the same gate
    out, _ = emitted
    with pytest.raises(SystemExit) as e2:
        H.main(["execute", "--out-dir", str(out)])
    assert H.EXECUTE_ENV_VAR in str(e2.value)


def test_execute_refuses_on_a_wrong_environment_variable_value(monkeypatch):
    monkeypatch.setenv(H.EXECUTE_ENV_VAR, "true")
    with pytest.raises(SystemExit) as e:
        H.require_execute_env()
    assert H.EXECUTE_ENV_VAR in str(e.value)


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "t"], check=True)
    (path / "f").write_text("x\n")
    subprocess.run(["git", "-C", str(path), "add", "f"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-qm", "c"], check=True)
    return path


def test_execute_refuses_without_the_freeze_ref(tmp_path: Path, monkeypatch):
    monkeypatch.setenv(H.EXECUTE_ENV_VAR, "1")
    repo = _init_repo(tmp_path / "repo")
    with pytest.raises(SystemExit) as e:
        H.require_freeze_ref(repo)
    assert H.FREEZE_REF in str(e.value)
    assert "precondition 2 of 3" in str(e.value)


def test_freeze_ref_gate_passes_once_the_ref_exists(tmp_path: Path, monkeypatch):
    monkeypatch.setenv(H.EXECUTE_ENV_VAR, "1")
    repo = _init_repo(tmp_path / "repo")
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    subprocess.run(["git", "-C", str(repo), "update-ref", H.FREEZE_REF, head], check=True)
    assert H.require_freeze_ref(repo) == head


def test_execute_refuses_on_a_manifest_hash_mismatch(emitted):
    out, manifest = emitted
    assert H.require_manifest_match(out) == manifest      # clean state passes
    victim = sorted(manifest["files"])[0]
    p = out / victim
    p.write_bytes(p.read_bytes() + b"# tampered\n")
    with pytest.raises(SystemExit) as e:
        H.require_manifest_match(out)
    msg = str(e.value)
    assert "precondition 3 of 3" in msg
    assert victim in msg
    assert manifest["files"][victim]["sha256"] in msg


def test_execute_refuses_on_a_missing_input_file(emitted):
    out, manifest = emitted
    victim = sorted(manifest["files"])[0]
    (out / victim).unlink()
    with pytest.raises(SystemExit) as e:
        H.require_manifest_match(out)
    assert f"{victim}: missing" in str(e.value)


def test_execute_refuses_without_a_manifest(tmp_path: Path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(SystemExit) as e:
        H.require_manifest_match(empty)
    assert "no input manifest" in str(e.value)


# ------------------------------------------------------------------------------------------------------
# 6. Guard: no torch at import time, no model contact in emit-inputs mode
# ------------------------------------------------------------------------------------------------------

def test_source_has_no_module_level_torch_or_modal_import():
    tree = ast.parse(HARNESS.read_text())
    banned = {"torch", "modal", "ms_pred", "pytorch_lightning", "rdkit", "muru"}
    for node in tree.body:                      # module level only
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name.split(".")[0] not in banned, a.name
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned, node.module


def test_importing_the_module_loads_no_torch_and_emit_inputs_contacts_no_model(tmp_path: Path, population: Path):
    script = tmp_path / "guard.py"
    script.write_text(textwrap.dedent(f"""
        import importlib.util, json, sys
        from pathlib import Path

        WATCH = ("torch", "modal", "ms_pred", "pytorch_lightning", "rdkit")
        spec = importlib.util.spec_from_file_location("h", {str(HARNESS)!r})
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        after_import = sorted(m for m in WATCH if m in sys.modules)
        mod.emit_inputs(Path({str(population)!r}), Path({str(tmp_path / 'rec.csv')!r}),
                        Path({str(tmp_path / 'guard_out')!r}))
        after_emit = sorted(m for m in WATCH if m in sys.modules)
        print(json.dumps({{"after_import": after_import, "after_emit": after_emit}}))
    """))
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    got = json.loads(r.stdout.strip().splitlines()[-1])
    assert got["after_import"] == []
    assert got["after_emit"] == []


def test_emit_inputs_writes_only_into_its_output_directory(tmp_path: Path, population: Path):
    out = tmp_path / "only_here"
    H.emit_inputs(population, tmp_path / "rec.csv", out)
    produced = sorted(p.name for p in out.iterdir())
    assert produced == sorted([H.MANIFEST_NAME] + [H.input_filename(m, k) for m in H.MODELS for k in H.MAPPINGS])
    # nothing else appeared beside the population file in tmp_path
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(["design_a_compounds.csv", "only_here"])


# ------------------------------------------------------------------------------------------------------
# 7. Population validation
# ------------------------------------------------------------------------------------------------------

def test_missing_population_file_is_a_hard_refusal(tmp_path: Path):
    with pytest.raises(SystemExit) as e:
        H.load_population(tmp_path / "nope.csv")
    assert "population file not found" in str(e.value)


def test_missing_required_column_is_a_hard_refusal(tmp_path: Path):
    p = tmp_path / "bad.csv"
    p.write_text("compound_id,representative_smiles\nA,CCO\n")
    with pytest.raises(SystemExit) as e:
        H.load_population(p)
    assert "theoretical_mh" in str(e.value)


def test_duplicate_compound_id_is_a_hard_refusal(tmp_path: Path):
    p = tmp_path / "dup.csv"
    p.write_text("compound_id,representative_smiles,theoretical_mh\nA,CCO,100.0\nA,CCO,100.0\n")
    with pytest.raises(SystemExit) as e:
        H.load_population(p)
    assert "duplicate compound_id" in str(e.value)
