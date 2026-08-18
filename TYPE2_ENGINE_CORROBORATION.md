# TYPE2_ENGINE_CORROBORATION.md

**The frozen independent-engine corroboration standard, and the development
diagnosis behind it.**

Master plan §13.3: "If two engines with different search dynamics converge on
equivalent expressions, that is evidence. If they do not, the expression is a
search artifact."

---

## 1. What Phase 3 found

| Block | Worlds | Engines agree | Support match | PySR matches planted | gplearn matches planted |
|---|---|---|---|---|---|
| `G1` | 30 | 3% | 3% | 3% | 0% |
| `G3` | 8 | 0% | 0% | 62% | 0% |
| `G4` | 30 | 60% | 63% | — | — |

Phase 3 reported this as measured and drew the conservative reading: PySR's
selected expressions were not independently corroborated.

## 2. Development diagnosis

`PHASE3_PREREGISTRATION.md` §11 of this study's terms asks which of four causes
was operating: weak gplearn configuration, an inappropriate agreement criterion,
true functional non-identifiability, or a genuinely engine-specific effect.

Re-adjudicating the stored Phase 3 gplearn fronts under the Type 2 signature —
**development evidence, counting toward nothing** — gives the answer:

| Block | Worlds | Block-level support agrees | Mass-block exponent within ±0.15 | Signs agree |
|---|---|---|---|---|
| `G1` | 30 | **18/30 (60%)** | **22/30 (73%)** | 26/30 (87%) |
| `G3` | 8 | **8/8 (100%)** | 4/8 (50%) | 8/8 (100%) |

The dominant cause was **an inappropriate agreement criterion combined with true
non-identifiability inside the mass block**. gplearn repeatedly selected
`sqrt(heteroatom_fraction · total_atom_count)` where PySR selected
`sqrt(precursor_mz · (heteroatom_fraction + c))`. Those are different strings and
different variables; they are the same structural claim, on a corpus that cannot
distinguish `precursor_mz` from `total_atom_count`.

The remaining disagreement is real and is not explained away. In `G3` gplearn
consistently returns `sqrt(mass)`, exponent 0.5, where the planted exponent is
0.6 and PySR recovers 0.57–0.69: gplearn's grammar reaches a half-integer power
cheaply and a general one not at all, so it rounds the exponent. That is a
genuine engine-specific effect and it is why the exponent criterion is a real
test rather than a formality.

## 3. The frozen standard

Corroboration is judged on what a Type 2 claim is made of, **not** on expression
strings.

**Gate.** On the fresh **G1B moderate-regime** worlds — the block where a real
molecule-conditional relationship exists and where corroboration therefore has
content — the comparison arm must reproduce PySR's reported family on:

1. **block-level effective support**, in **≥ 50%** of worlds, and
2. the **mass-block scaling exponent within ±0.15**, in **≥ 50%** of worlds.

Both must hold. Failure means the corroboration condition of the authorization
rule is not met, and `TYPE2_VALIDATION_DECISION.md` cannot read
`AUTHORIZE RE-SCOPED PHASE 4`.

**Also measured and reported, never used as the gate:** variable-level support
agreement, sign agreement on shared blocks, full Type 2 family membership, and
exact functional equivalence of the two expressions — the last so the comparison
with Phase 3's 3% stays available.

## 4. Why ±0.15 and 50%

±0.15 is the master plan's §18.3 tolerance, already in force for exponent
recovery everywhere else in this study. 50% is a simple majority of worlds: an
engine that reproduces the structural claim in fewer than half of the worlds
where the claim is true is not corroborating it. Neither number is chosen from
the development table — 60% and 73% sit above the bar, but on Phase 3's fixed
constants, and the fresh worlds redraw every constant and rotate the non-mass
carrier across three descriptors.

## 5. Scope

`gplearn 0.4.3` at its Phase 3 configuration, on **88 worlds × 10 seeds = 880
runs**: the whole of `G1B`, `G1C` and `G3`, plus the first 30 `G4` nulls. Full
duplication of 9,690 PySR runs would multiply compute without additional
scientific value; the master plan makes the second engine a comparison arm on
T2, not a second full engine.

The configuration is **unchanged from Phase 3**. Development considered whether
to strengthen it and declined: changing the arm's configuration and then judging
corroboration by it would make the standard depend on a tuning choice made after
seeing that the arm disagreed.

## 6. What corroboration cannot do

gplearn cannot rescue a failing PySR calibration, exactly as in Phase 3. If PySR
fails a gate and gplearn passes it, the project is not switched: that would
require an explicit documented deviation and an independent recalibration.
Disagreement is reported honestly in either direction, and an engine that cannot
reproduce even support or scaling is recorded as **evidence against** a strong
Type 2 claim.
