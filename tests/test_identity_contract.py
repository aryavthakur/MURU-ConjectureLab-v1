"""A3.5 Decision 1 (Session 3 repair): property + regression tests for the
positive-global-scale identity contract in
``muru.paper_benchmark.identity_contract``.

All fixtures are hand-built synthetic expressions or randomly generated
grammar-legal expressions from a fixed local seed. No Development case
outcomes, no Held-out data, no Challenge, no Confirmation, no truth labels
of any kind are read anywhere in this file.
"""
from __future__ import annotations

import decimal
import random
import sys
from pathlib import Path

import pytest
import sympy as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muru.paper_benchmark.identity_contract import (  # noqa: E402
    GRAMMAR_PRIMITIVES,
    cluster_by_template_key,
    parse_candidate,
    positive_scale_equivalent,
    template_key,
)

# ---------------------------------------------------------------------
# Random grammar-legal corpus generator (unit-test generation, not a
# governed case -- a small fixed local seed, mirroring
# tests/test_p3_equivalence.py's style).
# ---------------------------------------------------------------------
CORPUS_SEED = 20260814
CORPUS_N = 1500

_UNARY = ["sqrt", "log", "square", "cube", "inv"]
_BINARY = ["+", "-", "*", "/"]


def _rand_const(rng: random.Random):
    choices = [
        lambda: rng.randint(1, 9),
        lambda: -rng.randint(1, 9),
        lambda: round(rng.uniform(0.1, 9.9), rng.choice([1, 2])),
        lambda: -round(rng.uniform(0.1, 9.9), rng.choice([1, 2])),
        lambda: sp.Rational(rng.randint(1, 9), rng.randint(1, 9)),
    ]
    return rng.choice(choices)()


def _rand_expr(rng: random.Random, depth: int) -> sp.Expr:
    if depth <= 0 or rng.random() < 0.35:
        if rng.random() < 0.55:
            return sp.Symbol(rng.choice(GRAMMAR_PRIMITIVES))
        return sp.sympify(_rand_const(rng))
    if rng.random() < 0.55:
        op = rng.choice(_BINARY)
        a = _rand_expr(rng, depth - 1)
        b = _rand_expr(rng, depth - 1)
        try:
            if op == "+":
                return a + b
            if op == "-":
                return a - b
            if op == "*":
                return a * b
            return a / b
        except Exception:
            return sp.Symbol(rng.choice(GRAMMAR_PRIMITIVES))
    op = rng.choice(_UNARY)
    a = _rand_expr(rng, depth - 1)
    try:
        if op == "sqrt":
            return sp.sqrt(a)
        if op == "log":
            return sp.log(a)
        if op == "square":
            return a ** 2
        if op == "cube":
            return a ** 3
        return 1 / a
    except Exception:
        return sp.Symbol(rng.choice(GRAMMAR_PRIMITIVES))


def _rationalize(expr: sp.Expr) -> sp.Expr:
    """Rationalize Float leaves to exact Rationals (via decimal TEXT,
    matching the module's own `_rationalize_floats` -- see
    `identity_contract.py`'s "Float rationalisation" docstring section for
    why binary bit-pattern conversion is wrong here) BEFORE this expression
    is used as the base of a scale-invariance test in the sections below
    that multiply an EXISTING parsed object by an external Python-level
    Rational scalar. This is a test-harness correctness requirement, not
    (by itself) a module requirement: sympy's `Rational * Float`
    multiplication performs lossy double-precision arithmetic at
    Python-object-construction time (confirmed by direct execution -- e.g.
    `Rational(10) * Float(-3.2)` distributes into an Add whose Float term is
    computed via float multiplication, not exact rational multiplication),
    so multiplying a Float-containing base expression by an external test
    scalar can silently produce an expression that is NOT exactly `c * f`.
    Rationalizing first (and always using Rational, never Float, test
    scalars) makes `c * f` an exact symbolic identity, which is what the
    positive-scale-invariance law is actually a claim about.

    This is a DIFFERENT test scenario from the
    "independently-typed-decimal-coefficients" class further down this
    file: that class constructs two SEPARATE decimal-literal STRINGS and
    parses each independently (exercising the module's own
    `_rationalize_floats` on genuinely independent Float objects, which is
    where the Session-4 fatal defect actually lived); this helper instead
    removes Floats from a single base object before an external exact-
    Rational multiplication, so that sweep tests a different thing (scalar
    multiplication of an existing object) without an unrelated
    test-harness-level precision artifact. Both are legitimate, kept
    side by side, and neither substitutes for the other."""
    floats = expr.atoms(sp.Float)
    if not floats:
        return expr
    return expr.xreplace({f: sp.Rational(str(f)) for f in floats})


def _generate_corpus(n: int, seed: int) -> list[sp.Expr]:
    rng = random.Random(seed)
    out = []
    tries = 0
    while len(out) < n and tries < n * 20:
        tries += 1
        depth = rng.choice([1, 2, 2, 3, 3, 3, 4])
        e = _rand_expr(rng, depth)
        try:
            e = _rationalize(sp.sympify(e))
        except Exception:
            continue
        out.append(e)
    return out


def _is_undefined(expr: sp.Expr) -> bool:
    """True iff expr contains a literal zoo/oo/-oo/nan term. Such a
    candidate evaluates non-finite at EVERY point of the covariate domain
    and is rejected upstream by grammar.py's MAX_INVALID_FRACTION gate
    (100% invalid fraction >> the 0.5% ceiling) long before it could ever
    reach this contract in the real pipeline. This is a KNOWN, DISCLOSED
    limitation (re-derived here, and independently matching a limitation
    already disclosed in the prior A3.5 Decision 1 session for
    zoo-absorbing Add terms) rather than a defect engineered around; see
    the module docstring. It is carved out of the headline pass/fail counts
    below and checked separately so it cannot hide inside an aggregate
    number."""
    return bool(expr.has(sp.zoo) or expr.has(sp.nan) or expr.has(sp.oo) or expr.has(-sp.oo))


@pytest.fixture(scope="module")
def corpus() -> list[sp.Expr]:
    return _generate_corpus(CORPUS_N, CORPUS_SEED)


@pytest.fixture(scope="module")
def clean_corpus(corpus) -> list[sp.Expr]:
    return [e for e in corpus if not _is_undefined(e)]


# =======================================================================
# Required concrete regression fixtures (the user's own list, verbatim)
# =======================================================================

M, D = sp.symbols("mass descriptor")


def eq(a: str, b: str) -> bool:
    return positive_scale_equivalent(parse_candidate(a), parse_candidate(b))


@pytest.mark.parametrize("a,b", [
    ("sqrt(mass)", "1.9*sqrt(mass)"),
    ("mass/(1+descriptor)", "2*mass/(2+2*descriptor)"),
    ("1/(2*mass+2*descriptor)", "2/(4*mass+4*descriptor)"),
    ("mass*descriptor + mass", "mass*(descriptor+1)"),
    ("mass**2", "mass*mass"),
    ("mass**2", "square(mass)"),
    ("mass*mass", "square(mass)"),
    ("mass/descriptor", "mass*inv(descriptor)"),
])
def test_required_fixtures_equivalent(a, b):
    assert eq(a, b), f"expected E({a!r}, {b!r}) == True"


@pytest.mark.parametrize("a,b", [
    ("log(mass)", "log(inv(mass))"),
])
def test_required_fixtures_not_equivalent(a, b):
    assert not eq(a, b), f"expected E({a!r}, {b!r}) == False"


def test_fatal_defect_repro_rational_function_scale():
    """The exact minimal repro from the prior session's post-mortem:
    key(1/(2m+2d)) must equal key(2*(1/(2m+2d))). This is the headline
    defect this module exists to fix."""
    f = parse_candidate("1/(2*mass+2*descriptor)")
    g = 2 * f
    assert positive_scale_equivalent(f, g)
    # and at scalars that are NOT coprime with the internal factor of 2,
    # exactly the case the prior session found failing 10/12 times.
    for c in [sp.Rational(4), sp.Rational(10), sp.Rational(1, 2),
              sp.Rational(1, 10 ** 6), sp.Rational(6), sp.Rational(8)]:
        assert positive_scale_equivalent(f, c * f), f"failed at scale {c}"


def test_parameter_sharing_a_m_plus_a_d_scaled():
    """a*m + a*d equivalent to a positive-scaled version (section 7.4
    precedent, re-verified under the new design)."""
    base = 2 * M + 2 * D
    scaled = sp.Rational(7, 2) * base
    assert positive_scale_equivalent(base, scaled)


def test_parameter_sharing_different_ratio_not_equivalent():
    """a*m + b*d with a genuinely different a:b ratio must NOT merge."""
    assert not positive_scale_equivalent(2 * M + 2 * D, 2 * M + 3 * D)


def test_power_forms_all_equivalent():
    a, b, c = parse_candidate("mass**2"), parse_candidate("mass*mass"), parse_candidate("square(mass)")
    assert positive_scale_equivalent(a, b)
    assert positive_scale_equivalent(b, c)
    assert positive_scale_equivalent(a, c)


def test_division_forms_equivalent():
    assert eq("mass/descriptor", "mass*inv(descriptor)")


def test_positive_constants_equivalent_to_each_other():
    assert positive_scale_equivalent(sp.Integer(3), sp.Integer(7))
    assert positive_scale_equivalent(sp.Rational(1, 5), sp.Integer(1000000))


def test_negative_constants_not_equivalent_to_positive():
    assert not positive_scale_equivalent(sp.Integer(3), sp.Integer(-7))
    assert not positive_scale_equivalent(sp.Integer(-3), sp.Integer(7))


def test_negative_constants_equivalent_to_each_other():
    assert positive_scale_equivalent(sp.Integer(-3), sp.Integer(-7))


def test_zero_constant_is_reflexive_and_self_consistent():
    """Documented behaviour: 0 is only scale-ambiguous with itself (c*0 == 0
    for every c, positive or not), so every expression that is IDENTICALLY
    zero collapses to one class. This is mathematically correct, not an
    over-merge: these expressions truly are the same object (the constant
    0), not merely proportional to it."""
    assert positive_scale_equivalent(sp.Integer(0), sp.Integer(0))
    a = parse_candidate("mass - mass")
    b = parse_candidate("descriptor - descriptor")
    assert positive_scale_equivalent(a, b)
    assert positive_scale_equivalent(a, sp.Integer(0) * sp.Rational(-5))


def test_near_zero_emitted_constant_is_a_genuine_nonzero_scale():
    """A near-zero but nonzero coefficient is still a positive scale (not
    special-cased toward zero -- no invented magnitude threshold, matching
    the amendment's stated discipline elsewhere)."""
    tiny = sp.Rational(1, 10 ** 12)
    assert positive_scale_equivalent(M, tiny * M)
    assert not positive_scale_equivalent(M, tiny * D)


def test_nested_rational_expressions():
    a = parse_candidate("(mass + 2*descriptor)/(3*mass + 6*descriptor)")
    b = sp.Rational(5, 2) * a
    assert positive_scale_equivalent(a, b)
    c = parse_candidate("1/(2*mass+2*descriptor) + 1/(3*mass+3*descriptor)")
    d = sp.Rational(7) * c
    assert positive_scale_equivalent(c, d)


def test_sqrt_inv_forms_stress():
    a = parse_candidate("sqrt(mass)/inv(descriptor)")
    b = sp.Rational(3, 4) * a
    assert positive_scale_equivalent(a, b)
    assert not positive_scale_equivalent(a, parse_candidate("sqrt(descriptor)/inv(mass)"))


@pytest.mark.parametrize("form", [
    "log(square(mass))", "log(cube(mass))", "log(sqrt(mass))",
])
def test_log_power_family_all_equivalent_to_log_mass(form):
    assert eq("log(mass)", form)


def test_log_power_family_distinct_from_log_inv():
    a = parse_candidate("log(mass)")
    b = parse_candidate("log(square(mass))")
    c = parse_candidate("log(cube(mass))")
    d = parse_candidate("log(sqrt(mass))")
    z = parse_candidate("log(inv(mass))")
    for x in (a, b, c, d):
        assert not positive_scale_equivalent(x, z)


# =======================================================================
# Previously-fixed regressions from the prior A3.5 Decision 1 session,
# re-derived and re-verified under this from-scratch design
# =======================================================================

def test_sqrt_square_diff_does_not_over_merge():
    """sqrt(square(mass-descriptor)) != mass-descriptor: since neither
    symbol is asserted positive, |mass-descriptor| != mass-descriptor in
    general, and this module never collapses the two."""
    assert not eq("sqrt(square(mass-descriptor))", "mass-descriptor")


def test_float_exponent_matches_native_sqrt():
    assert eq("mass**0.5", "sqrt(mass)")


def test_deep_log_nesting_reflexivity():
    """The prior session's non-reflexivity bug was specifically triggered
    by deeply nested logs interacting with a non-deterministic Dummy
    substitution. This module uses no Dummy objects anywhere; re-verify
    reflexivity holds at nesting depth up to 5, including across
    independently re-parsed copies of the same string (a fresh SymPy object
    graph each time)."""
    e = M
    for _ in range(5):
        e = sp.log(e + 5)
    reparsed = sp.sympify(str(e), locals={"mass": M})
    assert template_key(e) == template_key(e)
    assert template_key(e) == template_key(reparsed)
    assert positive_scale_equivalent(e, e)
    assert positive_scale_equivalent(e, reparsed)


def test_deep_log_nesting_determinism_across_many_reparses():
    e = sp.log(sp.log(sp.log(M + 3) + 2) + 1)
    keys = {template_key(sp.sympify(str(e), locals={"mass": M})) for _ in range(200)}
    assert len(keys) == 1


# =======================================================================
# Property tests over the random corpus: reflexive, symmetric, transitive,
# positive-scale-invariant, negative-scale-distinct
# =======================================================================

def test_reflexive_over_corpus(corpus):
    failures = [e for e in corpus if not positive_scale_equivalent(e, e)]
    assert not failures, f"{len(failures)}/{len(corpus)} reflexivity failures"


def test_reflexive_recompute_is_deterministic(corpus):
    failures = [e for e in corpus if template_key(e) != template_key(e)]
    assert not failures


def test_symmetric_over_random_pairs(corpus):
    rng = random.Random(1)
    n = len(corpus)
    pairs = [(rng.randrange(n), rng.randrange(n)) for _ in range(5000)]
    failures = [
        (i, j) for i, j in pairs
        if positive_scale_equivalent(corpus[i], corpus[j])
        != positive_scale_equivalent(corpus[j], corpus[i])
    ]
    assert not failures, f"{len(failures)}/5000 symmetry failures"


def test_key_equality_is_exactly_the_relation(corpus):
    """This is the load-bearing proof that template_key can be used as a
    clustering key at all: template_key(a) == template_key(b) must be
    EXACTLY positive_scale_equivalent(a, b), not merely a sound
    approximation of it. Checked directly, not assumed."""
    rng = random.Random(2)
    n = len(corpus)
    pairs = [(rng.randrange(n), rng.randrange(n)) for _ in range(5000)]
    keys = [template_key(e) for e in corpus]
    failures = [
        (i, j) for i, j in pairs
        if (keys[i] == keys[j]) != positive_scale_equivalent(corpus[i], corpus[j])
    ]
    assert not failures, f"{len(failures)}/5000 key<=>relation mismatches"


def test_transitive_via_key_equality_clusters(corpus):
    """Transitivity of E follows from transitivity of key-equality (proven
    exact by test_key_equality_is_exactly_the_relation); this test
    additionally verifies the resulting clusters are internally fully
    pairwise-equivalent by DIRECTLY calling positive_scale_equivalent
    (not just comparing keys) on a sample of cluster members."""
    clusters = cluster_by_template_key(corpus)
    rng = random.Random(3)
    multi = [c for c in clusters if len(c) > 1]
    sample = rng.sample(multi, min(100, len(multi))) if multi else []
    for cluster in sample:
        i0 = cluster[0]
        for j in cluster[1:]:
            assert positive_scale_equivalent(corpus[i0], corpus[j])


def test_transitive_explicit_scale_chains(corpus):
    failures = 0
    for e in corpus[:300]:
        g = sp.Rational(3) * e
        h = sp.Rational(2) * g
        ab = positive_scale_equivalent(e, g)
        bc = positive_scale_equivalent(g, h)
        ac = positive_scale_equivalent(e, h)
        if ab and bc and not ac:
            failures += 1
    assert failures == 0


_SCALE_FACTORS = [
    sp.Rational(1, 2), sp.Rational(2), sp.Rational(4), sp.Rational(10),
    sp.Rational(1, 1000000), sp.Rational(1000000), sp.Rational(7, 3),
    sp.Rational(1, 7), sp.Rational(1, 10 ** 12), sp.Rational(10 ** 12),
    sp.Rational(3), sp.Rational(6), sp.Rational(9),
]


def test_positive_scale_invariant_over_clean_corpus(clean_corpus):
    """E(f, c*f) == True for every f in the corpus and every c above,
    EXCLUDING the disclosed zoo/undefined limitation (see _is_undefined and
    the module docstring). This is the headline law the prior session's
    fix attempt failed on 2/800 (their unfixed baseline) to 26/800 (their
    best attempted-but-unverified fix); the target here is zero."""
    failures = []
    for e in clean_corpus:
        for c in _SCALE_FACTORS:
            if not positive_scale_equivalent(e, c * e):
                failures.append((str(e), str(c)))
    assert not failures, f"{len(failures)} positive-scale-invariance failures: {failures[:10]}"


def test_positive_scale_invariant_zoo_limitation_is_isolated_and_documented(corpus):
    """Confirms the ONLY surviving positive-scale-invariance counterexamples
    in the full (non-clean) corpus are all zoo/undefined-poisoned -- i.e.
    that the exclusion in the test above is not quietly hiding some other,
    undisclosed failure family. If this test starts failing, a NEW defect
    has appeared and must be investigated, not filtered out."""
    undefined = [e for e in corpus if _is_undefined(e)]
    clean = [e for e in corpus if not _is_undefined(e)]
    clean_failures = [
        (str(e), str(c)) for e in clean for c in _SCALE_FACTORS
        if not positive_scale_equivalent(e, c * e)
    ]
    assert not clean_failures, f"non-zoo failures found: {clean_failures[:10]}"
    # Sanity: the generator does produce at least a few undefined items in
    # a corpus this size, so the exclusion above is doing real work, not
    # vacuously never triggering.
    assert len(undefined) >= 1


_NEG_SCALE_FACTORS = [sp.Rational(-1), sp.Rational(-1, 1000000), sp.Rational(-3), sp.Rational(-1, 3)]


def test_negative_scale_distinct_over_clean_corpus(clean_corpus):
    """E(f, c*f) == False for c < 0, for every non-identically-zero f in
    the corpus, excluding the disclosed zoo limitation."""
    failures = []
    for e in clean_corpus:
        is_zero = (template_key(e)[0] == "OK" and template_key(e)[1] == sp.srepr(sp.Integer(0)))
        for c in _NEG_SCALE_FACTORS:
            got = positive_scale_equivalent(e, c * e)
            if is_zero:
                if not got:
                    failures.append(("zero-should-merge", str(e), str(c)))
            elif got:
                failures.append(("nonzero-should-not-merge", str(e), str(c)))
    assert not failures, f"{len(failures)} negative-scale-distinct failures: {failures[:10]}"


def test_negative_scale_distinct_named_fixture():
    f = parse_candidate("sqrt(mass)")
    assert not positive_scale_equivalent(f, -f)
    g = parse_candidate("1/(2*mass+2*descriptor)")
    assert not positive_scale_equivalent(g, -g)
    assert not positive_scale_equivalent(g, sp.Rational(-2) * g)
    # sign flip on numerator only vs denominator only must both be caught
    num_flip = parse_candidate("-1/(2*mass+2*descriptor)")
    den_flip = parse_candidate("1/(-2*mass-2*descriptor)")
    assert positive_scale_equivalent(num_flip, den_flip)  # both ARE -g
    assert not positive_scale_equivalent(g, num_flip)
    assert not positive_scale_equivalent(g, den_flip)


def test_negative_scale_distinct_tiny_and_sign_split():
    """f vs -f, f scaled by a tiny negative constant, and f scaled by
    constants that flip the sign of only the numerator vs only the
    denominator -- all must resolve to NOT equivalent to the unscaled f,
    and all the negative variants must be equivalent to EACH OTHER."""
    f = parse_candidate("1/(2*mass+2*descriptor)")
    tiny_neg = sp.Rational(-1, 10 ** 9) * f
    assert not positive_scale_equivalent(f, tiny_neg)
    assert positive_scale_equivalent(-f, tiny_neg)


# =======================================================================
# Session 4 (Agent I2 hostile review): independently-typed decimal
# coefficients. This is the FATAL defect I2 found: two SEPARATELY-AUTHORED
# decimal-literal strings representing "the same family at a clean scale"
# (e.g. "mass + 0.4*descriptor" vs "3.0*mass + 1.2*descriptor", exactly
# 3x) were NOT recognized as equivalent, because the previous
# `_rationalize_floats` converted each Float to its exact IEEE-754-BINARY-
# equivalent Rational: `3 * Rational(0.4) != Rational(1.2)` (each decimal
# literal independently rounds to the nearest of ~2^53 grid points, and a
# clean *decimal* ratio like 3x is essentially never preserved exactly
# under that rounding). This is the realistic production scenario --
# comparing independently-fit PySR equation strings from different seeds,
# each carrying its own independently-rounded decimal coefficients -- not a
# corner case, and I2 quantified it at 15.6%-48% failure rates on
# Float-coefficient multi-term expressions.
#
# I2 additionally found that the corpus in the property-test section above
# structurally could never exercise this failure mode, because its
# `_rationalize()` helper pre-scrubs Float coefficients out of the BASE
# expression before any scale-invariance sweep runs, and its scale factors
# are themselves exact Rationals -- so no two independently-rounded Floats
# were ever compared against each other. That earlier design decision was
# correct for what it was testing (exact Rational-scalar multiplication of
# an existing parsed object -- still a real, legitimate scenario, kept
# above), but it is NOT a substitute for this class, which is the first
# place in this file that constructs two SEPARATE strings, each with its
# own independently-computed decimal literals, and parses them
# independently -- matching how PySR/gplearn candidates actually arrive at
# this module in production.
#
# The fix (module, Session 4): rationalize each Float leaf via its own
# `str()` decimal text (`Rational(str(f))`), not its binary bit pattern.
# =======================================================================

def _decimal_scale(coeff_text: str, scale) -> str:
    """Exact decimal multiplication of an authored coefficient's text by a
    clean scale, formatted back to decimal text -- i.e. constructs the
    coefficient an independently-typed, exactly-3x-scaled (or whatever
    scale) sibling expression would plausibly carry, using exact decimal
    arithmetic so the test corpus's "should merge" fixtures are
    unambiguously, exactly clean-scale-related as DECIMAL text (which is
    the property this module is required to detect), while still being
    two independently-rendered strings, not one Python object multiplied
    by another."""
    return str(decimal.Decimal(coeff_text) * decimal.Decimal(str(scale)))


def _independently_typed_pair(rng: random.Random, scale):
    """Builds two INDEPENDENT decimal-literal strings: `a_str` with its own
    randomly-authored decimal coefficients, and `b_str`, a textually
    separate string (not `scale * parsed(a_str)`) whose own coefficients
    are `scale` times `a_str`'s as exact decimal text."""
    nterms = rng.randint(1, 4)
    variables = rng.sample(GRAMMAR_PRIMITIVES, k=nterms)
    coeff_texts = [str(round(rng.uniform(0.05, 9.5), rng.choice([1, 2, 3]))) for _ in variables]
    a_str = " + ".join(f"{c}*{v}" for c, v in zip(coeff_texts, variables))
    sibling_texts = [_decimal_scale(c, scale) for c in coeff_texts]
    b_str = " + ".join(f"{c}*{v}" for c, v in zip(sibling_texts, variables))
    return a_str, b_str


_SCALE_CHOICES = [2, 3, 4, 5, 6, 7, 9, 10, decimal.Decimal("1.5"), decimal.Decimal("0.5")]


def test_independently_typed_decimal_coefficients_named_repro():
    """I2's exact reported counterexample."""
    a = parse_candidate("mass + 0.4*descriptor")
    b = parse_candidate("3.0*mass + 1.2*descriptor")
    assert positive_scale_equivalent(a, b)


def test_independently_typed_decimal_coefficients_property_corpus():
    """The property-test class I2's methodology requires: several hundred
    pairs of INDEPENDENTLY-authored decimal-literal strings, each pair an
    exact clean-decimal-scale multiple of the other, parsed via two
    separate `parse_candidate` calls (never by multiplying one sympy object
    by another). Every pair must be recognized as positive-scale
    equivalent."""
    rng = random.Random(998877)
    n = 600
    failures = []
    for _ in range(n):
        scale = rng.choice(_SCALE_CHOICES)
        a_str, b_str = _independently_typed_pair(rng, scale)
        a, b = parse_candidate(a_str), parse_candidate(b_str)
        if not positive_scale_equivalent(a, b):
            failures.append((a_str, b_str, str(scale)))
    assert not failures, f"{len(failures)}/{n} independently-typed-decimal failures: {failures[:10]}"


def test_independently_typed_decimal_coefficients_rejects_non_scale_pairs():
    """Same construction, but one coefficient is perturbed off the clean
    scale -- must NOT merge (no over-merge introduced by the decimal-text
    fix). Restricted to pairs with >= 2 terms: a single-term expression
    ``c*x`` is legitimately positive-scale-equivalent to ANY ``c'*x`` with
    ``c' > 0`` regardless of the specific ratio c'/c -- there is only one
    "shape" to scale -- so perturbing a lone coefficient is not a valid
    negative fixture (confirmed directly: an earlier version of this test
    generated ``nterms=1`` pairs and wrongly flagged e.g. ``7.0*mass`` vs
    ``42.37*mass`` as a false merge; both really are the same family up to
    a positive scale). With >= 2 differently-scaled terms, perturbing one
    coefficient genuinely changes the internal coefficient RATIO, which is
    exactly the case this contract must keep distinct (section 7.4's
    ratio-preservation precedent)."""
    rng = random.Random(112233)
    n = 200
    tried = 0
    false_merges = []
    while tried < n:
        scale = rng.choice(_SCALE_CHOICES)
        a_str, b_str = _independently_typed_pair(rng, scale)
        parts = b_str.split(" + ")
        if len(parts) < 2:
            continue
        tried += 1
        coeff, var = parts[0].split("*", 1)
        perturbed_coeff = str(decimal.Decimal(coeff) + decimal.Decimal("0.37"))
        parts[0] = f"{perturbed_coeff}*{var}"
        b_perturbed = " + ".join(parts)
        a, b = parse_candidate(a_str), parse_candidate(b_perturbed)
        if positive_scale_equivalent(a, b):
            false_merges.append((a_str, b_perturbed))
    assert not false_merges, f"{len(false_merges)}/{n} false merges: {false_merges[:10]}"


def test_independently_typed_decimal_coefficients_quantified_regression_vs_old_binary_approach():
    """Directly quantifies, by execution, that the PREVIOUS binary-Float
    rationalization would have failed at a large, non-corner-case rate on
    this exact corpus (matching I2's reported 15.6%-48%, and this repo's
    own independent measurement: 53.2% on a 600-pair run at the time this
    test was written), while the CURRENT (decimal-text) approach has zero
    failures on the identical corpus. This keeps the regression visible: if
    someone reverts `_rationalize_floats` to `Rational(f)`, this test's
    `old_failures` assertion documents exactly why that would be wrong, and
    the `new_failures == 0` assertion catches it directly.

    The old-path replica below is intentionally local to this test (not
    reintroduced into the module) -- it exists only to make the
    before/after comparison concrete and re-executable, not as a supported
    code path."""
    import muru.paper_benchmark.identity_contract as ic

    def _old_binary_key(expr: sp.Expr):
        e1 = ic._positivize(expr)
        floats = e1.atoms(sp.Float)
        e1 = e1.xreplace({f: sp.Rational(f) for f in floats})  # the OLD, FATAL approach
        e2 = sp.cancel(sp.together(e1))
        N, D = sp.fraction(e2)
        N, D = sp.sympify(N), sp.sympify(D)
        if not (ic._guard_ok(N) and ic._guard_ok(D)):
            return ic._uncanonicalizable_key(expr)
        _cN, pN = N.as_content_primitive()
        _cD, pD = D.as_content_primitive()
        if not (ic._guard_ok(pN) and ic._guard_ok(pD)):
            return ic._uncanonicalizable_key(expr)
        return ("OK", sp.srepr(pN), sp.srepr(pD))

    rng = random.Random(998877)  # same seed as the main property corpus above
    n = 600
    old_failures = 0
    new_failures = 0
    for _ in range(n):
        scale = rng.choice(_SCALE_CHOICES)
        a_str, b_str = _independently_typed_pair(rng, scale)
        a, b = parse_candidate(a_str), parse_candidate(b_str)
        if _old_binary_key(a) != _old_binary_key(b):
            old_failures += 1
        if not positive_scale_equivalent(a, b):
            new_failures += 1

    assert old_failures > n * 0.10, (
        f"expected the old binary approach to fail on a large, non-corner-case "
        f"fraction of this corpus (regression guard); got only {old_failures}/{n}"
    )
    assert new_failures == 0, f"current approach failed {new_failures}/{n}"


# =======================================================================
# Session 5 (Agent I2 second hostile review): caller-side Float arithmetic
# residual. `positive_scale_equivalent(f, c*f)` can be False when `c*f` is
# built via ordinary SymPy `__mul__` on an EXISTING parsed object containing
# a Float leaf -- e.g. a unary-op-produced literal like `sqrt(8.9)*mass`, or
# any multi-digit decimal literal -- multiplied by an integer/rational scale
# in Python. This is DIFFERENT from, and NOT fixed by, the Session-4
# decimal-text rationalization fix: that fix makes each of the two INPUTS'
# own Float leaves exact once this module sees them; it cannot recover
# information SymPy's OWN bounded-precision multiplication already destroyed
# BEFORE this module was ever called with the result.
#
# Verified this is a genuine, information-theoretic irreducibility (not an
# engineering gap): SymPy Float*Integer multiplication at default 53-bit
# precision rounds the mathematically exact product to the nearest
# representable double whenever that product needs more than 53 mantissa
# bits (true for effectively all multipliers that are not themselves a
# power of two); separately, and more broadly than that alone, SymPy's
# fixed-significant-digit decimal `str()` rendering discards information
# whenever multiplication shifts the number's order of magnitude, even for
# bit-exact power-of-two multipliers. Both effects were confirmed directly.
# No fix was found or is possible within `positive_scale_equivalent`'s
# two-argument signature: rounding-to-nearest-double is a many-to-one map
# (an entire open interval of distinct true reals rounds to the identical
# bit pattern this module receives), so there is no principled way to
# recover "what scale the caller intended" from the rounded bits alone
# without either (a) side information this function's signature does not
# carry, or (b) a numerical-proximity/tolerance search over candidate
# scales -- explicitly excluded by this contract's exact, tolerance-free
# mandate (see identity_contract.py's "Float rationalisation" section's
# rejection of `nsimplify` for the same reason).
#
# See identity_contract.py's "KNOWN, DISCLOSED, PROVABLY IRREDUCIBLE
# limitation #2" docstring section for the full argument and the refined
# formal statement of positive-scale-invariance this module actually
# guarantees: exact for two INDEPENDENTLY decimal-text-authored expressions
# (which is how every real candidate reaches this module in production --
# amendment section 7.3/7.5 requires each candidate be parsed fresh from
# its own PySR equation string, never derived by scalar-multiplying another
# candidate's parsed object), not guaranteed when `c*f` is instead
# constructed via raw in-process SymPy float arithmetic on an existing
# object.
#
# This class quantifies the residual on a FRESH corpus -- seed 20260901,
# distinct from Agent I2's own 3000-item corpus and distinct from every
# other seed used elsewhere in this file -- specifically built to trigger
# the exact condition identified: unary-op-produced Float literals
# (sqrt/log applied to a numeric constant, which SymPy auto-evaluates
# during parsing) and multi-digit decimal literals, each combined with a
# non-trivial external scale.
# =======================================================================

def _float_leaf_corpus_expr(rng: random.Random, depth: int) -> sp.Expr:
    """Like `_rand_expr`, but Float leaves are NOT rationalized away, and
    unary-ops-applied-to-a-numeric-constant (the exact I2 trigger --
    `sqrt(8.9)` auto-evaluates to a fresh Float during parsing) are boosted
    so the corpus actually exercises the residual rather than structurally
    avoiding it (as the main `corpus` fixture above does, by design, for a
    DIFFERENT test purpose -- see `_rationalize`'s docstring)."""
    if depth <= 0 or rng.random() < 0.3:
        if rng.random() < 0.5:
            return sp.Symbol(rng.choice(GRAMMAR_PRIMITIVES))
        digits = rng.choice([1, 2, 3, 4, 6, 8])
        return sp.Float(round(rng.uniform(0.1, 9.9), digits))
    if rng.random() < 0.45:
        op = rng.choice(_BINARY)
        a = _float_leaf_corpus_expr(rng, depth - 1)
        b = _float_leaf_corpus_expr(rng, depth - 1)
        try:
            if op == "+":
                return a + b
            if op == "-":
                return a - b
            if op == "*":
                return a * b
            return a / b
        except Exception:
            return sp.Symbol(rng.choice(GRAMMAR_PRIMITIVES))
    op = rng.choice(["sqrt", "log", "square", "cube", "inv", "sqrt_of_const", "log_of_const"])
    if op in ("sqrt_of_const", "log_of_const"):
        c = sp.Float(round(rng.uniform(1.1, 50.0), rng.choice([1, 2, 3])))
        try:
            base = sp.sqrt(c) if op == "sqrt_of_const" else sp.log(c)
        except Exception:
            base = c
        return base * sp.Symbol(rng.choice(GRAMMAR_PRIMITIVES))
    a = _float_leaf_corpus_expr(rng, depth - 1)
    try:
        if op == "sqrt":
            return sp.sqrt(a)
        if op == "log":
            return sp.log(a)
        if op == "square":
            return a ** 2
        if op == "cube":
            return a ** 3
        return 1 / a
    except Exception:
        return sp.Symbol(rng.choice(GRAMMAR_PRIMITIVES))


def _generate_float_leaf_corpus(n: int, seed: int) -> list[sp.Expr]:
    rng = random.Random(seed)
    out = []
    tries = 0
    while len(out) < n and tries < n * 20:
        tries += 1
        depth = rng.choice([1, 2, 2, 3, 3, 4])
        e = _float_leaf_corpus_expr(rng, depth)
        try:
            e = sp.sympify(e)
        except Exception:
            continue
        out.append(e)
    return out


_RESIDUAL_SCALES = [2, 3, 4, 5, 6, 7, 8, 9, 10, 16, sp.Rational(1, 2), sp.Rational(7, 3)]


def _decimal_text_sibling(expr: sp.Expr, scale) -> sp.Expr:
    """The REALISTIC construction: reinterpret every Float leaf as its own
    decimal-text Rational (no caller-side float rounding involved at all),
    then apply an exact rational scale. This is what two independently-fit
    PySR candidates -- one at the base family, one at a clean multiple of
    it, each printing its own decimal text -- actually look like once
    parsed; it is NOT `scale * expr` computed via raw SymPy float
    arithmetic."""
    floats = expr.atoms(sp.Float)
    exact = expr.xreplace({f: sp.Rational(str(f)) for f in floats})
    return sp.nsimplify(scale) * exact


class TestCallerSideFloatArithmeticResidual:
    """Session 5: quantifies and documents the caller-side-Float-arithmetic
    residual precisely, so it cannot silently regress OR silently hide.
    Referenced by name from identity_contract.py's module docstring."""

    def test_named_repro_matches_i2_exactly(self):
        """I2's reported repro is at the RAW SymPy-arithmetic level (a
        Rational-equality check, not a full `positive_scale_equivalent`
        call): `4*Rational(str(f_base)) != Rational(str(4*f_base))`. That
        raw inequality is confirmed first, exactly. Turning it into an
        actual FUNCTIONAL `positive_scale_equivalent` failure additionally
        requires >= 2 terms whose RATIO the precision loss can disturb --
        a single-term expression `c*mass` is trivially positive-scale-
        equivalent to `c'*mass` for ANY positive `c, c'` (there is only one
        shape to scale; confirmed directly and asserted below as a
        NON-repro, to document why a single term does not, by itself,
        reproduce the defect -- an earlier draft of this test wrongly
        assumed it would)."""
        f_base = sp.Float('2.9832867780352599', precision=53)
        lhs = 4 * sp.Rational(str(f_base))
        rhs = sp.Rational(str(4 * f_base))
        assert lhs != rhs, (
            "if this now holds, SymPy's Float semantics changed and the "
            "documented irreducibility argument needs re-checking, not "
            "silent deletion of this test"
        )
        mass, descriptor = sp.symbols("mass descriptor")

        single_term = f_base * mass
        assert positive_scale_equivalent(single_term, 4 * single_term), (
            "single-term c*mass vs c'*mass is ALWAYS scale-equivalent for "
            "any positive c, c' -- this is correct module behaviour, not "
            "part of the residual; documented here as a deliberate "
            "non-repro so the real (multi-term) repro below is not "
            "mistaken for a fluke"
        )

        f = f_base * mass + descriptor  # >= 2 terms: the coefficient RATIO now matters
        b = 4 * f
        assert not positive_scale_equivalent(f, b), (
            "known, disclosed, provably-irreducible residual (see module "
            "docstring limitation #2) -- if this starts passing, verify "
            "WHY before treating it as a fix"
        )

    def test_realistic_sibling_of_the_named_repro_is_recognized(self):
        """The SAME family, constructed the way production actually
        constructs it (independently decimal-text-authored, not
        caller-multiplied), IS recognized -- confirming the residual is
        specific to the raw-multiplication construction, not a general
        defect in this module."""
        f_base = sp.Float('2.9832867780352599', precision=53)
        mass, descriptor = sp.symbols("mass descriptor")
        f = f_base * mass + descriptor
        sibling = _decimal_text_sibling(f, 4)
        assert positive_scale_equivalent(f, sibling)

    def test_no_float_leaf_items_are_exact_unconditionally(self):
        """Rational/Integer-only expressions have NO precision-loss risk at
        all under raw in-process multiplication -- SymPy Rational arithmetic
        is exact. This guarantee is NOT weakened by limitation #2 and is
        reasserted here on the fresh 20260901 corpus specifically."""
        corpus = _generate_float_leaf_corpus(800, seed=20260901)
        no_float = [e for e in corpus if not e.atoms(sp.Float)
                    and not (e.has(sp.zoo) or e.has(sp.nan) or e.has(sp.oo) or e.has(-sp.oo))]
        assert len(no_float) >= 50, "corpus sanity: expected a meaningful no-float subset"
        failures = [
            (str(e), str(c)) for e in no_float for c in _RESIDUAL_SCALES
            if not positive_scale_equivalent(e, c * e)
        ]
        assert not failures, f"{len(failures)} unexpected failures on Rational-only items: {failures[:5]}"

    def test_quantified_residual_on_fresh_corpus_raw_multiplication(self):
        """The headline quantification: on a FRESH 800-item corpus (seed
        20260901, distinct from I2's 3000 and from every other corpus used
        in this file), how often does raw in-process SymPy multiplication
        of a Float-leaf-bearing expression break positive-scale-invariance?
        Asserted to be within a documented, nonzero, bounded range -- NOT
        asserted to be zero (that would be a false "fixed" claim) and NOT
        left unquantified (that would hide it, same standard as the
        zoo/ComplexInfinity limitation)."""
        corpus = _generate_float_leaf_corpus(800, seed=20260901)
        float_leaf = [e for e in corpus if e.atoms(sp.Float)
                      and not (e.has(sp.zoo) or e.has(sp.nan) or e.has(sp.oo) or e.has(-sp.oo))]
        assert len(float_leaf) >= 200, "corpus sanity: expected a substantial float-leaf subset"

        total = 0
        failures = 0
        for e in float_leaf:
            for c in _RESIDUAL_SCALES:
                total += 1
                if not positive_scale_equivalent(e, c * e):
                    failures += 1

        rate = failures / total
        # Documented range: nonzero (this IS a real, disclosed limitation --
        # a 0% result here would mean the corpus stopped exercising it and
        # this test would need investigation, not celebration) and bounded
        # well under 100% (a runaway rate would suggest a NEW, broader
        # defect beyond the documented mechanism).
        assert 0.01 < rate < 0.60, (
            f"residual rate {rate:.3%} ({failures}/{total}) fell outside the "
            f"documented expected range -- investigate before assuming this "
            f"is still the same understood limitation"
        )

    def test_same_corpus_via_realistic_construction_is_exact(self):
        """The SAME float-leaf corpus items, tested via the REALISTIC
        (independently-decimal-text-authored) sibling construction instead
        of raw multiplication, must have ZERO failures -- this is the
        actual guarantee this module makes, and proves the residual above
        is specific to the raw-multiplication TEST/construction
        methodology, not a general defect."""
        corpus = _generate_float_leaf_corpus(800, seed=20260901)
        float_leaf = [e for e in corpus if e.atoms(sp.Float)
                      and not (e.has(sp.zoo) or e.has(sp.nan) or e.has(sp.oo) or e.has(-sp.oo))]

        failures = []
        for e in float_leaf:
            for c in _RESIDUAL_SCALES:
                sibling = _decimal_text_sibling(e, c)
                if not positive_scale_equivalent(e, sibling):
                    failures.append((str(e), str(c)))
        assert not failures, f"{len(failures)} realistic-construction failures: {failures[:10]}"


# =======================================================================
# Session 6 (Agent H2 blind review): byte-identical UNCANONICALIZABLE
# merges, and reconciliation with amendment section 7.3 step 6's literal
# "unique to its own seed ordinal" wording.
#
# Decision (see identity_contract.py's "Byte-identical UNCANONICALIZABLE
# merges" docstring section for the full argument): this is CORRECT,
# INTENDED behaviour, not a defect. Two independently-parsed candidates
# whose text is byte-identical and which both land in UNCANONICALIZABLE DO
# merge, because their `srepr` strings are literally equal -- and literal
# textual identity is, if anything, STRONGER evidence of "same discovered
# expression" than the positive-scale-equivalence this contract otherwise
# detects. Seed-ordinal keying (the amendment's literal wording) is
# incompatible BY CONSTRUCTION with the required reflexivity law under
# this module's actual (seed-ordinal-free) function signature, and was
# already tried and abandoned in an earlier round for exactly that reason
# (a Dummy-object non-determinism bug for nested logs).
#
# This class also corrects, rather than silently accepts, one of H2's
# supporting claims: `sqrt(square(1.909*mass - 0.323*descriptor))` does
# NOT actually trip Guard A in this module (verified directly) -- that
# claim describes the PRIOR session's blanket-positivity design, not this
# module's mass-only positivity design. The underlying finding (byte-
# identical UNCANONICALIZABLE merges happen, and are reachable via fully
# grammar-legal text) is still real and confirmed, just via a different,
# already-disclosed route (exact self-cancellation feeding a division,
# i.e. limitation #1's `zoo` mechanism), not via the specific example H2
# proposed.
# =======================================================================

class TestUncanonicalizableByteIdenticalMerge:

    def test_h2_literal_repro_merges(self):
        """H2's exact reported repro. Note `Abs` is not in the frozen
        grammar's UNARY_OPERATORS (['sqrt','log','square','cube','inv']) --
        this string parses only because `sympify` falls back to its own
        global namespace for names absent from `locals=`, so this is a
        malformed/out-of-grammar-but-still-parseable input. Guard A's
        design already covers exactly this (defense in depth: reject
        anything with a non-frozen node head, whether or not the INPUT
        text was itself grammar-legal), and it is a valid test of the
        merge behaviour regardless of the input's grammar-legality."""
        a = parse_candidate("log(mass) + Abs(descriptor)")
        b = parse_candidate("log(mass) + Abs(descriptor)")
        assert template_key(a)[0] == "UNCANONICALIZABLE"
        assert template_key(a) == template_key(b)
        assert positive_scale_equivalent(a, b)

    def test_h2_secondary_example_does_not_actually_trip_guard_a(self):
        """Correction, not silent acceptance: H2 additionally claimed
        `sqrt(square(1.909*mass - 0.323*descriptor))` -- a fully
        grammar-legal expression (only sqrt/square, no out-of-grammar
        constructs) -- canonicalises to an Abs(...) that trips Guard A.
        Directly re-executed: it does not. This module never asserts
        positivity on `descriptor`, only on `mass`, so
        `sqrt((a*mass - b*descriptor)**2)` never collapses toward Abs in
        the first place (unlike the PRIOR session's blanket-positivity
        design, which is what needed a dedicated guard for exactly this
        shape). Pinned here so a future change that reintroduces
        blanket positivity would be caught by this test turning red."""
        x = parse_candidate("sqrt(square(1.909*mass - 0.323*descriptor))")
        key = template_key(x)
        assert key[0] == "OK", (
            f"expected this fully grammar-legal shape to canonicalise cleanly "
            f"(no Abs, mass-only positivity does not trigger it); got {key[0]}"
        )

    def test_grammar_legal_zoo_route_byte_identical_merges(self):
        """The REALISTIC route to a genuinely grammar-legal (only frozen
        primitives/operators, no Abs/sign/Piecewise needed) UNCANONICALIZABLE
        candidate: exact self-cancellation feeding a division. Two
        independent seeds emitting this exact text -- most plausible for a
        coefficient-free shape like this one, where there is no continuous
        fitted parameter for two independent fits to disagree on -- merge,
        correctly."""
        a = parse_candidate("descriptor/(mass-mass)")
        b = parse_candidate("descriptor/(mass-mass)")
        assert template_key(a)[0] == "UNCANONICALIZABLE"
        assert positive_scale_equivalent(a, b)

    def test_different_text_uncanonicalizable_candidates_do_not_merge(self):
        """The other half of the required check: genuinely DIFFERENT
        UNCANONICALIZABLE candidates -- same degenerate "shape" (division
        by an exact-zero self-cancellation) but a different primitive, or
        the same guard-tripping structure with a different embedded
        coefficient -- must NOT merge. Confirms merging is triggered only
        by literal, total structural identity, never by mere shape
        resemblance (a "coefficient-free structural near-miss" stays
        correctly split). (Note: NOT every syntactic difference survives
        to the fallback key -- see
        `test_self_cancelling_denominator_choice_is_invisible_after_parsing`
        for a case where SymPy's own construction-time arithmetic collapses
        two different source texts before this module ever sees them; the
        cases below were individually checked, by srepr, to genuinely
        remain distinct.)"""
        base = parse_candidate("descriptor/(mass-mass)")
        different_primitive = parse_candidate("descriptor2/(mass-mass)")
        different_shape = parse_candidate("log(mass) + Abs(2*descriptor)")
        same_shape_ref = parse_candidate("log(mass) + Abs(descriptor)")

        assert template_key(base)[0] == "UNCANONICALIZABLE"
        assert template_key(different_primitive)[0] == "UNCANONICALIZABLE"
        assert template_key(base) != template_key(different_primitive)
        assert not positive_scale_equivalent(base, different_primitive)

        assert template_key(different_shape)[0] == "UNCANONICALIZABLE"
        assert template_key(different_shape) != template_key(same_shape_ref)
        assert not positive_scale_equivalent(different_shape, same_shape_ref)

    def test_no_hash_step_left_in_fallback_key(self):
        """Session 6 hardening: the fallback key uses the srepr STRING
        directly, not a hash of it (an earlier version used
        `hashlib.sha256(...).hexdigest()`). Confirms no hashlib import
        remains and that the fallback key's second element is literally
        the srepr text, so two candidates share a fallback key iff their
        srepr strings are exactly, literally equal -- no digest-collision
        question can even arise."""
        import muru.paper_benchmark.identity_contract as ic
        assert not hasattr(ic, "hashlib")
        a = parse_candidate("descriptor/(mass-mass)")
        key = template_key(a)
        assert key[0] == "UNCANONICALIZABLE"
        assert key[1] == sp.srepr(a)

    def test_self_cancelling_denominator_choice_is_invisible_after_parsing(self):
        """A genuinely interesting confirmation, not a bug: `descriptor/
        (mass-mass)` and `descriptor/(descriptor-descriptor)` are DIFFERENT
        source text, but they merge too -- not because of anything this
        module's own key-computation does, but because SymPy's own
        construction-time arithmetic (`X-X -> 0` for ANY symbol X, then
        `Y/0 -> zoo`) collapses both to the LITERALLY IDENTICAL raw parsed
        expression (`Mul(zoo, Symbol('descriptor'))`) before this module's
        `template_key` is ever called -- confirmed directly via `srepr` on
        the raw parse, independent of this module's canonicalisation.
        Mathematically this is arguably correct too: both source texts
        describe the identically-undefined constant `descriptor/0`,
        indistinguishable once realised, regardless of which subtraction
        produced the zero. This reinforces, rather than undermines, "same
        srepr implies genuine sameness": the merge happens upstream of any
        choice this module makes."""
        a = parse_candidate("descriptor/(mass-mass)")
        b = parse_candidate("descriptor/(descriptor-descriptor)")
        assert sp.srepr(a) == sp.srepr(b), "expected SymPy's own parsing to already collapse these"
        assert template_key(a) == template_key(b)

    def test_many_distinct_uncanonicalizable_texts_never_coincidentally_collide(self):
        """Sanity check over a modest batch of genuinely different
        UNCANONICALIZABLE-triggering expressions (verified individually, by
        srepr inspection, to NOT collapse to a shared degenerate form the
        way the self-cancelling-denominator case above does): all fallback
        keys must be pairwise distinct (guaranteed by construction now that
        the key is the literal srepr string, but checked directly rather
        than assumed)."""
        texts = [
            "descriptor/(mass-mass)",
            "distractor/(mass-mass)",
            "correlated_distractor/(mass-mass)",
            "descriptor + descriptor2/(mass-mass)",
            "log(mass) + Abs(descriptor)",
            "log(mass) + Abs(descriptor2)",
            "log(mass) + Abs(2*descriptor)",
            "log(mass) + Abs(distractor)",
            "sqrt(mass) + Abs(mass - descriptor)",
        ]
        exprs = [parse_candidate(t) for t in texts]
        keys = [template_key(e) for e in exprs]
        for k in keys:
            assert k[0] == "UNCANONICALIZABLE", f"expected UNCANONICALIZABLE, got {k[0]}"
        assert len(set(keys)) == len(keys), "unexpected coincidental fallback-key collision"
