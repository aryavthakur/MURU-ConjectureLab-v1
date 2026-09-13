# MURU-WUR-v2: Verification and MSnLib External Confirmation — Result

**Decision: VALIDATION NOT EXECUTED.**

This document closes the mandate given for this branch
(`claude/muru-v2-msnlib-confirmation`, forked from PR #5 head
`dc1f04d0d7ba6ee59fc3baf7be7c4c350671efda`): independently verify the
MURU-WUR-v2 repository state, build a reproducible scientific handoff, and
attempt one pre-registered external MSnLib confirmation of the frozen
`V2_TA_MORGAN_JOINT` candidate. The first two were completed. The third was
not: this execution sandbox has no network route to the MSnLib data hosts,
so the study was correctly stopped before validation-outcome access, per
its own governing rule. Nothing about the candidate, the comparator, or the
development evidence changed in this process.

## A. Development evidence (unchanged, independently re-verified)

- **PRIMARY:** candidate P1 0.1159994 vs Tier A comparator P1 0.1305460
  (ratio 0.8886, conditional scaffold-cluster 95% interval [0.865, 0.911],
  ten-arm simultaneous [0.860, 0.918]).
- **STRICT** structural-cluster ratio ≈ 0.9256.
- **AF** (compound RMSE > 0.20): candidate ≈ 6.3%, Tier A ≈ 10.3%.
- Every one of the above was independently reproduced bit-for-bit in this
  study, from a from-scratch, cache-bypassed rebuild in an isolated git
  worktree, starting only from committed code and committed raw data (see
  §Reproducibility below) — not merely re-read from prior documents.
- **Selection caveat:** this is a transparently post-result-selected
  development candidate. Admission criterion c4 was poorly specified for
  joint Tier-A + fingerprint models: the literal original criterion required
  the permuted joint model not to outperform Tier A at all, and corrected
  fingerprint permutations came out at approximately 0.9987, 1.0046, 1.0021,
  0.9979, 0.9982 relative to Tier A — the literal c4 fails in three of five
  permutations by tiny random amounts. Amendment A-3 restated the scientific
  negative-control condition (every permuted version must lose substantially
  to the unpermuted candidate; the mean permuted result must not demonstrate
  improvement beyond the empty-fingerprint/noise null) **after** development
  results were visible. That is scientifically reasonable but post-result,
  and is not rewritten as pre-registered here. The stricter-chemistry gain
  (STRICT ratio ≈ 0.926, roughly 7.4% improvement) is a better guide to
  novel-chemistry transfer than the raw ≈11% PRIMARY development gain.

MURU-WUR-v2 was, before this study, strong development-scaffold-held-out
evidence and nothing more. This study set out to test whether that
advantage transfers independently. It could not run that test in this
environment (§C).

## B. Prior anchor evidence (calibration/pilot only, not confirmatory)

328 of 402 census anchors produced both fixed rungs under the frozen rules;
1,935 anchor scans decoded; only anchor wells were downloaded, never the
validation population. The old absolute-agreement compatibility gate
(median |Δμ| ≤ 0.05 at every rung, Spearman ≥ 0.80, pooled RMSD ≤ 0.08) was
applied literally and **failed** at all three tested deployment adapters:

| Adapter | NCE20 median \|Δμ\| / Spearman | NCE60 | pooled RMSD | passes |
|---|---|---|---|---|
| A0 (frozen WUR map, zero parameters) | 0.0501 / 0.882 | 0.0320 / 0.902 | 0.0784 | no (NCE20 median over by 0.0001) |
| A1 (`E = k·NCE`) | 0.0500 / 0.881 | 0.0450 / 0.901 | 0.0811 | no (RMSD over by 0.0011) |
| A2 (`E = a + b·NCE`) | 0.0506 / 0.881 | 0.0303 / 0.902 | 0.0782 | no (NCE20 median over) |

This is not revisited, rounded, or reinterpreted as passing anywhere in
this study. Descriptively — not as a decision input — the underlying
observable is well-aligned (model-free Spearman 0.94-0.96 between MSnLib
and the exposed development coordinate); the failure is at the absolute-
agreement tolerance, by margins the source document itself characterizes as
smaller than anchor sampling noise. This is disclosed as exactly what it
is: pilot evidence that motivates a differently-scoped comparative study,
not evidence that MSnLib and WUR/LCSB are interchangeable.

## C. New external confirmation: NOT EXECUTED

A complete, self-contained pre-registration protocol
(`MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL.md`, identifier
`muru-v2-msnlib-confirmation-1.0`) was written and committed **before** any
attempt to access validation-outcome data — fixing the A0 deployment map
(zero MSnLib-fitted parameters), the endpoint, the outcome-blind
2,000-scaffold-group sampling rule (seed `20261010`), the whole-scaffold-
group bootstrap (B=10,000, seed `20261011`), the pre-registered success/
practical-strength/inconclusive/failure interpretation rule, the per-rung
and structural-novelty secondary analyses, and the claim scope.

It was not executed. Phase 0 of this study found, before any validation
data was touched, that this execution sandbox has no network route to
Zenodo (`zenodo.org`) or GNPS-external (`gnps-external.ucsd.edu`) — both
time out at the TCP/TLS layer while `github.com` is fully reachable and DNS
resolution and ICMP both work, indicating a host-level egress allowlist
that excludes the MSnLib data hosts, not a general outage — and no local
cache of raw MSnLib validation or anchor mzML exists in this checkout.
Population sampling (which needs the MSnLib design-frame identity tables),
header-only preflight, parser preflight, and the one-look decode are all
consequently blocked. **No MSnLib validation outcome of any kind was
accessed, requested, or seen at any point in this study.** The two
connectivity probes made (bare HTTPS connections to the domain roots of
`zenodo.org` and `gnps-external.ucsd.edu`, no path, no query, no scan or
compound identifier) returned no content and are not a data access event;
they are recorded in `MURU_V2_CONFIRMATION_PREFLIGHT.md` §0.8 as the
evidence for the blocker, nothing more.

No population count, scaffold-group count, spectrum count, P1, ratio,
bootstrap interval, or AF value exists for this study. None is fabricated,
approximated, or estimated here.

## D. Scope

**What this study supports:**
- An independent, from-scratch, cache-bypassed reproduction of every
  headline PRIMARY/STRICT development number for `V2_TA_MORGAN_JOINT` vs
  `V2_REF_TA_RIDGE`, starting only from committed code and committed raw
  data (`MURU_V2_REPRODUCIBILITY_MANIFEST.md`).
- A full-repository regression sweep (2,099 collected tests) showing zero
  new failures attributable to WUR v2 between PR #5's base and head
  (`MURU_V2_REGRESSION_VERIFICATION.md`).
- A complete, honest pre-registration for the external comparative study
  that a future session with MSnLib network access can execute unchanged
  (`MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL.md`).

**What this study does not support:**
- Any claim that MURU-WUR-v2 has been externally validated, confirmed, or
  disconfirmed on MSnLib or on any other independent source. The
  development evidence in §A remains development evidence only.
- Any claim about MSnLib/WUR-LCSB absolute interchangeability beyond what
  §B already discloses (rank-agreement good, absolute-agreement gate
  failed by small margins).
- Any statement about whether the ~11% PRIMARY / ~7.4% STRICT development
  advantage would transfer to MSnLib, to any other acquisition regime, or
  to prospectively-acquired data. That question remains exactly as open as
  it was before this study began.

## Independent verification performed in this study

Beyond the self-checks embedded in Phases 0-3, four independent adversarial
reviews were run against this study's own claims before this document was
finalized (a repository-integrity/ancestry/hash/network re-check from
scratch, a from-scratch reproducibility re-derivation in a separate
worktree, a regression-classification re-check with fresh test reruns, and
a red-team of the confirmation protocol for leakage/scope issues). All four
findings below were incorporated into the committed documents, not just
recorded here.

**Reproducibility reviewer — CONFIRMED, no discrepancies.** Independently
rebuilt representations and candidate/comparators in a separate fresh
worktree, from its own independently-written script (not a copy of this
study's), and reproduced every hash and every P1/ratio figure bit-for-bit.
Bonus corroboration: a from-scratch refit even reproduced the committed
cache's `.parquet` prediction files byte-for-byte (`git status` showed zero
diff after overwriting them).

**Ancestry/hash/network reviewer — CONFIRMED, with 2 corrections made.**
PR #5 ancestry, canonical-JSON hashes, network blocker, and the A0/A1/A2
anchor-gate table all independently reproduced exactly. Found two real
overclaims in the preflight document's exact wording, both now corrected
in `MURU_V2_CONFIRMATION_PREFLIGHT.md`: (1) a claim of "zero hits" for a
`git grep` of `validation_access`/`validation_result` was false (5 hits
exist, all in a pre-existing, never-executed MultiMS2 script; the
substantive conclusion — no VALIDATION-kind record exists — still holds);
(2) an exact DNS A-record count ("3 A records") did not reproduce on a
second independent lookup (6 records), plausibly anycast rotation, now
worded to not overclaim precision it doesn't have.

**Regression-classification reviewer — CONFIRMED core claim, found 1 real
defect.** Independently re-parsed both logs, confirmed the 25
pre-existing failure/error names are byte-identical in set and order
between HEAD and base, reran 4 of them fresh in isolation (ruling out
flakiness), and exactly reconciled the 47-test delta to 10 new WUR v2 test
files. But found that this study's first draft overstated "none of it
changed between base and head" for the environment-closure bucket: `lxml`
is a genuine new unpinned dependency from WUR v2's `external_mzml.py`,
masked by a test that was already failing for unrelated reasons. See
`MURU_V2_REGRESSION_VERIFICATION.md` §4 for the correction and this
study's reverted attempt to fix it directly (reverted after discovering it
cascades into a frozen, unrelated environment-closure hash contract).

**Protocol red-team reviewer — 3 MATERIAL findings, all closed before
finalization.** The A0 zero-parameter claim, outcome-blindness, and the
anchor-gate-failure disclosure were all rated CLEAN. Three process gaps
were rated MATERIAL, none yet exploited (no guard has been constructed, no
sampling has occurred) but all closeable in the specification before a
future session ever reaches step 5 of §11 — and all three are now closed
in `MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL.md`: (1) the frozen-seed
scaffold-group sampling rule under-specified the sort key and exact numpy
call, now pinned with a required pre-sampling hash of the eligible-group
list; (2) this document's description of the one-look guard as "refuses a
second construction" overstated its actual protection (it does not check
git history for a deleted-and-recreated record, nor hash-lock the freeze
document at guard-construction time) — corrected, with two explicit
process checks a future executor must perform that the code itself does
not enforce; (3) the structural-novelty secondary analysis lacked the
"only interpreted strongly if the primary result is supported" guard the
tail-risk secondary already had — added. Two minor findings (claim-scope
template ambiguity between "practically meaningful" and "modest" outcomes,
and an imprecise "commercial-screening" population label) were also
closed.

## E. 2026-09-13 continuation: transport resolved, then a real leakage incident — POPULATION EXPOSED, decision remains VALIDATION NOT EXECUTED

A later session resumed this branch with network access. Both blockers from
§C were resolved: 98 MassIVE files were fetched before that route was
cancelled by explicit instruction, and all nine official positive-mode
Zenodo mzML archives were independently authenticated (MD5, SHA256, and
byte size, against both user-supplied provenance and this repository's own
prior central-directory record) and used to cover the full frozen
2,402-file requirement. Header-only eligibility, structural-novelty bins,
a hardened one-look guard (`ConfirmationAccessGuard`,
`src/muru/wur_v2/confirmation_guard.py`), and a four-reviewer independent
pre-access audit (leakage, statistics, implementation, governance) all
proceeded, with two real pre-outcome code defects found and fixed (a
missing tail-risk override in the decision rule; a load-bearing file with
no builder in the tracked tree) before any freeze was committed.

**The leakage reviewer then found a real, material incident**: a parser-
preflight test script (`10_parser_preflight.py`), intended to re-test the
mzML/Numpress parser on already-exposed anchor data only, had a scoping bug
that decoded real MS2 peak arrays for 964 spectra (28.6% of 3,366 decoded)
matching 350 of the 2,140 eligible validation-population compounds, because
MSnLib wells are pooled and many "anchor" files are shared with sampled
validation compounds. The operator saw one real validation μ value (compound
`MURAVORBGFDSMA`, μ = 0.4535200362523742) in tool output before any formal
guard was ever constructed. Full record:
`MURU_V2_MSNLIB_CONFIRMATION_POPULATION_EXPOSED.md`.

Per explicit operator instruction and this program's own established
precedent for outcome exposure (the WUR-SEALED entry in the exposure
registry: one look, however partial, permanently changes a population's
status), **the entire 2,000-scaffold-group / 2,690-compound sample (seed
20261010) is now EXPOSED and can never support an independent confirmatory
claim.** It was not scored, not further summarized, and no P1/ratio/bootstrap
was computed. The tainted artifact and the exact buggy script are quarantined,
not deleted (`artifacts/wur_v2_confirmation/QUARANTINE_leakage_incident_2026-09-13/`);
the bug is fixed and regression-tested
(`tests/wur_v2/test_v2_parser_preflight_scope.py`); `MURU_V2_MSNLIB_CONFIRMATION_FREEZE.md`
is marked VOID rather than deleted, since the reviewed methodology and
infrastructure (transport, guard, statistics) remain sound for a future
attempt even though this specific sample is dead.

**Decision: VALIDATION NOT EXECUTED still stands** — no P1, ratio, bootstrap
interval, or AF value was ever computed for this population, so no
confirmation/disconfirmation claim of any kind is made here. This is now
compounded by the fact that this specific sample could not support such a
claim even if re-attempted. A new independent validation design, with a new
sample, is required and is explicitly out of scope for this branch — the
next session should define it separately, reusing the transport/guard
infrastructure but drawing an entirely new population.
