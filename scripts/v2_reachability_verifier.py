#!/usr/bin/env python3
"""Section 31.1's witness verifier, executed for real.

CRITIC_SCIENCE V3-H5 and CRITIC_GOVERNANCE N2/N3 both found that section 32.1's
"constructive reachability proof" was never mechanically checked: it was asserted,
and two of its own repairs (F12a, F14/F9) turned out to have zero witnesses under
the ordering the document itself declared. This script closes that gap.

It does two things, exhaustively rather than by inspection:

  1. TERMINAL-SET EQUALITY. The set of terminal names assigned by section 22.1's
     F1..F17 table (transcribed below, verbatim) must equal the set named in
     section 32's table. A rule with no printed terminal (F0's precedence note)
     is excluded.

  2. REACHABILITY. For every rule F1..F17, in the EXACT printed order, search for
     an integer per-condition vector (A,B,C+D,E summing to 138, applied identically
     across all 12 conditions -- the only form P1 permits) that satisfies that
     rule's condition AND is not pre-empted by any earlier rule. A rule with zero
     witnesses in a bounded search is reported UNVERIFIED, not silently passed.

Only rules F9..F16 depend on the routing arithmetic (S_1, Gate R, E6 headroom);
F1..F8 and F17 are non-arithmetic (freeze/schema/control conditions) and are
verified by construction, listed here for completeness rather than searched.
"""
from __future__ import annotations
import itertools, math, re, sys
from pathlib import Path

DELTA = 10 / 144
Z = 1.9599640
N = 1656

# section 22.1, transcribed. Order IS the precedence (F0).
RULE_ORDER = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11",
             "F12", "F13", "F14", "F15", "F16", "F17"]
RULE_TERMINAL = {
    "F1": "NO_ADMISSIBLE_SURFACE_WITHOUT_FREEZE_AMENDMENT",
    "F2": "BENCHMARK_INTEGRITY_DEFECT",
    "F3": "SURFACE_POPULATION_CONTAMINATED",
    "F4": "SURFACE_INCOMPLETE_COMPOSITION",
    "F5": "VOID_SCHEMA_INCOMPLETE",
    "F6": "VOID_CONTROL_FAILURE",
    "F7": "VOID_INSTRUMENT_INDETERMINATE",
    "F8": "VOID_SINGLE_SHOT_BROKEN",
    "F9": "SURFACE_DEGENERATE_NO_FRONT",
    "F10": "ROUTING_INDETERMINATE",
    "F11": "RC3_WITHDRAWN_RETENTION_NOT_THE_LOSS_STAGE",
    "F12": "E4A_ENTRY_LICENCE_PROPOSED",
    "F13": "E4A_ROUTE_CERTIFIED_NO_SAFETY_HEADROOM",
    "F14": "E4_GENERATION_LICENCE_PROPOSED_F09_F10",
    "F15": "E4_GENERATION_ROUTE_CERTIFIED_NO_SAFETY_HEADROOM",
    "F16": "ROUTE_DETERMINED_ARM_NOT_EXECUTABLE",
    "F17": "T1_NO_ADMISSIBLE_QUALIFICATION_EXISTS",
}
PROTOCOL_MD = (Path(__file__).resolve().parent.parent / "audit" / "muru_v2_reentry_20260819"
              / "MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md")


def parse_section_32_terminals() -> dict[str, str]:
    """PARSE the live protocol document's own section 32 table -- NOT a hand-copied
    literal, and NOT derived from RULE_TERMINAL above. A prior version of this
    function built the "section 32 side" of the equality check from the same
    dict as the "section 22 side", making the check tautological -- it could
    never fail regardless of what section 32 actually said
    (CRITIC_GOVERNANCE NEW-B). This reads the actual markdown table between the
    "## 32. TERMINAL STATES" header and the next "### 32.1" header, and returns
    {terminal_name: rule_id}.
    """
    text = PROTOCOL_MD.read_text()
    start = text.index("## 32. TERMINAL STATES")
    end = text.index("### 32.1", start)
    block = text[start:end]
    out: dict[str, str] = {}
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        term_cell, rule_cell = cells[0], cells[1]
        m_term = re.search(r"`([A-Z0-9_-]+)`", term_cell)
        if not m_term or m_term.group(1) in ("Terminal",):
            continue
        rule = rule_cell.strip("`").strip()
        out[m_term.group(1)] = rule
    return out


SECTION_32_TERMINALS_PARSED = parse_section_32_terminals()
SECTION_32_TERMINALS = set(SECTION_32_TERMINALS_PARSED.keys())

NON_ARITHMETIC = {"F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F17"}


def evaluate(v: tuple[int, int, int, int], headroom: bool):
    """Everything section 20/21 computes from one per-condition vector."""
    A, B, CD, E = v
    n = A + B + CD + E
    piA, piB, piCD, piE = A / n, B / n, CD / n, E / n
    S1 = 1 - piA
    S2 = piCD + piE
    cands = {"A": piA, "B": piB, "C+D": piCD}
    order = sorted(cands.items(), key=lambda x: -x[1])
    argmax, top = order[0]
    second = order[1][1]
    lead = top - second
    sigma = math.sqrt(max(top + second - lead**2, 0) / N)
    lcb = lead - Z * sigma
    certified = lead >= DELTA and lcb > 0
    exonerated = (not certified) and piB < DELTA and S1 > 0 and (S2 / S1) >= (1 - DELTA)
    degenerate = S1 == 0
    gate_row = (
        1 if certified and argmax == "B" else
        2 if certified and argmax == "A" else
        3 if certified and argmax == "C+D" else
        4 if exonerated else
        5
    )
    return dict(argmax=argmax, lead=lead, lcb=lcb, certified=certified,
               exonerated=exonerated, degenerate=degenerate, gate_row=gate_row,
               headroom=headroom)


def rule_fires(rule: str, ev: dict) -> bool:
    if rule == "F9":
        return ev["degenerate"]
    if rule == "F10":
        return ev["gate_row"] == 5
    if rule == "F11":
        return ev["gate_row"] == 4
    if rule == "F12":
        return ev["gate_row"] == 1 and ev["headroom"]
    if rule == "F13":
        return ev["gate_row"] == 1 and not ev["headroom"]
    if rule == "F14":
        return ev["gate_row"] == 2 and ev["headroom"]
    if rule == "F15":
        return ev["gate_row"] == 2 and not ev["headroom"]
    if rule == "F16":
        return ev["gate_row"] == 3
    raise ValueError(rule)


def search_witness(rule: str, budget: int = 600_000):
    """Bounded search over integer (A,B,C+D,E) vectors summing to 138, both
    headroom states, checking F0 precedence against every EARLIER arithmetic rule."""
    tried = 0
    for A in range(0, 139, 1):
        for B in range(0, 139 - A, 1):
            for CD in range(0, 139 - A - B, 1):
                E = 138 - A - B - CD
                if E < 0:
                    continue
                tried += 1
                if tried > budget:
                    return None
                for headroom in (True, False):
                    ev = evaluate((A, B, CD, E), headroom)
                    # F0 precedence: no earlier arithmetic rule may also fire
                    earlier_arith = [r for r in RULE_ORDER[:RULE_ORDER.index(rule)]
                                     if r not in NON_ARITHMETIC]
                    if any(rule_fires(r, ev) for r in earlier_arith):
                        continue
                    if rule_fires(rule, ev):
                        return (A, B, CD, E), headroom, ev
    return None


def main() -> dict:
    report = {"schema": "muru-v2-reachability-verifier-1.0.0"}

    # --- terminal-set equality, against the PARSED section 32 table -----------
    f_terms = set(RULE_TERMINAL.values())
    missing_from_32 = f_terms - SECTION_32_TERMINALS
    extra_in_32 = SECTION_32_TERMINALS - f_terms - {"T-INSTRUMENT-UNBOUNDED-ON-E2A"}
    # rule-ID cross-check: not just "the name appears somewhere in section 32", but
    # "section 32 attributes it to the SAME rule ID section 22 does".
    rule_id_mismatches = []
    for rule_id, term in RULE_TERMINAL.items():
        parsed_rule = SECTION_32_TERMINALS_PARSED.get(term)
        if parsed_rule is not None and parsed_rule != rule_id:
            rule_id_mismatches.append({"terminal": term, "section_22_rule": rule_id,
                                       "section_32_rule": parsed_rule})
    report["terminal_set_equality"] = {
        "f_rule_terminals": len(f_terms),
        "section_32_terminals_parsed": len(SECTION_32_TERMINALS),
        "missing_from_section_32": sorted(missing_from_32),
        "extra_in_section_32": sorted(extra_in_32),
        "rule_id_mismatches": rule_id_mismatches,
        "passed": (not missing_from_32 and not extra_in_32 and not rule_id_mismatches
                  and len(SECTION_32_TERMINALS) >= 15),  # sanity floor: parse did not silently return empty
    }

    # --- reachability, arithmetic rules only, in F0 order -----------------------
    results = {}
    for rule in RULE_ORDER:
        if rule in NON_ARITHMETIC:
            results[rule] = {"terminal": RULE_TERMINAL[rule],
                             "status": "NOT_SEARCHED (non-arithmetic; verified by construction)"}
            continue
        found = search_witness(rule)
        if found is None:
            results[rule] = {"terminal": RULE_TERMINAL[rule], "status": "UNVERIFIED_NO_WITNESS"}
        else:
            (A, B, CD, E), headroom, ev = found
            results[rule] = {"terminal": RULE_TERMINAL[rule], "status": "REACHABLE",
                             "witness": [A, B, CD, E], "headroom": headroom,
                             "gate_row": ev["gate_row"], "lead": round(ev["lead"], 6),
                             "lcb": round(ev["lcb"], 6)}
    report["reachability"] = results
    report["all_arithmetic_rules_reachable"] = all(
        r["status"] == "REACHABLE" for k, r in results.items() if k not in NON_ARITHMETIC)
    report["PASSED"] = (report["terminal_set_equality"]["passed"]
                        and report["all_arithmetic_rules_reachable"])
    return report


if __name__ == "__main__":
    import json
    r = main()
    print(json.dumps(r, indent=2))
    sys.exit(0 if r["PASSED"] else 1)
