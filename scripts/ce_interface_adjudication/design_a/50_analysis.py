"""MURU CE interface adjudication, Design A, step 50: the single frozen analysis.

One look only. The module refuses to run unless

  (a) MURU_CE_ADJUDICATION_ONE_LOOK=1 is set,
  (b) the freeze ref refs/muru-freeze/muru-ce-interface-adjudication-design-a resolves in git,
  (c) the score table and the population manifest match the sha256 values recorded in the
      frozen input manifest.

Reduction (frozen order, applied to the primary metric and, separately and identically, to the
Jensen-Shannon robustness metric):

  1. per (compound, model, mapping, nce): arithmetic mean of the record-level similarity over
     replicate records (the frozen replicate rule),
  2. per (compound, model, mapping): arithmetic mean over the two NCE cells, equal weight for
     NCE 30 and NCE 60,
  3. per (compound, mapping): arithmetic mean of the ICEBERG_2_1 and GLACIER values,
     giving S_K1, S_K2, S_K3.

The primary metric is the untransformed full-spectrum cosine. Jensen-Shannon similarity runs
through the identical pipeline as a robustness analysis only and can never change the primary
decision.

Resampling: compound-level paired comparison, B = 10,000, one fixed seed. The resampling unit
is chosen by a rule evaluated from identities only (the population manifest) and recorded in the
output: a whole-scaffold-group bootstrap if the population's scaffold clustering is nontrivial,
a molecule-level paired bootstrap otherwise. Every replicate draws one weight vector that is
reused unchanged for all three contrasts D12 = S_K1 - S_K2, D13 = S_K1 - S_K3,
D23 = S_K2 - S_K3, exactly as the comparator study does.

Decision: a mapping is SUPPORTED only if it has the highest observed primary composite score and
the Bonferroni-adjusted interval for its paired advantage over each of the other two mappings
lies wholly above zero. Otherwise INTERFACE_UNRESOLVED, which is a legitimate, fully reportable
outcome. The code never forces a selection.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]

PREREG_ID = "muru-ce-interface-adjudication-design-a"
FREEZE_REF = f"refs/muru-freeze/{PREREG_ID}"
ONE_LOOK_ENV = "MURU_CE_ADJUDICATION_ONE_LOOK"

SCORES_REL = "artifacts/ce_interface_adjudication/design_a/scores/record_scores.csv"
POPULATION_REL = "artifacts/ce_interface_adjudication/design_a/population/design_a_compounds.csv"
INPUT_MANIFEST_REL = "artifacts/ce_interface_adjudication/design_a/freeze/input_manifest.json"
RESULT_REL = "artifacts/ce_interface_adjudication/design_a/result/analysis.json"

MAPPINGS = ("K1", "K2", "K3")
MODELS = ("ICEBERG_2_1", "GLACIER")
NCE_CELLS = (30, 60)
PRIMARY_METRIC = "cosine"
ROBUSTNESS_METRIC = "js"

BOOT_B = 10_000
BOOT_SEED = 20260916
ALPHA = 0.05
N_CONTRASTS = 3
ADJUSTED_LEVEL = 1.0 - ALPHA / N_CONTRASTS          # 0.9833333333333333
DESCRIPTIVE_LEVEL = 0.95

# The three paired contrasts, in the frozen order and orientation.
CONTRASTS = (("D12", "K1", "K2"), ("D13", "K1", "K3"), ("D23", "K2", "K3"))

SCAFFOLD_CLUSTERING_NONTRIVIAL_FRACTION = 0.10
"""Frozen threshold of the resampling-unit selection rule.

Scaffold clustering counts as nontrivial when at least this fraction of the compounds in the
population manifest share a scaffold group with at least one other compound in the manifest.
The default states the preregistered wording "nontrivial means at least 10 percent of compounds
share a scaffold group with another compound". The preregistration fixes the value; pin it here
and nowhere else.
"""

REQUIRED_SCORE_COLUMNS = ("record_id", "compound_id", "scaffold_group", "nce", "model", "mapping",
                          "cosine", "js")
REQUIRED_POPULATION_COLUMNS = ("compound_id", "scaffold_group")
OPTIONAL_DROP_REASON_COLUMN = "drop_reason"


class GovernanceRefusal(RuntimeError):
    """Raised when a frozen precondition of the one-look analysis is not met."""


# --------------------------------------------------------------------------------------------
# governance
# --------------------------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_one_look(env: dict | None = None) -> None:
    env = os.environ if env is None else env
    if env.get(ONE_LOOK_ENV) != "1":
        raise GovernanceRefusal(
            f"refusing: set {ONE_LOOK_ENV}=1 only for the single frozen one-look analysis")


def check_freeze_ref(root: Path) -> str:
    p = subprocess.run(["git", "rev-parse", "--verify", "--quiet", FREEZE_REF],
                       cwd=str(root), capture_output=True, text=True)
    if p.returncode != 0 or not p.stdout.strip():
        raise GovernanceRefusal(f"refusing: freeze ref {FREEZE_REF} does not resolve in git")
    return p.stdout.strip()


MANIFEST_HASH_KEYS = ("sha256", "outputs_written", "inputs_read")


def recorded_hashes(manifest: dict) -> dict:
    """Recorded sha256 values, keyed by repo-relative path.

    Accepts either a dedicated {"sha256": {...}} block or the step-10 manifest layout that records
    the same digests under outputs_written and inputs_read. Later blocks never override earlier
    ones, and a path recorded twice with different digests is a refusal.
    """
    out: dict[str, str] = {}
    for key in MANIFEST_HASH_KEYS:
        block = manifest.get(key) or {}
        for rel, digest in block.items():
            if rel in out and out[rel] != digest:
                raise GovernanceRefusal(
                    f"refusing: input manifest records two different sha256 values for {rel}")
            out.setdefault(rel, digest)
    return out


def check_input_hashes(root: Path) -> dict:
    root = Path(root)
    man_path = root / INPUT_MANIFEST_REL
    if not man_path.exists():
        raise GovernanceRefusal(f"refusing: frozen input manifest missing at {INPUT_MANIFEST_REL}")
    manifest = json.loads(man_path.read_text())
    recorded = recorded_hashes(manifest)
    observed = {}
    for rel in (SCORES_REL, POPULATION_REL):
        if rel not in recorded:
            raise GovernanceRefusal(f"refusing: {rel} has no recorded sha256 in the input manifest")
        path = root / rel
        if not path.exists():
            raise GovernanceRefusal(f"refusing: input file missing at {rel}")
        observed[rel] = sha256_file(path)
        if observed[rel] != recorded[rel]:
            raise GovernanceRefusal(
                f"refusing: sha256 mismatch for {rel} "
                f"(recorded {recorded[rel]}, observed {observed[rel]})")
    return {"input_manifest": str(INPUT_MANIFEST_REL),
            "sha256_recorded": {rel: recorded[rel] for rel in (SCORES_REL, POPULATION_REL)},
            "sha256_observed": observed}


def governance_checks(root: Path, env: dict | None = None) -> dict:
    check_one_look(env)
    head = check_freeze_ref(root)
    hashes = check_input_hashes(root)
    return {"prereg_id": PREREG_ID, "one_look_env": ONE_LOOK_ENV, "freeze_ref": FREEZE_REF,
            "freeze_ref_commit": head, **hashes}


# --------------------------------------------------------------------------------------------
# mechanical completeness and the predeclared failure rule
# --------------------------------------------------------------------------------------------

def _check_schema(scores: pd.DataFrame, population: pd.DataFrame) -> None:
    for col in REQUIRED_SCORE_COLUMNS:
        if col not in scores.columns:
            raise GovernanceRefusal(f"refusing: score table is missing required column {col}")
    for col in REQUIRED_POPULATION_COLUMNS:
        if col not in population.columns:
            raise GovernanceRefusal(f"refusing: population manifest is missing required column {col}")
    bad_model = sorted(set(scores["model"].astype(str)) - set(MODELS))
    bad_mapping = sorted(set(scores["mapping"].astype(str)) - set(MAPPINGS))
    bad_nce = sorted(set(int(v) for v in scores["nce"]) - set(NCE_CELLS))
    if bad_model or bad_mapping or bad_nce:
        raise GovernanceRefusal(
            f"refusing: score table carries undeclared levels "
            f"(model {bad_model}, mapping {bad_mapping}, nce {bad_nce})")
    if scores["record_id"].duplicated().any():
        dup = sorted(scores.loc[scores["record_id"].duplicated(), "record_id"].astype(str))[:5]
        raise GovernanceRefusal(f"refusing: duplicated record_id values in the score table, e.g. {dup}")
    n_groups_per_compound = (population.assign(_g=population["scaffold_group"].astype(str))
                             .groupby(population["compound_id"].astype(str))["_g"].nunique())
    if (n_groups_per_compound > 1).any():
        bad = sorted(n_groups_per_compound[n_groups_per_compound > 1].index)[:5]
        raise GovernanceRefusal(
            f"refusing: population manifest gives a compound two scaffold groups, e.g. {bad}")
    pop_ids = population.drop_duplicates("compound_id").set_index(
        population.drop_duplicates("compound_id")["compound_id"].astype(str))["scaffold_group"].astype(str)
    inside = scores[scores["compound_id"].astype(str).isin(pop_ids.index)]
    mismatch = (inside["scaffold_group"].astype(str).to_numpy()
                != inside["compound_id"].astype(str).map(pop_ids).to_numpy())
    if mismatch.any():
        bad = sorted(set(inside.loc[mismatch, "compound_id"].astype(str)))[:5]
        raise GovernanceRefusal(
            f"refusing: score table and population manifest disagree on scaffold_group, e.g. {bad}")


def prepare_records(scores: pd.DataFrame, population: pd.DataFrame, metric: str = PRIMARY_METRIC) -> dict:
    """Apply the predeclared mechanical failure rule and report completeness.

    Rule, exactly as preregistered:
      * a record that produced no readable spectrum or no prediction is dropped with its reason
        recorded (mechanically: an explicit drop_reason, or a missing or non-finite similarity,
        or an expected cell that carries no row at all),
      * a compound that thereby loses an entire NCE cell for any model or mapping is dropped
        entirely from the primary analysis and counted,
      * a dropped compound is dropped identically for all three mappings, so the comparison
        stays paired.
    """
    _check_schema(scores, population)
    scores = scores.copy()
    scores["compound_id"] = scores["compound_id"].astype(str)
    scores["model"] = scores["model"].astype(str)
    scores["mapping"] = scores["mapping"].astype(str)
    scores["nce"] = scores["nce"].astype(int)

    pop = population.drop_duplicates("compound_id").copy()
    pop["compound_id"] = pop["compound_id"].astype(str)
    pop["scaffold_group"] = pop["scaffold_group"].astype(str)
    pop = pop.sort_values("compound_id").reset_index(drop=True)
    pop_ids = list(pop["compound_id"])

    extraneous = sorted(set(scores["compound_id"]) - set(pop_ids))
    scores = scores[scores["compound_id"].isin(pop_ids)]

    if OPTIONAL_DROP_REASON_COLUMN in scores.columns:
        flagged = scores[OPTIONAL_DROP_REASON_COLUMN].astype("string").fillna("").str.strip()
    else:
        flagged = pd.Series([""] * len(scores), index=scores.index, dtype="string")
    value = pd.to_numeric(scores[metric], errors="coerce").to_numpy(dtype=float)
    finite = np.isfinite(value)

    reason = np.where(flagged.to_numpy() != "", flagged.to_numpy(),
                      np.where(finite, "", f"missing_or_non_finite_{metric}"))
    keep_mask = (reason == "")
    dropped_records = [
        {"record_id": str(r.record_id), "compound_id": str(r.compound_id), "model": str(r.model),
         "mapping": str(r.mapping), "nce": int(r.nce), "reason": str(reason[i])}
        for i, r in enumerate(scores.itertuples(index=False)) if not keep_mask[i]]
    dropped_records.sort(key=lambda d: (d["compound_id"], d["model"], d["mapping"], d["nce"],
                                        d["record_id"]))
    kept = scores[keep_mask].copy()

    # mechanical completeness of the expected (compound, model, mapping, nce) grid
    present = set(map(tuple, kept[["compound_id", "model", "mapping", "nce"]].to_numpy().tolist()))
    present = {(str(c), str(m), str(k), int(n)) for c, m, k, n in present}
    submitted = set(
        (str(c), str(m), str(k), int(n))
        for c, m, k, n in scores[["compound_id", "model", "mapping", "nce"]].to_numpy().tolist())
    expected, empty_cells, absent_cells = [], [], []
    for c in pop_ids:
        for m in MODELS:
            for k in MAPPINGS:
                for n in NCE_CELLS:
                    cell = (c, m, k, n)
                    expected.append(cell)
                    if cell in present:
                        continue
                    rec = {"compound_id": c, "model": m, "mapping": k, "nce": n,
                           "reason": "no_surviving_record" if cell in submitted else "cell_absent_from_score_table"}
                    empty_cells.append(rec)
                    if cell not in submitted:
                        absent_cells.append(rec)

    dropped_compounds: dict[str, dict] = {}
    for rec in empty_cells:
        dropped_compounds.setdefault(rec["compound_id"], {
            "compound_id": rec["compound_id"],
            "reason": "lost_entire_nce_cell",
            "trigger_cell": {"model": rec["model"], "mapping": rec["mapping"], "nce": rec["nce"],
                             "cell_reason": rec["reason"]}})
    dropped = sorted(dropped_compounds.values(), key=lambda d: d["compound_id"])
    dropped_ids = set(dropped_compounds)

    analysed_ids = [c for c in pop_ids if c not in dropped_ids]
    kept = kept[kept["compound_id"].isin(analysed_ids)].copy()

    return {
        "metric": metric,
        "records": kept,
        "population": pop,
        "analysed_compound_ids": analysed_ids,
        "report": {
            "metric": metric,
            "n_population_manifest": len(pop_ids),
            "n_records_submitted": int(len(scores)),
            "n_records_dropped": int(len(dropped_records)),
            "n_records_kept": int(len(kept)),
            "n_expected_cells": len(expected),
            "n_cells_absent_from_score_table": len(absent_cells),
            "n_cells_with_no_surviving_record": len(empty_cells) - len(absent_cells),
            "mechanically_complete": len(absent_cells) == 0,
            "n_compounds_dropped": len(dropped),
            "n_compounds_analysed": len(analysed_ids),
            "n_compounds_outside_population_manifest": len(extraneous),
            "compounds_outside_population_manifest": extraneous,
            "dropped_records": dropped_records,
            "empty_cells": sorted(empty_cells, key=lambda d: (d["compound_id"], d["model"],
                                                              d["mapping"], d["nce"])),
            "dropped_compounds": dropped,
            "paired_invariant": "a dropped compound is dropped identically for all three mappings",
        },
    }


# --------------------------------------------------------------------------------------------
# the frozen reduction
# --------------------------------------------------------------------------------------------

def reduce_scores(records: pd.DataFrame, metric: str = PRIMARY_METRIC) -> dict:
    """Steps 1, 2 and 3 of the frozen reduction, in that exact order."""
    r = records.copy()
    r[metric] = pd.to_numeric(r[metric], errors="coerce").astype(float)
    cell = (r.groupby(["compound_id", "model", "mapping", "nce"], sort=True)[metric]
            .mean().rename("value").reset_index())                                  # step 1
    per_model = (cell.groupby(["compound_id", "model", "mapping"], sort=True)["value"]
                 .mean().rename("value").reset_index())                             # step 2
    composite = (per_model.groupby(["compound_id", "mapping"], sort=True)["value"]
                 .mean().rename("value").reset_index())                             # step 3
    S = composite.pivot(index="compound_id", columns="mapping", values="value").sort_index()
    S = S.reindex(columns=list(MAPPINGS))
    return {"cell": cell, "per_model": per_model, "composite": composite, "S": S}


# --------------------------------------------------------------------------------------------
# resampling-unit selection, evaluated from identities only
# --------------------------------------------------------------------------------------------

def select_resampling_unit(population: pd.DataFrame,
                           threshold: float = SCAFFOLD_CLUSTERING_NONTRIVIAL_FRACTION) -> dict:
    """Apply the frozen selection rule to a population manifest.

    Uses identities only (compound_id, scaffold_group). Returns the chosen unit together with the
    justification string that is recorded verbatim in the result JSON.
    """
    pop = population.drop_duplicates("compound_id")
    n = int(len(pop))
    sizes = pop["scaffold_group"].astype(str).value_counts()
    n_clustered = int(sizes[sizes >= 2].sum())
    n_groups = int(len(sizes))
    frac = float(n_clustered / n) if n else 0.0
    nontrivial = bool(frac >= threshold)
    unit = "scaffold_group" if nontrivial else "compound"
    justification = (
        f"{n_clustered} of {n} compounds ({frac:.6f}) share a scaffold group with at least one "
        f"other compound in the population manifest; the frozen threshold for nontrivial scaffold "
        f"clustering is {threshold:.6f}; the observed fraction is "
        f"{'at or above' if nontrivial else 'below'} the threshold, so scaffold clustering is "
        f"{'nontrivial' if nontrivial else 'trivial'} and the resampling unit is the "
        f"{'whole scaffold group (whole-scaffold-group bootstrap)' if nontrivial else 'molecule (molecule-level paired bootstrap)'}."
    )
    return {"unit": unit,
            "bootstrap": "whole_scaffold_group" if nontrivial else "molecule_level_paired",
            "scaffold_clustering_nontrivial": nontrivial,
            "threshold": float(threshold),
            "threshold_constant": "SCAFFOLD_CLUSTERING_NONTRIVIAL_FRACTION",
            "n_compounds_in_manifest": n,
            "n_scaffold_groups_in_manifest": n_groups,
            "n_compounds_sharing_a_scaffold_group": n_clustered,
            "fraction_sharing_a_scaffold_group": frac,
            "justification": justification,
            "evaluated_from": "population manifest identities only (compound_id, scaffold_group)"}


def unit_codes(compound_ids: list[str], population: pd.DataFrame, unit: str) -> tuple[np.ndarray, np.ndarray]:
    if unit == "compound":
        labels = np.asarray([str(c) for c in compound_ids])
    elif unit == "scaffold_group":
        p = population.drop_duplicates("compound_id")
        g = pd.Series(p["scaffold_group"].astype(str).to_numpy(),
                      index=p["compound_id"].astype(str).to_numpy())
        labels = np.asarray([g[str(c)] for c in compound_ids])
    else:
        raise ValueError(f"unknown resampling unit {unit!r}")
    uniq, codes = np.unique(labels, return_inverse=True)
    return codes.astype(int), uniq


# --------------------------------------------------------------------------------------------
# the paired bootstrap
# --------------------------------------------------------------------------------------------

def replicate_weights(codes: np.ndarray, n_units: int, n: int = BOOT_B,
                      seed: int = BOOT_SEED) -> np.ndarray:
    """One weight matrix, drawn once and reused unchanged for all contrasts of a run."""
    rng = np.random.default_rng(seed)
    return rng.multinomial(n_units, np.full(n_units, 1.0 / n_units), size=n).astype(float)


def _percentile_ci(draws: np.ndarray, level: float) -> list[float]:
    a = (1.0 - level) / 2.0 * 100.0
    return [float(v) for v in np.percentile(draws, [a, 100.0 - a])]


def paired_contrasts(S: pd.DataFrame, codes: np.ndarray, n_units: int, W: np.ndarray,
                     levels=(DESCRIPTIVE_LEVEL, ADJUSTED_LEVEL)) -> dict:
    """The three paired differences, all computed from the SAME replicate weights W."""
    counts = np.bincount(codes, minlength=n_units).astype(float)
    denom = W @ counts
    out = {}
    draws = {}
    for name, a, b in CONTRASTS:
        d = (S[a].to_numpy(dtype=float) - S[b].to_numpy(dtype=float))
        per_unit = np.bincount(codes, weights=d, minlength=n_units)
        rep = (W @ per_unit) / denom
        draws[name] = rep
        out[name] = {
            "contrast": f"S_{a} - S_{b}",
            "point_estimate": float(np.mean(d)),
            "ci95_percentile_descriptive": _percentile_ci(rep, levels[0]),
            "ci_bonferroni_adjusted_primary": _percentile_ci(rep, levels[1]),
            "adjusted_level": float(levels[1]),
            "n_boot": int(W.shape[0]),
            "n_units": int(n_units),
        }
    return {"contrasts": out, "draws": draws,
            "replicate_weights_sha256": hashlib.sha256(W.tobytes()).hexdigest()}


# --------------------------------------------------------------------------------------------
# the frozen decision rule
# --------------------------------------------------------------------------------------------

def _oriented_interval(a: str, b: str, intervals: dict[str, list[float]]) -> list[float]:
    """Interval for S_a - S_b, taking the stored contrast and flipping it when needed."""
    for name, x, y in CONTRASTS:
        if (x, y) == (a, b):
            return [float(intervals[name][0]), float(intervals[name][1])]
        if (x, y) == (b, a):
            return [-float(intervals[name][1]), -float(intervals[name][0])]
    raise KeyError(f"no frozen contrast for {a} against {b}")


def decide(composite_scores: dict[str, float], adjusted_intervals: dict[str, list[float]]) -> dict:
    """The frozen decision rule. Pure function of the computed quantities.

    SUPPORTED only if (a) the mapping has the highest observed primary composite score and
    (b) the Bonferroni-adjusted interval for its paired advantage over EACH other mapping lies
    wholly above zero. Otherwise INTERFACE_UNRESOLVED. Never forces a selection.
    """
    scores = {k: float(composite_scores[k]) for k in MAPPINGS}
    best = max(scores.values())
    leaders = [k for k in MAPPINGS if scores[k] == best]
    reasons: list[str] = []
    advantage = {}
    if len(leaders) != 1:
        return {"verdict": "INTERFACE_UNRESOLVED", "supported_mapping": None,
                "leader": None, "tied_leaders": leaders,
                "criterion_a_unique_highest_score": False,
                "criterion_b_all_adjusted_intervals_above_zero": False,
                "advantage_intervals_adjusted": {},
                "composite_scores": scores,
                "reasons": [f"no unique highest composite score: {leaders} tie at {best!r}"]}
    leader = leaders[0]
    all_above = True
    for other in MAPPINGS:
        if other == leader:
            continue
        ci = _oriented_interval(leader, other, adjusted_intervals)
        above = bool(ci[0] > 0.0)
        advantage[f"{leader}_over_{other}"] = {"ci_bonferroni_adjusted": ci, "wholly_above_zero": above}
        if not above:
            all_above = False
            reasons.append(f"adjusted interval for S_{leader} - S_{other} is {ci} and does not lie "
                           f"wholly above zero")
    verdict = "SUPPORTED" if all_above else "INTERFACE_UNRESOLVED"
    return {"verdict": verdict,
            "supported_mapping": leader if all_above else None,
            "leader": leader,
            "tied_leaders": leaders,
            "criterion_a_unique_highest_score": True,
            "criterion_b_all_adjusted_intervals_above_zero": all_above,
            "advantage_intervals_adjusted": advantage,
            "composite_scores": scores,
            "reasons": reasons or ["both frozen criteria met"]}


# --------------------------------------------------------------------------------------------
# descriptive companions
# --------------------------------------------------------------------------------------------

def model_agreement(per_model: pd.DataFrame) -> dict:
    """Compare the two models' orderings of K1, K2 and K3 and set the disagreement flag."""
    means = (per_model.groupby(["model", "mapping"], sort=True)["value"].mean()
             .unstack("mapping").reindex(index=list(MODELS), columns=list(MAPPINGS)))
    orderings = {}
    for m in MODELS:
        row = means.loc[m]
        orderings[m] = [str(k) for k in sorted(MAPPINGS, key=lambda k: (-float(row[k]), k))]
    keys = list(MODELS)
    disagree = orderings[keys[0]] != orderings[keys[1]]
    return {"per_model_mean_scores": {m: {k: float(means.loc[m, k]) for k in MAPPINGS} for m in MODELS},
            "orderings_best_to_worst": orderings,
            "MODEL_ORDERING_DISAGREEMENT": bool(disagree),
            "note": ("the two models order K1, K2 and K3 differently; this flag is descriptive but is "
                     "reported prominently even when the composite rule declares a mapping SUPPORTED")
            if disagree else "the two models order K1, K2 and K3 identically"}


def per_model_contrasts(per_model: pd.DataFrame, codes: np.ndarray, n_units: int,
                        W: np.ndarray) -> dict:
    out = {}
    for m in MODELS:
        sub = per_model[per_model["model"] == m]
        S = sub.pivot(index="compound_id", columns="mapping", values="value").sort_index()
        S = S.reindex(columns=list(MAPPINGS))
        res = paired_contrasts(S, codes, n_units, W)
        out[m] = {"mean_scores": {k: float(S[k].mean()) for k in MAPPINGS},
                  "contrasts": res["contrasts"],
                  "note": "descriptive only; never affects the primary verdict"}
    return out


def per_nce_breakdown(cell: pd.DataFrame) -> dict:
    by_model = (cell.groupby(["model", "mapping", "nce"], sort=True)["value"].mean())
    pooled = (cell.groupby(["compound_id", "mapping", "nce"], sort=True)["value"].mean()
              .groupby(["mapping", "nce"], sort=True).mean())
    return {
        "mapping_by_nce_equal_model_weight": {
            str(k): {str(n): float(pooled.loc[(k, n)]) for n in NCE_CELLS} for k in MAPPINGS},
        "model_by_mapping_by_nce": {
            str(m): {str(k): {str(n): float(by_model.loc[(m, k, n)]) for n in NCE_CELLS}
                     for k in MAPPINGS} for m in MODELS},
        "note": "descriptive only; never affects the primary verdict"}


# --------------------------------------------------------------------------------------------
# the analysis, pure of IO
# --------------------------------------------------------------------------------------------

def analyse_metric(scores: pd.DataFrame, population: pd.DataFrame, metric: str,
                   unit_choice: dict, n_boot: int = BOOT_B, seed: int = BOOT_SEED) -> dict:
    prep = prepare_records(scores, population, metric=metric)
    records, pop, ids = prep["records"], prep["population"], prep["analysed_compound_ids"]
    if not ids:
        raise GovernanceRefusal(
            f"refusing: no compound survives the mechanical failure rule for metric {metric}")
    red = reduce_scores(records, metric=metric)
    S = red["S"]
    codes, uniq = unit_codes(list(S.index), pop, unit_choice["unit"])
    n_units = int(len(uniq))
    W = replicate_weights(codes, n_units, n=n_boot, seed=seed)
    boot = paired_contrasts(S, codes, n_units, W)
    composite = {k: float(S[k].mean()) for k in MAPPINGS}
    adjusted = {name: boot["contrasts"][name]["ci_bonferroni_adjusted_primary"]
                for name, _a, _b in CONTRASTS}
    verdict = decide(composite, adjusted)
    return {
        "metric": metric,
        "completeness_and_drops": prep["report"],
        "n_compounds_analysed": int(len(ids)),
        "n_resampling_units_analysed": n_units,
        "composite_scores": composite,
        "contrasts": boot["contrasts"],
        "replicate_weights_sha256": boot["replicate_weights_sha256"],
        "replicate_weights_shared_across_contrasts": True,
        "decision": verdict,
        "model_agreement": model_agreement(red["per_model"]),
        "per_model_contrasts_descriptive": per_model_contrasts(red["per_model"], codes, n_units, W),
        "per_nce_descriptive": per_nce_breakdown(red["cell"]),
        "_draws": boot["draws"],
        "_S": S,
        "_per_model": red["per_model"],
    }


def analyse(scores: pd.DataFrame, population: pd.DataFrame, n_boot: int = BOOT_B,
            seed: int = BOOT_SEED) -> dict:
    pop = population.drop_duplicates("compound_id").copy()
    pop["compound_id"] = pop["compound_id"].astype(str)
    pop["scaffold_group"] = pop["scaffold_group"].astype(str)
    pop = pop.sort_values("compound_id").reset_index(drop=True)
    unit_choice = select_resampling_unit(pop)

    primary = analyse_metric(scores, pop, PRIMARY_METRIC, unit_choice, n_boot=n_boot, seed=seed)
    robustness = analyse_metric(scores, pop, ROBUSTNESS_METRIC, unit_choice, n_boot=n_boot, seed=seed)

    res = {
        "prereg_id": PREREG_ID,
        "design": "Design A, CE interface adjudication (K1 against K2 against K3)",
        "primary_metric": PRIMARY_METRIC,
        "robustness_metric": ROBUSTNESS_METRIC,
        "reduction_order": [
            "1: per (compound, model, mapping, nce), arithmetic mean over replicate records",
            "2: per (compound, model, mapping), arithmetic mean over the two NCE cells, equal weight",
            "3: per (compound, mapping), arithmetic mean of the ICEBERG_2_1 and GLACIER values"],
        "bootstrap": {"B": int(n_boot), "seed": int(seed), "alpha": ALPHA,
                      "n_contrasts": N_CONTRASTS, "adjusted_level": ADJUSTED_LEVEL,
                      "descriptive_level": DESCRIPTIVE_LEVEL,
                      "weights": "one multinomial weight vector per replicate, reused unchanged "
                                 "for D12, D13 and D23"},
        "resampling_unit_selection": unit_choice,
        "primary": {k: v for k, v in primary.items() if not k.startswith("_")},
        "verdict": primary["decision"]["verdict"],
        "supported_mapping": primary["decision"]["supported_mapping"],
        "MODEL_ORDERING_DISAGREEMENT": primary["model_agreement"]["MODEL_ORDERING_DISAGREEMENT"],
        "robustness_jensen_shannon": {
            **{k: v for k, v in robustness.items() if not k.startswith("_")},
            "status": "robustness only; can never change the primary decision"},
    }
    res["_primary_internals"] = primary
    res["_robustness_internals"] = robustness
    return res


# --------------------------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------------------------

def format_summary(res: dict) -> str:
    p = res["primary"]
    u = res["resampling_unit_selection"]
    L = []
    L.append(f"MURU CE interface adjudication, Design A ({res['prereg_id']})")
    L.append(f"  primary metric            : {res['primary_metric']} (untransformed full-spectrum)")
    L.append(f"  resampling unit           : {u['unit']} ({u['bootstrap']})")
    L.append(f"  unit justification        : {u['justification']}")
    L.append(f"  bootstrap                 : B = {res['bootstrap']['B']}, seed = {res['bootstrap']['seed']}, "
             f"adjusted level = {res['bootstrap']['adjusted_level']:.6f}")
    c = p["completeness_and_drops"]
    L.append(f"  population manifest       : {c['n_population_manifest']} compounds")
    L.append(f"  mechanically complete     : {c['mechanically_complete']} "
             f"(cells absent {c['n_cells_absent_from_score_table']}, cells emptied by record drops "
             f"{c['n_cells_with_no_surviving_record']})")
    L.append(f"  records dropped           : {c['n_records_dropped']} of {c['n_records_submitted']}")
    L.append(f"  compounds dropped         : {c['n_compounds_dropped']} "
             f"(identically for all three mappings)")
    L.append(f"  compounds analysed        : {p['n_compounds_analysed']} "
             f"in {p['n_resampling_units_analysed']} resampling units")
    L.append("  composite scores          : " +
             ", ".join(f"S_{k} = {p['composite_scores'][k]:.6f}" for k in MAPPINGS))
    for name, a, b in CONTRASTS:
        d = p["contrasts"][name]
        L.append(f"  {name} = S_{a} - S_{b}     : point {d['point_estimate']:+.6f}  "
                 f"ci95 [{d['ci95_percentile_descriptive'][0]:+.6f}, {d['ci95_percentile_descriptive'][1]:+.6f}]  "
                 f"adj [{d['ci_bonferroni_adjusted_primary'][0]:+.6f}, {d['ci_bonferroni_adjusted_primary'][1]:+.6f}]")
    L.append(f"  replicate weights sha256  : {p['replicate_weights_sha256']} "
             f"(identical for D12, D13 and D23)")
    ma = p["model_agreement"]
    flag = "YES" if ma["MODEL_ORDERING_DISAGREEMENT"] else "no"
    L.append(f"  MODEL ORDERING DISAGREEMENT: {flag}")
    for m in MODELS:
        L.append(f"    {m:<12} ordering best to worst: {' > '.join(ma['orderings_best_to_worst'][m])}")
    nce = p["per_nce_descriptive"]["mapping_by_nce_equal_model_weight"]
    for k in MAPPINGS:
        L.append(f"  per NCE cell {k}           : " +
                 ", ".join(f"NCE {n} = {nce[k][str(n)]:.6f}" for n in NCE_CELLS))
    r = res["robustness_jensen_shannon"]
    rv = r["decision"]["verdict"] + (f" ({r['decision']['supported_mapping']})"
                                     if r["decision"]["supported_mapping"] else "")
    L.append("  Jensen-Shannon robustness : " +
             ", ".join(f"S_{k} = {r['composite_scores'][k]:.6f}" for k in MAPPINGS) +
             f" -> {rv} (robustness only, cannot change the primary decision)")
    d = p["decision"]
    L.append(f"  VERDICT                   : {d['verdict']}"
             + (f" ({d['supported_mapping']})" if d["supported_mapping"] else ""))
    for reason in d["reasons"]:
        L.append(f"    reason: {reason}")
    return "\n".join(L)


def run(root: Path = ROOT, env: dict | None = None, n_boot: int = BOOT_B, seed: int = BOOT_SEED,
        write_result: bool = True) -> dict:
    root = Path(root)
    gov = governance_checks(root, env)
    scores = pd.read_csv(root / SCORES_REL)
    population = pd.read_csv(root / POPULATION_REL)
    res = analyse(scores, population, n_boot=n_boot, seed=seed)
    res["governance"] = gov
    public = {k: v for k, v in res.items() if not k.startswith("_")}
    if write_result:
        out = root / RESULT_REL
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(public, indent=1, sort_keys=False) + "\n")
        summary_path = out.with_name("analysis_summary.txt")
        summary_path.write_text(format_summary(res) + "\n")
        verdict_path = out.with_name("verdict.txt")
        verdict_path.write_text(
            f"{res['verdict']}\t{res['supported_mapping'] or 'none'}\t"
            f"MODEL_ORDERING_DISAGREEMENT={res['MODEL_ORDERING_DISAGREEMENT']}\n")
        res["result_path"] = str(out)
        res["summary_path"] = str(summary_path)
        res["verdict_path"] = str(verdict_path)
    return res


def main(argv=None) -> int:
    try:
        res = run()
    except GovernanceRefusal as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(format_summary(res))
    print(f"result written to {res.get('result_path')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
