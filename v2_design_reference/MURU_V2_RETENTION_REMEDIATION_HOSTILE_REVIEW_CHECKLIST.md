# MURU v2 Retention Remediation: Hostile-Review Checklist

**Purpose.** To be applied by an independent reviewer **after** this protocol
has produced its analysis output, and separately **before** any adoption
decision is acted on. Each item is a falsification attempt against this
design, in the register `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` section 5
already established. An item that cannot be checked with a yes/no against a
specific artifact is not a complete item.

Written results-blind, alongside the preregistration it reviews. Using this
checklist does not require having seen any E2a outcome; every check below is
verifiable from the protocol's own committed text and, after execution, from
the manifest and analysis output it produces.

---

## Section 1: Results-blindness of the design itself

- [ ] **1.1** `MURU_V2_RETENTION_REMEDIATION_MANIFEST_TEMPLATE.json`'s
      `committed_before_e2a_seal.preregistration_commit_timestamp_utc` is
      strictly earlier than `e2a_source.sealed_at_utc`. If this cannot be
      shown, every downstream claim of results-blindness is void regardless
      of what the documents say.
- [ ] **1.2** The git commit that introduced
      `MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md` touches no file
      under `results/e2/`. (`git show --stat <commit>` on the committing
      commit; a design commit that also modifies result files is a defect
      regardless of its prose claims.)
- [ ] **1.3** No number appearing in section 13's predictions (PRR-1 through
      PRR-5) or in any policy definition's free-parameter grid was chosen by
      a process that could have consulted E2a's outcomes. Grid values (R2's
      `k`, R4's `eps`) trace to `MURU_V2_G2_PARETO_STUDY_DESIGN.md` section
      3.1, frozen before this document existed; R6's constants trace to a
      stated, self-contained reason (section 5.2), not a fit.

## Section 2: The retain-everything trap

- [ ] **2.1** R3 (`whole front`) is excluded from
      `adoption_rule.eligible_policy_set` in
      `MURU_V2_RETENTION_REMEDIATION_PROTOCOL.json`. Confirm by direct
      inspection of the JSON, not the prose summary.
- [ ] **2.2** No other registered policy (R1, R2, R4, R5, R6) can degenerate
      into "retain everything" for any value in its frozen grid. Check: R2's
      grid tops out at `k=5`, strictly less than the reported mean front size
      (~15 rows per `MURU_V2_G2_PARETO_STUDY_DESIGN.md` section 2.10); R4's
      `eps` band is bounded above by 0.02 `valid_r2`, which does not admit the
      full front unless the front's `valid_r2` spread is itself under 0.02 --
      report whether this degenerate case occurred for any world, since if it
      did for many worlds R4 quietly became R3 for those cases and that must
      be disclosed, not averaged away.
- [ ] **2.3** `candidate_set_size` (metric 3) is reported for **every**
      policy, including the ones that win. An adoption decision made without
      inspecting this column is incomplete regardless of the recall numbers.

## Section 3: Free-parameter and multiple-comparison discipline

- [ ] **3.1** `dev_selection` records exist for both R2 and R4 in the analysis
      output, and their `selected_value` was computed **only** from
      `V2C_RET_DEV` (90 cases). Cross-check: re-derive
      `conditional_retention_recall` for the selected `k`/`eps` on
      `V2C_RET_DEV` independently from the case-level records filtered to
      `split == "V2C_RET_DEV"`, and confirm it matches
      `dev_selection.grid_values_dev_recall` at the selected index.
- [ ] **3.2** No `case_level_record` with `split == "V2C_RET_DEV"` appears in
      any `policy_summary` computed for the headline comparison (`split ==
      "V2C_RET_EVAL"`). The two populations are disjoint by the `replicate`
      predicate (section 6 of the preregistration); confirm no world_id
      appears in both.
- [ ] **3.3** The Holm-Bonferroni-adjusted significance flags
      (`holm_bonferroni_significant_at_0.05`) are reported alongside, not
      instead of, the raw paired bootstrap intervals, for all 6 head-to-head
      comparisons.
- [ ] **3.4** If R2 or R4 was disqualified at the Development stage
      (`disqualified: true`), confirm the analysis output still reports its
      `V2C_RET_EVAL` numbers for transparency (section 6.1, item 4) and that
      `adoption_decision` does not list it among eligible policies regardless
      of how favorable those numbers look.

## Section 4: Specificity substitution

- [ ] **4.1** Every mention of `false_structure_rate_proxy` in the analysis
      output and any downstream summary is labeled "proxy," not
      "false_structure_rate" bare, and is never presented as a completed E6
      run.
- [ ] **4.2** `adoption_decision.adoption_reason`, if an arm is adopted, states
      explicitly that a formal E6 run against that specific arm remains
      required before any v2 architecture change is finalized (section 10,
      item 2 of the preregistration; `out_of_scope` in the protocol JSON).
      An adoption reason silent on this is incomplete.
- [ ] **4.3** The 36-case `mass_power`-in-`V2C_RET_EVAL` population is large
      enough that its Wilson interval is informative, not vacuous. If the
      interval's width at any policy's point estimate exceeds roughly 0.3,
      say so explicitly rather than reporting a false sense of precision from
      a proxy already declared non-authoritative.

## Section 5: Attribution exclusivity

- [ ] **5.1** The vote-reduction rule (`argmax(valid_r2)` among a seed's
      retained set) is verified to be byte-identical across every policy's
      implementation -- not five separately-written functions that happen to
      agree today. A single shared function, called by every policy's
      cross-seed step, is the only acceptable implementation shape.
- [ ] **5.2** No metric attributes a `conditional_retention_recall` gain
      jointly to "a better retention rule" and "a better vote rule" for the
      same case. Since the vote rule is fixed, this should be structurally
      impossible; confirm it is, not merely assumed.

## Section 6: Boundary and governance leakage

- [ ] **6.1** `MURU_V2_RETENTION_REMEDIATION_E2_INPUT_CONTRACT.json`'s
      `what_this_protocol_never_reads` list was honored during this
      protocol's own authoring -- cross-check against the session's own tool-
      call record if available, or against `git log` / `git diff` on files
      under `results/e2/` never appearing as read operations.
- [ ] **6.2** A static import-graph check (preregistration section 11, item 4)
      exists in the implementation and was actually run, not merely described
      in prose, confirming no import of `registry.resolve_case_id` or any
      Held-out/Challenge loader.
- [ ] **6.3** `gate_evaluation.gate_1_result` is `PASS` before any
      `policy_summary` is produced. If it is `FAIL_SUSPEND_ALL_E4`, confirm
      the analysis output contains **no** `policy_summary` records at all --
      a partial run that scores policies anyway despite a failed Gate 1 is a
      protocol violation, not a partial result worth salvaging.
- [ ] **6.4** If `gate_evaluation.execution_status` is
      `EXECUTES_DIAGNOSTIC_ONLY`, confirm `adoption_decision.adopted_policy_id`
      is `null` and `adoption_reason` states the diagnostic-only status
      explicitly, rather than silently proceeding to an adoption verdict the
      gate did not license.

## Section 7: Replay and internal consistency

- [ ] **7.1** R0's `policy_summary` on the **full 540-case** population
      reproduces E2a's own sealed `first_loss_stage` counts exactly (section
      9, item 1 of the preregistration). This is a hard blocking check: if it
      fails, no other policy's numbers in the same run are trustworthy and
      must not be reported as though they were.
- [ ] **7.2** For every case, `stage_A_invariant` is identical across all
      seven `case_level_record`s sharing that `world_id` (stage A must not
      move with policy, per the taxonomy's own policy-invariance claim in
      section 2 of the preregistration).
- [ ] **7.3** `n_eligible_pool` in every `policy_summary` for a given split is
      identical across all seven policies (it is `540 - |A|` or
      `450 - |A restricted to EVAL|`, a policy-invariant quantity by
      construction).

## Section 8: Claim discipline

- [ ] **8.1** Every one of PRR-1 through PRR-5 is explicitly marked hit, missed,
      or partially-hit in the post-execution report, not silently dropped if
      it missed.
- [ ] **8.2** The denominators reported for `worst_family_performance`,
      `family_performance`, and the headline `conditional_retention_recall`
      all reconcile to `V2C_RET_EVAL`'s 450 cases (or the explicitly-labeled
      `V2C_RET_DEV`/`FULL_540` split) with zero symmetric difference, mirroring
      the closure discipline `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` section
      5 lens 8 requires.
- [ ] **8.3** Any claim in the eventual write-up that a policy "recovers X
      cases" is traceable to a specific `case_level_record` set (world_ids
      listed or listable), not only to a summary percentage.

---

## Disposition

A run whose analysis output fails any Section 1, 2, 6, or 7 item is **not
publishable as a v2 design input** regardless of how favorable its numbers
are -- these are structural validity checks, not judgment calls. Sections 3,
4, 5, and 8 failures should be recorded as declared residual risk (in the
style of `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` section 5's own hostile-
review summary table) rather than necessarily blocking, unless the reviewer
judges the specific failure material.
