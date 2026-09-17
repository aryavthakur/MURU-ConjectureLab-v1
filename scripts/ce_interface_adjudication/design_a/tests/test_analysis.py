"""Tests for the frozen Design A analysis. Synthetic data only; no real outcome data is read."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "50_analysis.py"
_spec = importlib.util.spec_from_file_location("ce_design_a_analysis", MODULE_PATH)
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

SMALL_B = 2000


# --------------------------------------------------------------------------------------------
# synthetic fixtures
# --------------------------------------------------------------------------------------------

def synth(n_compounds=60, mapping_means=None, group_size=1, model_offsets=None,
          nce_offsets=None, replicates=2, noise=0.02, seed=7, compound_spread=0.05):
    """Balanced synthetic score table plus its population manifest.

    mapping_means fixes the planted mapping effect; a per-compound offset common to all mappings
    creates the pairing that the paired bootstrap exploits.
    """
    mapping_means = mapping_means or {"K1": 0.60, "K2": 0.60, "K3": 0.60}
    model_offsets = model_offsets or {m: {} for m in A.MODELS}
    nce_offsets = nce_offsets or {}
    rng = np.random.default_rng(seed)
    ids = [f"C{i:03d}" for i in range(n_compounds)]
    groups = [f"G{i // group_size:03d}" for i in range(n_compounds)]
    pop = pd.DataFrame({"compound_id": ids, "scaffold_group": groups})
    shift = {c: float(rng.normal(0.0, compound_spread)) for c in ids}
    rows = []
    rid = 0
    for c, g in zip(ids, groups):
        for model in A.MODELS:
            for mapping in A.MAPPINGS:
                for nce in A.NCE_CELLS:
                    for _ in range(replicates):
                        v = (mapping_means[mapping] + shift[c]
                             + model_offsets.get(model, {}).get(mapping, 0.0)
                             + nce_offsets.get(nce, 0.0)
                             + float(rng.normal(0.0, noise)))
                        rows.append({"record_id": f"R{rid:06d}", "compound_id": c,
                                     "scaffold_group": g, "nce": nce, "model": model,
                                     "mapping": mapping, "cosine": v, "js": v * 0.9 + 0.01})
                        rid += 1
    return pd.DataFrame(rows), pop


def make_root(tmp_path, scores, pop, freeze=True, hashes="correct"):
    """Build a throwaway git repo with the frozen inputs and their recorded hashes."""
    root = Path(tmp_path) / "repo"
    (root / "artifacts/ce_interface_adjudication/design_a/scores").mkdir(parents=True, exist_ok=True)
    (root / "artifacts/ce_interface_adjudication/design_a/population").mkdir(parents=True, exist_ok=True)
    (root / "artifacts/ce_interface_adjudication/design_a/freeze").mkdir(parents=True, exist_ok=True)
    s_path, p_path = root / A.SCORES_REL, root / A.POPULATION_REL
    scores.to_csv(s_path, index=False)
    pop.to_csv(p_path, index=False)
    sha = {A.SCORES_REL: A.sha256_file(s_path), A.POPULATION_REL: A.sha256_file(p_path)}
    if hashes == "mismatch":
        sha[A.SCORES_REL] = hashlib.sha256(b"not the frozen table").hexdigest()
    (root / A.INPUT_MANIFEST_REL).write_text(
        json.dumps({"prereg_id": A.PREREG_ID, "sha256": sha}, indent=1) + "\n")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q",
                    "--allow-empty", "-m", "init"], cwd=root, check=True, capture_output=True)
    if freeze:
        subprocess.run(["git", "update-ref", A.FREEZE_REF, "HEAD"], cwd=root, check=True,
                       capture_output=True)
    return root


ONE_LOOK_OK = {A.ONE_LOOK_ENV: "1"}


# --------------------------------------------------------------------------------------------
# reduction order
# --------------------------------------------------------------------------------------------

def test_reduction_order_hand_computed_with_unequal_replicate_counts():
    """Replicates are averaged BEFORE the NCE mean and the model mean.

    One compound, one mapping. ICEBERG NCE 30 has three replicates (0.90, 0.30, 0.30) and NCE 60
    has one (0.10). GLACIER NCE 30 has one (0.40) and NCE 60 two (0.60, 0.80).
      step 1: ICEBERG 30 -> 0.50, ICEBERG 60 -> 0.10, GLACIER 30 -> 0.40, GLACIER 60 -> 0.70
      step 2: ICEBERG -> 0.30, GLACIER -> 0.55
      step 3: S = 0.425
    A record-pooled mean would give 8.1/9 = 0.4111..., and a cell-pooled mean without the
    replicate step would give a different number again, so the value 0.425 pins the order.
    """
    spec = [("ICEBERG_2_1", 30, [0.90, 0.30, 0.30]), ("ICEBERG_2_1", 60, [0.10]),
            ("GLACIER", 30, [0.40]), ("GLACIER", 60, [0.60, 0.80])]
    rows, rid = [], 0
    for model, nce, vals in spec:
        for v in vals:
            rows.append({"record_id": f"R{rid}", "compound_id": "C000", "scaffold_group": "G0",
                         "nce": nce, "model": model, "mapping": "K1", "cosine": v, "js": v})
            rid += 1
    df = pd.DataFrame(rows)
    red = A.reduce_scores(df, metric="cosine")
    cell = red["cell"].set_index(["model", "nce"])["value"]
    assert cell[("ICEBERG_2_1", 30)] == pytest.approx(0.50)
    assert cell[("ICEBERG_2_1", 60)] == pytest.approx(0.10)
    assert cell[("GLACIER", 30)] == pytest.approx(0.40)
    assert cell[("GLACIER", 60)] == pytest.approx(0.70)
    pm = red["per_model"].set_index("model")["value"]
    assert pm["ICEBERG_2_1"] == pytest.approx(0.30)
    assert pm["GLACIER"] == pytest.approx(0.55)
    assert float(red["S"].loc["C000", "K1"]) == pytest.approx(0.425)
    assert float(red["S"].loc["C000", "K1"]) != pytest.approx(8.1 / 9)


def test_nce_cells_carry_equal_weight_despite_unequal_replicates():
    rows, rid = [], 0
    for nce, vals in ((30, [1.0] * 9), (60, [0.0])):
        for model in A.MODELS:
            for v in vals:
                rows.append({"record_id": f"R{rid}", "compound_id": "C000", "scaffold_group": "G0",
                             "nce": nce, "model": model, "mapping": "K1", "cosine": v, "js": v})
                rid += 1
    S = A.reduce_scores(pd.DataFrame(rows), metric="cosine")["S"]
    assert float(S.loc["C000", "K1"]) == pytest.approx(0.5)


# --------------------------------------------------------------------------------------------
# decision rule
# --------------------------------------------------------------------------------------------

def test_planted_k2_advantage_returns_supported_k2(tmp_path):
    scores, pop = synth(n_compounds=80, mapping_means={"K1": 0.55, "K2": 0.75, "K3": 0.54},
                        noise=0.01, seed=11)
    root = make_root(tmp_path, scores, pop)
    res = A.run(root, env=ONE_LOOK_OK, n_boot=SMALL_B)
    assert res["verdict"] == "SUPPORTED"
    assert res["supported_mapping"] == "K2"
    d = res["primary"]["decision"]
    assert d["criterion_a_unique_highest_score"] and d["criterion_b_all_adjusted_intervals_above_zero"]
    for ci in (v["ci_bonferroni_adjusted"] for v in d["advantage_intervals_adjusted"].values()):
        assert ci[0] > 0.0
    assert (Path(res["result_path"]).exists())
    assert json.loads(Path(res["result_path"]).read_text())["verdict"] == "SUPPORTED"


def test_no_difference_population_returns_interface_unresolved(tmp_path):
    scores, pop = synth(n_compounds=60, mapping_means={"K1": 0.6, "K2": 0.6, "K3": 0.6},
                        noise=0.03, seed=3)
    root = make_root(tmp_path, scores, pop)
    res = A.run(root, env=ONE_LOOK_OK, n_boot=SMALL_B)
    assert res["verdict"] == "INTERFACE_UNRESOLVED"
    assert res["supported_mapping"] is None
    assert res["primary"]["decision"]["reasons"]


def test_highest_score_but_one_adjusted_interval_straddles_zero_is_unresolved():
    """Criterion (a) met, criterion (b) failed on one contrast only."""
    scores = {"K1": 0.50, "K2": 0.70, "K3": 0.69}
    intervals = {"D12": [-0.25, -0.15],     # K2 beats K1 decisively
                 "D13": [-0.24, -0.14],
                 "D23": [-0.04, +0.02]}     # K2 against K3 straddles zero
    out = A.decide(scores, intervals)
    assert out["leader"] == "K2"
    assert out["criterion_a_unique_highest_score"] is True
    assert out["criterion_b_all_adjusted_intervals_above_zero"] is False
    assert out["verdict"] == "INTERFACE_UNRESOLVED"
    assert out["supported_mapping"] is None
    assert out["advantage_intervals_adjusted"]["K2_over_K1"]["ci_bonferroni_adjusted"] == [0.15, 0.25]
    assert out["advantage_intervals_adjusted"]["K2_over_K3"]["wholly_above_zero"] is False


def test_decide_supported_only_when_both_criteria_hold():
    scores = {"K1": 0.50, "K2": 0.70, "K3": 0.60}
    intervals = {"D12": [-0.25, -0.15], "D13": [-0.14, -0.06], "D23": [0.05, 0.15]}
    out = A.decide(scores, intervals)
    assert out["verdict"] == "SUPPORTED" and out["supported_mapping"] == "K2"


def test_decide_never_forces_a_selection_on_an_exact_tie():
    intervals = {"D12": [0.0, 0.0], "D13": [0.0, 0.0], "D23": [0.0, 0.0]}
    out = A.decide({"K1": 0.6, "K2": 0.6, "K3": 0.5}, intervals)
    assert out["verdict"] == "INTERFACE_UNRESOLVED" and out["supported_mapping"] is None
    assert out["tied_leaders"] == ["K1", "K2"]


def test_decide_boundary_lower_bound_exactly_zero_is_not_supported():
    intervals = {"D12": [-0.20, -0.10], "D13": [-0.10, 0.00], "D23": [0.02, 0.09]}
    out = A.decide({"K1": 0.50, "K2": 0.70, "K3": 0.60}, intervals)
    assert out["advantage_intervals_adjusted"]["K2_over_K1"]["wholly_above_zero"] is True
    assert out["verdict"] == "SUPPORTED"
    # now flip so the leader's own interval touches zero
    intervals2 = {"D12": [-0.20, -0.10], "D13": [-0.15, -0.05], "D23": [0.00, 0.09]}
    out2 = A.decide({"K1": 0.50, "K2": 0.70, "K3": 0.60}, intervals2)
    assert out2["verdict"] == "INTERFACE_UNRESOLVED"


# --------------------------------------------------------------------------------------------
# model agreement
# --------------------------------------------------------------------------------------------

def test_model_ordering_disagreement_flag_fires(tmp_path):
    scores, pop = synth(
        n_compounds=60, mapping_means={"K1": 0.60, "K2": 0.60, "K3": 0.50}, noise=0.005, seed=5,
        model_offsets={"ICEBERG_2_1": {"K1": 0.10}, "GLACIER": {"K2": 0.10}})
    root = make_root(tmp_path, scores, pop)
    res = A.run(root, env=ONE_LOOK_OK, n_boot=SMALL_B)
    ma = res["primary"]["model_agreement"]
    assert ma["MODEL_ORDERING_DISAGREEMENT"] is True
    assert res["MODEL_ORDERING_DISAGREEMENT"] is True
    assert ma["orderings_best_to_worst"]["ICEBERG_2_1"][0] == "K1"
    assert ma["orderings_best_to_worst"]["GLACIER"][0] == "K2"
    assert "MODEL ORDERING DISAGREEMENT: YES" in A.format_summary(res)


def test_model_ordering_disagreement_is_surfaced_even_when_supported(tmp_path):
    """A planted K2 win plus a model that still ranks K1 first: the flag must survive SUPPORTED."""
    scores, pop = synth(
        n_compounds=80, mapping_means={"K1": 0.50, "K2": 0.62, "K3": 0.40}, noise=0.004, seed=17,
        model_offsets={"ICEBERG_2_1": {"K1": 0.20}, "GLACIER": {"K2": 0.02}})
    root = make_root(tmp_path, scores, pop)
    res = A.run(root, env=ONE_LOOK_OK, n_boot=SMALL_B)
    assert res["verdict"] == "SUPPORTED" and res["supported_mapping"] == "K2"
    assert res["MODEL_ORDERING_DISAGREEMENT"] is True
    summary = A.format_summary(res)
    assert "MODEL ORDERING DISAGREEMENT: YES" in summary and "SUPPORTED (K2)" in summary
    assert json.loads(Path(res["result_path"]).read_text())["MODEL_ORDERING_DISAGREEMENT"] is True


def test_model_agreement_flag_is_false_when_orderings_match(tmp_path):
    scores, pop = synth(n_compounds=40, mapping_means={"K1": 0.4, "K2": 0.7, "K3": 0.5},
                        noise=0.003, seed=23)
    root = make_root(tmp_path, scores, pop)
    res = A.run(root, env=ONE_LOOK_OK, n_boot=SMALL_B)
    assert res["primary"]["model_agreement"]["MODEL_ORDERING_DISAGREEMENT"] is False


# --------------------------------------------------------------------------------------------
# determinism and order invariance
# --------------------------------------------------------------------------------------------

def _public(res):
    drop = {"result_path", "summary_path", "verdict_path"}
    return {k: v for k, v in res.items() if not k.startswith("_") and k not in drop}


def test_run_writes_the_json_the_summary_and_the_verdict(tmp_path):
    scores, pop = synth(n_compounds=20, mapping_means={"K1": 0.5, "K2": 0.62, "K3": 0.52},
                        noise=0.01, seed=157)
    root = make_root(tmp_path, scores, pop)
    res = A.run(root, env=ONE_LOOK_OK, n_boot=SMALL_B)
    assert Path(res["result_path"]).name == "analysis.json"
    assert Path(res["result_path"]).parent == root / "artifacts/ce_interface_adjudication/design_a/result"
    assert A.format_summary(res) + "\n" == Path(res["summary_path"]).read_text()
    assert Path(res["verdict_path"]).read_text().startswith("SUPPORTED\tK2\t")


def test_determinism_and_row_order_invariance(tmp_path):
    scores, pop = synth(n_compounds=50, mapping_means={"K1": 0.55, "K2": 0.62, "K3": 0.58},
                        noise=0.02, seed=31)
    root = make_root(tmp_path, scores, pop)
    a1 = _public(A.run(root, env=ONE_LOOK_OK, n_boot=SMALL_B))
    a2 = _public(A.run(root, env=ONE_LOOK_OK, n_boot=SMALL_B))
    assert json.dumps(a1, sort_keys=True) == json.dumps(a2, sort_keys=True)

    shuffled = scores.sample(frac=1.0, random_state=99).reset_index(drop=True)
    pop_shuffled = pop.sample(frac=1.0, random_state=98).reset_index(drop=True)
    root2 = make_root(tmp_path / "b", shuffled, pop_shuffled)
    a3 = _public(A.run(root2, env=ONE_LOOK_OK, n_boot=SMALL_B))
    for block in ("composite_scores", "contrasts", "replicate_weights_sha256", "decision",
                  "model_agreement", "per_nce_descriptive", "n_compounds_analysed"):
        assert json.dumps(a1["primary"][block], sort_keys=True) == \
               json.dumps(a3["primary"][block], sort_keys=True), block
    assert a1["resampling_unit_selection"] == a3["resampling_unit_selection"]


# --------------------------------------------------------------------------------------------
# bootstrap weights
# --------------------------------------------------------------------------------------------

def test_the_three_contrasts_share_identical_replicate_weights():
    scores, pop = synth(n_compounds=40, mapping_means={"K1": 0.5, "K2": 0.6, "K3": 0.55},
                        noise=0.02, seed=41)
    prep = A.prepare_records(scores, pop, metric="cosine")
    S = A.reduce_scores(prep["records"], "cosine")["S"]
    codes, uniq = A.unit_codes(list(S.index), prep["population"], "compound")
    W = A.replicate_weights(codes, len(uniq), n=SMALL_B, seed=A.BOOT_SEED)
    out = A.paired_contrasts(S, codes, len(uniq), W)
    d = out["draws"]
    # with one shared weight vector per replicate the three contrasts are exactly additive
    assert np.allclose(d["D12"] + d["D23"], d["D13"], atol=1e-12, rtol=0)
    # and the recorded weight digest is the digest of an independently redrawn W at the same seed
    W2 = A.replicate_weights(codes, len(uniq), n=SMALL_B, seed=A.BOOT_SEED)
    assert np.array_equal(W, W2)
    assert out["replicate_weights_sha256"] == hashlib.sha256(W2.tobytes()).hexdigest()


def test_module_level_bootstrap_constants_are_the_frozen_ones():
    assert A.BOOT_B == 10_000
    assert A.BOOT_SEED == 20260916
    assert A.ALPHA == 0.05 and A.N_CONTRASTS == 3
    assert A.ADJUSTED_LEVEL == pytest.approx(1.0 - 0.05 / 3)
    assert A.PRIMARY_METRIC == "cosine" and A.ROBUSTNESS_METRIC == "js"
    assert A.SCAFFOLD_CLUSTERING_NONTRIVIAL_FRACTION == 0.10


def test_full_run_at_the_frozen_b_and_seed(tmp_path):
    scores, pop = synth(n_compounds=30, mapping_means={"K1": 0.5, "K2": 0.6, "K3": 0.55},
                        noise=0.02, seed=53)
    root = make_root(tmp_path, scores, pop)
    res = A.run(root, env=ONE_LOOK_OK)
    assert res["bootstrap"]["B"] == 10_000 and res["bootstrap"]["seed"] == 20260916
    assert res["primary"]["contrasts"]["D12"]["n_boot"] == 10_000


# --------------------------------------------------------------------------------------------
# resampling-unit selection
# --------------------------------------------------------------------------------------------

def test_unit_selection_nontrivial_clustering_picks_scaffold_groups():
    ids = [f"C{i:03d}" for i in range(100)]
    groups = [f"G{i // 2:03d}" for i in range(20)] + [f"S{i:03d}" for i in range(20, 100)]
    pop = pd.DataFrame({"compound_id": ids, "scaffold_group": groups})
    sel = A.select_resampling_unit(pop)
    assert sel["n_compounds_sharing_a_scaffold_group"] == 20
    assert sel["fraction_sharing_a_scaffold_group"] == pytest.approx(0.20)
    assert sel["scaffold_clustering_nontrivial"] is True
    assert sel["unit"] == "scaffold_group" and sel["bootstrap"] == "whole_scaffold_group"
    assert "nontrivial" in sel["justification"] and "0.100000" in sel["justification"]


def test_unit_selection_trivial_clustering_picks_molecules():
    ids = [f"C{i:03d}" for i in range(100)]
    groups = [f"G{i // 2:03d}" for i in range(4)] + [f"S{i:03d}" for i in range(4, 100)]
    pop = pd.DataFrame({"compound_id": ids, "scaffold_group": groups})
    sel = A.select_resampling_unit(pop)
    assert sel["fraction_sharing_a_scaffold_group"] == pytest.approx(0.04)
    assert sel["scaffold_clustering_nontrivial"] is False
    assert sel["unit"] == "compound" and sel["bootstrap"] == "molecule_level_paired"


def test_unit_selection_is_exactly_at_the_threshold():
    ids = [f"C{i:03d}" for i in range(100)]
    groups = [f"G{i // 2:03d}" for i in range(10)] + [f"S{i:03d}" for i in range(10, 100)]
    sel = A.select_resampling_unit(pd.DataFrame({"compound_id": ids, "scaffold_group": groups}))
    assert sel["fraction_sharing_a_scaffold_group"] == pytest.approx(0.10)
    assert sel["scaffold_clustering_nontrivial"] is True


def test_scaffold_group_unit_is_used_and_recorded(tmp_path):
    scores, pop = synth(n_compounds=60, group_size=3,
                        mapping_means={"K1": 0.5, "K2": 0.6, "K3": 0.55}, noise=0.02, seed=61)
    root = make_root(tmp_path, scores, pop)
    res = A.run(root, env=ONE_LOOK_OK, n_boot=SMALL_B)
    sel = res["resampling_unit_selection"]
    assert sel["unit"] == "scaffold_group"
    assert sel["fraction_sharing_a_scaffold_group"] == pytest.approx(1.0)
    assert res["primary"]["n_resampling_units_analysed"] == 20
    assert res["primary"]["contrasts"]["D12"]["n_units"] == 20
    assert sel["justification"] in A.format_summary(res)


def test_molecule_unit_when_every_compound_has_its_own_scaffold(tmp_path):
    scores, pop = synth(n_compounds=40, group_size=1, noise=0.02, seed=67)
    root = make_root(tmp_path, scores, pop)
    res = A.run(root, env=ONE_LOOK_OK, n_boot=SMALL_B)
    assert res["resampling_unit_selection"]["unit"] == "compound"
    assert res["primary"]["n_resampling_units_analysed"] == 40


# --------------------------------------------------------------------------------------------
# mechanical completeness and the drop rule
# --------------------------------------------------------------------------------------------

def test_record_level_drop_keeps_the_compound_when_the_cell_survives():
    scores, pop = synth(n_compounds=6, replicates=3, seed=71)
    sel = ((scores.compound_id == "C002") & (scores.model == "ICEBERG_2_1")
           & (scores.mapping == "K3") & (scores.nce == 60))
    idx = scores.index[sel][0]
    scores.loc[idx, "cosine"] = np.nan
    prep = A.prepare_records(scores, pop, metric="cosine")
    rep = prep["report"]
    assert rep["n_records_dropped"] == 1
    assert rep["dropped_records"][0]["reason"] == "missing_or_non_finite_cosine"
    assert rep["n_compounds_dropped"] == 0
    assert rep["n_compounds_analysed"] == 6
    assert rep["mechanically_complete"] is True


def test_compound_losing_an_entire_cell_is_dropped_for_all_three_mappings():
    scores, pop = synth(n_compounds=6, replicates=2, seed=73)
    sel = ((scores.compound_id == "C004") & (scores.model == "GLACIER")
           & (scores.mapping == "K1") & (scores.nce == 30))
    scores.loc[sel, "cosine"] = np.nan
    prep = A.prepare_records(scores, pop, metric="cosine")
    rep = prep["report"]
    assert rep["n_records_dropped"] == 2
    assert rep["n_compounds_dropped"] == 1
    assert rep["dropped_compounds"][0]["compound_id"] == "C004"
    assert rep["dropped_compounds"][0]["reason"] == "lost_entire_nce_cell"
    assert rep["n_cells_with_no_surviving_record"] == 1
    assert "C004" not in set(prep["records"].compound_id)
    assert prep["analysed_compound_ids"] == ["C000", "C001", "C002", "C003", "C005"]
    # the drop is identical across mappings, so the comparison stays paired
    counts = prep["records"].groupby("mapping")["compound_id"].nunique()
    assert set(counts.unique()) == {5}


def test_missing_rows_are_detected_as_mechanical_incompleteness_and_drop_the_compound():
    scores, pop = synth(n_compounds=5, replicates=2, seed=79)
    sel = ((scores.compound_id == "C001") & (scores.model == "ICEBERG_2_1")
           & (scores.mapping == "K2") & (scores.nce == 60))
    scores = scores[~sel].reset_index(drop=True)
    prep = A.prepare_records(scores, pop, metric="cosine")
    rep = prep["report"]
    assert rep["mechanically_complete"] is False
    assert rep["n_cells_absent_from_score_table"] == 1
    assert rep["empty_cells"][0] == {"compound_id": "C001", "model": "ICEBERG_2_1",
                                    "mapping": "K2", "nce": 60,
                                    "reason": "cell_absent_from_score_table"}
    assert rep["n_compounds_dropped"] == 1 and rep["n_compounds_analysed"] == 4
    assert "C001" not in prep["analysed_compound_ids"]


def test_explicit_drop_reason_column_is_honoured_and_recorded():
    scores, pop = synth(n_compounds=4, replicates=2, seed=83)
    scores["drop_reason"] = ""
    sel = scores.index[(scores.compound_id == "C001") & (scores.nce == 30)
                       & (scores.mapping == "K1") & (scores.model == "GLACIER")]
    scores.loc[sel[0], "drop_reason"] = "no_readable_spectrum"
    prep = A.prepare_records(scores, pop, metric="cosine")
    rep = prep["report"]
    assert rep["n_records_dropped"] == 1
    assert rep["dropped_records"][0]["reason"] == "no_readable_spectrum"
    assert rep["n_compounds_dropped"] == 0


def test_drop_rule_end_to_end_keeps_the_analysis_paired(tmp_path):
    scores, pop = synth(n_compounds=30, mapping_means={"K1": 0.5, "K2": 0.62, "K3": 0.52},
                        noise=0.01, seed=89)
    sel = ((scores.compound_id == "C007") & (scores.model == "GLACIER")
           & (scores.mapping == "K2") & (scores.nce == 30))
    scores.loc[sel, "cosine"] = np.inf
    scores.loc[sel, "js"] = np.inf
    root = make_root(tmp_path, scores, pop)
    res = A.run(root, env=ONE_LOOK_OK, n_boot=SMALL_B)
    c = res["primary"]["completeness_and_drops"]
    assert c["n_population_manifest"] == 30 and c["n_compounds_dropped"] == 1
    assert res["primary"]["n_compounds_analysed"] == 29
    assert res["robustness_jensen_shannon"]["n_compounds_analysed"] == 29
    assert [d["compound_id"] for d in c["dropped_compounds"]] == ["C007"]
    assert res["primary"]["contrasts"]["D12"]["n_units"] == 29


def test_compounds_outside_the_population_manifest_are_excluded_and_counted():
    scores, pop = synth(n_compounds=4, replicates=1, seed=97)
    extra = scores[scores.compound_id == "C000"].copy()
    extra["compound_id"] = "C999"
    extra["scaffold_group"] = "G999"
    extra["record_id"] = extra["record_id"] + "x"
    scores = pd.concat([scores, extra], ignore_index=True)
    prep = A.prepare_records(scores, pop, metric="cosine")
    assert prep["report"]["n_compounds_outside_population_manifest"] == 1
    assert prep["report"]["compounds_outside_population_manifest"] == ["C999"]
    assert "C999" not in prep["analysed_compound_ids"]


def test_schema_violations_refuse():
    scores, pop = synth(n_compounds=3, replicates=1, seed=101)
    bad = scores.copy()
    bad.loc[0, "mapping"] = "K4"
    with pytest.raises(A.GovernanceRefusal, match="undeclared levels"):
        A.prepare_records(bad, pop)
    bad2 = scores.drop(columns=["js"])
    with pytest.raises(A.GovernanceRefusal, match="missing required column js"):
        A.prepare_records(bad2, pop)
    bad3 = scores.copy()
    bad3.loc[bad3.index[0], "scaffold_group"] = "WRONG"
    with pytest.raises(A.GovernanceRefusal, match="disagree on scaffold_group"):
        A.prepare_records(bad3, pop)


# --------------------------------------------------------------------------------------------
# Jensen-Shannon robustness lane
# --------------------------------------------------------------------------------------------

def test_jensen_shannon_runs_the_identical_pipeline_and_cannot_change_the_verdict(tmp_path):
    scores, pop = synth(n_compounds=50, mapping_means={"K1": 0.50, "K2": 0.66, "K3": 0.52},
                        noise=0.01, seed=103)
    # make the JS lane point the other way; the primary verdict must be unaffected
    scores.loc[scores.mapping == "K2", "js"] = 0.10
    root = make_root(tmp_path, scores, pop)
    res = A.run(root, env=ONE_LOOK_OK, n_boot=SMALL_B)
    assert res["verdict"] == "SUPPORTED" and res["supported_mapping"] == "K2"
    r = res["robustness_jensen_shannon"]
    assert r["decision"]["supported_mapping"] != "K2"
    assert "robustness only" in r["status"]
    assert res["primary"]["decision"]["verdict"] == "SUPPORTED"


# --------------------------------------------------------------------------------------------
# refusal paths
# --------------------------------------------------------------------------------------------

def test_refuses_without_the_one_look_environment_variable(tmp_path):
    scores, pop = synth(n_compounds=5, replicates=1, seed=107)
    root = make_root(tmp_path, scores, pop)
    with pytest.raises(A.GovernanceRefusal, match="MURU_CE_ADJUDICATION_ONE_LOOK=1"):
        A.run(root, env={}, n_boot=10)
    with pytest.raises(A.GovernanceRefusal):
        A.run(root, env={A.ONE_LOOK_ENV: "0"}, n_boot=10)
    with pytest.raises(A.GovernanceRefusal):
        A.run(root, env={A.ONE_LOOK_ENV: "true"}, n_boot=10)


def test_refuses_when_the_freeze_ref_does_not_resolve(tmp_path):
    scores, pop = synth(n_compounds=5, replicates=1, seed=109)
    root = make_root(tmp_path, scores, pop, freeze=False)
    with pytest.raises(A.GovernanceRefusal, match="freeze ref"):
        A.run(root, env=ONE_LOOK_OK, n_boot=10)


def test_refuses_on_a_score_table_hash_mismatch(tmp_path):
    scores, pop = synth(n_compounds=5, replicates=1, seed=113)
    root = make_root(tmp_path, scores, pop, hashes="mismatch")
    with pytest.raises(A.GovernanceRefusal, match="sha256 mismatch"):
        A.run(root, env=ONE_LOOK_OK, n_boot=10)


def test_refuses_when_an_input_is_edited_after_the_manifest_was_frozen(tmp_path):
    scores, pop = synth(n_compounds=5, replicates=1, seed=127)
    root = make_root(tmp_path, scores, pop)
    edited = scores.copy()
    edited.loc[0, "cosine"] = 0.123456
    edited.to_csv(root / A.SCORES_REL, index=False)
    with pytest.raises(A.GovernanceRefusal, match="sha256 mismatch"):
        A.run(root, env=ONE_LOOK_OK, n_boot=10)


def test_step10_manifest_layout_is_accepted(tmp_path):
    """The population manifest's digest may be recorded under outputs_written by step 10."""
    scores, pop = synth(n_compounds=6, replicates=1, seed=149)
    root = make_root(tmp_path, scores, pop)
    sha_scores = A.sha256_file(root / A.SCORES_REL)
    sha_pop = A.sha256_file(root / A.POPULATION_REL)
    (root / A.INPUT_MANIFEST_REL).write_text(json.dumps(
        {"sha256": {A.SCORES_REL: sha_scores}, "outputs_written": {A.POPULATION_REL: sha_pop}}) + "\n")
    res = A.run(root, env=ONE_LOOK_OK, n_boot=10)
    assert res["governance"]["sha256_observed"][A.POPULATION_REL] == sha_pop


def test_refuses_when_a_path_carries_two_different_recorded_digests():
    with pytest.raises(A.GovernanceRefusal, match="two different sha256"):
        A.recorded_hashes({"sha256": {A.SCORES_REL: "a" * 64},
                           "outputs_written": {A.SCORES_REL: "b" * 64}})


def test_refuses_when_a_required_input_has_no_recorded_hash(tmp_path):
    scores, pop = synth(n_compounds=5, replicates=1, seed=151)
    root = make_root(tmp_path, scores, pop)
    (root / A.INPUT_MANIFEST_REL).write_text(json.dumps(
        {"sha256": {A.SCORES_REL: A.sha256_file(root / A.SCORES_REL)}}) + "\n")
    with pytest.raises(A.GovernanceRefusal, match="no recorded sha256"):
        A.run(root, env=ONE_LOOK_OK, n_boot=10)


def test_refuses_when_the_input_manifest_is_missing(tmp_path):
    scores, pop = synth(n_compounds=5, replicates=1, seed=131)
    root = make_root(tmp_path, scores, pop)
    (root / A.INPUT_MANIFEST_REL).unlink()
    with pytest.raises(A.GovernanceRefusal, match="input manifest missing"):
        A.run(root, env=ONE_LOOK_OK, n_boot=10)


def test_refuses_when_no_compound_survives(tmp_path):
    scores, pop = synth(n_compounds=3, replicates=1, seed=137)
    scores["cosine"] = np.nan
    root = make_root(tmp_path, scores, pop)
    with pytest.raises(A.GovernanceRefusal, match="no compound survives"):
        A.run(root, env=ONE_LOOK_OK, n_boot=10)


def test_main_returns_nonzero_without_the_one_look_variable(monkeypatch, capsys):
    monkeypatch.delenv(A.ONE_LOOK_ENV, raising=False)
    assert A.main() == 2


# --------------------------------------------------------------------------------------------
# output contract
# --------------------------------------------------------------------------------------------

def test_result_json_carries_the_required_fields(tmp_path):
    scores, pop = synth(n_compounds=25, mapping_means={"K1": 0.5, "K2": 0.6, "K3": 0.55},
                        noise=0.02, seed=139)
    root = make_root(tmp_path, scores, pop)
    res = A.run(root, env=ONE_LOOK_OK, n_boot=SMALL_B)
    j = json.loads(Path(res["result_path"]).read_text())
    for key in ("prereg_id", "primary_metric", "robustness_metric", "reduction_order", "bootstrap",
                "resampling_unit_selection", "primary", "verdict", "supported_mapping",
                "MODEL_ORDERING_DISAGREEMENT", "robustness_jensen_shannon", "governance"):
        assert key in j, key
    p = j["primary"]
    for key in ("completeness_and_drops", "composite_scores", "contrasts", "decision",
                "model_agreement", "per_model_contrasts_descriptive", "per_nce_descriptive",
                "replicate_weights_sha256"):
        assert key in p, key
    for name in ("D12", "D13", "D23"):
        d = p["contrasts"][name]
        assert set(("point_estimate", "ci95_percentile_descriptive",
                    "ci_bonferroni_adjusted_primary")) <= set(d)
        assert d["adjusted_level"] == pytest.approx(1.0 - 0.05 / 3)
        lo95, hi95 = d["ci95_percentile_descriptive"]
        lo_a, hi_a = d["ci_bonferroni_adjusted_primary"]
        assert lo_a <= lo95 <= hi95 <= hi_a      # the adjusted interval is the wider one
    assert set(p["per_model_contrasts_descriptive"]) == set(A.MODELS)
    assert set(p["per_nce_descriptive"]["mapping_by_nce_equal_model_weight"]) == set(A.MAPPINGS)
    assert A.PREREG_ID in A.format_summary(res)
