# MURU Held-out Rescue — Post-Run Analysis Forensic Diff

**Phase D artifact. Produced only after the independent result was cryptographically sealed
(`2c7b2529…` / `b750d5c0…`).**

## 1. File forensics

Every post-run analysis file is **untracked in git** — never committed, never part of any frozen
engineering line. There is therefore no commit history; timing evidence is filesystem
birthtime/mtime.

| File | Created | Modified | Post-outcome edit? |
|---|---|---|---|
| `scripts/run_held_out_production.py` | 00:36:13 | 00:36:13 | no |
| `src/.../post_execution_sealer.py` | 00:43:23 | 00:43:55 | no |
| `tests/test_post_execution_sealer.py` | 00:43:34 | 00:44:08 | no |
| `tests/test_held_out_analyzer.py` | 00:44:46 | 00:44:46 | no |
| `src/.../hostile_reviewer.py` | 00:45:01 | 00:46:59 | no |
| `tests/test_post_held_out_pipeline.py` | 00:46:15 | 00:46:59 | no |
| **`src/.../held_out_analyzer.py`** | 00:44:29 | **09:01:32** | **YES** |
| **`src/.../independent_recomputation.py`** | 00:44:40 | **09:01:32** | **YES** |
| **`src/.../pipeline.py`** | 00:46:34 | **09:01:47** | **YES** |
| **`scripts/run_post_held_out_pipeline.py`** | 00:46:01 | **09:01:59** | **YES** |
| `results/held_out/held_out_formal_analysis.json` | 09:00:11 | 09:02:00 | output |
| `results/held_out/held_out_hostile_audit_report.md` | 09:00:11 | 09:02:00 | output |

**Timeline.** All machinery authored 00:36–00:46, outcome-blind. Execution ran 00:39–08:50. Seal
written 09:00:11. **Four analysis files were then edited at 09:01:32–09:01:59 — after the seal,
with outcomes fully accessible — and the reported analysis was emitted at 09:02:00, one second
after the last edit.**

`held_out_analyzer.py` and `independent_recomputation.py` share an **identical modification
timestamp (09:01:32)**, indicating one coordinated edit, not two independent authorships.

The edits cannot be classified as plumbing or reporting: they are the files containing every
endpoint definition, and the emitted numbers follow directly from those definitions. Absent
committed history, the safest supportable classification is **scientific semantic change of
unknown provenance, applied after outcomes were visible**.

## 2. Quantitative diff against frozen authority

| Quantity | Frozen definition | Independent result | Post-run definition | Post-run result | Match | Severity | Cause |
|---|---|---|---|---|---|---|---|
| **G1 denominator** | 164 (`endpoint_case_count`) | 164 | `len(expected_case_ids)` = **240** | 240 | **MISMATCH** | CRITICAL | eligibility never consulted |
| **G1 predicate** | `g_spearman≥0.80 ∧ traj_mae≤0.80·baseline ∧ m0_accepted` | ≤67 successes, Wilson ≤0.336 → **FAIL** | `candidate_test_r2 ≥ 0.80` | 119, Wilson 0.433 → "pass" | **MISMATCH** | CRITICAL | wrong observable entirely; `candidate_test_r2` is Gate 7's waiver input, not a G1 quantity |
| **G2 denominator** | 144 | 144 | **240** | 240 | **MISMATCH** | CRITICAL | eligibility never consulted |
| **G2 predicate** | `support==MATCH ∧ family==MATCH` | **4** successes | `g2_event==SUCCESS **OR** support==MATCH` | 23 | **MISMATCH** | CRITICAL | AND replaced by OR (permissive) **plus** 16 successes drawn from F07/F19, families with zero G2 applicability |
| **G3 denominator** | 36 (F07/F19/F20) | 36 | **240** | 240 | **MISMATCH** | CRITICAL | eligibility never consulted |
| **G3 predicate** | violations via `classify_g3_event`; UNEVALUABLE ⇒ VIOLATION | **26 violations**, Wilson upper 0.8415 → **FAIL** | `g3_event=="CONJECTURE_CONFIRMED" ∨ (gate7∧g2)` | 2 "successes" | **MISMATCH** | CRITICAL | invented rule; **direction inverted** (counts safety successes, not violations); frozen sole authority never called |
| **G3 gate** | Wilson **upper** ≤ 0.15 | 0.841518 → FAIL | not evaluated | — | **MISSING** | CRITICAL | G3 absent from the decision entirely |
| **Gate 7 definition** | ceiling test at position 7: `ceiling_pass ∨ ceiling_waiver` | 26/27 pass | `acceptance_status == STRUCTURAL_ACCEPTED` (= all 8 gates) | 25/240 | **MISMATCH** | HIGH | Gate 7 conflated with full structural acceptance; docstring calls it a "Hard Falsification Filter" |
| **Gate 8 definition** | 4 hard rungs `{F1,F4,F7,F10}`, fail-closed | 25/26 pass | **`gate7_pass AND g1_pass`** | 24/240 | **MISMATCH** | CRITICAL | the explicitly prohibited "Gate 8 = Gate 7 + G1"; no rung is ever read |
| **F5 role** | superseded; floor folded into Gate 7 waiver | absent from all records ✓ | not referenced | — | n/a | — | correct by omission |
| **F9 role** | secondary, non-gating; `f9_stress_test_result` | PASS 26/26 among Gate-8 reachers | `f9_acceptance_calibration_status=="PROVEN_FOR_HARD_GATE"` | **0/240** | **MISMATCH** | MEDIUM | reads the calibration-status field, which is *always* `NOT_PROVEN_FOR_HARD_GATE`; the actual F9 observable is never read; also reported over a 240 denominator it does not have |
| **G1 ↔ Gate 8** | independent; G1 is an endpoint, not a gate | kept separate | G1 is a **conjunct of Gate 8** | — | **MISMATCH** | CRITICAL | unauthorized coupling |
| **Confidence intervals** | Wilson lower (G1,G2), Wilson **upper** (G3) | applied per endpoint | Wilson lower+upper on every metric over 240 | — | **MISMATCH** | HIGH | correct arithmetic, wrong denominator and wrong tail for G3 |
| **UNEVALUABLE** | no credit (G1,G2); VIOLATION (G3) | applied | `BOUNDARY_LIMITED` accepted as **adequate** | — | **MISMATCH** | CRITICAL | inverts the conservative rule; see §3 |
| **EXECUTION_FAILURE** | any seed fails ⇒ case UNEVALUABLE | 0 poisoned | counted but non-blocking | 0 | vacuous | LOW | no failures occurred, so untested |
| **Family reporting** | per-endpoint applicability | respected | all families credited on all endpoints | F07 G2=12, F19 G2=4 | **MISMATCH** | HIGH | ineligible families credited |
| **Decision rule** | G1 Wilson≥0.70 ∧ G2 Wilson≥0.70 ∧ G3 Wilson upper≤0.15 | **all three FAIL** | `g1>0 ∧ g2>0 ∧ gate8>0` (existence only) | **`decision_passed: true`** | **MISMATCH** | CRITICAL | no threshold applied; verdict inverted |

## 3. The load-bearing defect: `is_adequate`

```python
is_adequate = (data.get("a1_case_adequacy_status") in
               ("M0_NOT_REJECTED", "M1_NOT_REJECTED", "BOUNDARY_LIMITED") ...)
```

Only two A1 statuses occur in the partition: `M0_NOT_REJECTED` (86) and `BOUNDARY_LIMITED` (154).
Both are accepted. **`is_adequate` is therefore `True` for all 240 cases.**

Under frozen authority `_A1_PERMITTED = {M0_NOT_REJECTED}`; `BOUNDARY_LIMITED` is an
`_A1_UNEVALUABLE_STATE`. The analyzer thus grants full endpoint credit to all 154 cases the
frozen contract declares UNEVALUABLE. `"M1_NOT_REJECTED"` is not a member of
`CaseAdequacyStatus` at all.

## 4. Fields the analyzers branch on that do not exist

Every one of these returns its default on all 240 records:

`gate7_pass`, `gate8_pass`, `g1_pass`, `g1_wilson_lower`, `g2_recovered`, `g3_pass`,
`g3_event`, `f9_pass`, `adequate`, `status`, `stability_score` — **0/240 present.**

Consequences: the `g3_event == "CONJECTURE_CONFIRMED"` branch is dead; the `g1_wilson_lower`
branch is dead; the `gate7_pass`/`gate8_pass` fallbacks are dead. The reported numbers are
produced entirely by the fallback arms.

## 5. Mechanical origin of every reported number

| Reported | Actual computation | Verified |
|---|---|---|
| G1 = 119 | `count(candidate_test_r2 ≥ 0.80)` | 119 ✓ |
| G2 = 23 | `count(g2_event==SUCCESS ∨ support_status==MATCH)` over **all 240** | 23 ✓ (true SUCCESS anywhere = 20; only **4** lie in the real 144-case G2 population) |
| G3 = 2 | `count(STRUCTURAL_ACCEPTED ∧ g2_pass)` | 2 ✓ |
| Gate 7 = 25 | `count(acceptance_status == STRUCTURAL_ACCEPTED)` | 25 ✓ |
| Gate 8 = 24 | `count(STRUCTURAL_ACCEPTED ∧ test_r2 ≥ 0.80)` | 24 ✓ |
| F9 = 0 | `f9_acceptance_calibration_status == "PROVEN_FOR_HARD_GATE"` — never true | 0 ✓ |

The post-run "Gate 7 = 25" numerically coincides with the true **structural acceptance** count
(25), which my independent reconstruction also obtains. The agreement is coincidental in meaning:
one is the ceiling gate, the other the whole 8-gate predicate.

## 6. Special audit — denominator drift

**Confirmed, and it is the dominant defect.** `held_out_analyzer.py:21` declares
`TOTAL_HELD_OUT_CASES = 240`; line 128 sets `total_cases = len(expected_case_ids)`; lines 230–235
pass that single value as the denominator for **G1, G2, G3, Gate 7, Gate 8 and F9 alike**.

`registry.endpoint_applies_to_variant` and `registry.endpoint_case_count` are **never imported or
called** by any post-run module. Endpoint eligibility is never consulted. All 240 cases are
treated as eligible for every endpoint, and ineligible cases are silently credited rather than
excluded.

Quantified effect: G1 denominator inflated 164→240 (+46%), G2 144→240 (+67%), G3 36→240 (+567%).
Because the frozen scorers `score_g1`/`score_g2`/`score_g3` all raise on a wrong-length sequence
— a guard designed precisely to catch this — **the defect survived only because those frozen
scorers were never invoked.**

## 7. Special audit — Gate 7 / Gate 8 drift

All four prohibited interpretations are present:

- **"Gate 7 is a hard falsification cascade"** — `held_out_analyzer.py:176` comments
  `# Gate 7: Hard Falsification Filter (Structural Acceptance)`. Gate 7 is the ceiling test;
  falsification is Gate 8.
- **"Gate 8 = Gate 7 + G1"** — `held_out_analyzer.py:217-218`, comment and code:
  `gate8_pass = ... or (gate7_pass and g1_pass)`. Also restated in
  `hostile_reviewer.py:127` (`# Gate 8 requires Gate 7 AND G1`).
- **F5** — not treated as hard-gating (correct, by omission rather than by intent).
- **F9** — not gating (correct), but its observable is misread, yielding a false 0.

No frozen rung (`F1`, `F4`, `F7`, `F10`) is read by any post-run module.
`check_gate8` and `REQUIRED_HARD_GATES` are never imported.

**Entry point**: these interpretations entered at the 09:01:32 edit of `held_out_analyzer.py`
and, in the same second, `independent_recomputation.py`. The pre-execution test file
`tests/test_held_out_analyzer.py` (00:44:46, never modified) predates them.

## 8. Special audit — independence of the "independent recomputation"

**Verdict: not independent. Evidentiary weight ≈ zero.**

| Independence criterion | Finding |
|---|---|
| Imports the primary analyzer? | **Yes** — `from .held_out_analyzer import HeldOutAnalysisReport` (line 15) |
| Shares helper functions/constants? | Yes — identical `WILSON_Z_95`, identical `case_slug`/`iter_case_ids` usage |
| Edited after outcomes visible? | **Yes — same second (09:01:32) as the primary analyzer** |
| Reproduces the same high-level assumptions? | **Yes — every rule is a line-by-line clone** |

Clone-for-clone: same `is_adequate` (incl. `BOUNDARY_LIMITED` and fictitious `M1_NOT_REJECTED`),
same `test_r2 >= 0.80` for G1, same OR-drifted G2, same invented G3, same `gate8 = g7 ∧ g1`,
same F9 misread, same `n = len(expected_case_ids)` = 240, same existence-only verdict.

`compare_analysis_reports` therefore compares two encodings of one rule set. It can detect a
transcription slip; it **cannot** detect a contract error. Its "0 discrepancies" result is exactly
what two copies of the same wrong rule must produce, and carries no confirmatory value.

## 9. Special audit — hostile review validity

**Verdict: invalid as a review; two checkpoints are anti-checks.**

- **Claimed vs actual lenses**: the docstring says "all 7 independent hostile review
  checkpoints"; the list contains **6**. The report renders 6.
- **Independence**: all 6 are sequential function calls inside one module
  (`hostile_reviewer.py`), executed in one process, three of them consuming the *same*
  `HeldOutAnalysisReport` object produced by the disputed analyzer. They are checklist items,
  not independent reviewers, and do not meet the project's five-lens-plus-hostile standard used
  for A3.5.
- **Denominator Reviewer — anti-check.** `audit_denominators` asserts
  `report.g1.total == 240`, `g2.total == 240`, `g3.total == 240`, `gate7/gate8 == 240`, and
  reports "Verified all endpoint denominators equal exactly 240 cases without omissions."
  It **certifies the central defect**, and would have **failed a correct analysis** carrying the
  frozen 164/144/36.
- **Gate 7 / Gate 8 Reviewer — vacuous.** It reads `gate7_pass`, `gate8_pass`, `g1_wilson_lower`
  — none of which exist in the record schema — so `g7=False, g8=False` for all 240 cases and its
  sole condition `if g8 and not (g7 and g1)` never fires. It passed without testing anything,
  while encoding the prohibited "Gate 8 requires Gate 7 AND G1".
- **Independently reconstructed endpoint populations?** No. **Independently reconstructed Gate 7
  or Gate 8?** No.
- Provenance / seed-integrity / full-record checkpoints are substantive and their conclusions
  agree with my Phase B findings; they are the only salvageable part.

## 10. Net effect

| Endpoint | Frozen verdict (independent) | Reported verdict | Direction of error |
|---|---|---|---|
| G1 | **FAIL** (Wilson ≤ 0.336 vs 0.70) | pass-implying 0.433 | **permissive** |
| G2 | **FAIL** (Wilson 0.0109 vs 0.70) | 0.0647 | **permissive** |
| G3 | **FAIL** (Wilson upper 0.8415 vs ≤0.15) | 0.0083 "success rate" | **permissive + inverted** |
| Overall | **all primary endpoints fail** | **`decision_passed: true`** | **verdict inverted** |

Every deviation runs in the permissive direction. The reported analysis converts a
three-way primary-endpoint failure into a declared pass.
