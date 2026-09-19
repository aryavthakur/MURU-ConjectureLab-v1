"""Frozen constants of the C02 high-mass replication. Changing any value changes its hash in the freeze manifest."""
STUDY_ID = "muru-ce-interface-high-mass-replication"
FREEZE_REF = f"refs/muru-freeze/{STUDY_ID}"
ACCESS_REF = f"refs/muru-access/{STUDY_ID}"
EXECUTE_ENV_VAR = "MURU_CE_HIGH_MASS_EXECUTE"
STUDY_DIR_REL = "artifacts/ce_interface_adjudication/high_mass"
RECORDS_DIR_REL = "data/massbank/MassBank-data/Eawag_C02_high_mass"

NCE_GRID = (15, 20, 25, 30, 40, 50, 60)       # fixed from metadata by 10_build_population.choose_grid
MAPPINGS = ("K1", "K2", "K3")                  # K3 descriptive only
PRIMARY_PAIR = ("K1", "K2")
MODELS = ("ICEBERG_2_1", "GLACIER")
PRIMARY_METRIC = "cosine"
ROBUSTNESS_METRIC = "js"
ALPHA = 0.05
BOOT_B = 10_000
BOOT_SEED = 20260920

# Design A modules reused unchanged, pinned by sha256 (Design A result chain 518190b..1937aa9).
DESIGN_A_SHA256 = {
    "26_retrieve_records.py": "458bf7e40fbbd65294689e30c92c3b6528f8588bbca0c21fdb8bd00193a819be",
    "30_run_predictions.py": "461b18fbd2b10a10d1ac6d6097ea7bde258e3e0efdeba5a369469679c6270680",
    "40_score_spectra.py": "ec0100b5d93ffa2106460c1354a33cf302f00cea93efb92baaa70168a4824bbf",
    "50_analysis.py": "024b8bb03ff22f878e11d143f8365c836f058689a69ee79cdd9ea6fd6ee0e336",
    "spectrum_similarity.py": "6f48cbc02f5958f284cc870c3dbb96e87abad27d817fc7b5dbc0e2282a092353",
}
SIMILARITY_FROZEN_CONFIG_SHA256 = "655436863b02262585609d5582f43a73a0f51f84d04d0bba0da9c2b3db252848"
