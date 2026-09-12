"""Frozen Stage 1 constants, from MURU_WUR_REAL_DATA_PREREGISTRATION.md.

Every value here was fixed before any real delta was computed. They live in
one module, imported rather than inlined, so that changing one is a visible
diff against a preregistered document and not an edit buried in an analysis
script. A change to any of them voids the gate, and the preregistration says
so in those words.
"""

SEED = 20260911

LADDER_ENERGIES = (15.0, 30.0, 45.0, 60.0, 75.0, 90.0)

# Base preprocessing cell, configs/preprocessing.yaml.
BASE_CELL = {
    "relative_cutoff": 0.0,
    "include_precursor": True,
    "intensity_transform": "raw",
}
PRECURSOR_MATCH_PPM = 10.0

# Duplicate (connectivity_key, energy) spectra collapse to one mu by this
# aggregator, chosen before any real mu existed.
DUPLICATE_AGGREGATOR = "median"

# The gate.
MEDIAN_ABS_DELTA_MAX = 0.05   # ~1.7x the 0.0295 inter-mixture repeatability SD
SPEARMAN_MIN = 0.80
MIN_PASSING_ENERGIES = 5      # of 6
MIN_PAIRS_FOR_CORRELATION = 3  # below this a Spearman rho is undefined
MIN_POPULATION_B = 30          # erratum E-1; see preregistration section 5.1

# Entry condition for the POOL_AFTER_ENERGY_ALIGNMENT branch.
OFFSET_MAX = 0.15

# The monotone affine energy map T(E) = a + b*E, fitted only if that branch
# is entered. A generous a-priori box, not tuned.
ALIGNMENT_A_BOUNDS = (-30.0, 30.0)
ALIGNMENT_B_BOUNDS = (0.5, 2.0)
ALIGNMENT_MAXITER = 1000
ALIGNMENT_TOL = 1e-8
ALIGNMENT_POLISH = True
