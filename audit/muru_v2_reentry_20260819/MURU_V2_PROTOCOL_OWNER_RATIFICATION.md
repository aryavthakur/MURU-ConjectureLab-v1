# MURU v2 — PROTOCOL-OWNER RATIFICATION RECORD

**Status: RATIFIED by the protocol owner.**
**Nature: a governance act. It creates no scientific evidence and alters none.**

This record implements decisions D1–D6 and D2-extended, issued by the protocol
owner as the disposition of the sealed Gate 1 failure. Every decision below is
the owner's, not the analyst's. This document records them; it does not derive
them.

| | |
|---|---|
| Upstream sealed commit | `0c75c0e` |
| Upstream terminal state | `A. GATE_1_FAIL_DEFINITIVELY_SEALED_AND_FORWARD_PATH_RESOLVED` |
| Ratification branch | `claude/muru-v2-autonomous-reentry` |
| Sealed evidence altered | **NONE** — verified by hash after writing (see §8) |

---

## 1. What is being ratified — and what is not

The sealed Gate 1 adjudication is a **closed upstream result**. It is not
reopened, re-litigated, or recomputed here. Verified at ratification time from the
repository:

```
E2B_IDENTITY = PASS          GATE_1 = FAIL         GATE_1_DEFINITIVE = YES
CRITIC_A = PASS              CRITIC_B = PASS       UNRESOLVED_DEFECTS = 0
SUCCESS 4 · LOST_IN_CROSS_SEED 71 · LOST_IN_RETENTION 55 · NEVER_ON_FRONT 14  (144)
DIRECT_RETENTION 55 vs 69 → dev 14 ; DIRECT_GENERATION 14 vs 57 → dev 43
frozen materiality threshold: more than 10 cases (strict >)
all 18 sealed artifact hashes verify against ARTIFACT_SHA256.txt
```

## 2. D1 — Republished attribution — **RATIFIED**

The corrected explanatory attribution for the historical v1 Held-out G2 failures is:

| Class | Count | Share |
|---|---:|---:|
| `LOST_IN_CROSS_SEED` | 71 | 49.31% |
| `LOST_IN_RETENTION` | 55 | 38.19% |
| `NEVER_ON_FRONT` | 14 | 9.72% |
| `SUCCESS` | 4 | 2.78% |

This supersedes the prior stage attribution **for explanatory purposes only**.

Explicit limits, ratified as stated:
- It does **not** change the original v1 endpoint result.
- It does **not** by itself license any E4 arm.
- It does **not** convert E2b into decision-admissible evidence.

## 3. D2 — Operative 69/57 class mapping — **RATIFIED**

```
retention-class  = LOST_IN_RETENTION
generation-class = NEVER_ON_FRONT
```

is the operative interpretation of the 69/57 falsification hook, settled for
governance purposes. The previously disclosed mapping sensitivity remains on the
record in `GATE_1_DEFINITIVE.json`
(`MAPPING_SENSITIVITY_DISCLOSED`, `EXHAUSTIVE_MAPPING_SPACE`), including the
finding that every mapping using E2b's front-level information FAILs and that the
PASS-producing alternatives measure replay↔seal fidelity rather than attribution
correctness. **Gate 1 is not reopened on alternative mappings.**

## 4. D2-extended — Post-republication posture — **RATIFIED**

Gate 1 failure is **not** permanent termination of the MURU programme. It is
**continuation-eligible only after the contradiction is prospectively resolved.**

- All E4 arms (E4a–E4f) remain **suspended**.
- The programme may continue only after a valid new **decision-admissible**
  calibration qualification.
- **There is no automatic E4 re-entry.**

## 5. D3 — Definition of "resolved" — **RATIFIED**

**PUBLICATION_RESOLUTION** — achieved when all four hold:

| # | Requirement | Status at this commit |
|---|---|---|
| 1 | D1 formally recorded | **MET** — §2 of this document |
| 2 | D2 formally recorded | **MET** — §3 of this document |
| 3 | Corrected attribution published in the repository | **MET** — `ATTRIBUTION_REVISION.md`/`.json`, sealed at `0c75c0e` |
| 4 | E2a/E2b divergence explicitly preserved in the record | **MET** — `GATE_1_DEFINITIVE.json` → `E2A_E2B_DIVERGENCE_REPORT` |

→ **PUBLICATION_RESOLUTION = ACHIEVED at this commit.**

**EXPERIMENTAL_REENTRY_RESOLUTION** — requires all eight:

| # | Requirement | Status |
|---|---|---|
| 1 | Prospectively frozen decision-admissible calibration/re-entry protocol | PENDING |
| 2 | Full required schema | PENDING |
| 3 | Predeclared qualification/acceptance rule | PENDING |
| 4 | Predeclared routing rule | PENDING |
| 5 | Predeclared failure rule | PENDING |
| 6 | Independent adjudication procedure | PENDING |
| 7 | Results-blind freeze before new outcomes are inspected | PENDING |
| 8 | Successful execution of that qualification protocol | PENDING |

E2b may serve as **explanatory or falsification evidence only**. It may **not**
positively license re-entry or select an E4 arm.

## 6. D4 — E5 — **RATIFIED: DEFERRED**

E5 is deferred. It is **not** executed merely because it is not literally an E4
arm. It is reconsidered automatically if and only if the newly qualified causal
path makes it scientifically relevant **and** its dependencies are prospectively
satisfied.

## 7. D5 — E2a calibration status — **RATIFIED**

The existing E2a corpus is **INVALIDATED AS A HELD-OUT-FACING CALIBRATION
SURFACE**.

- Its measurements remain valid as **synthetic-domain diagnostic evidence**.
- Its historical Gate 2 result, including `LOCKED_EXECUTE_E4A`
  (`results/e2/run_x86_e2a_v1/X86_E2A_SEAL.json`), **no longer has
  forward-licensing force**.
- This is a limitation on **role**, not deletion or repudiation of data.

Consequence carried forward: the sealed counts `A=122 B=196 C=102 D=0 E=119`
remain in the record as diagnostics, and the plurality of `B` may **not** be cited
to license E4a.

## 8. D6 — Corpus schema disposition — **RATIFIED**

- Existing corpora may continue to support analyses **already validly sealed from
  the fields actually present**.
- **No** retroactive fabrication of missing provenance fields.
- **No** silent waiver of prospective schema requirements.
- The existing E2b corpus is **not** promoted into a generic decision-licensing E4
  rescoring corpus.
- Any new decision-relevant corpus must satisfy the prospectively frozen required
  schema **from inception**.
- Where an existing decision-admissible corpus lacks fields a newly authorized
  analysis needs, **regenerate prospectively** under a new frozen protocol rather
  than imputing.

This is why the E2b front corpus — which lacks `admissibility` and 15 other
mandated §2.4 fields — cannot be reused as the new calibration surface, and why
the replacement surface must be generated fresh.

## 9. Verification that this ratification altered no sealed evidence

Performed after writing this document and recorded in
`RATIFICATION_VERIFICATION.json`:

- all 18 sealed artifact hashes re-verified against `ARTIFACT_SHA256.txt`;
- `git status` on `results/` empty (no sealed Mac evidence touched);
- frozen evaluator SHA-256 still `ee285a8b…9743`;
- all 10 `muru-authority/*` tags present locally and on the remote.

## 10. What this ratification authorizes next

`PUBLICATION_RESOLUTION` is achieved; `EXPERIMENTAL_REENTRY_RESOLUTION` is not.
The next authorized action is therefore to construct, results-blind, the
prospectively frozen decision-admissible calibration/re-entry protocol required by
D3 items 1–7 — via a design council, hostile review, and hash-freeze **before any
new scientific compute**.

Documents created under that authority are **prospective post-Gate-1
protocol-owner amendments**. They are **not** historically preregistered and must
never be described as such.
