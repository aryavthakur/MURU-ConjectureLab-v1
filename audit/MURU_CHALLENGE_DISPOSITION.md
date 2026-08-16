# MURU Challenge Partition — Disposition

## **CHALLENGE REMAINS UNOPENED BY FROZEN GOVERNANCE**

## 1. Why this was adjudicated blind

The context that restored the Held-out analysis knows the Held-out outcome. A decision about whether
to open a second sealed partition, taken by a context that knows how the first one turned out, is
not credible however carefully it is reasoned — the reasoning and the knowledge cannot be separated
after the fact.

The adjudication was therefore delegated to a **fresh outcome-blind context**, given only the frozen
governing authorities at the run commit and explicitly forbidden from reading any results directory,
any execution worktree, any rescue or restoration artifact, or any branch or history beyond its own
HEAD. It was pinned to a clean worktree detached at `8d87143` which contains **no `results/`
directory at all**, so there was no outcome material present to encounter.

Adjudication: `audit/MURU_CHALLENGE_BLIND_ADJUDICATION.md`,
SHA-256 `14a3c037db09991f40f1b6f91d5ff390524cadda32b462a84e3ee2cdeba12eed`.

### 1.1 Blinding hazard, disclosed

The adjudicating context reported that its shell was initialised with a working directory inside the
restoration worktree — a path on its own prohibited list. It states that it never read, listed or
searched that directory, that every command it issued used an absolute path into the blind worktree,
and that the harness independently refused two git commands and a direct write into that tree.

This is recorded because it is a real hazard, not because it is believed to have been realised. Two
things bound its consequence: the blind worktree contains no results, and — decisively — the verdict
rests on four supports that are each a constant, a mechanical count, a quoted sentence, or a
file-existence check, none of which any outcome could alter. The verdict is checkable without
trusting the attestation.

## 2. Verdict

**Primary question: (c) — Challenge is not authorized by anything currently frozen.** Opening it
would itself require a new prospective amendment (an "A3.7") together with an authorization delta,
and no such instrument exists.

**Decisive sub-question: YES — the decision would be identical regardless of the Held-out outcome.**

The blind context ran both counterfactuals explicitly. Had all three primary endpoints passed, A3.6
would still forbid Challenge, no amendment would authorize it, and the three frozen scorers would
still assert Held-out lengths. Had all three failed, identically so — and additionally the one
frozen post-endpoint rule blocks the positive claim while retaining descriptive reporting, and the
frozen role statement keeps Challenge out of every primary denominator, so Challenge could repair
nothing.

## 3. Independent verification of the load-bearing citations

Every citation the verdict rests on was re-checked directly in this (non-blind) context. All confirm.

| Claim | Source | Verified |
|---|---|---|
| A3.6 forbids Challenge | `rc5_authorization.py:3-5`, quoting A3.6: *"RC5.1 is not authorized to construct or execute Challenge, or open Confirmation."* | ✓ |
| The prohibition is implemented | `rc5_authorization.py:23`: `AUTHORISED_PARTITIONS = frozenset({"development", "held_out"})` | ✓ |
| Challenge carries no primary role | `MURU_PAPER_BENCHMARK_PROTOCOL.md:13`: *"Challenge cases do not enter primary denominators."* | ✓ |
| The frozen post-endpoint rule omits Challenge | `MURU_PAPER_BENCHMARK_METRICS.md`: *"Any failed gate blocks the positive claim while retaining descriptive endpoint reports."* — two branches, Challenge in neither | ✓ |
| A1, A3.1, A3.2, A3.3, A3.4 never mention Challenge | `grep -c -i challenge` = **0** for all five | ✓ |

### 3.1 The blind context's residual uncertainty, now closed

The adjudication flagged that the A3.5 and A3.6 **primary texts were absent from its worktree**, so
its reading of them was mediated by audit records and source docstrings. It asked that whoever holds
those commits confirm directly. Done, and both confirm its verdict:

**A3.6 §A3.6.6.1**, at `327b5553` — verbatim:

> "**Challenge Partition**: The 60 Challenge cases remain UNAUTHORIZED for primary benchmark scoring
> and execution under this amendment."

**A3.6 §3** describes the role: Challenge "serves as exploratory stress testing outside primary
denominators."

**A3.5**, at `560bf285`, states that Challenge "is excluded from all primary denominators and
reserved for descriptive robustness only", records its status as `NOT CONSTRUCTED OR EXECUTED`, and
declares that RC5 "is **not** authorized to open Held-out, construct or execute Challenge, open
Confirmation."

Neither amendment contains a Challenge trigger, schedule, stopping rule, or authorization. The
residual uncertainty resolves in favour of (c), and it resolves on text the blind context could not
reach.

## 4. Why the "open Challenge" branch could not have been executed as planned

The plan for opening Challenge assumed an **authorization-only A3.7 plus a permission-only RC5.2
delta with zero scientific semantic change** — the same shape as A3.6/RC5.1, which was verified to
be exactly that.

**That assumption does not hold for Challenge, and this is a substantive finding rather than a
technicality.** A3.6/RC5.1 was permission-only because Held-out already had a complete frozen
scoring contract; only the door needed unlocking. Challenge has no scoring contract at all:

- `rc5_g1_bridge.py:432-436` raises unless the G1 sequence is exactly **164**;
- `g2_contract.py:475` fixes the G2 denominator at **144**;
- `g3_contract.py:258-262` raises with `expected 36 G3 events, got N`.

All three hard-assert **Held-out** denominators. A Challenge population would make every frozen
primary scorer raise. Challenge denominators, per-endpoint applicability, aggregation and reporting
are unspecified in every frozen instrument. Under the project's own taxonomy that is an
`UNFROZEN_SCIENTIFIC_DECISION`, and the established precedent on encountering one is to stop and
amend — the precedent set when RC5 halted execution over six unfrozen execution semantics.

So even had the authorization question gone the other way, an RC5.2 could not have been
permission-only, and "prove zero scientific semantic change" could not have been discharged: new
science would have had to be written.

## 5. A further reason (c) is right rather than merely technically correct

The blind context searched the protocol, the freeze record, the metrics document, the case families,
all seven present amendments, the registry and the generator, and found that **the scientific
question Challenge is meant to answer was never written down.** It also established that the
generator does not branch on partition — a partition-identity property test requires byte-identical
payloads across partition labels — so Challenge cases are not harder by construction. The "stress
and boundary conditions" framing has no generative backing in the frozen registry; A3.6's own
description is "exploratory stress testing outside primary denominators."

A partition whose scientific question was never specified cannot have been prospectively scheduled
to answer it. Opening it now would mean writing that question **after** a primary result exists,
which is precisely the prospectivity failure the entire governance structure was built to prevent.

## 6. Action taken

**None. Challenge was not opened, and nothing was created that would make opening it easier.**

| | Status |
|---|---|
| `AUTHORISED_PARTITIONS` | **unchanged**: `{"development", "held_out"}` |
| A3.7 | **not created** |
| RC5.2 | **not created** |
| Challenge worktree / manifest | **not created** |
| Challenge cases generated | **0** |
| Challenge searches executed | **0** of the 1,800 that a 60 × 30 run would require |
| Challenge records, outcomes, or scores | **none** |
| Confirmation (real data) | **sealed, untouched** |

## 7. What would have to be true to open Challenge later

Recorded so that a future decision starts from the right list rather than re-deriving it, and
explicitly **not** an endorsement that it should be opened.

A frozen **A3.7** would have to: supersede A3.6's refusal by naming the clause it lifts, for both
construction and execution; specify the Challenge scoring contract from scratch, including
applicability, denominators, aggregation and uncertainty treatment, while restating that no
Challenge quantity enters any primary denominator or gate; state what scientific question Challenge
answers, honestly reflecting that the generator makes its cases no harder; carry an
outcome-invariance attestation recording that no Challenge denominator, applicability set, threshold
or reporting choice was selected with knowledge of the Held-out outcome, and under what blinding it
was written; declare its temporal position relative to sealed material, including that Held-out has
been executed; and be frozen as a tag with a per-path digest artifact added to the protected set.

A corresponding **RC5.2** would extend `AUTHORISED_PARTITIONS`, correct the refusal message, and
implement the new Challenge scorers as an additive path that cannot reach the primary aggregate.

The fourth item is the hard one. A3.7 would be the first benchmark instrument written after a
primary result exists, and its outcome-invariance would be the first thing an adversarial reviewer
attacks. That difficulty is a reason for care, not a reason to hurry.

## 8. Incidental finding, independently corroborated

The blind context found, without prompting and without access to this restoration's work, the same
integrity gap recorded in the supersession ledger §5: `scripts/pb_rc5_a3_5_authorized_delta.py` pins
`rc5_authorization.py` at `fd1dfe74…` while the file now hashes to `e8fc53c5…`, and no RC5.1 ledger
exists. Two independent contexts, one of them blind, reaching the same finding from different
starting points strengthens it. Disposition unchanged: governance bookkeeping, not science,
deliberately not repaired here.

---

**CHALLENGE REMAINS UNOPENED BY FROZEN GOVERNANCE**

The synthetic study closes on the Held-out partition.
