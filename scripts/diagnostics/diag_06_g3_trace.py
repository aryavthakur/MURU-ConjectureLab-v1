"""Stage 6: inspect all 36 G3 (principal_structural_safety) cases.

G3 is inverted: a low violation rate is good.  ``g3_contract`` charges a
VIOLATION for an UNSAFE structural acceptance *and* for an UNEVALUABLE
acceptance status, the latter deliberately and conservatively.

This stage separates those two, independently of the sealed aggregate, by
re-deriving each case's G3 event from the sealed acceptance status and effective
support with the frozen per-variant classifiers.  It then answers the two
questions the aggregate cannot:

1. Why is each violation a violation?  For every UNEVALUABLE case it walks back
   to the gate the acceptance predicate stopped at, and -- when that gate is
   ``a1_adequacy`` -- links it to the A1 status from stage 1, establishing
   whether G3's failures share the G1 root cause or are independent.

2. Was any unsafe formula ever structurally accepted?  This is checked twice:
   once through the frozen classifiers, and once by an independent direct scan
   that ignores them and simply asks whether any G3 case reached
   ``STRUCTURAL_ACCEPTED`` with non-mass effective support.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from muru_v1_diag_common import (  # noqa: E402
    OUT_DIR,
    eligible_case_ids,
    install_frozen_src,
    load_case_manifest,
    load_sealed_records,
    read_json,
    write_json,
)

install_frozen_src()

from muru.paper_benchmark.g3_contract import (  # noqa: E402
    G3_HELD_OUT_DENOMINATOR,
    G3_WILSON_UPPER_GATE,
    G3Event,
    classify_g3_event,
    score_g3,
)
from muru.paper_benchmark.structural_acceptance import (  # noqa: E402
    AcceptanceResult,
    AcceptanceStatus,
)

#: A1 states that route the acceptance predicate straight to UNEVALUABLE.
A1_UNEVALUABLE = {
    "INSUFFICIENT_DATA",
    "BOUNDARY_LIMITED",
    "NUMERICAL_FAILURE",
    "MODEL_FIT_FAILURE",
    "TIMEOUT",
    "CONTRACT_FAILURE",
}


def main() -> int:
    manifest = load_case_manifest()
    sealed = load_sealed_records()
    a1 = {r["case_id"]: r for r in read_json(OUT_DIR / "a1_decomposition.json")["per_case"]}

    case_ids = eligible_case_ids("G3", manifest)
    if len(case_ids) != G3_HELD_OUT_DENOMINATOR:
        raise SystemExit(f"expected {G3_HELD_OUT_DENOMINATOR} G3 cases, got {len(case_ids)}")

    rows = []
    events = []
    for case_id in case_ids:
        record = sealed[case_id]
        variant = manifest[case_id]["variant"]
        status = AcceptanceStatus(record["acceptance_status"])
        support = record["effective_support"]
        support_set = frozenset(support) if support is not None else None

        event = classify_g3_event(
            variant,
            AcceptanceResult(status=status, gate_reached=record["acceptance_gate_reached"]),
            support_set,
        )
        events.append(event)

        detail = a1[case_id]
        a1_status = detail["recomputed_a1_status"]
        if event is G3Event.VIOLATION:
            if record["acceptance_gate_reached"] == "a1_adequacy" and a1_status in A1_UNEVALUABLE:
                cause = "A1_INDETERMINATE"
                mechanism = (
                    f"A1 returned {a1_status}; structural_acceptance gate 1 maps every "
                    f"A1 indeterminate state to UNEVALUABLE, and g3_contract charges "
                    f"UNEVALUABLE as a violation by design"
                )
            else:
                cause = "OTHER_UNEVALUABLE"
                mechanism = (
                    f"acceptance stopped UNEVALUABLE at gate "
                    f"{record['acceptance_gate_reached']!r} with A1 status {a1_status}"
                )
        elif event is G3Event.UNSAFE:
            cause = "UNSAFE_ACCEPTANCE"
            mechanism = (
                f"structural acceptance admitted support {sorted(support_set or [])} "
                f"under variant {variant}"
            )
        else:
            cause = "NONE"
            mechanism = (
                "evaluable and safe: "
                + (
                    "mass-only acceptance permitted by the variant"
                    if status is AcceptanceStatus.STRUCTURAL_ACCEPTED
                    else f"legitimate non-acceptance ({status.value})"
                )
            )

        rows.append(
            {
                "case_id": case_id,
                "family_id": record["family_id"],
                "variant": variant,
                "g3_event": event.value,
                "is_violation": event in (G3Event.UNSAFE, G3Event.VIOLATION),
                "violation_cause": cause,
                "mechanism": mechanism,
                "acceptance_status": status.value,
                "acceptance_gate_reached": record["acceptance_gate_reached"],
                "a1_status_sealed": record["a1_case_adequacy_status"],
                "a1_status_recomputed": a1_status,
                "a1_blocking_detectors": detail["blocking_detectors"],
                "effective_support": sorted(support_set) if support_set is not None else None,
                "discovered_expression": record["discovered_expression_string"],
                "selection_count": record["selection_count"],
                "valid_r2": record["valid_r2"],
                "complexity": record["complexity"],
            }
        )

    score = score_g3(events)

    # ---- independent safety scan, deliberately not using the classifiers ----
    accepted = [r for r in rows if r["acceptance_status"] == "STRUCTURAL_ACCEPTED"]
    accepted_non_mass = [
        r
        for r in accepted
        if r["effective_support"] is not None and set(r["effective_support"]) - {"mass"}
    ]
    mass_only_permitted = {"F07", "F19A", "F19B"}
    accepted_under_no_acceptance_variant = [
        r for r in accepted if r["variant"] not in mass_only_permitted
    ]

    cause_counts = Counter(r["violation_cause"] for r in rows if r["is_violation"])
    event_counts = Counter(r["g3_event"] for r in rows)

    # Overlap with the G1 root cause.
    g1_ids = set(eligible_case_ids("G1", manifest))
    violations = [r for r in rows if r["is_violation"]]
    overlap = {
        "violations": len(violations),
        "violations_caused_by_a1_indeterminate": cause_counts.get("A1_INDETERMINATE", 0),
        "violations_also_in_the_g1_population": sum(
            1 for r in violations if r["case_id"] in g1_ids
        ),
        "violations_outside_the_g1_population": sum(
            1 for r in violations if r["case_id"] not in g1_ids
        ),
        "note": (
            "16 of the 36 G3 cases (F19C, F20A/B/C) carry no scalar_competence "
            "endpoint, so they cannot appear in G1's 164.  They still run A1, and "
            "an indeterminate A1 still routes them to UNEVALUABLE."
        ),
    }

    write_json(
        OUT_DIR / "g3_trace.json",
        {
            "denominator": G3_HELD_OUT_DENOMINATOR,
            "gate": f"wilson_upper_95 <= {G3_WILSON_UPPER_GATE}",
            "event_counts": dict(event_counts),
            "violations": score.violations,
            "violation_rate": score.violation_rate,
            "wilson_upper_95": score.wilson_upper,
            "gate_passed": score.gate_passed,
            "violation_cause_counts": dict(cause_counts),
            "independent_safety_scan": {
                "method": (
                    "direct scan of sealed acceptance_status and effective_support, "
                    "bypassing the g3_contract classifiers entirely"
                ),
                "structurally_accepted_cases": len(accepted),
                "accepted_with_non_mass_support": len(accepted_non_mass),
                "accepted_under_a_variant_where_no_acceptance_is_safe": len(
                    accepted_under_no_acceptance_variant
                ),
                "unsafe_acceptances_found": len(accepted_non_mass)
                + len(accepted_under_no_acceptance_variant),
                "accepted_case_ids": [r["case_id"] for r in accepted],
                "accepted_support": {
                    r["case_id"]: r["effective_support"] for r in accepted
                },
            },
            "g1_root_cause_overlap": overlap,
            "per_case": rows,
        },
    )
    print(f"  G3 events: {dict(event_counts)}")
    print(f"  violations: {score.violations}/{G3_HELD_OUT_DENOMINATOR} "
          f"wilson_upper={score.wilson_upper:.6f} gate_passed={score.gate_passed}")
    print(f"  violation causes: {dict(cause_counts)}")
    print(f"  independent scan: {len(accepted)} accepted, "
          f"{len(accepted_non_mass)} with non-mass support, "
          f"{len(accepted_under_no_acceptance_variant)} under no-acceptance variants")
    print(f"  wrote {OUT_DIR / 'g3_trace.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
