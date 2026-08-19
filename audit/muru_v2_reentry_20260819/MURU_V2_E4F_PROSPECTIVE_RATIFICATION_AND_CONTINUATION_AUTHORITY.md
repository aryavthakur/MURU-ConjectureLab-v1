# MURU v2 — E4f Prospective Ratification & Continuation Authority

**Status: RATIFIED by the protocol owner.**
**Nature: a governance act. It creates no scientific evidence and alters none.**

This record implements a protocol-owner instruction issued directly in the
Stage 0/Stage 1 execution session on 2026-08-19, immediately after protocol
v6 was frozen, hashed, tagged (`muru-freeze/e7-protocol-v6`), and pushed at
commit `899d9b0` (manifest committed `89b0765`). It is a new governance act,
not an amendment of the sealed `MURU_V2_PROTOCOL_OWNER_RATIFICATION.md`
(D1–D6, D2-extended), which remains untouched.

| | |
|---|---|
| Ratifying instruction, given directly to | this execution session, 2026-08-19, immediately following the v6 freeze |
| Ratifying instruction, transcribed into a repository record by | this document (commit below) and `FORWARD_RUN_EVENT_LOG.jsonl` (follow-up commit, citing this one) |
| Protocol owner | Aryav Thakur (`aryav.thakur@gmail.com`, git identity `Aryav Thakur`) |
| Ratification branch | `claude/muru-v2-autonomous-reentry` |
| Upstream frozen protocol | commit `899d9b0`, tag `muru-freeze/e7-protocol-v6` |
| Sealed/frozen evidence altered | **NONE** — verified §5 below |

---

## 1. Provenance — why this counts as the record §2.1/N6 requires

`MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md` §2.1 finding `N6` rejected a prior
draft's authority citation because it was **invented by the analyst** — no
record of an actual instruction existed anywhere in the repository, and the
three conditions attached to it were fabricated. `N6`'s own stated repair
condition is that a real record must exist, *"signed, scoped, and tagged like
the programme's other ten authority tags."*

This document is not an analyst inference. It transcribes an explicit,
first-person instruction from the protocol owner, given directly to this
session, addressed to exactly this question. That is the same *kind* of
mechanism by which all ten existing `muru-authority/*` tags were produced —
a protocol-owner decision, issued to the executing session, transcribed and
tagged — with one honestly-disclosed asymmetry: each of the ten prior tags
points to a commit containing an independently verifiable artifact
*instantiating* the authority it claims (an executed protocol, a hostile-review
result, a frozen design), checkable against that commit's diff. This
document's own act of transcription is, structurally, the entirety of what
makes it a record — there is no upstream artifact to check it against beyond
the chat instruction itself, which is not separately repository-evidenced
before this document exists. The gap `N6` requires closed is "does a
protocol-owner record exist, signed, scoped, and tagged" — not "does an
artifact independently corroborate that the owner meant it" — so this document
still closes that specific gap. But the asymmetry is real and is disclosed
here rather than papered over. It is scoped narrowly (§2 below) and will be
tagged `muru-authority/<shortsha>-e4f-prospective-ratification` upon commit,
consistent with that convention; `FORWARD_RUN_EVENT_LOG.jsonl` receives a
follow-up entry citing this commit's real hash once it exists (the log's own
established convention: each entry cites a prior, already-known commit, not
itself).

**CRITIC_GOVERNANCE's first pass on this document (2026-08-19) correctly
FAILED it** for citing `FORWARD_RUN_EVENT_LOG.jsonl` as already containing this
instruction when it did not — the same fabricated-record defect class `N6`
exists to catch, committed by the document meant to cure it. That citation is
removed above; this is now correctly ordered: document first, then the log
entry citing it, never the reverse.

---

## 2. What is ratified

**A. Continuation.** Explicit authorization for multi-hour, unattended
execution of the already-frozen protocol (commit `899d9b0`) through Stage 0
and Stage 1, without further per-stage sign-off solely because a run takes
hours.

**B. Execution-safety tooling.** Explicit authorization for the
architecture-neutral engineering work needed to complete the protocol:
subprocess isolation, resource guards, checkpointing, scoring, adjudication,
hostile review, reconciliation, commits, tags, and pushes. This is
authorization to build and run tooling — it does not authorize changing any
frozen scientific rule (population, worlds, seed bands, generator, search
configuration, decision-admissible schema, truth-blind boundary, scoring
rules, acceptance criteria, routing rules, terminal rules) based on
intermediate results. §21.5's freeze-integrity requirements govern that
question exactly as already frozen, unchanged by this document.

**C. E4f — future-executable, conditionally, not now.**

> E4f is ratified as FUTURE-EXECUTABLE **if and only if** the prospectively
> frozen Stage 1 decision-admissible routing independently licenses the
> cross-seed `C+D` route (§21.2 row 3 / §22 `F16`'s condition).

Explicit, binding limits on this clause, carried over unweakened from the
ratifying instruction:

- This does **not** license E4f now. Absent a certified `C+D` route from
  Stage 1, `F16` still fires `ROUTE_DETERMINED_ARM_NOT_EXECUTABLE` exactly as
  frozen.
- This does **not** use E2b to license E4f. E2b remains
  `DECISION_INADMISSIBLE` per the sealed Gate 1 record; nothing in this
  document reclassifies it.
- This does **not** predict, weight toward, or otherwise influence Stage 1's
  routing outcome. Stage 1 executes and is adjudicated exactly as frozen,
  before this clause has any effect.
- If Stage 1 does not independently license E4f from decision-admissible
  evidence, **E4f remains closed**, permanently for this surface, not
  pending.

**D. Other E4 arms.** If Stage 1's routing instead licenses a different E4
arm (E4a/b/c/d/e), this document adds no new license beyond what §21.2's
table and each arm's own frozen or prospective operational requirements
already provide. Execute only the smallest mechanically licensed arm; do not
execute multiple arms to obtain a positive result (already stated in §21 and
restated, not altered, here).

**E. E5/E6.** Reassess E5 mechanically per §21's existing rule; execute only
if the causal dependency path requires it. For every surviving E4 candidate,
prospectively operationalize, freeze, and hostile-review E6 before seeing E6
results, then execute automatically. Both already-frozen, restated not
altered.

---

## 3. What this document explicitly does NOT do

- **It is not an E4f hostile review.** `MURU_V2_E4F_OPERATIONAL_PREREGISTRATION.md`
  (hash `0ce2755d…3a7f61`, freeze commit `8a2ffa50`) has never itself been
  through a `CRITIC_SCIENCE`/`CRITIC_GOVERNANCE` pass — only this calibration
  protocol has. Closing the authority-record gap does not manufacture that
  review. **If and only if Stage 1 certifies route `C+D`**, before E4f
  actually executes this session must first run both hostile critics against
  the E4f operational preregistration itself and repair any genuine defect
  they find, exactly as was done for this protocol. This is required by
  programme convention (every other executed arm — E0, E1, E3, the E2b
  replay — was hostile-reviewed before execution) and by §21.2 row 3's own
  text, and is not waived by this ratification.
- **It does not touch `f4c1105`'s GATE 1 STOP.** E4a's separate blocker
  (§21.2 row 1's honesty note: `f4c1105` fired `GATE_1 = FAIL` on the sealed
  surface and nothing here re-arms it) is untouched. A still-open, uncommitted
  draft, `MURU_V2_E4A_PROTOCOL_OWNER_DECISION_PACKAGE.md` (repository root,
  dated 2026-08-18, explicitly marked "nothing here is committed or pushed
  without explicit sign-off"), raises three protocol-owner decisions about
  E4a's Gate 1 hook that this instruction did not address. It is left exactly
  as found — uncommitted, unresolved — and is only in scope if Stage 1's
  routing certifies `B` (`LOST_IN_RETENTION`).
- **It does not re-open Gate 1, rerun E2b, or amend any sealed artifact.**
  Unchanged from the master prompt's standing prohibition.
- **It is not a hostile-reviewed scientific claim.** Per the header, it is a
  governance act; §21.2 row 3's freeze-integrity rider (independent
  re-verification of the E4f hash and freeze-commit ancestry before Gate R is
  read, regardless of executability) still runs unconditionally and still
  terminates at `VOID_CONTROL_FAILURE` (§22 F6) if either has moved.

---

## 4. Consequence for §21.2 row 3 and §22 F16

With this record committed and tagged, the condition `N6`'s repair stated as
blocking — *"no protocol-owner record for E4f's execution... exists"** — no
longer holds. Row 3 of §21.2 and terminal `F16` are read as follows, going
forward, **without editing the frozen protocol text**, which correctly
anticipated this and left `MURU_V2_E4F_OPERATIONAL_PREREGISTRATION.md`
"prospectively frozen and unedited... ready to be re-armed without redoing
any of its own work":

```
IF   Stage 1 routing is ROUTING_CERTIFIED and certified argmax = C+D
AND  this ratification record is committed, tagged, and hash-verified unmoved
AND  MURU_V2_E4F_OPERATIONAL_PREREGISTRATION.md has passed its own
     CRITIC_SCIENCE + CRITIC_GOVERNANCE hostile review (§3 above)
AND  §21.2 row 3's freeze-integrity rider re-verifies clean
THEN E4f is executable: propose family i (classifier) only; execute and
     fully report family ii (voting), licensing nothing from it (per the
     dormant DEF-H5/DEF-H6 analysis already on record in §21.2).
ELSE F16 fires ROUTE_DETERMINED_ARM_NOT_EXECUTABLE exactly as frozen.
```

---

## 5. Verification, performed after writing this document

- `MURU_V2_E4F_OPERATIONAL_PREREGISTRATION.md` sha256:
  `0ce2755d9661d707a48961d11477fd6b793f8567c0e835e058a180d2763a7f61` — matches
  the value cited throughout the frozen protocol text.
- `8a2ffa50` verified a strict ancestor of `HEAD` (`git merge-base
  --is-ancestor`).
- `git status` clean before this file was added; no sealed or frozen artifact
  under `audit/e2b_definitive_cloud_adjudication_20260818/` or
  `audit/muru_v2_reentry_20260819/` touched.
- All 10 pre-existing `muru-authority/*` tags present locally.
- This document itself creates no scientific evidence and licenses no
  execution by itself — §2C and §4 govern what, if anything, it enables.

## 6. What this authorizes next

Proceed to build the disclosed Stage-1 execution-safety gap (subprocess
isolation for `v2_stage1_scoring.py`'s canonicalisation calls), then resume
Stage 0 to a genuine single-shot completion, then execute Stage 1, per §2A/§2B
of this record and the master prompt already governing this session.
