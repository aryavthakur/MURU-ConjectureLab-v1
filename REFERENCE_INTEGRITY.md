# REFERENCE_INTEGRITY.md

Generated 2026-08-11 23:05 UTC by `scripts/t1_00_reference_integrity.py`. No file in the reference pack was modified, repaired, or moved.

## Verdict on the reported defect

The planning analysis reported that several files named `.pdf` appeared not to be genuine PDF byte streams, and that their hashes did not match the provided manifest. Both halves of that claim were tested independently.

- **File type:** 3 of 3 files named `.pdf` carry a valid `%PDF-` header and parse as PDF documents. **0 are not genuine PDFs.**
- **Hashes:** 3 of 3 manifest-listed files match `SHA256SUMS.txt` exactly. **0 mismatch.**

**FAILED TO REPRODUCE.** Neither half of the reported defect is present in the files on disk. Every `.pdf` is a genuine PDF byte stream and every manifest hash matches. The reference pack is internally consistent.

Status of the reported defect: **FAILED** (tested and unsupported), using this project's epistemic vocabulary. If the defect was real at some earlier point, the files were replaced before this session began; nothing in the repository records such a replacement.

## Per-file audit

| File | Declared | Detected | Ext matches | SHA-256 (actual) | Manifest SHA-256 | Status | Readable |
|---|---|---|---|---|---|---|---|
| `DATASET_SOURCE.md` | md | Markdown | yes | `fb8dbb91e256d50b...` | `_not listed_` | **NOT_IN_MANIFEST** | yes |
| `README.md` | md | Markdown | yes | `10ebcc179eef008b...` | `_not listed_` | **NOT_IN_MANIFEST** | yes |
| `SHA256SUMS.txt` | txt | text/utf-8 | yes | `db10186064fee12f...` | `_not listed_` | **NOT_IN_MANIFEST** | yes |
| `SOURCES.md` | md | Markdown | yes | `76cd527d8909e919...` | `_not listed_` | **NOT_IN_MANIFEST** | yes |
| `references/Elapavalore_2023_MassBank_Multi_CE.pdf` | pdf | PDF | yes | `d5974ee5a0a242c3...` | `d5974ee5a0a242c3...` | MATCH | yes |
| `references/Li_2021_Spectral_Entropy.pdf` | pdf | PDF | yes | `59577e1d00676f43...` | `59577e1d00676f43...` | MATCH | yes |
| `references/MassBank_Parser_Field_Guide.md` | md | Markdown | yes | `e1d43f3063a1001c...` | `_not listed_` | **NOT_IN_MANIFEST** | yes |
| `references/Neumann_2025_MassBank_FAIR.pdf` | pdf | PDF | yes | `873f0a4a1c0c34aa...` | `873f0a4a1c0c34aa...` | MATCH | yes |

## PDF structural detail

| File | Header | Version | %%EOF | Pages | Extracted text (chars) |
|---|---|---|---|---|---|
| `references/Elapavalore_2023_MassBank_Multi_CE.pdf` | %PDF- | 1.6 | present | 14 | 67,859 |
| `references/Li_2021_Spectral_Entropy.pdf` | %PDF- | 1.4 | present | 19 | 53,292 |
| `references/Neumann_2025_MassBank_FAIR.pdf` | %PDF- | 1.4 | present | 6 | 34,579 |

## Scientific interpretation vs provenance

| Question | Answer |
|---|---|
| Does any discrepancy affect scientific interpretation? | **No.** All content is readable and traceable. |
| Does any discrepancy affect provenance? | **No.** Every hash matches its manifest entry. |
| Was any file repaired? | **No.** This audit is read-only. |

## Content traceability

Beyond byte integrity, the two claims MURU actually depends on were traced back into the reference text itself:

- **Spectral entropy definition** (Li et al. 2021): the text states the minimum is "zero for a single fragment ion", that uniform intensities give "ln (number of ions)", and that normalized entropy divides by "ln (number of ions)". This pins the logarithm base and is asserted in `tests/test_features.py`. **VERIFIED from the primary source.**
- **Collision-energy design** (Elapavalore et al. 2023): the text states spectra were "fragmented at 6 different nominal collision energy (NCE) levels (15, 30, 45, 60, 75, and 90 NCE) in separate runs". **VERIFIED from the primary source.**
- **Replicate mix design** (Elapavalore et al. 2023): "mix 5 included the replicate set of mix 1" and "Mix 7 comprised 270 substances plus the replicate set from mix 1", with Table 1 mapping mix 1/5/7 to 499/503/505. **VERIFIED from the primary source.**
- **Thermo NCE-to-eV conversion**: the master plan cites Revesz et al. 2023 and Thermo PSB 104. Neither is in the reference pack and neither was retrieved. The formula is therefore **SUPPORTED (cited, not independently verified)** and every derived E_lab / E_com in this project is labelled conditional. See `CE_AUDIT.md`.

## Non-blocking observation

`file(1)` reports `Li_2021_Spectral_Entropy.pdf` as "23 pages" while `pypdf` counts 19. This is a difference between counting `/Page` objects in the raw byte stream and walking the resolved page tree, not evidence of corruption: the document parses, paginates and yields text normally. Recorded as MINOR; no action.
