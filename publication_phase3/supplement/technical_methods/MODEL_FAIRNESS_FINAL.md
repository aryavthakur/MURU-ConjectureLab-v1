# Model-comparison fairness audit

The external comparison pairs a frozen Tier A + Morgan-count joint ridge with a separate Tier A ridge. The candidate has 12 standardized Tier A descriptors plus 2,048 log1p Morgan count features weighted 0.1; α=0.3. The reference has Tier A only and selected α=0.1. Both use the same fixed response profile and external measured endpoints, and both receive the same fixed deployment energy coordinate. This is a fair paired predictive comparison of the two frozen model pipelines on the same compounds and cells.

It is not a feature-isolation experiment. Feature representation, feature scaling, regularization and model selection differ. The observed difference cannot be attributed solely to Morgan fingerprints or to any particular structural motif. The independent study supports the statement that the frozen candidate pipeline had lower mean pooled error than this reference under the fixed map, with a small effect that missed the 5% practical criterion.

The full-spectrum comparator benchmark is less directly matched: FIORA-OS, ICEBERG and GLACIER differ from MURU in output, training corpora, architecture, preprocessing, and potentially CE units. Its results are conditional sensitivity analyses and cannot rank a scalar model against full-spectrum models as equivalent tasks.
