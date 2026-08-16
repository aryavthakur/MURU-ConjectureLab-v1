"""Proves the fold-to-compound sufficient-statistics reduction
(E1_PROTOCOL.md Sec 10) is lossless for every criterion in Sec 7.1: scoring
the aggregated compound row must equal a brute-force "any fold, any model,
any probe" scan over the same synthetic fold records, for adversarially
constructed multi-fold, multi-probe patterns (the max hidden in an early vs
late fold; the max coming from m0 vs mk; a fold with no probes at all).

Run: python3 scripts/test_e1_aggregation.py
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e1_fit as e1f  # noqa: E402
import e1_rules as e1r  # noqa: E402


def make_fold(fold_index, n_fold=5, m0_gain_rel=None, mk_gain_rel=None,
              m0_gain_abs=None, mk_gain_abs=None, m0_profile=None, mk_profile=None,
              sigma_hat_sq=0.01, m0_unresolved_c0=False, mk_unresolved_c0=False,
              m0_err=0.1, mk_err=0.08, m0_relaxed=None, mk_relaxed=None):
    m0s = e1f.ProbeSummary(n_touched=1 if m0_gain_rel is not None else 0,
                            max_probe_gain_rel=m0_gain_rel, max_probe_gain_abs=m0_gain_abs,
                            max_profile_ratio=m0_profile)
    mks = e1f.ProbeSummary(n_touched=1 if mk_gain_rel is not None else 0,
                            max_probe_gain_rel=mk_gain_rel, max_probe_gain_abs=mk_gain_abs,
                            max_profile_ratio=mk_profile)
    return e1f.FoldRecord(
        fold_index=fold_index, n_fold=n_fold, held_energy=30.0, held_response=0.5,
        m0_objective=0.001, m0_abs_error=m0_err, mk_objective=0.001, mk_abs_error=mk_err,
        m0_boundary_contact=m0_gain_rel is not None, mk_boundary_contact=mk_gain_rel is not None,
        m0_unresolved_c0=m0_unresolved_c0, mk_unresolved_c0=mk_unresolved_c0,
        sigma_hat_sq=sigma_hat_sq, m0_probe_summary=m0s, mk_probe_summary=mks,
        mk_relaxed_abs_error=mk_relaxed, m0_relaxed_abs_error=m0_relaxed,
    )


def brute_force_c1(folds, delta):
    for f in folds:
        for s in (f.m0_probe_summary, f.mk_probe_summary):
            if s.max_probe_gain_rel is not None and s.max_probe_gain_rel > delta:
                return True
    return False


def brute_force_c2(folds, delta):
    for f in folds:
        for s in (f.m0_probe_summary, f.mk_probe_summary):
            if s.max_probe_gain_abs is None or not f.sigma_hat_sq or not f.n_fold:
                continue
            if s.max_probe_gain_abs > delta * f.sigma_hat_sq * f.n_fold:
                return True
    return False


def brute_force_c3(folds, rho):
    for f in folds:
        for s in (f.m0_probe_summary, f.mk_probe_summary):
            if s.max_profile_ratio is not None and s.max_profile_ratio > rho:
                return True
    return False


def brute_force_c0(folds):
    return any(f.m0_unresolved_c0 or f.mk_unresolved_c0 for f in folds)


def check_case(name, folds, mae_m0=0.10, mae_alt=0.08):
    rec = type("R", (), dict(compound_id="C000", detector="M3", observed_energy_count=6,
                              execution_state="OK", mae_m0=mae_m0, mae_alt=mae_alt,
                              boundary_contact=any(f.m0_boundary_contact or f.mk_boundary_contact for f in folds)))()
    agg = e1f.aggregate_compound(rec, folds)
    df = pd.DataFrame([agg])

    ok = True
    for delta in (1e-3, 3e-3, 1e-2, 3e-2, 1e-1):
        got = bool(e1r.c1_unresolved(df, delta).iloc[0])
        want = brute_force_c1(folds, delta)
        if got != want:
            print(f"FAIL {name} C1 delta={delta}: got {got} want {want}")
            ok = False
    for delta in (0.25, 0.5, 1, 2, 4):
        got = bool(e1r.c2_unresolved(df, delta).iloc[0])
        want = brute_force_c2(folds, delta)
        if got != want:
            print(f"FAIL {name} C2 delta={delta}: got {got} want {want}")
            ok = False
    for rho in (0.05, 0.10, 0.25):
        got = bool(e1r.c3_unresolved(df, rho).iloc[0])
        want = brute_force_c3(folds, rho)
        if got != want:
            print(f"FAIL {name} C3 rho={rho}: got {got} want {want}")
            ok = False
    got_c0 = bool(e1r.c0_unresolved(df).iloc[0])
    want_c0 = brute_force_c0(folds)
    if got_c0 != want_c0:
        print(f"FAIL {name} C0: got {got_c0} want {want_c0}")
        ok = False
    return ok


def main():
    cases = {}

    # Max hidden in an early fold, on the m0 side.
    cases["max_in_early_fold_m0"] = [
        make_fold(0, m0_gain_rel=0.5, m0_gain_abs=0.02, m0_profile=0.9, sigma_hat_sq=0.001, m0_unresolved_c0=True),
        make_fold(1, mk_gain_rel=0.001, mk_gain_abs=0.0001, mk_profile=0.01),
        make_fold(2),
    ]

    # Max hidden in a late fold, on the mk side.
    cases["max_in_late_fold_mk"] = [
        make_fold(0, m0_gain_rel=0.001),
        make_fold(1),
        make_fold(2, mk_gain_rel=0.7, mk_gain_abs=0.05, mk_profile=0.6, sigma_hat_sq=0.002, mk_unresolved_c0=True),
    ]

    # No probes anywhere (no boundary contact at all): everything resolved.
    cases["no_contact"] = [make_fold(0), make_fold(1), make_fold(2)]

    # Multiple folds each with moderate values, none individually maximal,
    # but distributed across both m0 and mk.
    cases["distributed"] = [
        make_fold(0, m0_gain_rel=0.02, m0_gain_abs=0.001, m0_profile=0.08, sigma_hat_sq=0.01),
        make_fold(1, mk_gain_rel=0.015, mk_gain_abs=0.0009, mk_profile=0.07, sigma_hat_sq=0.01),
        make_fold(2, m0_gain_rel=0.011, mk_gain_rel=0.012, m0_gain_abs=0.0008, mk_gain_abs=0.0011, sigma_hat_sq=0.01,
                   m0_profile=0.06, mk_profile=0.11),
    ]

    all_ok = True
    for name, folds in cases.items():
        ok = check_case(name, folds)
        print(f"{'PASS' if ok else 'FAIL'} {name}")
        all_ok = all_ok and ok

    # C4 verdict-flip: relaxed fit changes the win/no-win verdict.
    folds_flip = [
        make_fold(0, mk_gain_rel=0.05, mk_gain_abs=0.001, mk_profile=0.3, m0_err=0.10, mk_err=0.095, mk_relaxed=0.05),
        make_fold(1, m0_err=0.10, mk_err=0.095, mk_relaxed=0.095),
    ]
    rec_flip = type("R", (), dict(compound_id="C000", detector="M3", observed_energy_count=6,
                                   execution_state="OK", mae_m0=0.10, mae_alt=0.095, boundary_contact=True))()
    agg_flip = e1f.aggregate_compound(rec_flip, folds_flip)
    # Original: mae_alt=0.095 <= 0.9*0.10=0.09? No (0.095 > 0.09) -> NO_PRACTICAL_WIN
    # Relaxed: mean([0.05,0.095])=0.0725 <= 0.09 -> PRACTICAL_WIN. Verdict should flip.
    if not agg_flip["c4_verdict_flip"]:
        print("FAIL c4_verdict_flip: expected True")
        all_ok = False
    else:
        print("PASS c4_verdict_flip")

    if all_ok:
        print("ALL AGGREGATION EQUIVALENCE CHECKS PASS")
        sys.exit(0)
    else:
        print("AGGREGATION EQUIVALENCE CHECKS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
