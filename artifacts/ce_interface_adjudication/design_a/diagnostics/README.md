# Design A separation diagnostics (K1, K2, K3)

Evidence convention, as used by the other documents in this study: **VERIFIED** = read in code or data,
or recomputed here; **INFERRED** = reasoned from verified facts, not directly observed.

## What this is, and what it is not

VERIFIED: these numbers are computed from `../population/design_a_compounds.csv` only. They are an
identifiability diagnostic. **No compound is excluded by anything in this directory, and nothing here
may be used to change the population.** The population was frozen by `10_build_population.py` before
this script ran.

## Frozen semantics

VERIFIED, implemented exactly as stated:

- `K1 = float(NCE)`
- `K2 = float(NCE) * theoretical_mh / 500.0` in IEEE-754 binary64, no rounding
- `K3 = math.floor(K2)` as a float (floor toward negative infinity; `K2 > 0` for every cell here)

`theoretical_mh` is the theoretical [M+H]+ of the frozen representative structure, not the deposited
`PRECURSOR_M/Z`.

## CE encoding distance

VERIFIED: the 64-dimension fixed sinusoid of Phase 0 provenance section 6, 32 sin and 32 cos of
`c / 10000^(2i/64)` for `i = 0..31`, implemented from that definition and checked against the
distances the same section quotes: `d(20,12) = 4.38`, `d(20,60) = 5.76`, and the difference-only
reference points 0.5 -> 0.75, 1 -> 1.47, 5 -> 4.12, 40 -> 5.76, 300 -> 6.73. All reproduce to two
decimal places; the check is an assertion inside the script, so the numbers below cannot be produced
if it fails. VERIFIED consequence of that same section: the encoding has no normalisation, clipping or
bucketing, so this distance is the whole of what the three candidate inputs look like to the frozen
checkpoints at the input layer.

## Leverage

VERIFIED, from `k_separation_summary.json`:

- Pooled over the 66 (compound, cell) pairs, `|K1 - K2|` has median 16.74, q05 4.21, q95 43.82, range 1.36 to 48.00.
- In the encoding the models actually see, `d(K1, K2)` has median 4.94, q05 4.05, q95 5.76, against the difference-only reference points quoted above (a difference of 1 gives 1.47, of 5 gives 4.12, of 40 gives 5.76) and a random-phase expectation of 8.0.
- `d(K2, K3)` has median 0.70 and max 1.45: K2 and K3 differ only by the fractional part of K2, so the K2-against-K3 contrast is the weakest of the three by construction, bounded above by d(1, 0) = 1.47.
- `d(K1, K3)` has median 4.94, q05 4.04, q95 5.78.
- Compounds in the 450 to 550 null region, where K1 and K2 are intrinsically hard to separate: 1 of 33. Within 5 percent of m/z 500: 1. Within 20 percent: 7.
- Cells with `|K1 - K2|` below 1: 0 of 66; below 2: 1; below 5: 5.
- The NCE 60 cell carries more separation than the NCE 30 cell throughout, because `K1 - K2 = NCE x (1 - mh/500)` scales linearly in NCE: median `|K1 - K2|` is 11.85 at NCE 30 against 23.69 at NCE 60.


## The interpretation a null result requires

INFERRED, and a preregistration author must state it before the study runs: a null or unresolved
adjudication outcome on this population is **not** evidence that the three interfaces are the same.
Separation on the energy axis is bounded by the mass composition of the 33 compounds, and this
population was drawn from the one public source that satisfies the identity exclusions, not designed
for energy-axis leverage. Where `|K1 - K2|` is small, or where the encoding distance between two
candidates is small relative to what the models resolve, a null outcome is what lack of leverage
predicts, and it is indistinguishable at this size from a genuine absence of an interface difference.
The high-mass and null-mass strata of the Design B acquisition exist precisely to remove that
ambiguity.

## Files

| File | Contents |
| --- | --- |
| `k_separation_per_compound.csv` | one row per (compound, NCE cell): K1, K2, K3, absolute separations, encoding distances, mass-window flags |
| `k_separation_summary.json` | full distributions per cell and pooled, mass-window counts, threshold counts, embedding-distance distributions, the embedding self-check, and a sha256 manifest |
| `README.md` | this file |
