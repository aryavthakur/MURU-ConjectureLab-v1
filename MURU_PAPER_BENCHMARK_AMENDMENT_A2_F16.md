# MURU paper benchmark — Amendment A2: F16 generator/truth consistency repair

## A2.0 Amendment record

| Field | Value |
|---|---|
| Amendment | A2 — F16 combined-violation generator/truth consistency repair |
| Original content freeze | `d94d2c9` ("Prepare prospective paper benchmark content freeze") |
| Original freeze designation | BENCHMARK CONTENT FREEZE V1, preserved permanently and unmodified |
| Adequacy amendment A1 | `2ac86c5` ("Amendment A1: bind the M0/M1/M2/M3 adequacy decision rule") |
| Branch | `science/muru-paper-benchmark-f16-amendment`, created from `2ac86c5` |
| Contract version | `paper-benchmark-amendment-a2-integrity-1.0.0` |
| Effective content freeze | the commit introducing this document, tagged `benchmark-content-freeze-a2` |

**Reason for amendment.** A pre-execution review found that F16's frozen
registry entry and machine-readable truth declare the family's adequacy truth as
`M1+M2+M3` and make it applicable to all three detector-sensitivity endpoints,
while the frozen `combined_violation` generator introduced only an M1
horizontal-shape term and an M2 high-energy floor term. Its low-energy plateau
was pinned at the M3-neutral value for every compound, so no M3 deviation
existed. Twelve of the twenty-four cases in the frozen M3 sensitivity
denominator were therefore M3-negative worlds carrying M3-positive truth. A1
recorded the observation in A1.7 and deliberately deferred it; A2 resolves it.

**Contamination status.** No Development scientific outcome and no Held-out
outcome was executed, scored, enumerated, parsed, summarised, or inspected in
preparing this amendment. Case content was generated and hashed, and generated
rows were compared as opaque whole lines; no response value was decoded, no case
was fitted or scored, and no question about detectability was asked. The
declaration binding the repaired M3 parameters was made prospectively, before
any outcome existed.

**Scientific change.** The F16 generator is brought into conformity with the
F16 truth that V1 already declared. Nothing else changes.

**Historical benchmark changes.** None. The family population, case IDs,
partition assignments, root seed, derived seed scheme, compound and scaffold
assignments, energy grid, endpoint denominators, G1/G2/G3 thresholds, and every
A1 adequacy decision rule and constant are unchanged. `d94d2c9` and `2ac86c5`
are not rewritten.

**Precedence.** A2 does not weaken any frozen refusal. The held-out guard
remains `PENDING_LOCK`; A2 does not authorise held-out execution.

---

## A2.1 Classification

**FROZEN SPECIFICATION / GENERATOR IMPLEMENTATION MISMATCH.**

The frozen specification clearly and redundantly establishes F16 as M1+M2+M3:

- `src/muru/paper_benchmark/registry.py:150` — `adequacy="M1+M2+M3"`, with
  `endpoints=("m1_sensitivity", "m2_sensitivity", "m3_sensitivity")`;
- `docs/superpowers/specs/2026-08-13-muru-paper-benchmark-design.md:107` —
  `| F16 | Combined mild non-scalar violation | ... | M1+M2+M3 |`;
- the frozen endpoint tables in the design spec (lines 186–188) and A1.7
  (lines 327–329), which both attribute 12 held-out F16 cases to each of the M1,
  M2 and M3 sensitivity denominators.

Both files are byte-identical at `d94d2c9` and `2ac86c5`, so the declared truth
is original V1 content and not an A1 artefact. The mismatch is therefore an
implementation defect measured against an unambiguous frozen declaration, and
the repair direction follows: the generator is corrected to honour the declared
truth. F16 is **not** removed from the M3 denominator.

---

## A2.2 The defect

The frozen `combined_violation` branch was:

```python
shape = 1 + 0.15 * np.tanh(compounds.descriptor.to_numpy())
floor = np.clip(mu_inf + 0.05 * (compounds.descriptor2.to_numpy() - 0.5), 0.03, 0.55)
mu = floor[:, None] + (1 - floor[:, None]) * np.exp(-(u**(phi_p * shape[:, None])))
```

Against the A1.2 model definitions, `shape` is the M1 deviation (`s_i != 1`) and
`floor` is the M2 deviation (`a_i != A_HI`). The low-energy plateau is

```
floor + (1 - floor) * S(0)  =  floor + (1 - floor)  =  1
```

identically for every compound — that is `b_i = A_LO` exactly, which A1.2 names
as the M3 **neutral** value. Verified numerically: the minimum and maximum
plateau across compounds were both `1.000000000000`.

---

## A2.3 Repaired mathematical form

A1.2 defines each single deviation against the frozen training-side shape `S`,
with `E_REF = 45.0`:

| Model | A1.2 form | Neutral at |
|---|---|---|
| M0 | `A_HI + (A_LO - A_HI) * S(E / g_i)` | — |
| M1 | `A_HI + (A_LO - A_HI) * S(E_REF * (E / (E_REF * g_i))**s_i)` | `s_i = 1` |
| M2 | `a_i + (A_LO - a_i) * S(E / g_i)` | `a_i = A_HI` |
| M3 | `A_HI + (b_i - A_HI) * S(E / g_i)` | `b_i = A_LO` |

F16 now uses their natural simultaneous composition:

```
mu_i(E) = a_i + (b_i - a_i) * S(E_REF * (E / (E_REF * g_i)) ** s_i)
```

implemented as `generator.combined_response`. No competing explicit F16 formula
exists anywhere in the frozen repository — the A1 ladder defines M0 versus M1,
M2 and M3 individually and defines no combined model — so this form conflicts
with nothing frozen.

The reductions are exact, not approximate. Each is asserted by
`tests/test_paper_benchmark_f16_combined.py` with `np.array_equal`:

| Setting | Result |
|---|---|
| `s = 1`, `a = A_HI`, `b = A_LO` | the M0 branch, exactly |
| `s` only non-neutral | the standalone `m1_horizontal` branch, exactly |
| `a` only non-neutral | the standalone `m2_high_energy` branch, exactly |
| `b` only non-neutral | the standalone `m3_low_energy` branch, exactly |
| `b` pinned at `1` | the pre-amendment F16 branch, exactly |

The last row states the defect precisely: the frozen implementation *was* the
correct combined form evaluated at the M3-neutral point.

---

## A2.4 Parameter generation

M1 and M2 are preserved byte-for-byte; no implementation error was found in
either. The V1 numeric literals are unchanged and are now named constants.

| Component | Rule | Driver | Amplitude | Provenance |
|---|---|---|---|---|
| M1 | `s_i = 1 + A * tanh(descriptor)` | `descriptor` | `0.15` | frozen V1, unchanged |
| M2 | `a_i = clip(mu_inf + A * (descriptor2 - 0.5), 0.03, 0.55)` | `descriptor2` | `0.05` | frozen V1, unchanged |
| M3 | `b_i = clip(1 - A * descriptor, 0.6, 0.99)` | `descriptor` | `11/180` | **A2 declaration** |

### The M3 declaration

No frozen prospective rule fixed F16's M3 amplitude, its driving covariate, or
its clip window, and the two attenuation ratios already frozen for F16 are not
equal (`0.15/0.45 = 1/3` for M1, `0.05/0.18 = 5/18` for M2), so no ratio rule
could be derived. The review therefore halted and returned
`GOVERNANCE REVIEW REQUIRED` rather than inventing a distribution. The benchmark
owner then bound the rule prospectively, and A2 implements exactly that binding:

> Preserve the standalone F15 M3 mechanism — same driving covariate, same
> functional form, same directionality, same clip window `(0.6, 0.99)` — and
> attenuate only the amplitude, by the smaller of the two attenuation ratios
> already frozen for F16's existing components, namely `5/18`.

so that

```
F15 amplitude * 5/18  =  11/50 * 5/18  =  11/180  ~=  0.0611111111111111
```

Choosing the *smaller* ratio is conservative: it guarantees the newly repaired
component is not relatively stronger than either pre-existing combined
component, which is what F16's declared "combined mild" character requires. The
full F15 amplitude of `0.22` was explicitly **not** used, because grafting a
full-strength deviation into a family declared mild would have made F16's M3
term its dominant deviation and no harder to detect than the dedicated F15
family — a change in the favourable direction.

**Binary64 note.** `11/180` and the left-to-right product `0.22 * (5 / 18)` are
not the same double: they differ by one unit in the last place
(`0x1.f49f49f49f49fp-5` versus `0x1.f49f49f49f4a0p-5`). The declaration named
the exact rational and directed that the rational-derived constant be used, so
`COMBINED_M3_AMPLITUDE = 11 / 180` is bound and its hex representation is pinned
by test. This is recorded rather than left implicit because it is the difference
between two defensible readings of the same declaration.

No amplitude was selected by observing any benchmark outcome; none existed.

---

## A2.5 Truth metadata

F16 truth is unchanged in **form** and now correct in **substance**. Every F16
case records:

- `m0_adequacy_truth = "M1+M2+M3"` — all three components present;
- `applicable_endpoints = ["m1_sensitivity", "m2_sensitivity", "m3_sensitivity"]`
  — the frozen detector-specific applicability, preserved;
- `scalar_truth_defined = False`, `symbolic_truth_kind = "none"`.

The `TruthRecord` schema is deliberately **not** extended with per-component
boolean fields. `truth_version` and every field name are part of each case's
hashed payload, so adding a field would rewrite all 380 truth records and
destroy the non-F16 byte immutability A2 must preserve. The composite
`"M1+M2+M3"` string is the frozen representation, and it now matches the actual
response mechanism — which is what the consistency requirement asks for. The
match is asserted directly against generated cases: the tests recompute `s`, `a`
and `b` for a real F16 case from its own truth-recorded `mu_inf` and require all
three to be non-neutral, with the M3 ceiling below `1` for more than 90% of
compounds.

`GENERATOR_VERSION` is likewise deliberately unchanged at
`paper-benchmark-generator-1.0.0`: it is part of every case's hashed payload, so
bumping it would alter all 380 content hashes. The A2 commit is the
discriminator between the two generator states. This is called out explicitly
because an unchanged version constant beside a changed generator is otherwise a
legitimate integrity concern.

---

## A2.6 Regeneration scope and integrity

Regeneration used the already-frozen case IDs, partition assignments, root seed
`20260813`, derived seed scheme, compound and scaffold assignments, and energy
grid. The repair adds no random draw, so every per-case RNG stream is
positionally identical to A1.

Before the repair, this environment rebuilt the A1 generator state and
reproduced the tracked `paper_benchmark_case_manifest.json`,
`paper_benchmark_partition_manifest.json`, `paper_benchmark_truth_manifest.json`
and `paper_benchmark_hash_inventory.json` **byte-identically**, which also
confirms the untracked row files by inventory. Determinism is therefore
established independently of the repair.

`scripts/pb_31_amendment_a2_integrity.py` rebuilds both the A1 and A2 generator
states and compares them line by line:

| Stream | Lines | F16 changed | non-F16 changed |
|---|---:|---:|---:|
| `inputs/development.jsonl` | 80 | 4 | 0 |
| `truth/development.jsonl` | 80 | 4 | 0 |
| `inputs/held_out.jsonl` | 240 | 12 | 0 |
| `truth/held_out.jsonl` | 240 | 12 | 0 |
| `inputs/challenge.jsonl` | 60 | 3 | 0 |
| `truth/challenge.jsonl` | 60 | 3 | 0 |

All 19 F16 case records changed and all 361 non-F16 case records are
byte-identical. Notably F13, F14 and F15 are unchanged, which proves the
extraction of the shared amplitude constants was byte-neutral.

Held-out F16 bytes were regenerated mechanically and hashed. They were not
parsed for performance, summarised, or examined for detectability.

### Allowed-change manifest, relative to `2ac86c5`

253 tracked paths, 245 unchanged.

| Path | Why it may change |
|---|---|
| `src/muru/paper_benchmark/generator.py` | the F16 `combined_violation` branch gains its declared M3 ceiling |
| `artifacts/paper_benchmark_case_manifest.json` | per-case content hashes for the 19 F16 cases |
| `artifacts/paper_benchmark_hash_inventory.json` | SHA-256 of the six regenerated row files |
| `artifacts/paper_benchmark_preflight.json` | `artifact_bytes` follows the F16 rows |
| `artifacts/paper_benchmark_content_freeze.json` | records the new inventory and preflight digests |
| `artifacts/paper_benchmark_amendment_a1.json` | bookkeeping: the V1-relative report now attributes each change to A1 or A2 |
| `scripts/pb_30_amendment_a1_integrity.py` | bookkeeping: attributes V1-relative changes to their owning amendment |
| `tests/test_paper_benchmark_amendment_integrity.py` | bookkeeping: asserts the A1/A2 attribution split |

Added: this document, the pre-repair governance review, the A2 integrity script,
the A2 integrity manifest, and the two A2 test modules.

**Disclosure.** `paper_benchmark_preflight.json` also carries `wall_seconds`,
`cpu_seconds` and `peak_rss_bytes`, which are environment re-measurements and do
not depend on F16. They changed because the frozen preflight script was re-run
rather than hand-edited; fabricating stable timings would have been worse. The
scientifically meaningful field, `artifact_bytes`, moved from `8326553` to
`8326688`, tracking the four F16 development cases.

**Unchanged and re-verified:** 20 families; 380 cases; F16 at 19 cases
(12 held-out, 4 development, 3 challenge); M0 specificity 164; M1 sensitivity
36; M2 sensitivity 24; M3 sensitivity 24; scalar competence 164; family recovery
144; principal structural safety 36; G1 and G2 lower-bound gates at `0.70`; G3
upper-bound gate at `0.15`; `MU_FLOOR`, `MU_CEIL`, `MIN_VERTICAL_AMPLITUDE` and
every A1 model definition. `registry.py`, `truth.py`, `protocol.py`,
`governance.py`, `adequacy.py`, `analysis.py`, the partition manifest and the
truth manifest are all byte-identical to A1.

---

## A2.7 Tests

`tests/test_paper_benchmark_f16_combined.py` and
`tests/test_paper_benchmark_amendment_a2_integrity.py` add 41 contract tests.
They prove the exact M0/M1/M2/M3 reductions, that the generated F16 case carries
non-neutral `s`, `a` and `b`, that F16 truth marks all three components present
and retains all three sensitivity endpoints, that the M3 amplitude equals F15's
attenuated by exactly `5/18` with the pinned binary64 value, that the
denominators remain 36/24/24, that F16 case counts and the registry population
are unchanged, that sampled non-F16 content hashes still equal their A1 values,
and that the A1 adequacy constants and G1/G2/G3 thresholds are untouched.

These are contract tests. None fits an adequacy model, scores a case, or asks
whether the repaired F16 violation is discoverable. That question belongs to
Engineering RC 2 and remains unasked.

**Environment note.** `tests/test_models.py`, `test_p3_falsify.py`,
`test_p3_protocol.py`, `test_parser.py` and `test_splits.py` cannot be collected
here because `rdkit` is not installed, and `tests/test_ov_blinding.py` has two
failures from a missing `fastparquet`. Both conditions were verified to be
present at `2ac86c5` before any A2 change and belong to the real-data and
objective-validation tracks, not the paper benchmark. Every paper-benchmark test
passes.

---

## A2.8 Freeze

| Freeze | Commit | Status |
|---|---|---|
| V1 | `d94d2c9` | original content freeze, preserved unmodified |
| A1 | `2ac86c5` | adequacy decision rule bound |
| A2 | this commit | **effective benchmark content freeze** |

The A2 commit is the effective benchmark content freeze supplied to Engineering
RC 2. The held-out execution guard remains `PENDING_LOCK` and A2 does not
authorise held-out execution.
