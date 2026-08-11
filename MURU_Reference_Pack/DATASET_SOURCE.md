# Initial Dataset Candidate

## Primary candidate

MassIVE accession: `MSV000091754`

Associated publication:

Anjana Elapavalore et al. Adding open spectral data to MassBank and PubChem using open source tools to support non-targeted exposomics of mixtures. Environmental Science: Processes & Impacts, 2023. DOI: `10.1039/D3EM00181D`.

## Why this dataset is attractive for MURU v1

The publication reports MS/MS fragmentation at six nominal collision energy settings:

* 15 NCE
* 30 NCE
* 45 NCE
* 60 NCE
* 75 NCE
* 90 NCE

The collision energies were acquired in separate runs for each mixture and ionization mode.

The repository contains raw files, mzML files, compound lists, settings, and workflow outputs according to the paper.

This creates a much cleaner starting design than indiscriminately combining spectra from unrelated MassBank contributors and instruments.

## Important scientific caveat

The ENTACT samples are chemical mixtures, not isolated single compound injections. The paper discusses isomer and isobar ambiguity and reports tightened quality control procedures in later record generation. MURU must therefore use the curated records or apply equivalent identity safeguards rather than assuming every raw precursor feature maps uniquely to one compound.

## Phase 1 verification checklist

Before building the main ingestion pipeline, verify:

1. The accession is reachable and the files are downloadable.
2. The exact file naming convention allows mapping file to mixture, ion mode, and NCE.
3. Compound identity can be mapped reproducibly across collision energies.
4. Positive and negative modes are kept separate unless a later analysis explicitly justifies combining them.
5. Instrument configuration is sufficiently consistent for the intended comparison.
6. The selected records have enough repeated NCE measurements per molecule for the proposed analyses.
7. Any ambiguous isomer or isobar records are excluded or explicitly labeled.
8. The data version or retrieval date is recorded for reproducibility.

## Do not do this

Do not start by downloading all of MassBank and then attempt to harmonize every collision energy representation across every instrument.

First prove the MURU pipeline on one internally coherent multi energy dataset.
