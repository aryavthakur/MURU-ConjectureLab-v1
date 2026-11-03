"""WUR Stage 2: the first real-data MURU runs.

Stage 2A runs the frozen pre-WUR MURU on WUR development data exactly once.
Stage 2B is a new development generation. Nothing in this package reads a
WUR-SEALED peak, mu, descriptor or outcome; every population it builds is
asserted disjoint from the sealed key list before any spectrum is decoded.
"""
