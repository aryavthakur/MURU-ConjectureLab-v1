# CE_AUDIT.md

Generated 2026-08-11 23:20 UTC.

## What the record actually says

```
AC$MASS_SPECTROMETRY: COLLISION_ENERGY 15
```

A bare integer. No unit. No convention marker. The record title reads `CE: 15`, which is equally unitless. **Nothing inside any record in this corpus identifies the number as normalized collision energy.**

| Check | Result |
|---|---|
| Records with a parseable energy | 5,582 / 5,582 |
| Records declaring a unit | **0** |
| Distinct parse statuses | {'NO_UNIT_IN_RECORD': np.int64(5582)} |
| Distinct energy values | [15, 30, 45, 60, 75, 90] |
| Records outside {15,30,45,60,75,90} | **0** (0.000%) |

| NCE | Positive | Negative | Total |
|---|---|---|---|
| 15 | 574 | 372 | 946 |
| 30 | 566 | 374 | 940 |
| 45 | 569 | 370 | 939 |
| 60 | 564 | 365 | 929 |
| 75 | 574 | 352 | 926 |
| 90 | 564 | 338 | 902 |

## Provenance chain for `energy_type`

```
record field   AC$MASS_SPECTROMETRY: COLLISION_ENERGY = "15"
               |  no unit, no convention marker
               v
publication    Elapavalore et al. 2023, methods:
               "fragmented at 6 different nominal collision energy
                (NCE) levels (15, 30, 45, 60, 75, and 90 NCE)
                in separate runs"          <- VERIFIED from the PDF
               |
               v
MURU stores    raw_value    = "15"
               numeric_value= 15.0
               unit         = null
               energy_type  = NCE_ASSUMED_FROM_PUBLICATION
               provenance   = Elapavalore 2023 methods
```

All 5,582 records carry `energy_type = NCE_ASSUMED_FROM_PUBLICATION`. MURU refuses to merge these with any record whose `energy_type` differs.

## An ambiguity the master plan does not record

The publication expands NCE as **"nominal collision energy"**. The string "normalized collision" does not occur anywhere in the paper (0 hits across 67,872 extracted characters). The Thermo conversion in master plan section 6.2 is the **normalized** collision energy formula.

On Thermo Q Exactive instruments the user-facing parameter *is* the normalized collision energy, and 'nominal' is near-universally used loosely for it, so the intended meaning is almost certainly normalized CE. But the primary source does not say so, and this audit will not assert what the source does not.

**Status: SUPPORTED, not VERIFIED.** Consequence: E_lab and E_com below are derived and conditional. No Phase 1 conclusion depends on them; NCE is used as the energy axis throughout.

## Charge state

- Distinct precursor types: {'[M+H]+': np.int64(3411), '[M-H]-': np.int64(2171)}
- Distinct inferred charges: [1]
- Records with undetermined charge: **0**

**Assumption A5 VERIFIED.** Every precursor is singly charged, so the Thermo charge factor f(z) is identically 1 across the corpus. The one place the cited formula could have introduced an error is therefore inert here.

## Derived energies

```
E_lab(eV) = NCE * (m/z_precursor / 500) * f(z),  f(1) = 1
E_com(eV) = E_lab * 28 / (28 + M_ion)
          = 0.056 * NCE * M_ion / (M_ion + 28)   for z = 1
```

Formula status: **SUPPORTED (cited, not independently verified)**. The master plan attributes it to Revesz et al. 2023 (Mass Spectrom Rev) and Thermo PSB 104. Neither source is in the reference pack and neither was retrieved during this implementation, so per the instruction not to treat the planning document as an authority for instrument physics, the chain stops at 'cited'. The center-of-mass transform itself is standard two-body kinematics and is independent of Thermo.

| NCE | E_lab min | E_lab median | E_lab max | E_com min | E_com median | E_com max | E_com spread |
|---|---|---|---|---|---|---|---|
| 15 | 3.45 | 8.60 | 25.13 | 0.676 | 0.765 | 0.813 | 16.9% |
| 30 | 6.90 | 17.10 | 50.25 | 1.351 | 1.530 | 1.626 | 16.9% |
| 45 | 10.35 | 25.93 | 75.38 | 2.027 | 2.297 | 2.438 | 16.9% |
| 60 | 13.92 | 34.58 | 100.50 | 2.707 | 3.062 | 3.251 | 16.7% |
| 75 | 17.40 | 43.07 | 125.63 | 3.383 | 3.827 | 4.064 | 16.7% |
| 90 | 20.88 | 52.04 | 150.76 | 4.060 | 4.595 | 4.877 | 16.7% |

The master plan (section 6.2) predicts E_com spread under 13% across the mass range at fixed NCE, computed on a 151-526 m/z sample. At full corpus the mass range is wider (115.0-837.5 m/z) and the spread is correspondingly larger. The qualitative claim -- that CoM energy is far less mass-dependent than E_lab -- holds; the specific 13% figure does not survive the wider mass range. Recorded as a **partial contradiction** of section 6.2.

## Kill criterion K2

*Trigger:* more than 5% of records carry energy values that cannot be assigned a convention, or evidence that the six settings were not applied as documented.

- Records outside the expected set: **0 (0.000%)** vs a 5% trigger
- Records with unparseable energy: **0**
- Records with absent energy: **0**
- Slot-implied energy disagreeing with the field: **0**
- Six-setting design corroborated by the publication: **yes**

### K2: **DOES NOT FIRE**

Every record carries an unambiguous integer from the documented set, cross-validated against an independent encoding (the accession slot) with zero disagreement. The residual ambiguity is not *which* number, but *what unit the number is in* -- and that is documented, provenance-tracked, and confined to the derived E_lab/E_com columns that no Phase 1 conclusion uses.
