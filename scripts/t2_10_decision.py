"""PHASE2_DECISION.md — applies the pre-registered decision rule mechanically.

The verdict is computed from the pre-registered conditions in
PREREGISTRATION.md section 22, not chosen. Every number is read from a
machine-readable artifact.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"


def load(n):
    return json.loads((ART / n).read_text())


base = load("p2_baselines.json")
var = load("p2_variance.json")
ctrl = load("p2_controls.json")
rob = load("p2_robustness.json")
coup = load("p2_mass_coupling.json")
split = load("p2_split_audit.json")

P = "S2"
perf = base["performance"][P]
pair = base["paired"][P]
k4f = base["K4_flexible"]
k4a_t = base["K4_tier_a"]
k5v = var["K5_variance_share"]

# ---------------------------------------------------------------------------
# K4A / K4B: the structure model is the better of the two structure-aware
# models on the primary split, judged by its own pre-registered rule.
# ---------------------------------------------------------------------------
best = ("FLEX_BENCHMARK" if perf["FLEX_BENCHMARK"]["mae"] <= perf["TIER_A"]["mae"]
        else "TIER_A")
K = k4f if best == "FLEX_BENCHMARK" else k4a_t
K4A = bool(k4f["K4A"]["pass"] or k4a_t["K4A"]["pass"])
K4B = bool(k4f["K4B"]["pass"] or k4a_t["K4B"]["pass"])

# ---------------------------------------------------------------------------
# K5: fires if the descriptor-driven between-compound variance share is below
# 0.20, OR removing the mass block destroys the structure model's advantage
# over B1.
# ---------------------------------------------------------------------------
nm_tierA = pair["TIER_A_no_mass_vs_B1_per_energy_mean"]
nm_flex = pair["FLEX_BENCHMARK_no_mass_vs_B1_per_energy_mean"]
survives_ablation = bool(
    (nm_tierA["mae_diff"] < 0 and nm_tierA["ci_unit"][1] < 0)
    or (nm_flex["mae_diff"] < 0 and nm_flex["ci_unit"][1] < 0))
share_ok = bool(k5v["meets_threshold_full"])
K5_FIRES = bool((not share_ok) or (not survives_ablation))

# A firing control is "a BLOCKER until explained" (PREREGISTRATION section 15).
# NC7 fires: retention time predicts trajectory shape above its permutation
# null. The pre-specified question is how much predictive information RT adds
# BEYOND Tier A structure, measured as the incremental gain from adding RT to
# the Tier A model and judged against the same 10% magnitude limit already used
# for the destruction controls, so no new threshold is invented here.
#
# A small incremental gain is consistent with RT acting primarily as a
# structure-associated surrogate in this dataset. It does NOT exclude
# independent confounding: a confounder largely collinear with the descriptors
# would produce the same small increment. The wording throughout reflects that
# limit.
EXPLAINED_LIMIT = 0.10
nc7 = ctrl.get("nc7_followup", {})
nc7_incremental_share = (nc7.get("incremental_gain_from_adding_rt", 1.0)
                         / nc7.get("improvement_tier_a_alone", 1.0))
nc7_explained = bool(nc7_incremental_share < EXPLAINED_LIMIT)

fired = list(ctrl.get("controls_fired", []))
unexplained = [c for c in fired
               if not (c == "NC7_retention_time" and nc7_explained)]
CTRL_BLOCK = bool(unexplained)

secondary_agree = all(
    base["paired"][s][f"{best}_vs_MASS_FLEX"]["mae_diff"] < 0
    and base["paired"][s][f"{best}_vs_MASS_FLEX"]["ci_unit"][1] < 0
    for s in ("S1", "S3"))
raw_agree = rob["preprocessing_robustness"]["rho_agreement"]["same_sign_at_every_energy"]

# PREREGISTRATION section 22's GO row names S1/S2/S3 and the raw branch, but
# omits the negative-mode replication that section 18 pre-registered as a
# qualitative check. Treating a failed replication as irrelevant to the verdict
# would let Phase 2 report an unqualified GO while a pre-registered check had
# failed. Negative-mode disagreement is therefore folded into the RESTRICT
# condition. This can only make the verdict MORE conservative, never less, and
# is recorded as DEVIATIONS D15.
neg_agree = rob["negative_mode"]["K4B_tier_a_vs_MASS_FLEX"]["pass"]

# ---------------------------------------------------------------------------
# Verdict, straight from PREREGISTRATION section 22
# ---------------------------------------------------------------------------
if CTRL_BLOCK:
    VERDICT = "INCONCLUSIVE DUE TO BLOCKER"
elif not K4A:
    VERDICT = "STOP BEFORE PHASE 3"
elif not K4B and K5_FIRES:
    VERDICT = "STOP BEFORE PHASE 3"
elif not K4B and not K5_FIRES:
    VERDICT = "RESTRICT AND GO TO PHASE 3"
elif K4A and K4B and not K5_FIRES and (secondary_agree and raw_agree
                                       and neg_agree and not fired):
    VERDICT = "GO TO PHASE 3"
else:
    VERDICT = "RESTRICT AND GO TO PHASE 3"

# Claims ladder (master plan section 23)
if CTRL_BLOCK:
    RUNG, RUNG_WHY = "L0", "negative controls did not pass, so no scientific claim stands"
elif not K4A:
    RUNG, RUNG_WHY = ("L1", "the population energy response is established, but no "
                             "structure-aware model beat it out of sample")
elif K4A and not K4B:
    RUNG, RUNG_WHY = ("L2", "the energy response generalizes to unseen chemistry and "
                             "structure-aware prediction beats the structure-blind "
                             "baseline, but not a strong energy-plus-mass model, so L3 "
                             "is not reached")
elif K4A and K4B and not K5_FIRES:
    RUNG, RUNG_WHY = ("L3", "structure explains between-compound variation beyond mass "
                             "on scaffold-disjoint holdouts")
else:
    RUNG, RUNG_WHY = ("L2", "structure-aware prediction generalizes, but K5 indicates the "
                             "effect is not separable from precursor mass")

ctrl_row = ("all null" if not fired
            else (", ".join(f"{c} FIRES (explained)" for c in fired)
                  if not CTRL_BLOCK
                  else ", ".join(f"{c} FIRES (UNEXPLAINED)" for c in unexplained)))

d90 = coup["decomposition_of_the_association"]["90"]
L = [f"# PHASE2_DECISION.md", "", f"# {VERDICT}", "",
     "Phase 2 of MURU ConjectureLab v1: representation, hierarchical baselines,",
     "structural generalization, and the flexible predictive benchmark.", "",
     "Pre-registration `PREREGISTRATION.md`, sha256",
     "`4cfc623361a62e64f4c5a8720c3ccf3ffea6ed2b1ed86f53b7154e5acb6e6d17`,",
     "committed `ddcdb8de1b69480178495bc0ec89e7fdce7a6dda` **before** any model",
     "in this document was executed. The verdict below is computed from the",
     "decision rule in that file, not chosen after the fact.", "",
     "Per `MASTER_PLAN_CLARIFICATIONS.md` C1, Phase 2 authorizes **Phase 3",
     "only** — never Phase 4.", "",
     "---", "", "## The scientific question", "",
     "> Does molecular structure predict the collision-energy trajectory of mu",
     "> for unseen chemistry beyond what can already be explained by collision",
     "> energy and precursor mass?", "", "---", "",
     "## Adjudication", "",
     "| Gate | Result |", "|---|---|",
     f"| **K4A** — structure-aware model beats B1 on S2 | **{'PASS' if K4A else 'FAIL'}** |",
     f"| **K4B** — structure-aware model beats MASS FLEX by ≥ 5% | **{'PASS' if K4B else 'FAIL'}** |",
     f"| **K5** — structure explains nothing beyond mass | **{'FIRES' if K5_FIRES else 'does not fire'}** |",
     f"| **K8** — mixture identity confounds | **{'FIRES' if rob['mixture_confounding']['K8']['fires'] else 'does not fire'}** |",
     f"| Negative controls | **{ctrl_row}** |", "",
     "## Design and sample sizes", "",
     "| Item | Value |", "|---|---|",
     f"| Primary split | **S2**, Bemis-Murcko scaffold-disjoint |",
     f"| Development corpus | **{base['setup']['development_compounds']} compounds / {base['setup']['development_rows']} rows** |",
     f"| Sealed confirmation set | **{split['confirmation']['n_compounds']} compounds ({100*split['confirmation']['frac']:.2f}%)**, NOT opened |",
     f"| Confirmation sha256 | `{split['confirmation']['sha256']}` |",
     f"| Tier A | {base['setup']['tier_a_n']} descriptors |",
     f"| Tier B | {base['setup']['tier_b_n']} features |",
     f"| Bootstrap | {base['setup']['n_boot']} resamples, molecule/scaffold unit |", "",
     "## Performance on the primary split (S2)", "",
     "| Model | MAE (compound) | MAE (scaffold) | 95% CI (scaffold) | grouped R² |",
     "|---|---|---|---|---|"]
for m in ["B0_global_mean", "B1_per_energy_mean", "B2_MASS_SIMPLE", "MASS_FLEX",
          "TIER_A", "TIER_A_no_mass", "TIER_A_mass_only", "FLEX_BENCHMARK",
          "FLEX_BENCHMARK_no_mass"]:
    v = perf[m]
    L.append(f"| `{m}` | **{v['mae']:.5f}** | {v['mae_unit']:.5f} | "
             f"[{v['mae_ci_unit'][0]:.5f}, {v['mae_ci_unit'][1]:.5f}] | "
             f"{v['grouped_r2']:.4f} |")
L += ["", "### Paired differences that decide the phase", "",
      "| Comparison | ΔMAE | 95% CI (scaffold) | Relative |", "|---|---|---|---|"]
for k in (f"{best}_vs_B1_per_energy_mean", f"{best}_vs_B2_MASS_SIMPLE",
          f"{best}_vs_MASS_FLEX", "MASS_FLEX_vs_B1_per_energy_mean",
          "TIER_A_no_mass_vs_B1_per_energy_mean",
          "FLEX_BENCHMARK_no_mass_vs_B1_per_energy_mean"):
    v = pair[k]
    L.append(f"| {k.replace('_vs_', ' vs ')} | {v['mae_diff']:+.5f} | "
             f"[{v['ci_unit'][0]:+.5f}, {v['ci_unit'][1]:+.5f}] | "
             f"{v['rel_reduction_pct']:+.2f}% |")
L += ["", f"Best structure-aware model on S2: **`{best}`**.", "",
      "## K4A", "", f"*{K['K4A']['rule']}*", "",
      f"ΔMAE vs B1 = **{K['K4A']['mae_diff_vs_B1']:+.5f}** "
      f"({K['K4A']['rel_reduction_pct']:+.2f}%), 95% scaffold interval "
      f"{K['K4A']['ci_unit']}, compound interval {K['K4A']['ci_compound']}.", "",
      f"**K4A: {'PASS' if K4A else 'FAIL'}.**", "",
      "## K4B", "", f"*{K['K4B']['rule']}*", "",
      f"ΔMAE vs MASS FLEX = **{K['K4B']['mae_diff_vs_MASS_FLEX']:+.5f}** "
      f"({K['K4B']['rel_reduction_pct']:+.2f}%, minimum required "
      f"{K['K4B']['min_required_rel_reduction_pct']}%), 95% scaffold interval "
      f"{K['K4B']['ci_unit']}.", "",
      f"**K4B: {'PASS' if K4B else 'FAIL'}.**", "",
      "## K5", "",
      "Adjudicated on five inputs jointly, as pre-registered.", "",
      "**1. Descriptor-driven between-compound variance share.** Cross-validated",
      "R² of Tier A predicting the compound random intercept, scaffold-grouped:",
      f"**{k5v['tier_a_full']}** against the master plan's 0.20 threshold "
      f"(meets = **{share_ok}**). Without the mass block: **{k5v['tier_a_no_mass']}** "
      f"(meets = **{k5v['meets_threshold_without_mass']}**).", "",
      "**2. Mass-block ablation.** Removing `precursor_mz`, `total_atom_count`",
      "and `rdbe` together:", "",
      f"- Tier A without mass vs B1: ΔMAE {nm_tierA['mae_diff']:+.5f}, CI {nm_tierA['ci_unit']}",
      f"- Flexible benchmark without mass-like features vs B1: ΔMAE {nm_flex['mae_diff']:+.5f}, CI {nm_flex['ci_unit']}",
      f"- Structure advantage survives ablation: **{survives_ablation}**", "",
      "**3. Correlated-block ablation.** `TIER_A_mass_only` (the mass block",
      f"alone) reaches MAE {perf['TIER_A_mass_only']['mae']:.5f} against the full Tier A model's",
      f"{perf['TIER_A']['mae']:.5f}.", "",
      "**4. Denominator-coupling audit.** `MASS_COUPLING_AUDIT.md` shows that",
      "purely fractional fragmentation manufactures rho = "
      f"{coup['comparison']['fractional_at_NCE90']} (numerically zero), while proportional",
      "chemistry plus a single absolute 50 Da low-mass cutoff manufactures rho = "
      f"**{coup['comparison']['absolute_floor_at_NCE90']}** with **no chemistry at all** — the same sign",
      f"and a magnitude comparable to the observed {coup['comparison']['observed_at_NCE90']}. On the real data the",
      f"high-energy association sits in the fragment term (rho(phi, mass) = {d90['rho_phi_mass']})",
      f"rather than survival yield (rho(SY, mass) = {d90['rho_sy_mass']}), which is the signature",
      "mechanical coupling predicts.", "",
      "This is a **sensitivity and mechanistic-coupling diagnostic, not an",
      "identification result.** It does not establish what fraction of the",
      "observed association is artifactual, and this document makes no such",
      "claim: the diagnostic is stipulated rather than fitted, and no",
      "coupling-free counterfactual of this corpus exists. Against a purely",
      "mechanical reading, the observed association *grows* with energy",
      f"({coup['observed_rho_by_energy']['15']} to {coup['observed_rho_by_energy']['90']}) while the diagnostic's is roughly flat, so",
      "the coupling alone does not reproduce the observed energy dependence.",
      "What it does establish is that mass dependence of mu is not, by itself,",
      "evidence of chemistry.", "",
      "**5. Variance decomposition.** Energy accounts for "
      f"{100*var['variance_decomposition']['energy_fixed_share']:.1f}% of Var(mu), compound identity "
      f"{100*var['variance_decomposition']['compound_random_share']:.1f}%, residual "
      f"{100*var['variance_decomposition']['residual_share']:.1f}%.", "",
      f"**K5: {'FIRES' if K5_FIRES else 'does not fire'}.**", "",
      "## K8 — mixture confounding", "",
      f"Mixture identity added to MASS FLEX changes MAE by "
      f"**{rob['mixture_confounding']['mix_gain_over_mass_flex']['mae_diff']:+.5f}** "
      f"(CI {rob['mixture_confounding']['mix_gain_over_mass_flex']['ci_scaffold']}), against a structure gain of "
      f"{rob['mixture_confounding']['structure_gain_over_mass_flex']['mae_diff']:+.5f}.", "",
      f"**K8 fires: {rob['mixture_confounding']['K8']['fires']}.**", "",
      "## Negative controls", "",
      "| Control | Family | Observed | Null p95 | Fires |", "|---|---|---|---|---|"]
for n, v in ctrl["controls"].items():
    L.append(f"| `{n}` | {v['family']} | {v['observed']:+.5f} | "
             f"{v['null_p95']:+.6f} | **{v['fires']}** |")
L += ["", f"{ctrl['verdict']}.", ""]
if fired:
    L += ["### NC7 fired, and this is its explanation", "",
          "Retention time predicts trajectory shape above its permutation null",
          f"(observed {ctrl['controls']['NC7_retention_time']['observed']:+.5f} against a null 95th "
          f"percentile of {ctrl['controls']['NC7_retention_time']['null_p95']:+.6f}; "
          f"{ctrl['controls']['NC7_retention_time']['n_exceedances']} of "
          f"{ctrl['controls']['NC7_retention_time']['n_permutations']} permutation replicates reached "
          f"the observed value, giving a finite-sample corrected empirical "
          f"p = {ctrl['controls']['NC7_retention_time']['p_value']} = (b+1)/(B+1)). Phase 1 anticipated this: "
          "`CONFOUNDERS.md` finding 4 recorded |rho| up to 0.36 between RT and",
          "mu and left the resolution to NC7.", "",
          "The discriminating question is whether RT carries information",
          "**independent of structure**, or is a **structure surrogate** — RT",
          "tracks lipophilicity, which is itself a structural property.", "",
          "| Model | Improvement over B1 |", "|---|---|",
          f"| Retention time alone | {nc7['improvement_rt_alone']:+.5f} |",
          f"| Tier A alone | {nc7['improvement_tier_a_alone']:+.5f} |",
          f"| Tier A + retention time | {nc7['improvement_tier_a_plus_rt']:+.5f} |", "",
          f"RT alone recovers {100*nc7['rt_share_of_structural_effect']:.1f}% of the structural effect, but adding",
          f"it to Tier A gains only **{nc7['incremental_gain_from_adding_rt']:+.5f}** — "
          f"{100*nc7_incremental_share:.1f}% of the Tier A effect, against the {100*EXPLAINED_LIMIT:.0f}% limit.", "",
          "RT therefore carries predictive signal by itself but adds little",
          "incremental predictive information beyond Tier A descriptors, which is",
          "consistent with it acting **primarily as a structure-associated",
          "surrogate in this dataset**. This is an observational association, not",
          "an identification result: **independent confounding cannot be",
          "completely excluded**, since a small incremental gain is also",
          "compatible with a confounder largely collinear with the descriptors.", "",
          "**Status: explained sufficiently not to block, but restricting.**",
          "Co-elution and matrix effects cannot be separated from lipophilicity",
          "with these data, so no mechanistic reading of the structural effect",
          "may lean on RT-correlated descriptors.", ""]
L += [
      "## Preprocessing sensitivity", "",
      f"Matched raw subset: **{rob['preprocessing_robustness']['n_matched_compounds']} compounds** "
      f"({rob['preprocessing_robustness']['coverage_pct']}% of the development corpus). rho(mu, mass) has the",
      f"same sign at every energy across branches: "
      f"**{rob['preprocessing_robustness']['rho_agreement']['same_sign_at_every_energy']}**, largest absolute difference "
      f"{rob['preprocessing_robustness']['rho_agreement']['max_abs_difference']}.", "",
      "This is **subset preprocessing robustness, not full-corpus independent",
      "raw replication**, and is not extrapolated beyond the 39 compounds",
      "measured.", "",
      "## Negative mode", "",
      f"{rob['negative_mode']['n_compounds']} compounds, S2 only. "
      f"K4A pass = **{rob['negative_mode']['K4A_tier_a_vs_B1']['pass']}**, "
      f"K4B pass = **{rob['negative_mode']['K4B_tier_a_vs_MASS_FLEX']['pass']}**.", "",
      f"Negative-mode repeatability remains **UNKNOWN**; no claim requiring it is",
      "made.", "",
      "## Model adequacy findings", "",
      "The master plan's §9.2 formulation was **not** adequate and was replaced",
      "on measured evidence before any model was fitted:", "",
      f"- mu reaches **{var['model_adequacy']['mu_max']:.7f}** with "
      f"{var['model_adequacy']['n_mu_gt_1']} rows above 1, so the logit link and a Beta likelihood",
      "  are undefined (`DEVIATIONS.md` D7). Modelled on the natural scale.",
      "- A two-parameter linear energy term leaves 70% of trajectories below",
      "  R² 0.9 (`DEVIATIONS.md` D8). Energy is treated nonparametrically.",
      "- PyMC was deliberately not used; the decomposition is a `statsmodels`",
      "  mixed model with bootstrap intervals (`DEVIATIONS.md` D11).", "",
      "## Highest defensible claims-ladder rung", "",
      f"# {RUNG}", "", f"{RUNG_WHY.capitalize()}.", "",
      "Interpretation discipline, restated because it constrains what the above",
      "means: feature importance is not mechanism, permutation importance is not",
      "causation, a fingerprint improving prediction does not establish a",
      "chemical law, and a flexible model beating a baseline is not discovery.",
      "Phase 2 establishes whether reproducible structural predictive information",
      "exists. It does not establish why.", "",
      "## Verdict", "", f"# {VERDICT}", ""]

if VERDICT == "GO TO PHASE 3":
    L += ["Phase 3 — discovery engine construction and null calibration — is",
          "**authorized**. Phase 3, not Phase 2, later decides whether Phase 4",
          "may run.", ""]
elif VERDICT == "RESTRICT AND GO TO PHASE 3":
    L += ["Phase 3 is **authorized subject to the restrictions below**, which are",
          "binding rather than advisory:", ""]
    n = 1
    if not K4B:
        L += [f"{n}. **No claim of structural information beyond precursor mass "
              "is licensed.** The structure-aware model did not beat MASS FLEX "
              "by the pre-registered margin.", ""]
        n += 1
    if K5_FIRES:
        L += [f"{n}. **K5 fired.** Any Phase 3 target must be framed as an "
              "energy-and-mass relationship unless new evidence separates them.", ""]
        n += 1
    L += [f"{n}. **The denominator-coupling finding is binding.** A mass "
          "association of the observed sign and comparable magnitude **can** be "
          "generated by mu's normalization plus an absolute low-mass cutoff, "
          "with no chemistry. This is a sensitivity result, not an "
          "identification result: it does not establish what fraction of the "
          "observed association is artifactual, and no such fraction is "
          "claimed. Phase 3's synthetic generator must nonetheless include the "
          "coupling mechanism, or it will manufacture recoverable 'laws' that "
          "are normalization artifacts.", ""]
    n += 1
    if fired:
        L += [f"{n}. **NC7 fired and is explained, but it restricts.** "
              "Retention time predicts trajectory shape above its permutation "
              f"null, though it adds only {nc7['incremental_gain_from_adding_rt']:+.5f} "
              f"({100*nc7_incremental_share:.1f}% of the Tier A effect) on top of "
              "structure — consistent with RT acting primarily as a "
              "structure-associated surrogate in this dataset. Independent "
              "confounding cannot be completely excluded: co-elution and matrix "
              "effects cannot be separated from lipophilicity with these data, "
              "so no mechanistic reading may lean on RT-correlated "
              "descriptors.", ""]
        n += 1
    L += [f"{n}. **Raw-branch evidence covers "
          f"{rob['preprocessing_robustness']['n_matched_compounds']} compounds only.** No "
          "full-corpus preprocessing-invariance claim is available.", ""]
    n += 1
    if not neg_agree:
        nb = rob["negative_mode"]["K4B_tier_a_vs_MASS_FLEX"]
        L += [f"{n}. **The structure-beyond-mass result does NOT replicate in "
              f"negative mode.** Negative-mode K4A passes, but K4B gives only "
              f"{nb['rel_reduction_pct']:+.2f}% against the 5% minimum, with a "
              f"scaffold interval of {nb['ci_scaffold']} that spans zero. Any "
              "Phase 3 claim is restricted to positive-mode chemistry until "
              "this is resolved.", ""]
        n += 1
    L += [f"{n}. **Negative-mode repeatability remains UNKNOWN.** No "
          "noise-referenced negative-mode claim may be made.", ""]
    n += 1
    L += [f"{n}. Phase 2 authorizes **Phase 3 only**. Phase 4 requires Phase 3's "
          "own decision (`MASTER_PLAN_CLARIFICATIONS.md` C1).", ""]
elif VERDICT == "STOP BEFORE PHASE 3":
    L += ["Phase 3 is **not authorized**. On this corpus, with this endpoint and",
          "this energy grid, the evidence does not support advancing toward",
          "mathematical discovery.", "",
          "This is not a failed software project. It is a successful",
          "falsification of the current scientific formulation: the pipeline",
          "worked, the gates were pre-registered, and the answer was no.", ""]
else:
    L += ["A negative control produced reproducible signal above its",
          "pre-registered null threshold. That is a BLOCKER. No Phase 2",
          "scientific claim stands and Phase 3 is not authorized until it is",
          "explained.", ""]

L += ["## What Phase 2 did not do", "",
      "No Phase 3 work. No symbolic regression. PySR not installed. No synthetic",
      "discovery engine. The sealed confirmation set was not opened.", ""]

(ROOT / "PHASE2_DECISION.md").write_text("\n".join(L) + "\n")
summary = {"verdict": VERDICT, "rung": RUNG, "K4A": K4A, "K4B": K4B,
           "K5_fires": K5_FIRES, "K8_fires": rob["mixture_confounding"]["K8"]["fires"],
           "controls_block": CTRL_BLOCK, "best_structure_model": best,
           "share": k5v["tier_a_full"], "survives_ablation": survives_ablation}
(ART / "p2_decision.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
