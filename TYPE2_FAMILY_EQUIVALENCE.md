# TYPE2_FAMILY_EQUIVALENCE.md

**When two expressions make the same Type 2 empirical claim.**

Frozen by `TYPE2_VALIDATION_PREREGISTRATION.md` before any fresh world exists.
Implemented in `muru.objval.equiv.same_family`.

"Same family" is the load-bearing definition of this study, and a vague one
would let any negative result be talked away. It is therefore a conjunction of
six checkable conditions, each of which can fail on its own, and each of which is
invariant to multiplying a candidate by a positive constant — the only freedom
the collapse model `mu = Phi(E/g(z))` leaves in `g`.

---

## The predicate

Two candidates `a` and `b` are in the same Type 2 family when **all** hold.

| # | Condition | Tolerance | Where it comes from |
|---|---|---|---|
| 1 | both are a usable positive scale over the evaluation domain | ≥ 95% of lattice points positive and finite | `g` is an energy scale; a candidate that goes negative is not one |
| 2 | identical **block-level effective support** | exact set equality | the claim is "which structural slots matter"; blocks per `TYPE2_SELECTION_RULE.md` §6 |
| 3 | same **sign** for every shared block effect | exact | direction of an effect is part of the claim |
| 4 | **scaling exponents** agree per block | **±0.15** | master plan §18.3, the plan's own declared resolution for an exponent claim |
| 5 | **monotonicity** agrees per block over the domain | exact match of the monotone flag | a monotone and a non-monotone dependence are different claims |
| 6 | **dense predictive agreement** up to positive scale | `r ≥ 0.99` and relative RMSE `≤ 0.10` on an independently generated Latin hypercube | master plan §13.5 fingerprinting, relaxed to the Type 2 claim class |

No condition is waived. A candidate carrying an **extra** effective variable
outside the planted support fails condition 2, so "no additional unsupported
variables" is enforced rather than assumed.

## Effective support, not symbolic support

A variable can appear in an expression and move the prediction by nothing. The
support used in conditions 2 and 3 is the **effective** one: variables whose
median elasticity — or, where a variable can be zero, whose additive effect over
one standard deviation expressed as a fraction of the candidate's own magnitude —
exceeds **0.02**. Symbolic support is computed and reported alongside in every
artifact, and where the two differ the difference is printed.

## Scaling exponent

For a candidate `f` and variable `z_j`,

    e_j(z) = (∂f/∂z_j) · z_j / f(z)

estimated by a central multiplicative perturbation of ±0.1% and summarized by its
median over the lattice. For a law `f = c · m^0.5 · (1 + a·h)` this returns
exactly 0.5 in `m`, for every `c > 0` — which is why the exponent, and not the
expression, is the reportable quantity.

At **block** level every member of the block is perturbed together, so the
number returned is the response to a proportional change in molecular size
rather than to one arbitrarily chosen proxy.

## What this predicate deliberately does NOT decide

It does not decide whether the algebraic form is right. Phase 3's tolerances are
kept, unchanged, for that separate question:

| Question | Test | Tolerance |
|---|---|---|
| same Type 2 family? | this file | ±0.15 exponent, 0.10 relative RMSE |
| **functionally equivalent** expressions? | `equiv.functional_class` | `r > 0.999`, relative RMSE `< 0.02` |
| **symbolically equivalent** expressions? | `equiv.functional_class` | relative RMSE `< 1e-6`, or algebraic proof |

The number of distinct **functional** classes inside one reported Type 2 family
is the identifiability measure. One class means the algebraic form is identified.
More than one means it is not, and the honest report is:

> the empirical family, its variable support and its scaling behaviour are
> identified within the experimental domain; the exact algebraic form is not
> identified at the current experimental resolution.

## Non-uniqueness is a permitted outcome

If several **non-equivalent** families satisfy every predictive criterion, the
correct conclusion is that empirical predictive structure exists and the equation
family itself is not uniquely identified. The selection rule reports the
runner-up family and its selection frequency in every world for exactly this
reason. Uniqueness is never forced by construction.

Conversely, if candidate families disagree materially in support, scaling or
extrapolative behaviour, the family is **not** identified and must not be
reported as such.
