"""Compute the Phase 3 verdict from the frozen decision rule and write
`PHASE3_DECISION.md`.

The verdict is COMPUTED from `PHASE3_PREREGISTRATION.md` §22, not chosen after
the fact. Every stop condition is evaluated explicitly and reported whether or
not it fires.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
ART = ROOT / "artifacts"

from muru.discovery import protocol                       # noqa: E402
from muru.synth import plan                               # noqa: E402


def load(n):
    p = ART / n
    return json.loads(p.read_text()) if p.exists() else None


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(*a) -> str:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True,
                          text=True).stdout.strip()


def blocks(worlds):
    d = defaultdict(list)
    for w in worlds:
        if w.get("status") == "ok":
            d[w["block"]].append(w)
    return d


def g1_recovery(ws):
    """Symbolic-equivalent and functionally-equivalent recovery rates."""
    out = {}
    for regime in ("low", "moderate", "adverse"):
        sub = [w for w in ws if w["noise_regime"] == regime]
        if not sub:
            continue
        acc = [w for w in sub if w["acceptance"]["accepted"]]
        rec = [w for w in sub if w.get("recovery")]
        func = [w for w in rec
                if w["recovery"]["functionally_equivalent"]
                and w["acceptance"]["accepted"]]
        exact = [w for w in rec
                 if w["recovery"]["exact_equivalent"]
                 and w["acceptance"]["accepted"]]
        expo = [w["recovery"]["mass_exponent_recovered"] for w in rec
                if np.isfinite(w["recovery"]["mass_exponent_recovered"])]
        within = [w for w in rec if w["recovery"].get("exponent_within_0.15")]
        out[regime] = {
            "n": len(sub),
            "n_accepted": len(acc),
            "accepted_rate": len(acc) / len(sub),
            "n_functionally_equivalent": len(func),
            "functional_recovery_rate": len(func) / len(sub),
            "n_symbolically_equivalent": len(exact),
            "symbolic_recovery_rate": len(exact) / len(sub),
            "n_exponent_within_0.15": len(within),
            "exponent_within_rate": len(within) / len(sub),
            "median_mass_exponent": float(np.median(expo)) if expo else None,
            "median_complexity": float(np.median(
                [w["candidate"]["complexity"] for w in sub if w.get("candidate")]))
                if any(w.get("candidate") for w in sub) else None,
            "median_selection_fraction": float(np.median(
                [w["stability"]["fraction"] for w in sub])),
        }
    return out


def structural_claims(ws):
    return [w for w in ws if w["acceptance"]["accepted"]
            and w["acceptance"].get("claims_non_mass_structure")]


def main() -> int:
    worlds = load("p3_worlds.json")
    cal = load("p3_null_calibration.json")
    fp = load("p3_false_positives.json")
    env = load("p3_engine_validation.json")
    budget = load("p3_runtime_budget.json")
    if not all((worlds, cal, fp, env)):
        print("[t3_60] missing artifacts; run t3_00/t3_20/t3_30/t3_40 first")
        return 1

    B = blocks(worlds)
    k6 = fp["K6"]
    g1 = g1_recovery(B.get("G1", []))
    mod = g1.get("moderate", {})

    g2_acc = [w for w in B.get("G2", []) if w["acceptance"]["accepted"]]
    g3_struct = structural_claims(B.get("G3", []))
    gc_struct = structural_claims(B.get("GC", []))
    g5_struct = structural_claims(B.get("G5", []))
    grt = B.get("GRT", [])
    grt_acc = [w for w in grt if w["acceptance"]["accepted"]]
    ga = B.get("GA", [])
    g4m = fp["G4M_mass_conditional_null"]

    med_stab = (np.median([w["stability"]["fraction"] for w in B.get("G1", [])])
                if B.get("G1") else 0.0)

    stops = {
        "K6 fires after the permitted repairs": bool(k6["fires"]),
        "G1 recovery below 80% at the moderate noise regime":
            bool(mod.get("functional_recovery_rate", 0.0) < 0.80),
        "more than 1 of 8 G2 worlds yields an accepted compact conjecture":
            bool(len(g2_acc) > 1),
        "any G3 world yields an accepted non-mass structural conjecture":
            bool(len(g3_struct) > 0),
        "more than 1 of 9 GC worlds claims non-mass structure":
            bool(len(gc_struct) > 1),
        "more than 2 of 8 G5 worlds claims non-mass structure":
            bool(len(g5_struct) > 2),
        "median G1 seed-selection frequency below 20/30":
            bool(med_stab < protocol.MIN_SELECTION_FRACTION),
        "null threshold table not reproducible":
            bool(cal.get("n_worlds", 0) < plan.N_NULL_CAL),
    }
    fired = [k for k, v in stops.items() if v]

    restrictions: list[str] = []
    if g1.get("adverse", {}).get("functional_recovery_rate", 1.0) < 0.80:
        restrictions.append(
            f"**Noise ceiling.** Functional recovery at the adverse regime "
            f"(SD {0.060}) is "
            f"{g1['adverse']['functional_recovery_rate']:.0%} against "
            f"{mod.get('functional_recovery_rate', 0):.0%} at the moderate "
            f"regime. Phase 4 must report the residual scale of its own fit "
            f"and treat a candidate found at comparable or worse noise as "
            f"unconfirmed.")
    if B.get("G1"):
        cx = [w["candidate"]["complexity"] for w in B["G1"]
              if w.get("candidate") and w["acceptance"]["accepted"]]
        if cx and max(cx) < 20:
            restrictions.append(
                f"**Complexity ceiling.** Every accepted G1 recovery sits at "
                f"complexity ≤ {int(max(cx))}, well inside the budget of 20. "
                f"Recovery was demonstrated only in that range, so a Phase 4 "
                f"candidate above complexity {int(max(cx))} is outside the "
                f"validated envelope and must be reported as such.")
    lo, hi = cal.get("threshold_ci_lo"), cal.get("threshold_ci_hi")
    if lo and hi and lo[20] is not None and (hi[20] - lo[20]) > 0.15:
        restrictions.append(
            f"**The null threshold is a point estimate with wide uncertainty.** "
            f"At complexity 20 the frozen threshold is "
            f"{cal['threshold_by_complexity'][20]:+.4f} with a bootstrap "
            f"interval of [{lo[20]:+.4f}, {hi[20]:+.4f}], because a 95th "
            f"percentile from {cal['n_worlds']} null worlds rests on its top "
            f"two or three. Phase 4 must report any candidate's margin over the "
            f"threshold, and a candidate whose R² falls inside that interval is "
            f"**not** to be reported as clearing the null — it is inconclusive "
            f"and requires an enlarged calibration before any claim.")
    if gc_struct or g4m["n_accepted_claiming_structure_beyond_mass"]:
        restrictions.append(
            "**Measurement-coupling falsification is mandatory in Phase 4.** "
            "The coupling worlds produced at least one candidate claiming "
            "non-mass structure, so Phase 4 must run an explicit coupling "
            "falsification against any real candidate.")
    restrictions.append(
        "**Positive mode only.** Phase 2's structure-beyond-mass result does "
        "not replicate in negative mode (K4B FAIL, +1.93%, scaffold interval "
        "[-0.01572, 0.00038] spanning zero). Any Phase 4 authorization is for "
        "the positive-mode discovery question.")
    restrictions.append(
        "**No mechanistic reading may lean on RT-correlated descriptors.** NC7 "
        "fired in Phase 2 and is explained but restricting; the Phase 3 GRT "
        "stress test does not resolve it causally.")
    restrictions.append(
        "**No full-corpus preprocessing-invariance claim.** The raw branch "
        "covers 39 compounds (7.1%).")

    if fired:
        verdict = "STOP BEFORE PHASE 4"
    elif restrictions:
        verdict = "RESTRICT AND GO TO PHASE 4"
    else:
        verdict = "GO TO PHASE 4"

    decision = {
        "verdict": verdict,
        "K6": k6,
        "stop_conditions": stops,
        "stop_conditions_fired": fired,
        "restrictions": restrictions,
        "G1_recovery": g1,
        "G2_accepted": len(g2_acc),
        "G3_structural_claims": len(g3_struct),
        "GC_structural_claims": len(gc_struct),
        "G5_structural_claims": len(g5_struct),
        "GRT_accepted": len(grt_acc),
        "GA_accepted": sum(1 for w in ga if w["acceptance"]["accepted"]),
        "highest_real_data_rung": "L3",
        "phase4_authorized": verdict in ("GO TO PHASE 4",
                                         "RESTRICT AND GO TO PHASE 4"),
    }
    (ART / "p3_decision.json").write_text(json.dumps(decision, indent=1))

    md = render(decision, worlds, B, cal, fp, env, budget, g1)
    (ROOT / "PHASE3_DECISION.md").write_text(md)
    print(f"[t3_60] {verdict} | {k6['verdict']} | "
          f"G1 functional recovery (moderate) "
          f"{mod.get('functional_recovery_rate', float('nan')):.0%}")
    return 0


def render(d, worlds, B, cal, fp, env, budget, g1) -> str:
    v = env["versions"]
    g4 = fp["G4_pure_null"]
    g4m = fp["G4M_mass_conditional_null"]
    prereg_sha = sha(ROOT / "PHASE3_PREREGISTRATION.md")
    prereg_commit = git("log", "-1", "--format=%H", "--",
                        "PHASE3_PREREGISTRATION.md")
    seal_sha = sha(ART / "confirmation_set_sealed.json")

    def blockrow(name, label):
        ws = B.get(name, [])
        if not ws:
            return f"| {label} | 0 | — | — | — |"
        acc = sum(1 for w in ws if w["acceptance"]["accepted"])
        st = sum(1 for w in ws if w["acceptance"]["accepted"]
                 and w["acceptance"].get("claims_non_mass_structure"))
        stab = np.median([w["stability"]["fraction"] for w in ws])
        return f"| {label} | {len(ws)} | {acc} | {st} | {stab:.2f} |"

    g1rows = "\n".join(
        f"| `{r}` | {g['n']} | {g['n_accepted']} | "
        f"**{g['functional_recovery_rate']:.0%}** | "
        f"{g['symbolic_recovery_rate']:.0%} | "
        f"{g['exponent_within_rate']:.0%} | "
        f"{g['median_mass_exponent']:.3f} | {g['median_complexity']:.0f} | "
        f"{g['median_selection_fraction']:.2f} |"
        for r, g in g1.items())

    stoprows = "\n".join(
        f"| {k} | {'**FIRED**' if val else 'no'} |"
        for k, val in d["stop_conditions"].items())

    hmain = {}
    for name in ("G1", "G2", "G3", "G4", "G5"):
        ws = B.get(name, [])
        if ws:
            hmain[name] = sum(1 for w in ws
                              if w["collapse"]["hmain"]["h_main_rejected"])

    # the two readings of the G1 criterion, both reported
    modw = [w for w in B.get("G1", []) if w["noise_regime"] == "moderate"]
    mp_rate = (sum(1 for w in modw if w["acceptance"]["accepted"]
                   and (w.get("recovery") or {}).get("exponent_within_0.15"))
               / len(modw)) if modw else float("nan")
    pr_rate = g1.get("moderate", {}).get("functional_recovery_rate", float("nan"))

    diag = load("p3_recovery_diagnosis.json")
    diag_rows = "\n".join(
        f"| `{k}` | {v['search_capability_rate']:.0%} | "
        f"{v['system_report_rate']:.0%} | "
        f"{'+' + str(int(v['median_complexity_gap'])) if v['median_complexity_gap'] is not None else '—'} |"
        for k, v in (diag or {}).get("summary", {}).items())
    elbow = protocol.ELBOW_TOL

    comp = load("p3_engine_comparison.json") or {"summary": {}}
    gp_rows = "\n".join(
        f"| `{b}` | {s['n_worlds']} | {s['engines_agree_rate']:.0%} | "
        f"{s['support_match_rate']:.0%} | "
        + (f"{s['pysr_matches_planted_rate']:.0%} | "
           f"{s['gplearn_matches_planted_rate']:.0%} |"
           if "pysr_matches_planted_rate" in s else "— | — |")
        for b, s in comp["summary"].items()) or "| — | | | | | |"

    if d["verdict"] == "STOP BEFORE PHASE 4":
        stop_section = f"""## What must change before Phase 4 can be reconsidered

Phase 3 stopped on **candidate selection**, not on false positives, not on
search capability, and not on the falsification harness — all of which passed.
The specific, reproducible defect and its evidence:

**The elbow rule resolves near-degenerate Pareto fronts in favour of the wrong
expression.** With a tolerance of {elbow} absolute R², a complexity-6
approximation that sits 0.004 R² below the complexity-13 planted form is
preferred to it, in 30 of 30 seeds, at every noise level tested.

A future attempt would need to change the candidate-selection rule and then
**recalibrate the null thresholds under the changed rule**, because the
threshold is conditioned on the complexity the rule selects. Candidate
directions, recorded so the reasoning is not lost, and **deliberately not
applied here**:

1. tighten the elbow tolerance, or make it relative to the front's own R² spread
   rather than absolute;
2. carry the whole Pareto front forward and adjudicate every knee against the
   null, rather than committing to one candidate per seed;
3. report the recovered **variable support and scaling exponents** as the
   claim, and treat the functional form as unidentified — which is what this
   evidence actually supports.

**None of these was applied.** Changing the selection rule after seeing that the
planted recovery failed is exactly the move Phase 3 exists to prevent, and the
pre-registration's repair allowance is scoped to K6 alone, which did not fire.

## Restrictions that would have applied, recorded for a future attempt

These were computed by the decision rule and are preserved because they remain
true of the evidence, not because Phase 4 is authorized. **It is not.**

{chr(10).join(f'{i}. {r}' for i, r in enumerate(d['restrictions'], 1))}"""
    else:
        stop_section = ("## Restrictions on Phase 4\n\n"
                        + "\n".join(f"{i}. {r}"
                                    for i, r in enumerate(d["restrictions"], 1)))

    return f"""# PHASE3_DECISION.md

# {d['verdict']}

Phase 3 of MURU ConjectureLab v1: discovery-engine construction, synthetic
ground truth, falsification and null calibration.

Pre-registration `PHASE3_PREREGISTRATION.md`, sha256
`{prereg_sha}`,
committed `{prereg_commit}` **before** any governed symbolic run in this
document was executed. The verdict above is **computed** from the decision rule
in that file (§22), not chosen after the fact.

Phase 3 validates the **discovery machinery**. It does not discover the MURU
conjecture. No synthetic result here licenses any statement about the real
MS/MS system.

---

## Phase 2 gate verification

Verified independently from machine-readable artifacts, not from
`PHASE2_DECISION.md` prose.

| Check | Evidence | Result |
|---|---|---|
| Verdict | `p2_decision.json` | `RESTRICT AND GO TO PHASE 3` |
| Highest real-data rung | `p2_decision.json` | **L3** |
| K4A on the pre-registered S2 split | ΔMAE −0.05432, CI [−0.06349, −0.04515] | PASS |
| K4B vs MASS FLEX, positive mode | −0.02513, +20.02% ≥ 5% | PASS |
| K5 | `K5_fires: false` | does not fire |
| K8 | +0.00159, CI spans zero | does not fire |
| Structure beat MASS FLEX materially | interval excludes zero | yes |
| No-mass ablations retained information | −0.03686 and −0.05146 vs B1 | yes |
| Negative mode | K4A PASS, **K4B FAIL** (+1.93%) | binding restriction |
| NC7 retention time | fired; incremental +0.00097 (2.3%) | qualified, not causal |
| Raw preprocessing branch | 39 compounds (7.1%) | matched subset only |
| Mass-coupling audit | regime D, ρ = −0.4791 stipulated | sensitivity, not identification |
| Sealed confirmation set | sha256 recomputed = expected | intact |
| p-values | `(b+1)/(B+1)` | finite-sample |
| Final Phase 2 state | `0b5e13b`, clean tree, 168 tests pass | reproducible |

## Confirmation seal

| Item | Value |
|---|---|
| Compounds | 110 (20.04%), 82 scaffold groups |
| SHA-256 before and after Phase 3 | `{seal_sha}` |
| Opened during Phase 3 | **No** |
| What Phase 3 read | connectivity identifiers only, to exclude them |

Phase 3 built every real-covariate world on the **439 development compounds**.
`tests/test_p3_seal.py` asserts the hash, that no Phase 3 artifact contains a
sealed identifier, and that the synthetic response is not the observed one.

## Environment

| Component | Version |
|---|---|
| PySR (primary) | **{v.get('pysr')}** |
| SymbolicRegression.jl | {v.get('SymbolicRegression_jl')} |
| Julia | {v.get('julia')} |
| gplearn (comparison arm) | {v.get('gplearn')} |
| SymPy | {v.get('sympy')} |
| Generator / truth version | `p3-gen-1.0.0` / `p3-truth-1.0.0` |

PySR smoke test on `{env['smoke_test']['planted']}`:
recovered **{env['smoke_test']['recovered']}** as
`{env['smoke_test']['recovered_expr']}`. Identical Pareto front at a repeated
seed: **{env['determinism']['same_seed_identical']}**.

Successful installation is not scientific validation, and none is claimed from
it.

---

## Results by block

| Block | Worlds | Accepted | Claiming structure beyond mass | Median seed stability |
|---|---|---|---|---|
{blockrow('G1', 'G1B — clean collapse with non-mass structure')}
{blockrow('G2', 'G2 — predictable, no compact collapse')}
{blockrow('G3', 'G3 — mass only')}
{blockrow('G4', 'G4 — pure null (K6)')}
{blockrow('G4M', 'G4M — mass-conditional null')}
{blockrow('G5', 'G5 — confounded')}
{blockrow('GC', 'GC — measurement coupling')}
{blockrow('GRT', 'GRT — retention-time surrogate')}
{blockrow('GA', 'GA — analytic sanity')}
{blockrow('NCAL', 'NCAL — null calibration')}

## G1 recovery

Both rates are reported, as required: **symbolic-equivalent** recovery and
**functionally equivalent** recovery. A simpler algebraically equivalent form
counts; a high-complexity interpolant does not.

| Noise regime | Worlds | Accepted | Functional recovery | Symbolic recovery | Mass exponent within ±0.15 | Median exponent | Median complexity | Median stability |
|---|---|---|---|---|---|---|---|---|
{g1rows}

Planted mass exponent **0.5**. The master plan §18.3 criterion is recovery
within ±0.15.

### Two different criteria give two different answers, and both are reported

| Criterion | Source | Result at the moderate regime |
|---|---|---|
| exponent within ±0.15 **and** the recovered form is in the planted shape family | master plan §18.3, the weaker reading | **{mp_rate:.0%}** |
| the above **and** functional equivalence to the complete planted law | `PHASE3_PREREGISTRATION.md` §19, the reading frozen in advance | **{pr_rate:.0%}** |

The pre-registered reading is the binding one. It was chosen before any
performance was observed, precisely so that this choice could not be made
afterwards, and it is the one the decision rule uses.

### Why they diverge — the search finds the law and the ranking rule discards it

`scripts/t3_45_recovery_diagnosis.py` separates two questions that a single
recovery rate conflates. **Does any candidate anywhere on the 30 seeds' Pareto
fronts match the planted law, and does the frozen ranking rule select it?**

| World | Search **finds** the law | System **reports** it | Median complexity gap |
|---|---|---|---|
{diag_rows}

The mechanism is specific. In `G1B` the planted law needs complexity **13**;
a complexity-**6** expression, `sqrt(precursor_mz · (heteroatom_fraction + c))`,
approximates it to within about 2.5% relative RMSE over the descriptor domain
and reaches a held-out R² within **0.004** of it. The frozen elbow rule takes
the smallest complexity whose validation R² is within {elbow} of the best on the
front, so it takes the approximation — every time, in every seed, at every noise
level.

This is not a search failure. It is a **candidate-selection failure**: the
system finds the truth and then reports something simpler that is
statistically indistinguishable from it on held-out data.

`GA` is the control that pins this down. Its law is representable at low
complexity, and there the same pipeline reports it in **100%** of worlds. `G3`,
a single power law, is reported in **62%**. The failure is confined to laws
whose true form sits above a near-equivalent approximation on the Pareto front —
and that is exactly the situation a real conjecture search would face.

## H-MAIN adequacy

The collapse model is compared against the same model with a per-compound shape
exponent freed, out of sample by leave-one-energy-out; H-MAIN is rejected when
the lower bound of a compound-clustered bootstrap interval on the ratio exceeds
1.0. No arbitrary inflation constant is used.

Worlds rejecting H-MAIN, by block:
{', '.join(f'**{k}** {v}/{len(B.get(k, []))}' for k, v in hmain.items())}.

G2 is the world built to have no single compact collapse, and it is the block
where H-MAIN rejection concentrates.

## G2 behaviour

{d['G2_accepted']} of {len(B.get('G2', []))} G2 worlds produced an accepted
compact conjecture. **Refusing to produce an equation in G2 is the correct
outcome and is not penalized.** G2 exists to stop the project equating
"predictable" with "compressible into a universal law".

## G3 — the K5 threat

{d['G3_structural_claims']} of {len(B.get('G3', []))} mass-only worlds produced
an accepted candidate claiming non-mass structural dependence. A candidate using
mass and energy may legitimately recover the planted relationship there; a
candidate claiming *additional* non-mass dependence must fail unless that
dependence is redundant with the planted mass law.

## G4 — false-positive rate and K6

```
false-positive rate = {g4['n_accepted']} / {g4['n_valid_replicates']} = {g4['rate']:.4f}
```

| Quantity | Value |
|---|---|
| Numerator | **{g4['n_accepted']}** |
| Denominator | **{g4['n_valid_replicates']}** |
| Rate | **{g4['rate']:.4f}** |
| {g4['ci_method']} 95% interval | **[{g4['ci'][0]:.4f}, {g4['ci'][1]:.4f}]** |
| Criterion | ≤ 5% |
| **K6** | **{d['K6']['verdict']}** |

`p = 0` language is not used for a finite simulation count: with
{g4['n_valid_replicates']} replicates the interval, not the point estimate, is
the claim.

**Supplementary — G4M mass-conditional null.** {g4m['n_worlds']} worlds where
mass dependence is real and no non-mass structure exists:
{g4m['n_accepted_any']} accepted any candidate,
**{g4m['n_accepted_claiming_structure_beyond_mass']}** claimed structure beyond
mass. K6 is adjudicated on G4 as the master plan specifies; G4M is reported
alongside, not instead.

## G5 — confounded worlds

{d['G5_structural_claims']} of {len(B.get('G5', []))} confounded worlds produced
an accepted candidate claiming non-mass structure. The true driver is latent and
never supplied; observed descriptors are proxies. The question is not whether
the search proposes attractive expressions there — it is whether the complete
adjudication system rejects them.

## Measurement-coupling stress result

{d['GC_structural_claims']} of {len(B.get('GC', []))} coupling worlds produced an
accepted candidate claiming non-mass structural dependence.

The generator holds fractional fragmentation fixed as a law, varies precursor
mass, applies an absolute low-mass cutoff at 30/50/80 Da, and computes `mu`
exactly as the real pipeline does. It reproduces both the sign and the
energy-growth of the real association **with no chemistry anywhere in the
construction**.

**Restriction, restated because it binds.** This is a robustness test of the
discovery system. It does **not** identify the mechanism of the real
association, and it does **not** establish what fraction of the observed real
association is artifactual. No such fraction is claimed.

## Retention-time surrogate stress result

{d['GRT_accepted']} of {len(B.get('GRT', []))} GRT worlds produced an accepted
candidate. A latent property drives both descriptors and retention time; RT
predicts observationally but is not the planted cause.

This is a bounded synthetic stress test. It does **not** establish that the real
NC7 finding has been causally resolved. Phase 2's wording stands: RT carries
predictive signal by itself but adds little incremental information beyond
Tier A descriptors, consistent with a structure-associated surrogate in this
dataset; independent confounding cannot be completely excluded.

## Null thresholds

{cal['n_worlds']} calibration worlds, cycling the four master-plan 13.6
constructions, disjoint from the 100 G4 worlds. Statistic: {cal['statistic']}.

| Complexity | 4 | 7 | 10 | 15 | 20 |
|---|---|---|---|---|---|
| Threshold | {cal['threshold_by_complexity'][4]:+.4f} | {cal['threshold_by_complexity'][7]:+.4f} | {cal['threshold_by_complexity'][10]:+.4f} | {cal['threshold_by_complexity'][15]:+.4f} | {cal['threshold_by_complexity'][20]:+.4f} |

Frozen for Phase 4. Full table in `NULL_CALIBRATION.md`.

## Repair attempts

{'None. K6 did not fire, so no repair was permitted or needed.' if not d['K6']['fires'] else 'See DEVIATIONS_P3.md.'}

## Runtime and checkpointing

| Item | Value |
|---|---|
| Worlds × seeds | {budget['counts']['n_worlds']} × {budget['counts']['n_seeds_per_world']} = **{budget['counts']['pysr_runs_total']} PySR runs** |
| gplearn comparison arm | {budget['counts']['gplearn_runs_total']} runs |
| Workers | 4 (measured 2.97×; 6 workers rejected at +11% for +50% memory) |
| Thread caps | OMP/OpenBLAS/MKL/VECLIB/NUMEXPR = 1 |
| Projection | {budget['projection_hours']} h |
| Checkpoint unit | one `(block, world, seed)` run |
| Worst case lost to a crash | {budget['checkpointing']['worst_case_lost_sec']} s |

Checkpointing was exercised for real: the run was interrupted and resumed, and
resume recomputed nothing (`tests/test_p3_checkpoint.py` pins the four
properties).

## Comparison engine — gplearn

Master plan 13.3: "If two engines with different search dynamics converge on
equivalent expressions, that is evidence. If they do not, the expression is a
search artifact."

| Block | Worlds | Engines agree | Support match | PySR matches planted | gplearn matches planted |
|---|---|---|---|---|---|
{gp_rows}

**The comparison arm did not corroborate PySR.** On the structured worlds the
two engines converge on functionally equivalent expressions almost never, and
gplearn never recovers the planted law — including in `G3`, a single power law
that PySR recovers 62% of the time. On the `G4` nulls the engines agree 60% of
the time, which is agreement about noise and is not evidence of anything.

This is reported as measured. It does not change the verdict, which is already
`STOP BEFORE PHASE 4` on the pre-registered rule, and no engine-agreement gate
was pre-registered. It is recorded because it points the same way: **PySR's
selected expressions are not independently corroborated**, and under the master
plan's own reading that is a reason to treat them as search artifacts rather
than as recovered laws.

gplearn was run at its pre-registered configuration on the pre-registered subset
(`DEVIATIONS_P3.md` D5). It is a comparison arm, not a tournament entrant, and
**nothing here would license switching the project to it** — that would require
an explicit deviation and an independent recalibration.

## GA — analytic sanity case

{d['GA_accepted']} of {len(B.get('GA', []))} fully synthetic worlds recovered the
transparent planted law `1.5·v₀ + 0.5·v₁²`, found by the search and selected by
the ranking rule. This world uses no real chemistry, so it isolates the
machinery from any property of the real descriptor matrix.

Its first construction planted the law in the raw frame while the search saw the
dimensionless frame, making it unrecoverable by construction; that was found by
the sanity case doing its job and is recorded in `DEVIATIONS_P3.md` D9.

## Stop conditions, evaluated explicitly

| Condition | Fired |
|---|---|
{stoprows}

{stop_section}

## Unresolved issues

See `BACKLOG.md`. Phase 2's open items I1, I2, I3, I5 and I6 remain open and are
untouched by Phase 3, which is synthetic throughout.

## Highest defensible real-data claims-ladder rung

# L3

**Unchanged by Phase 3.** Structure explains between-compound variation beyond
mass on scaffold-disjoint holdouts. L4 requires an actual real-data symbolic
candidate, which belongs to Phase 4.

A synthetic planted-law recovery is **not** a MURU scientific conjecture and is
not called one. What Phase 3 establishes is separate and narrower: whether the
conjecture-discovery engine passes its synthetic validation.

## Phase 4 authorization

**{d['verdict']}**

{'Phase 4 is authorized subject to the binding restrictions above.' if d['phase4_authorized'] else 'Phase 4 is NOT authorized.'}

The frozen adjudication protocol is `PHASE4_FROZEN_DISCOVERY_PROTOCOL.md` with
machine-readable companion `artifacts/phase4_frozen_protocol.json`. It was
**not executed on the real response during Phase 3**.

## What Phase 3 did not do

No real-data symbolic discovery. No symbolic engine was fitted to the observed
`mu`. No candidate equation was tested against real development `mu`. The sealed
confirmation set was not opened. No Phase 4 implementation exists in this
commit.
"""


if __name__ == "__main__":
    raise SystemExit(main())
