# MURU ConjectureLab Reference Pack

This folder is intentionally small. It contains the sources that should govern the scientific and data engineering decisions for MURU v1.

## Read first

1. `references/Elapavalore_2023_MassBank_Multi_CE.pdf`
   Purpose: primary experimental reference for the first MURU dataset. The study generated MS/MS data at six nominal collision energy settings, 15, 30, 45, 60, 75, and 90 NCE, in separate runs. It also identifies the deposited raw and mzML dataset as MassIVE accession MSV000091754.

2. `references/Neumann_2025_MassBank_FAIR.pdf`
   Purpose: current authoritative overview of MassBank, its data governance, versioned releases, record validation, metadata model, and rationale for repeated measurements at different collision energies.

3. `references/Li_2021_Spectral_Entropy.pdf`
   Purpose: methodological reference for spectral entropy and entropy based MS/MS similarity. Treat spectral entropy as a candidate quantitative feature, not as a required endpoint.

4. `references/MassBank_Parser_Field_Guide.md`
   Purpose: compact implementation guide for the MassBank fields most relevant to MURU. It points back to the official MassBank Record Format 2.6.0 specification.

5. `DATASET_SOURCE.md`
   Purpose: pins the first dataset candidate, accession, experimental structure, and rules Claude must verify before ingestion.

## Rules for Claude Code

Do not treat every paper as a feature request.

Use these sources to answer four questions only:

1. What data are scientifically comparable?
2. How is collision energy represented?
3. What spectral quantities can be computed defensibly?
4. How should provenance and validation be preserved?

If a source conflicts with an assumption in the code, stop and resolve the scientific assumption before expanding the implementation.

Do not mix absolute collision energy and normalized collision energy as if they were the same variable.

Do not randomly split spectra from the same molecule across training and test partitions when evaluating generalization to unseen molecules.

Do not let a difficult minor parser case create a new project phase. Record nonblocking exceptions and continue once the current phase acceptance criteria are satisfied.
