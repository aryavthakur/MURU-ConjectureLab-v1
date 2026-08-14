# Table 8. Reproducibility & Software Dependency Stack

| Package / Component | Exact Bound Version | Purpose in Benchmark Pipeline |
|---|---|---|
| `python` | `3.13.12` | Runtime interpreter (plan recorded 3.12 target; full stack verified on 3.13) |
| `scikit-learn` | `1.9.0` | HistGradientBoostingRegressor GBDT ceiling estimator |
| `pysr` | `1.5.10` | Symbolic regression search engine under Julia backend |
| `sympy` | `1.14.0` | Symbolic expression parsing, differentiation, and normalisation |
| `numpy` | `1.26.4` | Numerical array operations and linear-method quantile estimation |
| `scipy` | `1.17.1` | Statistical distributions, correlations, and optimization routines |
| `pandas` | `2.2.2` | Structured dataset, manifest, and partition frame handling |
| `matplotlib` | `3.11.1` | Vector figure generation (SVG / PDF) and 300-DPI PNG previews |
