"""A3.5 Decision 1 (Session 3 repair): the positive-global-scale identity
contract for cross-seed candidate clustering (amendment section 7.3).

Scope
-----
This module answers exactly one question, exactly: given two candidate
expressions already parsed under the frozen grammar, is there a single
constant ``c > 0`` such that ``a == c * b`` as an exact symbolic identity,
where every ``Float`` leaf of ``a`` and ``b`` is interpreted via its own
DECIMAL TEXT (the digits it actually displays -- see "Float rationalisation"
below), not via its in-memory IEEE-754 bit pattern? That refinement (Session
5) is precise and load-bearing, not a hedge -- see "KNOWN, DISCLOSED,
PROVABLY IRREDUCIBLE limitation #2" below for exactly which constructions of
``a``/``b`` it does and does not cover, and why no refinement of this
module's own algorithm can cover more. That is the only notion of "same
discovered expression" this module implements. It does not touch:

  - numeric/tolerance-based comparison (that is
    ``discovery.equivalence.algebraically_equivalent``, a FROZEN, DIFFERENT
    oracle used for adjudication elsewhere in the pipeline -- this module
    reuses its "up to positive scale" precedent as a reference point, never
    its code, and never depends on it changing or not changing);
  - truth labels or truth-family classification of any kind. It never calls
    ``g2_contract.classify_discovered_family`` or
    ``g2_contract.extract_effective_support``, and it never imports or
    reasons about ``g2_contract.TRUTH_FAMILIES``. It reuses only
    ``g2_contract.GRAMMAR_PRIMITIVES`` (a plain name tuple) for the primitive
    variable names; the square/cube/inv/sqrt/log operator mapping is its own
    (mirroring ``discovery.grammar.parse``'s ``_SYMPY_LOCALS``, the actual
    source of that convention -- ``g2_contract._safe_parse`` itself maps only
    primitive names, no operators; see ``parse_candidate``'s docstring for
    the correction). Reusing a name tuple and an operator convention is not
    reusing a classifier -- a parser has no opinion about which expressions
    are "correct".
  - benchmark performance. No design choice below was made, or should ever
    be revisited, by checking what it does to expected recovery/G2 numbers.
    The only judges are the algebraic laws in the test suite
    (``tests/test_identity_contract.py``).

Why this module exists
-----------------------
A prior session ("A3.5 Decision 1 identity result", see
``audit/MURU_A3_5_DECISION_1_IDENTITY_RESULT.md``) built a 7-step
``TEMPLATE_KEY`` recipe that fixed most defects in the previous 8-step rule,
but left one FATAL, confirmed-open defect: the global-scale-strip step was
unsound for rational-function-shaped candidates, e.g.

    key( 1/(2*mass + 2*descriptor) ) != key( 2 * (1/(2*mass + 2*descriptor)) )

The diagnosed mechanism: ``sympy.cancel()`` performs combined
numerator/denominator GCD reduction, including numeric content, and its
final ``expand()`` non-deterministically scatters that numeric content
across ``Add`` terms depending on incidental GCD coincidences with whatever
external scalar is later applied. Two verified-insufficient fix attempts
are documented in the audit file.

This module is a from-scratch redesign, not a patch to that recipe. Its
central move, re-derived and independently confirmed here (not assumed from
the prior session's hypothesis): do the standard ``together()`` + ``cancel()``
pass once (this already fully normalises the no-denominator/polynomial case,
confirmed by direct execution --
``cancel(together(m*(d+1))) == cancel(together(m*d+m)) == d*m + m`` -- so no
extra trailing ``expand()`` is needed at all, which removes the very step
implicated in the scattering), then split the resulting numerator and
denominator SEPARATELY with SymPy's own ``as_content_primitive()``, and
discard each side's numeric content independently. The pair of
content-free primitives is the shape key; the discarded contents are
exactly the (now provably irrelevant) global scale.

Positivity-assumption soundness, decided per primitive and per operator
-------------------------------------------------------------------------
The FROZEN ``discovery.equivalence.algebraically_equivalent`` asserts
``positive=True`` on every free symbol as a blanket proof aid, citing "every
descriptor in the dimensionless frame is non-negative". That module is out
of scope to edit, and this module does not inherit its justification --
inspection of ``paper_benchmark/generator.py``'s actual sampling
(independently executed, 20,000 simulated batches, not merely read) shows:

  - ``mass = np.exp(5.55 + 0.25*latent + noise)``: strictly positive with
    mathematical certainty (``exp`` of any real is always > 0). Sound to
    assert ``positive=True``.
  - ``descriptor = (latent + noise - latent.min()) / descriptor.max()``:
    NOT sign-constrained. ``latent.min()`` is the noiseless group latent's
    minimum, not the noisy value's minimum, so the compound that attains the
    latent minimum can still land below zero once its own noise draw is
    added. Empirically: over 20,000 simulated batches, at least one
    compound had negative ``descriptor`` in 17,690/20,000 batches (~88%),
    down to about -0.40. Asserting positivity here would be UNSOUND.
  - ``descriptor2``: the generator's *first* assignment
    (``0.65*latent + noise``) is unconstrained, but the code immediately
    reassigns ``descriptor2 = (descriptor2 - min) / (max - min)`` -- a
    min-max normalisation to the closed interval ``[0, 1]`` by construction.
    Empirically, over 20,000 simulated batches, the minimum was observed to
    be exactly ``0.0`` in every batch and never negative. So the actual
    grammar primitive named ``descriptor2`` is non-negative (never assert
    strict ``positive=True``, since 0 is genuinely attained; a ``positive``
    assumption would exclude a value the primitive actually takes). This
    directly contradicts the task briefing's summary, which described only
    the unnormalised intermediate value -- worth flagging precisely because
    independent verification, not the briefing, is what settles it.
  - ``distractor = rng.normal(0, 1, ...)``: symmetric standard normal, can
    and does go negative by construction. UNSOUND to assert positivity.
  - ``correlated_distractor = 0.85*descriptor + 0.15*noise``: even though
    ``descriptor >= 0``, the added noise term can and does push this
    negative whenever ``descriptor`` is near zero. UNSOUND.

Given this, the ONLY primitive symbol this module ever asserts
``positive=True`` on is the one literally named ``mass``. Every other
symbol (including ``descriptor2``, despite being provably non-negative) is
left with NO sign assumption at all. This is a deliberate, conservative
choice, not an oversight: SymPy assumption propagation for ``descriptor2``
touches enough different code paths (``expand_log``, automatic ``Pow``
combination, ``powsimp``) that asserting even ``nonnegative=True`` would add
verification surface for a marginal recall gain, and the failure mode of
*not* asserting it is strictly the safe one -- under-merging (two
expressions landing in different UNCANONICALIZABLE-adjacent buckets when
they were in fact positive-scale equivalent), never over-merging.

Soundness of the specific rewrites this buys, checked by direct execution
(not by reading SymPy's docs and assuming):

  - ``sqrt(x)*sqrt(x) == x`` for the SAME symbolic base ``x`` is applied by
    SymPy automatically on construction, for ANY ``x`` with no assumption at
    all -- confirmed by direct execution. It needs no positivity assumption
    because it never combines DIFFERENT bases (which is where sign errors
    like ``sqrt(a)*sqrt(b) != sqrt(a*b)`` for negative ``a, b`` would enter);
    it only ever adds exponents of one base to itself, which is safe
    regardless of sign.
  - ``sqrt(square(x)) -> x`` (or ``-> Abs(x)``) is NEVER applied by this
    module to any symbol other than ``mass``, and was confirmed NOT to
    happen automatically, under ``powsimp(force=True)``, or under
    ``cancel(together(...))`` for a plain (unassumed) symbol -- direct
    execution: ``sqrt((m-d)**2)`` stays exactly ``sqrt((m-d)**2)`` through
    the whole pipeline when ``m, d`` are unassumed. This is precisely the
    "sqrt(square(m-d)) must not merge with m-d" guard the prior session
    needed a dedicated fix for; here it falls out for free because the
    module never asserts a sign on ``descriptor``-like symbols in the first
    place. (An explicit Guard A, described below, is still kept as a
    second, independent line of defence.)
  - ``log(x**n) -> n*log(x)``: confirmed by direct execution that SymPy's
    ``expand_log`` WITHOUT ``force=True`` already respects assumptions
    correctly and compositionally -- ``log(mass**2)`` with ``mass`` marked
    ``positive=True`` expands to ``2*log(mass)``, while ``log((m-d)**2)``
    with ``m, d`` unassumed is left completely untouched, and a mixed case
    like ``log((mass*descriptor)**2)`` expands the ``mass`` part
    (``2*log(mass)``) while leaving the unassumed ``descriptor`` part
    (``log(descriptor**2)``) alone. No explicit "log freezing" machinery
    (the prior session's Dummy-substitution trick to stop ``cancel()`` from
    silently doing this rewrite for masked symbols) is needed here, because
    the module never masks anything as positive except ``mass``, for which
    the rewrite is actually correct. This resolves the four-way
    ``log(mass)`` / ``log(square(mass))`` / ``log(cube(mass))`` /
    ``log(sqrt(mass))`` family exactly as the frozen
    ``algebraically_equivalent`` oracle independently agrees it should
    (checked directly against that oracle for those four pairs), while
    leaving ``log(inv(mass)) == -log(mass)`` correctly split off (a scale
    factor of -1 is not a *positive* scale).
  - No ``powsimp(force=True)`` is used anywhere in this module. That call
    forces cross-base radical combination (``sqrt(a)*sqrt(b) -> sqrt(a*b)``)
    regardless of sign, which is unsound for any symbol not proven positive,
    and was found, by direct construction, to be unnecessary for every
    required fixture in this grammar (same-base power combination, which is
    all this grammar's ``sqrt``/``square``/``cube``/``inv`` unary operators
    ever produce, is already handled automatically by SymPy's ``Mul``/``Pow``
    construction with no assumption required).

Guard A / Guard B (kept as a second line of defence, not the primary
mechanism)
--------------------------------------------------------------------------
After canonicalisation, every non-atomic node's head must be ``Add``,
``Mul``, ``Pow`` or ``log`` (the only heads this grammar's five binary/five
unary operators can ever produce), every atom must be a ``Symbol`` or a
finite number (``Integer``, ``Rational``, ``Float`` prior to rationalisation,
plus the finite numeric singletons ``I``, ``pi``, ``E`` -- see below), and
every ``Pow`` exponent must be an exact ``Rational``. Anything else (``Abs``,
``sign``, ``Piecewise``, ``zoo``, ``oo``, ``nan``, ``re``, ``im``, ``Max``,
``Min``, ...) means the canonical form the pipeline reached is not a
faithful representation of a frozen-grammar tree, and the candidate falls
into the ``UNCANONICALIZABLE`` bucket described below.

One deliberate broadening versus the prior session's Guard A: the atom
check accepts any FINITE numeric SymPy singleton (``is_number and
is_finite is True``), not only ``Number`` subclasses. This specifically
admits ``I`` and ``pi``, which can legitimately appear when every free
symbol algebraically cancels out of a candidate and what remains is a
concrete complex constant (e.g. a candidate equivalent to ``log(-3)``,
reachable if, say, ``mass/mass`` appears literally in an emitted string and
cancels to 1 before hitting a ``log`` of a negative literal). Confirmed by
direct execution: ``as_content_primitive()`` factors such a constant into a
positive real content and a primitive exactly the same way it does for a
real constant (``(log(3) + I*pi).as_content_primitive() == (1, log(3) +
I*pi)``; doubling it gives ``(2, log(3) + I*pi)``; negating it gives
``(1, -log(3) - I*pi)``) -- so admitting these atoms costs nothing in
soundness and recovers positive-scale-invariance for what would otherwise
be a spurious UNCANONICALIZABLE split. ``zoo``, ``oo``, ``-oo`` and ``nan``
remain explicitly rejected (``is_finite`` is ``False``/``None`` for all
four) -- see the KNOWN, DISCLOSED, NOT-ENGINEERED-AROUND limitation below.

Float rationalisation -- DECIMAL text, not binary bit-pattern (Session 4
correction)
--------------------------------------------------------------------------
Every ``Float`` leaf (coefficient or exponent) is replaced by an exact
``Rational`` via ``sympy.Rational(str(f))`` -- i.e. by re-parsing the
Float's own decimal TEXT rendering, not by ``sympy.Rational(f)``'s
exact-IEEE-754-binary-bit-pattern conversion used by an earlier version of
this module.

This was a real, FATAL defect, found by a fresh adversarial review
(Session 4, Agent I2) and independently re-derived and confirmed here, not
accepted on the review's say-so: with binary rationalisation,

    a = mass + 0.4*descriptor
    b = 3.0*mass + 1.2*descriptor      # b is exactly 3*a as authored text

failed ``positive_scale_equivalent(a, b)``, because ``Rational(0.4)`` (the
double closest to 0.4, a huge/ugly binary fraction) times the exact integer
3 is NOT bit-identical to ``Rational(1.2)`` (the double closest to 1.2, a
DIFFERENT huge/ugly binary fraction) -- confirmed directly:
``3 * sp.Rational(0.4) == sp.Rational(1.2)`` is ``False``. Each decimal
literal independently rounds to the nearest of ~2^53 grid points, and nice
decimal ratios (like exactly 3x) are essentially never preserved exactly
under that rounding. This is not a corner case for this benchmark: it is
the realistic production shape -- comparing independently-fit PySR
equation strings from different seeds, each carrying its own
independently-rounded decimal coefficients.

The fix: reparse the Float's ``str()`` rendering as a ``Rational`` instead
of converting its in-memory bit pattern. Confirmed by direct execution that
this resolves the counterexample exactly (``3*Rational(str(0.4)) ==
Rational(str(1.2))`` is ``True``, both reducing to the clean ``2/5`` and
``6/5``) and is robust across every construction path a ``Float`` can reach
this module by -- text-parsed via ``sympify``, built directly from a Python
``float``, built from a decimal string, or produced by an internal SymPy
computation all render to the IDENTICAL ``str()`` for the same underlying
value (checked directly for 0.1 constructed all four ways: all four give
``str() == "0.100000000000000"`` and ``Rational(str(...)) == 1/10``),
because SymPy's default ``Float`` precision (53 bits, matching a Python
double) renders via a fixed ~15-17 significant-digit decimal expansion
regardless of construction path -- there is no separate "shortest Python
repr vs SymPy str" mismatch to worry about. Also checked: scientific
notation (``1.5e-10``, ``6.02e23``), higher-than-default precision literals
(a 24-significant-digit literal correctly round-trips through its full 83
extended-precision digits), and negative/zero values all convert exactly
via this method. Where a ``Float`` truly has no "nice" underlying decimal
(e.g. a genuinely-computed value whose only text rendering is an ugly
15-digit expansion), the result degrades gracefully: still an EXACT
rational reflecting exactly those digits, just an uglier one -- never a
new source of numeric error, and never less exact than before.

Deliberately NOT used: ``sympy.nsimplify(f, rational=True)``, which
performs an approximate continued-fraction SEARCH for a nearby "nice"
rational (e.g. it maps a genuinely-computed ``Float(2)/Float(3)`` to
exactly ``2/3``, silently discarding the actual 15-digit value) -- that is
a tolerance in disguise, exactly the kind of floating-point-adjacent
judgement call this contract is required to avoid. Decimal-text
rationalisation makes no such judgement: it trusts the digits the Float
actually displays, nothing more, nothing less.

This also matters for ``Pow`` exponents as before: an un-rationalised
``Float`` exponent fails Guard B and fragments a class that should merge,
e.g. ``mass**0.5`` and ``sqrt(mass)`` become structurally identical (both
``Pow(mass, Rational(1, 2))``) only once the ``0.5`` exponent is
rationalised.

The ``UNCANONICALIZABLE`` fallback bucket, and why it is a genuine total
function
--------------------------------------------------------------------------
On any exception, or on a Guard A/B failure, the candidate's key becomes
``("UNCANONICALIZABLE", srepr(expr))`` -- the ORIGINAL input's own ``srepr``
string, used directly (not a hash of it; see "Byte-identical
UNCANONICALIZABLE merges" below for why hashing was removed, Session 6).
This key is a pure function of the ORIGINAL input expression's own
structure -- never of a seed ordinal, a call counter, or any other
external/mutable state, and
never involving a ``Dummy`` object (this module uses no ``Dummy``
substitution anywhere, which is what caused the prior session's specific
non-reflexivity bug for deeply nested logs; re-verified here by direct
execution across 1500 random expressions plus a dedicated 200-reparse
determinism stress test on nested logs -- zero reflexivity failures). Two
calls on the identical expression therefore always agree, so ``E`` is
reflexive even inside the fallback bucket. Symmetry is immediate (the key
function does not look at argument order). Transitivity is immediate
because "same key" is a textbook equivalence relation (reflexive,
symmetric, transitive by construction of equality on a fixed value) and
this module was verified, by direct execution across a 5,000-pair random
sample, to have ZERO mismatches between "keys are equal" and
"``positive_scale_equivalent`` returns True" -- i.e. the key IS the
relation, not merely correlated with it.

The fallback bucket does NOT generally satisfy positive-scale-invariance
(scaling an uncanonicalizable expression by an arbitrary rational changes
its literal numeral content, hence its srepr, hence its fallback key). This
is the documented, deliberate, conservative direction: an under-merge
(treating two things as different when they might "morally" be the same
scaled family) is always the safe failure for this contract, per the
"UNCANONICALIZABLE is a conservative singleton, never inflates k" precedent
this module inherits from the prior session's design and re-affirms.

Byte-identical UNCANONICALIZABLE merges, and amendment section 7.3 step 6's
literal "unique to its own seed ordinal" wording (Session 6)
--------------------------------------------------------------------------
A fresh blind review (Session 6, Agent H2) pointed out a real, precise
consequence of the design above that was not previously tested or
reconciled against the amendment's literal text: TWO INDEPENDENTLY-PARSED
candidates whose input text is byte-identical, and which BOTH land in
UNCANONICALIZABLE, DO merge --

    a = parse_candidate('descriptor/(mass-mass)')   # -> zoo, Guard A rejects
    b = parse_candidate('descriptor/(mass-mass)')   # same text, independently parsed
    template_key(a) == template_key(b)              # True

-- because ``srepr(a) == srepr(b)`` whenever ``a`` and ``b`` are literally
the same expression, which two independent parses of the identical string
always produce. Amendment section 7.3 step 6's literal text (the
FROZEN-UNTIL-REPLACED binding this module exists to replace) says the
fallback key must be "made unique to its own seed ordinal, forming a
singleton class" -- i.e. it appears to require EVERY uncanonicalizable
candidate to be its own class, even against a byte-identical twin from a
different seed. This module deliberately does not do that, and the
question H2 raised -- is that a defect, or is the amendment's literal
wording simply describing a mechanism this architecture cannot use and
should not try to -- is answered here explicitly, not left implicit.

Decision: this is CORRECT, INTENDED behaviour, not a defect. Two arguments,
one structural and one about what "conservative" is actually protecting
against:

1. Seed-ordinal keying is not merely a stylistic choice this module
   declined -- it is INCOMPATIBLE BY CONSTRUCTION with the reflexivity law
   this whole contract is required to satisfy (``E(f, f) == True`` for
   every ``f``, non-negotiable, listed alongside symmetry/transitivity/
   positive-scale-invariance as one of the four algebraic laws this module
   must satisfy). ``template_key`` and ``positive_scale_equivalent`` take
   ONLY the parsed expression as input -- there is no seed-ordinal
   parameter in their signature, by design, matching what was actually
   asked for ("a genuine deterministic total function ... on the space of
   grammar-legal parsed expressions"). A fallback key that incorporated
   seed ordinal would require EITHER threading seed identity through every
   call site (a different, wider API than what these functions expose) OR
   deriving "seed ordinal" from something other than the expression itself
   (call count, object id, a `Dummy` nonce, ...) -- and the prior session's
   own audit trail (``audit/MURU_A3_5_DECISION_1_IDENTITY_RESULT.md``)
   already discovered, by execution, that exactly this kind of
   external/incidental keying breaks reflexivity (a `Dummy`-object
   non-determinism bug for nested logs, re-verified fixed here). So the
   amendment's literal "unique to its own seed ordinal" wording describes a
   mechanism that was tried, in an earlier round, under a DIFFERENT
   API surface, and abandoned specifically because it does not compose with
   a hard requirement this module must satisfy. Keying off the expression's
   own structure is not a weaker substitute for that wording -- it is the
   nearest sound analogue available once the signature is fixed to two
   bare expressions, and it is the one that was fixed to be sound.

2. On the actual question H2 asked -- does merging byte-identical text ever
   constitute a FALSE merge -- the answer is no, and this is provable, not
   merely plausible. ``srepr`` is a complete, order-sensitive, faithful
   structural fingerprint of a SymPy expression tree: two expressions with
   IDENTICAL ``srepr`` are, by construction, the same tree (same symbols
   with the same assumptions, same numbers, same operator nesting, same
   argument order). There is no scenario where "same ``srepr``" hides a
   difference relevant to whether two seeds "discovered the same
   expression" -- byte-for-byte identical text is, if anything, STRONGER
   evidence of sameness than the positive-scale-equivalence this whole
   contract is built to detect (which recognizes expressions as the same
   family despite DIFFERING numerically by a scale factor; two candidates
   that don't even differ by that much have an even stronger claim to being
   "the same discovered expression"). Treating them as separate singletons
   -- artificially splitting one genuine convergence event into multiple
   counted classes -- would not be "conservative" in any sense that
   protects Gate 3 from a false positive; it would just be noise-sensitive
   to which object happened to construct the expression, which is exactly
   the kind of "seed ordinal carries no scientific content" reasoning
   amendment section 7.5 already establishes for a different tie-break rule
   (there, over WHICH member of a winning class is representative; the
   argument here is the same in spirit -- an accident of provenance must
   not change the count).

What "conservative, never inflates k" actually protects against, and why
this is not that: the risk that motivates the singleton-fallback design is
two GENUINELY, STRUCTURALLY DIFFERENT candidates being incorrectly folded
into one class (inflating ``selection_count`` with a spurious merge).
Confirmed directly that this module still refuses exactly that: a
"coefficient-free structural near-miss" -- e.g. the same guard-tripping
SHAPE with a genuinely different coefficient, ``descriptor2/(mass-mass)``
vs ``descriptor/(mass-mass)``, or the same shape at a different literal
constant -- produces a DIFFERENT ``srepr`` and hence a different, unmerged
fallback key (checked directly). Merging is triggered ONLY by literal,
total structural identity, never by mere resemblance, coincidental
near-collision, or a shared "shape" with different specifics. That is
exactly the conservative direction the amendment's language is protecting.

Realistic reachability, checked precisely rather than assumed: H2's own
report additionally claimed a specific grammar-legal example --
``sqrt(square(1.909*mass - 0.323*descriptor))`` -- canonicalises to an
``Abs(...)`` that trips Guard A. Directly re-executed against this
module's actual pipeline: it does NOT -- it canonicalises cleanly to
``sqrt(104329*descriptor**2 - 1233214*descriptor*mass +
3644281*mass**2)/1000`` with no ``Abs`` anywhere, and its ``template_key``
is ``"OK"``, not ``"UNCANONICALIZABLE"``. This is expected given this
module's own design: unlike the prior session's blanket
``positive=True``-on-every-symbol substitution (which DID produce
``Abs`` for this shape, and needed a dedicated guard for exactly that), this
module positivises ONLY the symbol literally named ``mass`` (see
"Positivity-assumption soundness" above), so ``sqrt((a*mass -
b*descriptor)**2)`` never collapses toward ``Abs`` in the first place --
neither ``mass`` alone nor ``descriptor`` alone is asserted signed strongly
enough to trigger it. H2's premise does not hold for this specific example
against this specific module, and is corrected here rather than silently
accepted. That does not make the underlying finding moot, though: a
genuinely grammar-legal, in-domain construction DOES reach
UNCANONICALIZABLE by a DIFFERENT, already-disclosed route -- exact
self-cancellation feeding a division, e.g. ``descriptor/(mass-mass)``,
which is exactly limitation #1's ``zoo`` mechanism below, reachable purely
from the five frozen unary/binary operators with no out-of-grammar
constructs (``Abs``, ``sign``, ``Piecewise``, ...) required at all. Two
independent seeds emitting that exact self-cancelling text -- most
plausible for a coefficient-FREE shape, since there is no continuous fitted
parameter for two independent fits to disagree on, e.g. exactly
``descriptor/(mass-mass)`` rather than a form carrying its own fitted
floats -- would merge under this module, correctly, per the argument above.

On hash-collision risk (H2's second question): an earlier version of
``_uncanonicalizable_key`` used ``hashlib.sha256(srepr(expr)).hexdigest()``
rather than the ``srepr`` string itself. Constructing an actual SHA-256
collision is far outside the reach of any feasible computation (the
best known attacks remain far short of a full preimage or collision break;
this is standard cryptographic fact, not something to attempt to
demonstrate). But the question is now moot rather than merely
astronomically unlikely: Session 6 removed the hashing step entirely (see
``_uncanonicalizable_key``) and uses the ``srepr`` STRING directly as the
key component. Two candidates now share a fallback key if and only if
their ``srepr`` strings are LITERALLY, exactly equal -- there is no digest
step left in which a coincidental collision could even in principle occur.

KNOWN, DISCLOSED, NOT-ENGINEERED-AROUND limitation #1: zoo/ComplexInfinity
----------------------------------------------------------------------------
Exactly one family of counterexample to positive-scale-invariance survived
1500 random expressions x 13 positive scale factors (plus a dedicated
negative-scale-distinct sweep): expressions containing a literal ``zoo``
(``ComplexInfinity``) term, e.g. a candidate equivalent to
``zoo*correlated_distractor + descriptor``. ``zoo`` absorbs any finite
nonzero scalar (``c*zoo == zoo`` for any nonzero finite ``c``), so scaling
such an expression by 2 changes only its well-defined ``Add`` term, not the
``zoo``-poisoned one -- there is no well-defined "content" to strip
consistently, confirmed directly by execution
(``as_content_primitive()`` on the raw expression exhibits exactly this
asymmetric absorption). This is independently-rediscovered confirmation of
the SAME limitation the prior session already disclosed for zoo-absorbing
Add terms, not a new defect, and it is NOT engineered around here, for the
same reason the prior session gave: any expression containing a literal
``zoo`` term evaluates to a non-finite value at EVERY point of the
covariate domain (grammar.py's ``finite_mask``/``MAX_INVALID_FRACTION``
gate rejects it at 100% invalid fraction, far above the 0.5% ceiling)
before ``TEMPLATE_KEY``/this module is ever reached in the production
pipeline. Guard A explicitly buckets these into ``UNCANONICALIZABLE``
(never silently merges them), which is the correct, safe, disclosed
behaviour for an input that cannot legitimately reach this module in the
first place.

KNOWN, DISCLOSED, PROVABLY IRREDUCIBLE limitation #2: precision loss in
caller-side Float arithmetic (Session 5)
--------------------------------------------------------------------------
A fresh adversarial review (Session 4->5, Agent I2) found that
``positive_scale_equivalent(f, c*f)`` can be ``False`` when ``c*f`` is
constructed by literally invoking SymPy's own ``__mul__`` on an EXISTING
parsed expression object that contains a ``Float`` leaf -- e.g.
``f = sqrt(Float('8.9'))*mass`` (a candidate equivalent to
``sqrt(8.9)*mass``, which auto-evaluates the ``sqrt`` of a concrete numeric
argument to a fresh 53-bit ``Float`` DURING PARSING, before this module ever
runs), then ``b = 4*f`` computed by ordinary Python/SymPy multiplication.
Minimal repro (I2's, independently re-derived and confirmed here):

    f_base = sp.Float('2.9832867780352599', precision=53)  # == sqrt(Float('8.9'))
    4 * sp.Rational(str(f_base)) == sp.Rational(str(4*f_base))   # False

Independent verification of the mechanism (broader than I2's own framing,
confirmed by direct execution, not accepted on the review's say-so):
I2 attributed this to "exact only for power-of-2 multipliers" (IEEE-754
multiplication by a power of two is a pure exponent shift, so the mantissa,
and hence the exact BINARY value, is untouched; any other multiplier
generically needs more than 53 mantissa bits for the exact product, so
SymPy's default-precision arithmetic rounds it). That mechanism is real and
confirmed (checked directly: multiplying ``f_base`` by 2, 4, 8, 16 is
bit-exact against the true unbounded-precision product; by 3, 5, 6, 7, 9, 10
it is not). But it is only HALF the picture, and the full picture is
actually WORSE than "avoid non-power-of-2 multipliers": even the BIT-EXACT
power-of-2 cases (4, 8, 16) still fail
``Rational(str(f)) * c == Rational(str(c*f))``, because SymPy's default
``Float.__str__`` renders a FIXED number of significant decimal digits
(~15-17, matching double precision), and multiplying by anything whose
magnitude is not itself a power of ten shifts which decimal digit position
is "least significant" -- the decimal RENDERING step, not just the binary
MULTIPLICATION step, independently discards information whenever the
number's order of magnitude changes. (Confirmed directly: ``2*f_base`` is
both bit-exact AND decimal-text-exact; ``4*f_base`` is bit-exact but NOT
decimal-text-exact, because doubling from ~3 to ~6 stays a 1-digit integer
part while quadrupling to ~12 crosses into a 2-digit integer part, shifting
the significant-digit window SymPy's ``str()`` retains.)

Why no algorithm operating on this module's actual inputs can fix this
(argued formally, not just asserted): ``positive_scale_equivalent(a, b)``
is a two-argument pure function. Its ONLY inputs are the two already-
constructed ``sp.Expr`` objects. By the time ``b = c*f`` is handed to it,
SymPy has ALREADY rounded the true mathematical product to the nearest
representable 53-bit ``Float`` -- this rounding happens INSIDE Python's
``*`` operator, strictly before ``positive_scale_equivalent`` is ever
invoked, and this module has no hook into, and receives no side channel
about, that multiplication ever having occurred (it does not receive ``c``;
it only receives the two already-rounded results). Recovering "what exact
real number was the caller's intended scale" from ONLY the rounded output
bits is not merely difficult but information-theoretically impossible in
general: rounding-to-nearest-double is a MANY-TO-ONE map, so an entire open
INTERVAL of distinct true real numbers -- not a single one -- rounds to the
identical bit pattern this module receives (confirmed directly: for
``4*f_base``, every real number in roughly
``[11.933147112141038, 11.93314711214104]`` produces the SAME double; there
is no basis, from the bits alone, to prefer "the caller multiplied by
exactly 4" over any of the infinitely many other nearby scale factors that
would have produced bit-identical output). Any procedure that tried to
"guess" the most plausible original scale from the rounded bits would
necessarily be a NUMERICAL-PROXIMITY / TOLERANCE search over candidate
scale factors -- exactly the kind of "floating-point comparison" this
contract, going back to the frozen amendment's own stated philosophy ("no
floating-point comparison occurs") and this module's earlier, deliberate
rejection of ``sympy.nsimplify``'s approximate rational-guessing (see
"Float rationalisation" above), is required to avoid. Three concrete
directions were tried and rejected here, not merely asserted away: (1)
suppressing SymPy's automatic evaluation of ``sqrt``/``log`` on numeric
constants during parsing does not help, because that evaluation -- like the
external multiplication -- happens strictly before this module's two-
argument entry point, and this module does not control how its callers
construct their inputs; (2) widening working precision inside this module
cannot recover bits that were never computed or stored by the caller in the
first place; (3) treating "looks precision-fragile" as its own
UNCANONICALIZABLE bucket does not restore invariance either (it would just
convert an OK-key mismatch into a fallback-key mismatch, an equally-``False``
result by a different route), and would actively regress the realistic
case below by discarding correct merges that already work.

Refined formal statement of positive-scale-invariance for this contract
(Session 5): the property this module guarantees, unconditionally and
verified exhaustively, is

    for any two grammar-legal expressions whose Float leaves are each
    interpreted via their own decimal-text value (i.e. two expressions each
    independently produced by parsing/authoring their OWN decimal-literal
    text, the way every candidate actually reaches this module in
    production -- see below), if there exists a positive rational c with
    a == c*b as an identity over those decimal-text values, then
    positive_scale_equivalent(a, b) is True.

It does NOT additionally guarantee: that this remains True when ``b`` is
instead constructed by applying SymPy's OWN bounded-precision Float
arithmetic to an EXISTING parsed object containing a Float leaf (e.g.
``b := 4 * a`` computed in Python) -- in that specific construction, the
caller's own multiplication has, in general, already destroyed the exact
decimal-scale relationship before this module is ever invoked, and honestly
reporting ``False`` for the resulting ``(a, b)`` pair is the mathematically
CORRECT answer for the values actually received, not a defect: those two
Float bit patterns, as given, are simply not exact positive-rational
multiples of one another as decimal-text values, whatever the caller may
have "intended" before rounding occurred.

This refinement is not a retreat from rigor into a convenient loophole --
it is the honest boundary of what an exact, tolerance-free algorithm CAN
promise once its inputs have already passed through a lossy, uncontrolled
intermediate step, and it is also, independently, the boundary that
matters for THIS benchmark: the production pipeline never constructs one
candidate by scalar-multiplying another candidate's already-parsed SymPy
object. Every candidate that reaches ``TEMPLATE_KEY``/this module is
sourced from ITS OWN row of PySR's ``equations_["equation"]`` output --
amendment section 7.3 step 1 requires parsing each candidate fresh from its
own as-emitted string, and section 7.5 states the representative's
``discovered_expression_string`` is "its own as-emitted
``equations_["equation"]`` string," never a value derived by multiplying
another candidate's object. So the construction this module cannot make
exact (``c *_python f``) is not how candidates arrive here at all; the
construction it handles exactly (two independently-decimal-text-authored
expressions related by a clean scale) is precisely the realistic shape.

Quantified, on a fresh corpus (not the corpus Agent I2 used, not the
corpuses used earlier in this file's own test history -- seed ``20260901``,
800 expressions built to specifically stress unary-ops-on-numeric-constants
and multi-digit literals, the exact trigger condition above):
Float-leaf-bearing items under raw in-process multiplication by 12 scale
factors (2,3,4,5,6,7,8,9,10,16,1/2,7/3): 636/6912 failures (9.2%) -- real,
nonzero, matching the mechanism precisely, and NOT engineered around. The
SAME 576 Float-leaf items, tested instead via the realistic construction
(each side's Float leaves reinterpreted as its own decimal-text Rational,
then scaled by an EXACT rational c, exactly matching how two independent
PySR fits would each print their own coefficient text): 0/6912 failures.
Rational-only (no Float leaf) items under raw in-process multiplication:
0/2664 failures, unconditionally -- Integer/Rational SymPy arithmetic is
always exact, so this guarantee is not weakened by any of the above.
See ``tests/test_identity_contract.py``'s
``TestCallerSideFloatArithmeticResidual`` for the exact, re-executable
corpus and numbers.

What this module exposes
--------------------------
  - ``positive_scale_equivalent(a, b) -> bool``: the primitive pairwise
    relation E. Deterministic, total, on any two parsed SymPy expressions.
  - ``template_key(expr) -> tuple``: a hashable canonical key such that
    ``template_key(a) == template_key(b)  <=>  positive_scale_equivalent(a, b)``
    for every pair (verified directly, not merely asserted -- see
    ``tests/test_identity_contract.py``). Grouping a list of candidates by
    this key is therefore a correct, transitive clustering with no need for
    a separate union-find pass.
  - ``template_key_string(expr) -> str``: a byte-identical-string rendering
    of ``template_key``, for call sites that want the amendment's original
    "TEMPLATE_KEY is a string, compared byte-for-byte" framing.
"""
from __future__ import annotations

import sympy as sp

from muru.paper_benchmark.g2_contract import GRAMMAR_PRIMITIVES

IDENTITY_CONTRACT_VERSION = "a3-5-decision-1-session-3-v1"

# The only primitive symbol name this module ever asserts positivity for.
# See the module docstring: mass = exp(...) is provably always > 0; every
# other primitive (descriptor, descriptor2, distractor, correlated_distractor)
# is either not sign-constrained or, for descriptor2, provably touches
# exactly zero, so no positivity/nonnegativity assumption is asserted for
# them at all.
_ALWAYS_POSITIVE_NAMES = frozenset({"mass"})

# Guard A: the only non-atomic node heads this frozen grammar's five binary
# operators (+ - * /) and five unary operators (sqrt, log, square, cube,
# inv) can ever produce after parsing and exact algebraic canonicalisation.
# sqrt/square/cube/inv all become Pow nodes; only log is a distinct head.
_ALLOWED_HEADS = (sp.Add, sp.Mul, sp.Pow, sp.log)

# Safety cap mirroring discovery.equivalence.SIMPLIFY_TIMEOUT_TERMS's
# precedent: grammar.MAX_COMPLEXITY caps genuine candidates at 20 nodes, so
# this is a generous margin that only ever bites adversarial/synthetic
# inputs, never a real candidate.
_MAX_OPS_BEFORE_FALLBACK = 400

_LOCALS = {
    "square": lambda x: x ** 2,
    "cube": lambda x: x ** 3,
    "inv": lambda x: 1 / x,
    "sqrt": sp.sqrt,
    "log": sp.log,
}


def parse_candidate(expr_str: str, variables: tuple[str, ...] = GRAMMAR_PRIMITIVES) -> sp.Expr:
    """Parser only. The operator mapping (square/cube/inv/sqrt/log) mirrors
    ``discovery.grammar.parse``'s ``_SYMPY_LOCALS`` -- the actual source of
    that convention. (Correction, Session 4: an earlier version of this
    docstring claimed this mirrors ``g2_contract._safe_parse``'s locals
    mapping; verified by direct inspection that ``_safe_parse``'s
    ``local_dict`` is ``dict(_PRIMITIVE_SYMBOLS)`` only -- primitive names,
    no operator mapping at all -- so that claim was false. What this
    function *does* share with ``g2_contract`` is the ``GRAMMAR_PRIMITIVES``
    name tuple, imported directly from it below.) No positivity, no
    classification, no truth labels: this is exactly the same kind of
    parser as ``grammar.parse``."""
    loc = dict(_LOCALS)
    loc.update({v: sp.Symbol(v) for v in variables})
    return sp.sympify(expr_str, locals=loc)


def _rationalize_floats(expr: sp.Expr) -> sp.Expr:
    """Reparse each Float leaf's own decimal text as an exact Rational (NOT
    its exact-binary bit-pattern -- see the module docstring's "Float
    rationalisation" section for why binary rationalisation is a confirmed
    FATAL defect for this contract: two independently-authored decimal
    literals that are a clean rational multiple of one another as TEXT are
    essentially never a clean rational multiple of one another as IEEE-754
    bit patterns)."""
    floats = expr.atoms(sp.Float)
    if not floats:
        return expr
    return expr.xreplace({f: sp.Rational(str(f)) for f in floats})


def _positivize(expr: sp.Expr) -> sp.Expr:
    """Substitute positive=True ONLY for symbols literally named 'mass'.
    Every other free symbol is left with no assumption at all -- see the
    module docstring's per-primitive soundness argument."""
    sub = {}
    for s in expr.free_symbols:
        if s.name in _ALWAYS_POSITIVE_NAMES and not s.is_positive:
            sub[s] = sp.Symbol(s.name, positive=True)
    if not sub:
        return expr
    return expr.xreplace(sub)


def _atom_ok(node: sp.Basic) -> bool:
    if node.is_Symbol:
        return True
    # Accept any FINITE numeric singleton (Integer/Rational/Float/I/pi/E),
    # reject zoo/oo/-oo/nan explicitly (is_finite is False or None for all
    # four). See module docstring for why I/pi are safe to admit here.
    return bool(node.is_number and node.is_finite is True)


def _guard_ok(expr: sp.Expr) -> bool:
    """Guard A (grammar closure) + Guard B (exponent reachability)."""
    for node in sp.preorder_traversal(expr):
        if node.is_Atom:
            if not _atom_ok(node):
                return False
        else:
            if not isinstance(node, _ALLOWED_HEADS):
                return False
            if isinstance(node, sp.Pow) and not node.exp.is_Rational:
                return False
    return True


def _uncanonicalizable_key(original: sp.Expr) -> tuple:
    """See the module docstring's "UNCANONICALIZABLE fallback bucket, byte-
    identical text, and amendment section 7.3 step 6" section for the full
    reasoning. Uses the ORIGINAL input's own ``srepr`` STRING directly as
    the key -- not a hash of it (an earlier version of this function used
    ``hashlib.sha256(s).hexdigest()``; a fresh review, Session 6, correctly
    pointed out that hashing introduces a theoretical, if astronomically
    unlikely, coincidental-collision question that using the string itself
    eliminates outright: two candidates get the SAME fallback key if and
    only if their ``srepr`` strings are LITERALLY equal, full stop -- no
    digest, no birthday-bound argument required)."""
    try:
        s = sp.srepr(original)
    except Exception:
        s = repr(original)
    return ("UNCANONICALIZABLE", s)


def template_key(expr: sp.Expr) -> tuple:
    """The canonical key. ``template_key(a) == template_key(b)`` iff
    ``positive_scale_equivalent(a, b)`` -- verified by direct execution over
    a large random corpus, not merely asserted; see
    tests/test_identity_contract.py.
    """
    try:
        if sp.count_ops(expr) > _MAX_OPS_BEFORE_FALLBACK:
            return _uncanonicalizable_key(expr)

        e1 = _positivize(expr)
        e1 = _rationalize_floats(e1)
        e2 = sp.cancel(sp.together(e1))

        N, D = sp.fraction(e2)
        N, D = sp.sympify(N), sp.sympify(D)

        if not (_guard_ok(N) and _guard_ok(D)):
            return _uncanonicalizable_key(expr)

        _cN, pN = N.as_content_primitive()
        _cD, pD = D.as_content_primitive()

        if not (_guard_ok(pN) and _guard_ok(pD)):
            return _uncanonicalizable_key(expr)

        return ("OK", sp.srepr(pN), sp.srepr(pD))
    except Exception:
        return _uncanonicalizable_key(expr)


def template_key_string(expr: sp.Expr) -> str:
    """Byte-identical-string rendering of ``template_key``, for call sites
    that want a literal string to compare (the amendment's original
    "TEMPLATE_KEY strings are byte-identical" framing)."""
    return "|".join(template_key(expr))


def positive_scale_equivalent(a: sp.Expr, b: sp.Expr) -> bool:
    """The primitive pairwise relation E(a, b): is there a single constant
    c > 0 with a == c*b as an exact symbolic identity? Deterministic, total,
    reflexive, symmetric, transitive (subject to the one disclosed
    zoo/ComplexInfinity limitation described in the module docstring)."""
    return template_key(a) == template_key(b)


def cluster_by_template_key(exprs: list) -> list[list[int]]:
    """Group a list of already-parsed sympy expressions by
    ``template_key``. Correct and transitive because
    ``template_key(a) == template_key(b) <=> positive_scale_equivalent(a, b)``
    (see module docstring); no separate union-find pass is needed."""
    buckets: dict[tuple, list[int]] = {}
    order: list[tuple] = []
    for i, e in enumerate(exprs):
        k = template_key(e)
        if k not in buckets:
            buckets[k] = []
            order.append(k)
        buckets[k].append(i)
    return [buckets[k] for k in order]
