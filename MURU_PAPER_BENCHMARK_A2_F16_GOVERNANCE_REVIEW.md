# MURU paper benchmark — A2 F16 consistency review: GOVERNANCE REVIEW REQUIRED

This document is **not** an amendment and **not** a content freeze. It is a
pre-execution governance record. No generator, registry, truth, artifact,
denominator, threshold, or A1 rule was modified. The effective benchmark content
freeze remains `2ac86c5`.

## A2.0 Record

| Field | Value |
|---|---|
| Original content freeze V1 | `d94d2c9` ("Prepare prospective paper benchmark content freeze") |
| Adequacy amendment A1 | `2ac86c5` ("Amendment A1: bind the M0/M1/M2/M3 adequacy decision rule") |
| Review branch | `science/muru-paper-benchmark-f16-amendment`, created from `2ac86c5` |
| Worktree | `.claude/worktrees/muru-paper-benchmark-f16-amendment` |
| Outcome | **GOVERNANCE REVIEW REQUIRED** — halted at repair section 5 (M3 parameter generation) |
| Tracked changes | this document only |

**Contamination status.** No Development scientific outcome and no Held-out
outcome was executed, scored, enumerated, parsed, summarised, or inspected. No
benchmark case was generated. Only frozen specification documents, the registry,
the generator source, the A1 model definitions, and two already-tracked metadata
manifests (`paper_benchmark_case_manifest.json` counts and applicability fields;
`paper_benchmark_truth_manifest.json` top-level keys) were read. One
self-contained numerical script exercised the deviation algebra on dummy arrays
that are not benchmark inputs.

---

## A2.1 The declared F16 truth is unambiguous

F16's adequacy truth is declared `M1+M2+M3` in two independently frozen places,
both byte-identical at `d94d2c9` and `2ac86c5`:

- `src/muru/paper_benchmark/registry.py:150` —
  `_family("F16", "combined mild non-scalar violation", ..., adequacy="M1+M2+M3", ..., endpoints=_endpoints("m1_sensitivity", "m2_sensitivity", "m3_sensitivity"), ..., kind="combined_violation")`
- `docs/superpowers/specs/2026-08-13-muru-paper-benchmark-design.md:107` —
  `| F16 | Combined mild non-scalar violation | Are jointly mild violations flagged rather than accepted as M0? | M1+M2+M3 | diagnostic only | no |`

F16 contributes to three detector-sensitivity endpoints, with frozen
denominators reproduced identically in the design spec (lines 186–188) and in
A1.7 (lines 327–329):

| Endpoint | Applicable families | Held-out denominator | F16 share |
|---|---|---:|---:|
| M1 sensitivity | F06, F13, F16 | 36 | 12 |
| M2 sensitivity | F14, F16 | 24 | 12 |
| M3 sensitivity | F15, F16 | 24 | **12 of 24** |

`git diff d94d2c9 2ac86c5 -- generator.py registry.py` is empty: A1 did not touch
either file. The declared truth is therefore original frozen V1 content, not an
A1 artefact.

**Section 2 gate result:** the frozen specification *does* clearly establish F16
as M1+M2+M3. The review proceeds rather than stopping here.

## A2.2 The generator implements only M1 and M2

`src/muru/paper_benchmark/generator.py:124-128`:

```python
elif kind == "combined_violation":
    shape = 1 + 0.15 * np.tanh(compounds.descriptor.to_numpy())
    floor = np.clip(mu_inf + 0.05 * (compounds.descriptor2.to_numpy() - 0.5), 0.03, 0.55)
    mu = floor[:, None] + (1 - floor[:, None]) * np.exp(-(u**(phi_p * shape[:, None])))
    adequacy = "M1+M2+M3"
```

Against the A1.2 model definitions:

- `shape` scales the profile exponent per compound → the **M1** horizontal-shape
  deviation (`s_i != 1`). Present.
- `floor` replaces `mu_inf` per compound → the **M2** high-energy asymptote
  deviation (`a_i != A_HI`). Present.
- The low-energy plateau is `floor + (1 - floor) * S(0) = floor + (1 - floor) = 1`
  identically, for every compound. In A1.2 terms `b_i = A_LO` exactly, which is
  the stated M3 **neutral** value. **No M3 deviation exists.**

Verified numerically: the frozen branch's low-energy plateau is `1.000000000000`
for both its minimum and maximum across compounds.

## A2.3 Truth metadata asserts a component the mechanism does not contain

`generator.generate_case` writes
`m0_adequacy_truth = variant.m0_adequacy_truth if variant.m0_adequacy_truth != "M0" else generated_adequacy`.
For F16 the variant value is `"M1+M2+M3"`, so the registry string is written
through unconditionally and the generated `adequacy` label is discarded.
`applicable_endpoints` is likewise copied from the registry, and the frozen
`paper_benchmark_case_manifest.json` records
`["m1_sensitivity", "m2_sensitivity", "m3_sensitivity"]` on all 19 F16 cases
(12 held-out, 4 development, 3 challenge).

Every F16 case therefore carries machine-readable truth asserting an M3
component that its response mechanism does not contain. **12 of the 24 cases in
the frozen M3 sensitivity denominator are M3-negative worlds labelled M3-positive.**

**Mismatch confirmed: YES.**
**Classification: FROZEN SPECIFICATION / GENERATOR IMPLEMENTATION MISMATCH.**

A1.7 recorded this observation and deliberately deferred it
(`MURU_PAPER_BENCHMARK_AMENDMENT_A1_ADEQUACY.md:331-337`). This review confirms
it against the source.

## A2.4 The repaired mathematical form is determined and conflict-free

A1.2 defines each single deviation against the frozen training-side shape `S`:

| Model | A1.2 form | Neutral at |
|---|---|---|
| M0 | `A_HI + (A_LO - A_HI) * S(E / g_i)` | — |
| M1 | `A_HI + (A_LO - A_HI) * S(E_REF * (E / (E_REF * g_i))**s_i)` | `s_i = 1` |
| M2 | `a_i + (A_LO - a_i) * S(E / g_i)` | `a_i = A_HI` |
| M3 | `A_HI + (b_i - A_HI) * S(E / g_i)` | `b_i = A_LO` |

The natural simultaneous composition is

```
mu_i(E) = a_i + (b_i - a_i) * S(E_REF * (E / (E_REF * g_i)) ** s_i)
```

with `E_REF = 45.0`. No competing explicit F16 formula exists anywhere in the
frozen repository — the A1 ladder is M0 versus M1, M2, M3 individually and
defines no combined model — so section 4 raises no conflict stop.

All five required reductions were verified to exact floating-point equality
against the frozen generator branches:

| Check | Result |
|---|---|
| `s=1, a=A_HI(mu_inf), b=A_LO(1)` reproduces the M0 branch | exact |
| `s` only reproduces the frozen `m1_horizontal` branch | exact |
| `a` only reproduces the frozen `m2_high_energy` branch | exact |
| `b` only reproduces the frozen `m3_low_energy` branch | exact |
| the form at `b = 1` reproduces the frozen `combined_violation` branch | exact |

The last row is the precise statement of the defect: the frozen implementation
*is* the correct combined form evaluated at the M3-neutral point.

## A2.5 The blocking issue: no prospective rule fixes the F16 M3 parameters

Section 5 permits reuse of the F15 low-energy parameterization "wherever
scientifically compatible", and requires a stop where no prospective rule exists
and a new scientific distribution would have to be invented. The frozen
amplitudes are:

| Family | Deviation | Frozen parameterization | Driver | Amplitude |
|---|---|---|---|---:|
| F13 | M1 | `1 + 0.45 * tanh(descriptor)` | `descriptor` | 0.45 |
| F14 | M2 | `clip(mu_inf + 0.18 * (descriptor - 0.5), 0.03, 0.55)` | `descriptor` | 0.18 |
| F15 | M3 | `clip(1 - 0.22 * descriptor, 0.6, 0.99)` | `descriptor` | 0.22 |
| F16 | M1 | `1 + 0.15 * tanh(descriptor)` | `descriptor` | 0.15 |
| F16 | M2 | `clip(mu_inf + 0.05 * (descriptor2 - 0.5), 0.03, 0.55)` | `descriptor2` | 0.05 |
| F16 | M3 | **absent** | **undetermined** | **undetermined** |

F16 is specifically declared a **"combined *mild* non-scalar violation"**, and
its frozen scientific question is "Are jointly *mild* violations flagged rather
than accepted as M0?". The only operationalization of "mild" that exists
anywhere in the frozen content is F16's own attenuation of the single-violation
amplitudes. Three independent degrees of freedom are consequently unresolved:

1. **Amplitude.** Reusing F15's exact 0.22 would make F16's M3 component
   full strength — the largest deviation in the family, no harder to detect than
   the dedicated F15 family — which contradicts the declared "jointly mild"
   character and moves detectability in the *favorable* direction on a primary
   endpoint. Deriving an attenuated value instead requires a ratio, and the two
   frozen F16 ratios do not agree: `0.15 / 0.45 = 0.333333` but
   `0.05 / 0.18 = 0.277778`, yielding 0.0733 or 0.0611 respectively. No frozen
   rule selects between them.
2. **Driving covariate.** F16's M1 uses `descriptor` (as F13 does), but F16's M2
   uses `descriptor2` where F14 uses `descriptor` — so F16 demonstrably departs
   from the single-violation driver in at least one component. Whether F16's M3
   should be driven by `descriptor` (collinear with its own M1 term) or by
   `descriptor2` (collinear with its own M2 term) or by neither is not fixed by
   any frozen rule, and the choice materially changes whether the three
   components are separable.
3. **Clip window.** F15's `(0.6, 0.99)` clip is not stated to be F16-applicable,
   and F16's M2 clip does match F14's — so no consistent inheritance rule can be
   read off.

An exhaustive search of the frozen content found no F16-specific amplitude rule.
The design spec's only statement on generative parameters is that "per-case
`mu_inf`, `p`, scale and law coefficients are drawn from declared bounded
ranges" — it declares no deviation amplitude for F13, F14, F15, or F16. The word
"mild" appears in exactly two frozen places, both qualitative: the registry
family name and the design-spec scientific question. `MIN_VERTICAL_AMPLITUDE =
0.05` in A1.2 is a *fitting identifiability floor* for the M2/M3 estimators, not
a generative amplitude, and A1 explicitly describes its bounds as "permissive
supersets of the frozen generative ranges, not tight fits to them".

Selecting any of these values would set, after the freeze and by the reviewer's
own judgment, the effect size of a positive control supplying half of a primary
adequacy endpoint's denominator. That is a prospective scientific decision
reserved to the benchmark owner, and section 5 forbids resolving it here.

**Repair halted at section 5. Sections 6–11 were not executed:** the generator
was not modified, no artifact was regenerated, no integrity manifest was
produced, no contract tests were added, no amendment document was issued, and no
new content freeze was created.

## A2.6 Decision required from the benchmark owner

The mathematical form (A2.4) is settled and needs no decision. Exactly one
prospective declaration is needed, on all three axes of A2.5, before the repair
can be completed mechanically:

- **the M3 amplitude** for `combined_violation`;
- **the driving covariate** for that term;
- **the clip window** for the resulting ceiling.

Candidate resolutions, offered without preference and each requiring explicit
owner adoption as a prospective rule:

| Option | Rule | Consequence |
|---|---|---|
| A | reuse F15 exactly: `clip(1 - 0.22 * descriptor, 0.6, 0.99)` | simplest provenance; abandons F16's declared mildness for the M3 term and maximizes its detectability |
| B | declare a single F16 attenuation factor and apply it to all three components, restating F16's M1 and M2 amplitudes accordingly | internally consistent; changes frozen F16 M1/M2 bytes, so it is a larger amendment than A2 was scoped for |
| C | declare an F16-specific M3 amplitude directly, with recorded provenance | narrowest change; requires the owner to state a number and its justification |
| D | keep the generator and amend the registry/spec instead, redeclaring F16 as M1+M2 and the M3 denominator as 12 | contradicts the section 3 repair principle and shrinks a frozen primary denominator |

Whichever is adopted must be recorded as a prospective declaration before the
generator is touched, so that the amplitude is provably not outcome-derived.

## A2.7 Evidence hashes at review time

Branch `science/muru-paper-benchmark-f16-amendment`, parent `2ac86c5`, tree
otherwise byte-identical to A1.

| Path | SHA-256 |
|---|---|
| `src/muru/paper_benchmark/registry.py` | `3f5164fdffc0bb54e5a380ac9ff2f0cad03c47a25095fd6b9a71be3f4b83d1d9` |
| `src/muru/paper_benchmark/generator.py` | `be026dc88f3f8c0a1eea042a34e7b49d907b499de55280d95621add22823ea48` |
| `src/muru/paper_benchmark/adequacy.py` | `1a96ef6e450aebba6a1ffac5e1fdc6c4bb9e52f29401745a1fafd73b69a0a6e2` |
| `src/muru/paper_benchmark/truth.py` | `b773d458b86390bb63a8f95e54b5d299783acc777ea6134c894d8f227c5d4719` |
| `artifacts/paper_benchmark_case_manifest.json` | `f5f838ac24ce1f1949d7e182181b7a46ebec4f4708a6c330a750beb524c8d0d3` |
| `artifacts/paper_benchmark_truth_manifest.json` | `c26595a1a34f59adac54b91a1f8c13cccd5ec0fd924d7af81dff2952027ce477` |
| `artifacts/paper_benchmark_content_freeze.json` | `fc8acfdf924e18ca32a4a88830707e490de903aaa09645e3f479de07c1067dfc` |
| `MURU_PAPER_BENCHMARK_AMENDMENT_A1_ADEQUACY.md` | `2ae2022c8344088be0e64f11bd11c9d021e59b4f9fe08ee9e2d95719e39987dd` |
| `docs/superpowers/specs/2026-08-13-muru-paper-benchmark-design.md` | `8ce2fdfc2e0cc6e14c161107123f6ebbd57d01352555fcfb930d595112cf9202` |

Unchanged and re-confirmed from the registry: 20 families, 380 cases, F16 = 19
cases (12 held-out / 4 development / 3 challenge), M0 specificity 164, M1
sensitivity 36, M2 sensitivity 24, M3 sensitivity 24.

**The effective benchmark content freeze supplied to Engineering RC 2 remains
`2ac86c5`. Engineering RC 2 must not proceed on the strength of this review.**
