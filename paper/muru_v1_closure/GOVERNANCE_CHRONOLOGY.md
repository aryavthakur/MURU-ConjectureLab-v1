# MURU ConjectureLab v1 — Governance Chronology

Every science freeze and engineering freeze, in creation order, with the tag that pins it. Science
content and engineering implementation are frozen on **separate** tag lines so that an
implementation change can never silently carry a science change.

## 1. Freeze line

| Date | Tag | Layer | What it froze |
|---|---|---|---|
| 2026-08-11 | `phase1-complete` | phase | Phase 1 closed |
| 2026-08-12 | `phase2-complete` | phase | Phase 2 closed |
| 2026-08-13 | `benchmark-content-freeze-a1` | **science** | A1 — the adequacy ladder: M0 and the M1/M2/M3 contrasts, the LOEO protocol, the frozen `log_g ∈ [-2,2]` grid and refinement |
| 2026-08-13 | `benchmark-content-freeze-a2` | **science** | A2 — family F16 (combined mild non-scalar violation) |
| 2026-08-13 | `benchmark-content-freeze-a2-1` | **science** | A2.1 — generator versioning |
| 2026-08-13 | `benchmark-content-freeze-a3-1` | **science** | A3.1 — the structural acceptance predicate with typed states; G2's support-and-family conjunction; G3's variant semantics; the fixed denominators |
| 2026-08-14 | `engineering-rc3-a3-1` | engineering | RC3 — A3.1 implemented |
| 2026-08-14 | `benchmark-content-freeze-a3-2` | **science** | A3.2 — the structural-null calibration table (digest `b9b6148…`) |
| 2026-08-14 | `engineering-rc3-1-a3-2` | engineering | RC3.1 — A3.2 wired in |
| 2026-08-14 | `benchmark-content-freeze-a3-3` | **science** | A3.3 — the secondary symbolic evaluation contracts (parameter recovery, predictive equivalence) |
| 2026-08-14 | `benchmark-content-freeze-a3-4` | **science** | A3.4 — the A3.3 scorers made deterministic and case-wired |
| 2026-08-14 | `a3-4-temporal-provenance-erratum` | erratum | temporal provenance correction to A3.4 metadata |
| 2026-08-14 | `engineering-rc4-a3-4` | engineering | RC4 — A3.4 implemented |
| 2026-08-14 | `engineering-rc4-1-environment-closure` | engineering | RC4.1 — executable environment closed, dependency graph pinned |
| 2026-08-14 | `engineering-rc4-2-core-defect-repair` | engineering | RC4.2 — defects R1–R4 repaired |
| 2026-08-14 | `engineering-rc4-2-1-integrity-closure` | engineering | RC4.2.1 — integrity closure and the Development boundary |
| 2026-08-15 | `benchmark-content-freeze-a3-5` | **science** | A3.5 — Gate 7 amended (F5's floor folded into the waiver branch); F5 superseded; Gate 8 reduced to four hard rungs and made fail-closed; F9 fixed as secondary and non-gating; G1's LOEO bridge specified; §8.2 execution-failure semantics; §8.3 G3 sole authority |
| 2026-08-15 | `engineering-rc5-a3-5` | engineering | RC5 — A3.5 implemented, after an initial *NOT FROZEN* verdict |
| 2026-08-16 | `benchmark-content-freeze-a3-6` | **science** | A3.6 — Held-out authorization, binding **zero scientific change** |
| 2026-08-16 | `engineering-rc5-1-heldout-authorization` | engineering | **RC5.1 — the run commit `8d87143d…`** |

## 2. Governance events worth recording

**RC5 was refused once.** The tag line shows `ad75bb1 RC5: hostile review record and engineering
decision — RC5 NOT FROZEN` preceding the eventual RC5 freeze. An independent hostile review found
blocking defects; they were repaired (`97b28d3`) and RC5 was frozen only afterwards. The review was
load-bearing, not ceremonial.

**A self-audit preceded external review.** `d04358b RC5: close three provenance defects found by
self-audit before external review` — provenance defects were found and closed before the reviewer
saw the tree.

**An execution blocker was recorded rather than worked around.** `e54364b Record the Development
execution blocker: RC4 has no executable case path`, and separately `a605120 RC5 Gate 1: stop, six
execution semantics have no prospective authority` — execution was halted on the finding that six
execution semantics lacked prospective authority, rather than proceeding and documenting afterwards.

**Calibration evidence was rescued.** `44e5e36 Preserve the A3.2 calibration evidence, which was
never committed anywhere` — the calibration table backing every Gate-2 and Gate-7 decision existed
only in a working tree and was committed before it could be lost.

**A3.6 is authorization-only, and this was verified rather than assumed.** The forensic rescue
diffed `7cdd5a6 → 8d87143` independently: eight files touched, and the only non-test, non-audit
source change is a one-line edit to `AUTHORISED_PARTITIONS`, from `{"development"}` to
`{"development", "held_out"}`. No endpoint, gate, falsification, scoring, registry, selection or
manifest module was modified. A3.6 §A3.6.5 independently binds "zero scientific changes" and
enumerates NO-change bindings for Gate 7, Gate 8, F5, F9, G1, G2, G3 and all denominators. Code and
text agree.

## 3. Held-out execution and sealing

| Time (local, 2026-08-16) | Event |
|---|---|
| 00:36 | execution manifest written; production runner authored |
| 00:39 | Held-out execution begins under `8d87143d…`, tree clean |
| 00:36–00:46 | all post-run analysis machinery authored — **outcome-blind**, before any result existed |
| 03:11 | 239 of 240 cases complete |
| 08:50 | the last case (`PB\|held_out\|F14\|r008`, 24,216 s) completes |
| **09:00:11** | **raw evidence sealed** — 482 files hashed, receipt written |
| 09:01:32–09:01:59 | **four analysis files edited, after the seal, with outcomes accessible** |
| 09:02:00 | the defective analysis emitted, one second after the last edit |

The seal is correctly ordered: no raw file has an mtime later than the seal, and the two analysis
outputs written at 09:02 are outside the sealed set.

## 4. The analysis-contract failure

The originally reported analysis inverted the study's verdict. It reported `decision_passed: true`
by scoring every endpoint over a 240 denominator, substituting `candidate_test_r2` for G1, relaxing
G2's conjunction to a disjunction, inventing a G3 rule with inverted direction, conflating Gate 7
with full structural acceptance, and composing Gate 8 as the explicitly prohibited "Gate 7 AND G1".
Its load-bearing defect accepted `BOUNDARY_LIMITED` — and a status that does not exist,
`M1_NOT_REJECTED` — as adequate, making `is_adequate` true for all 240 cases. **Every deviation ran
in the permissive direction.**

Its two checks could not have caught it. The "independent" recomputation imported the analyzer it
was auditing and cloned every rule; the hostile review claimed seven lenses and had six, of which
the denominator lens *asserted every endpoint total equalled 240* — certifying the defect — and the
Gate 7 / Gate 8 lens branched on fields absent from the record schema, so its only condition never
fired.

**Detection.** A forensic rescue, working in strict phase order — reconstruct the frozen authority
first, verify raw integrity second, score independently third, and only then open the post-run
artifacts — established that the raw execution was valid and the analysis was not. Its independent
scoring was cryptographically sealed (`b750d5c0…`) *before* the post-run artifacts were examined,
so the target the repair had to hit was fixed in advance.

**Repair.** The analysis layer was reconstructed to invoke the frozen scorers rather than
reimplement them, cross-checked by a structurally independent recomputation and seven hostile
lenses with mutation-tested teeth, and reproduces the sealed forensic result exactly on all eight
determinate quantities. G1's exact count — open at the end of the rescue — was closed by
search-independent recomputation with verified content identity. No search was rerun; no sealed
evidence was modified.

**What the process got right, and what it did not.** The freeze discipline worked: because the
contract was frozen prospectively and the raw evidence sealed before analysis, the defect was
*detectable and correctable* without rerunning anything, and the correct answer was recoverable
from bytes already on disk. What failed is that a defective analysis reached a reported result at
all, and that its accompanying self-checks were constructed so as to be incapable of failing. The
structural remedy adopted here — reconstruct rather than assert, and prove every check can fail by
mutation — is carried forward as a standing requirement.

## 5. Partition status at closure

| Partition | Status |
|---|---|
| Development (80 cases) | executed, used for development |
| **Held-out (240 cases, 7,200 searches)** | **executed once, sealed, analysed, frozen. All three primary endpoints FAIL.** |
| Challenge (60 cases) | **not opened.** No authorization, no A3.7, no RC5.2, no records, no outcome |
| Confirmation (real data) | **sealed, never opened** |

`AUTHORISED_PARTITIONS` remains `{"development", "held_out"}` throughout and at closure.
