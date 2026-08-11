# BACKLOG.md

Issues recorded during Phase 1 under the master plan's bug policy (section
29.5). BLOCKERs are fixed before Phase 1 closes and therefore do not appear
here. IMPORTANT items are documented with reproduction and scientific impact.
MINOR items are recorded and carried.

## BLOCKERs — all resolved, none open

| # | Issue | Resolution |
|---|---|---|
| B1 | `mu = SY + (1-SY)*phi` fails on 10,588 rows at up to 5.9e-6 | Not an implementation defect. The identity as stated in the master plan is false in general; the exact form carries a `mz_observed/mz_declared` factor and holds to 4.4e-16. mu is computed from its definition, never reconstructed. See deviation D1. Both magnitudes are pinned by tests. |

No other BLOCKER-class condition was observed: zero parse failures, zero hash
mismatches, zero energy misassignments, zero grouping collisions, zero silent
missing-value coercions across 5,582 records.

---

## IMPORTANT — open

### I1. Four mix-505 mzML files not acquired (MassIVE rate limiting)

**Reproduction.** `GET https://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?forceDownload=true&file=f.MSV000091754/peak/20200303_ENTACT_RP_mzML/mix505/20200303_ENTACT_RP_mix505_pos_CE30.mzML`
returns HTTP 429 persistently. Two acquisition strategies were attempted: a
Python client with exponential backoff (30/60/90/120/150 s, five retries) and a
shell client with eight attempts at 300 s intervals. Mix 499 (6/6), mix 503
(6/6) and mix 505 CE 15 were acquired; mix 505 CE 30, 45, 60 and 75 were not.
13 of a possible 17 files, 1.18 GB.

**Scientific impact.** Repeatability rests on a triplicate at NCE 15 and a
duplicate (mixes 499, 503) at NCE 30-90. The pooled inter-mixture SD for mu is
0.0295. At NCE 15, where both structures are available, the duplicate estimate
was 0.0245 and the triplicate 0.0281 — a 15% increase, in the conservative
direction. Extrapolating that ratio, a full triplicate would raise the pooled SD
to roughly 0.034 and lower mu's K3 ratio from 15.2x to about 13x, which does not
approach the 3x trigger. **The K3 verdict is insensitive to this gap.**

**Two-attempt rule applied.** External host throttling, not a defect in this
code. Documented and carried rather than expanded into a new phase.

**Action for Phase 2.** Re-attempt acquisition at a different time of day, or
request the files via MassIVE's FTP/aspera path. Refresh `REPEATABILITY.md`
if obtained.

### I2. Negative-mode repeatability is UNKNOWN

**Cause.** Deliberate scope decision (deviation D5): positive mode is the
primary experiment and K3 needs one endpoint to clear one gate; acquiring both
modes would have roughly doubled a download that was already rate-limited.

**Scientific impact.** Any negative-mode claim that requires a noise floor —
including H-MAIN's "residual within measurement repeatability" clause applied to
the negative-mode replication — is not currently supportable. Positive-mode
noise must not be assumed to transfer: ESI polarity changes precursor ion,
charge localization and fragmentation chemistry.

**Action for Phase 2.** Acquire `20200303_ENTACT_RP_mix{499,503,505}_neg_CE*.mzML`
(all 18 exist) before making any negative-mode noise-referenced claim.

### I3. mu's residual mass association

**Observation.** Spearman rho(mu, precursor m/z) runs -0.10 at NCE 15 to -0.68
at NCE 90, after mu has already been normalized by precursor m/z.

**Scientific impact.** This is risk R4 and it fires before any model exists. A
fitted "structure law" on mu could be substantially a mass law. Kill criterion
K5 is live.

**Action for Phase 2.** Baseline B2 (per-energy mean + linear precursor m/z) is
the primary competitor, not a formality. F8 descriptor ablation must report what
happens when precursor mass is removed.

---

## MINOR — recorded, no action

| # | Issue | Note |
|---|---|---|
| M1 | Master plan's "zero duplicate InChIKeys in the curated layer" is false at full corpus | 6 of 967 compound-by-mode keys map to two internal IDs. Too few for repeatability; conclusion unaffected. Deviation D3. |
| M2 | Master plan's "E_com spread under 13%" does not survive the full corpus mass range | The qualitative claim it supports is unaffected. Deviation D2. |
| M3 | `file(1)` reports Li_2021 PDF as 23 pages, `pypdf` counts 19 | Object-count vs page-tree difference. Document parses and yields text normally. No corruption. |
| M4 | The 0.1% relative-intensity cutoff cell is inert on the curated branch | RMassBank's formula filter already removed everything below it. The grid axis is only meaningful on the raw branch. Recorded so it is not mistaken for a null result. |
| M5 | Publication says "nominal collision energy (NCE)"; "normalized collision" appears zero times | The Thermo conversion assumes *normalized*. Immaterial to Phase 1, which uses NCE as the axis. Matters for cross-instrument work. See `CE_AUDIT.md`. |
| M6 | Environment uses `venv` + pinned requirements and Python 3.13, not `uv` + 3.12 | `uv` not installed; installing it is outside the Phase 1 mandate. Deviation D4. |
| M7 | Master plan cites the Thermo NCE formula to sources absent from the reference pack | Recorded as SUPPORTED, not VERIFIED. Every derived E_lab/E_com is labelled conditional. |

---

## Explicitly not done (Phase 2+ scope)

Splits of any kind, descriptors beyond identity checking, any model, any
symbolic search, negative-mode analysis beyond census, neutral losses,
ClassyFire classes, the falsification ladder beyond Phase-1-relevant checks.
None of these was built, and no dependency supporting them was installed.
