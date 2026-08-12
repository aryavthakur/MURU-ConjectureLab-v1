"""Phase 3 discovery engine: grammar, search, equivalence, falsification.

Nothing in this package may import `muru.synth.truth` or `muru.synth.generators`,
directly or transitively. The search reads synthetic data from disk; it never
reads the planted law. `tests/test_p3_import_graph.py` enforces this.
"""
