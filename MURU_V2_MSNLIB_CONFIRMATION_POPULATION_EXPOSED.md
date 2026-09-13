# MURU-WUR-v2 MSnLib Confirmation: Validation Population EXPOSED (incident record)

**Status: the frozen 2,000-scaffold-group / 2,690-compound MSnLib validation
sample (seed 20261010, drawn 2026-09-13) is PERMANENTLY EXPOSED and may never
be used for an independent confirmatory claim.** This is not a reversible
data-quality issue; it is a leakage event, and per this program's own
established precedent (`MURU_WUR_STAGE3_RESULT.md` / the exposure registry's
WUR-SEALED entry: "one look... can never again support an independent
external claim"), exposure is permanent regardless of scale or intent.

## What happened

`scripts/wur_v2_confirmation/10_parser_preflight.py`, written and run during
this session to re-test the mzML/Numpress parser on already-exposed anchor
data (protocol §6, "re-test the complete parser... using anchor files
only"), had a real scoping bug: it selected the first six rung-tagged scans
**by position** in each of the 561 designated "anchor" files, instead of
restricting to the specific anchor compound's own selected-ion m/z via
`match_compounds` (the function every other script in this pipeline
correctly uses for exactly this purpose).

MSnLib wells are pooled — one physical injection holds 8–10 unrelated
compounds — and 146 of the 561 designated "anchor" files are wells also
shared with sampled validation-population compounds. The positional
selection therefore decoded real MS2 peak arrays for validation-population
spectra, before any formal one-look guard existed and before this document
or its freeze were ever committed.

**Scope, reconstructed from header data only** (no further peak decode was
performed to determine this):

| | |
|---|---|
| Files processed by the buggy preflight | 561 |
| Total (file, spectrum_id) pairs decoded | 3,366 |
| Pairs matching a validation-population compound (≤ 0.01 Da) | **964 (28.6%)** |
| Affected files | 367 of 561 (65.4%) |
| Affected validation-population compounds | **350 of 2,140 eligible (16.4%)** |
| Affected scaffold groups | **314 of 1,658 eligible (18.9%)** |

Full lists: `artifacts/wur_v2_confirmation/QUARANTINE_leakage_incident_2026-09-13/incident_record.json`
and `affected_spectra_full_list.csv`.

**Values actually surfaced to the operator** (printed to a terminal and seen
by the person/agent running this study, not merely decoded in memory): three
spectra's computed μ, one of which is confirmed to match validation compound
**`MURAVORBGFDSMA`** (selected-ion m/z 613.177856 vs. theoretical [M+H]+
613.177915, Δ = 0.00006 Da; **μ = 0.4535200362523742**). This is the fact
that makes the incident real and operator-facing, not merely a latent file on
disk — it is the reason the whole 2,690-compound sample is treated as burned
rather than only the 350 compounds whose spectra were mechanically decoded.

**Root cause:** `10_parser_preflight.py`'s `TestGuard` set `authorized=True`
unconditionally with no population scope, and the file-selection loop pulled
`rung_scans.spectrum_id.tolist()[:6]` directly from `fixed_rung_scans()`
output with no call to `match_compounds()`.

**Detected by:** an independent leakage-review subagent, part of a
four-reviewer pre-access review dispatched before this freeze was committed
(leakage, statistics, implementation, governance). Confirmed by the operator
against their own earlier tool output in the same session.

## What was NOT affected

The sampling call, the eligible-population/scaffold-group/spectrum-manifest
construction, and every other script in this pipeline were independently
rebuilt from raw inputs by the same reviewer and reproduce exactly —
zero contamination in the population-construction path itself. This is
isolated to the ad hoc parser-preflight test script.

## Disposition (per explicit operator instruction, 2026-09-13)

1. The tainted `parser_preflight.json` was moved, not deleted, to
   `artifacts/wur_v2_confirmation/QUARANTINE_leakage_incident_2026-09-13/parser_preflight_TAINTED.json`
   (sha256 `8f22d4ad134621f3c5fc9e6b1f28db599465279b55ed41e96bc0c4c1b942040b`).
   The exact buggy script, as run, is preserved at
   `.../10_parser_preflight_BUGGY_AS_RUN.py` (sha256
   `90b7d2e5e59ad6b6c133236cc24797d7fd1c2a65de551f8df9b923d91aec0cb1`).
2. `10_parser_preflight.py` is fixed (scoped through `match_compounds`) and a
   regression test (`tests/wur_v2/test_v2_parser_preflight_scope.py`) proves
   a co-plated non-anchor spectrum can never be selected, regardless of
   position, for this or any future study reusing this parser.
3. This validation population is **not scored, not summarized further, and
   not used for any confirmatory claim.** `MURU_V2_MSNLIB_CONFIRMATION_FREEZE.md`
   is marked VOID (see its own banner) rather than deleted.
4. **STOP.** No replacement sample has been drawn. A new, independent
   validation design is out of scope for this session and will be defined
   separately.

## What remains usable

- The candidate, comparator, A0 map, endpoint, and all frozen protocol rules
  are entirely unaffected — nothing about the model or its deployment
  changed.
- The transport/authentication work (all nine Zenodo archives verified;
  MassIVE re-fetch route confirmed working) is reusable infrastructure for
  any future MSnLib validation attempt, independent of which specific
  compounds get sampled.
- The hardened `ConfirmationAccessGuard` and the parser-preflight fix are
  reusable, general-purpose safeguards, not specific to this burned sample.
