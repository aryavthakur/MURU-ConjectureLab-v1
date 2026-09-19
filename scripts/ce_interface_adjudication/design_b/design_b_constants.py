"""Frozen constants shared by every Design B step. Changing any value here changes its hash in the freeze manifest."""
STUDY_ID = "muru-ce-interface-adjudication-design-b"
FREEZE_REF = f"refs/muru-freeze/{STUDY_ID}"
PROCUREMENT_REF = f"refs/muru-procurement/{STUDY_ID}"
SPECTRA_REF = f"refs/muru-spectra/{STUDY_ID}"
PREDICTIONS_REF = f"refs/muru-predictions/{STUDY_ID}"

FRAME_REL = "artifacts/ce_interface_adjudication/design_b/sourcing/eligible_universe.csv"
FRAME_SHA256 = "5a99c75ffbc29ccec6178a2686f3608f4f4bc354ab4399acbfab67efe2b2b4bd"

STRATA = {"L": (130.0, 300.0), "N": (485.0, 515.0), "H": (700.0, 900.0)}
STRATUM_PRIORITY = ("N", "H", "L")          # cross-stratum scaffold rule, as the sourcing screen
PROCUREMENT_TARGET_PER_STRATUM = 66
ANALYSABLE_TARGET_PER_STRATUM = 60
UNDERPOWERED_FLOOR = 50                       # disclosure label only, never changes a verdict

NCE_GRID = (15, 30, 45, 60, 75)
MAPPINGS = ("K1", "K2", "K3")
PRIMARY_PAIR = ("K1", "K2")
MODELS = ("ICEBERG_2_1", "GLACIER")
PRIMARY_METRIC = "cosine"
ROBUSTNESS_METRIC = "js"
TRAINING_CE_Q95 = 90.0                        # grid_support_audit.json, training numeric CE q95

ALPHA = 0.05
BOOT_B = 10_000
BOOT_SEED = 20260919
SIMILARITY_FROZEN_CONFIG_SHA256 = "655436863b02262585609d5582f43a73a0f51f84d04d0bba0da9c2b3db252848"

# Procurement skip reasons: the only reasons a queued candidate may be passed over.
SKIP_REASONS = {
    "NO_SUPPLY": "no current MCE, TargetMol or Selleck listing can supply the compound",
    "PURITY_LT_95": "vendor cannot provide purity >= 95%",
    "IDENTITY_MISMATCH": "supplied material does not match the frozen structure or identity",
    "INSUFFICIENT_QUANTITY": "insufficient material for the planned acquisition plus one re-injection",
    "SCAFFOLD_ALREADY_ACCEPTED": "scaffold group already accepted under the fixed cross-stratum rule",
}
MIN_QUANTITY_MG = 1.0                         # minimum supplied amount counted as sufficient
VERIFICATION_DEADLINE_BUSINESS_DAYS = 15      # no answer after a logged request and one reminder = NO_SUPPLY
