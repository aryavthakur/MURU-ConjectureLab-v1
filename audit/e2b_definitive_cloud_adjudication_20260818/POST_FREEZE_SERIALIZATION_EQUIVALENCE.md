# AGENT 2 — POST-FREEZE SERIALIZATION EQUIVALENCE (DEFECT A)

**Question.** The E2b full-front replay was frozen at `dabcb4b`. After launch, front
serialization failed because `sympy_format`, `lambda_format` and `CallableEquation`
objects are not JSON-serializable. The runner was patched mid-flight, and the
4,320-front corpus that exists today was produced under the *patched* serializer.
Is that patch scientific, or purely observational?

**Verdict.** `POST_FREEZE_PATCH_SCIENTIFICALLY_NEUTRAL = YES`

---

## 1. Exact scope of the post-freeze change

```
$ git diff --stat dabcb4b 6b18dd8
 results/.../E2B_FULLFRONT_REPLAY_REPORT.json        | 1621 ++++
 results/.../MURU_E2B_FULLFRONT_REPLAY_FINAL.md      |  315 ++
 results/.../gate/MURU_E2B_DIRECT_69_57_CASES.csv    |  145 +
 results/.../gate/MURU_E2B_DIRECT_69_57_GATE.json    | 1320 ++++
 results/.../gate/completeness_check.json            |   43 +
 results/.../manifest.jsonl                          | 4320 ++++
 results/.../MURU_E2B_FULLFRONT_MANIFEST.sha256      |    1 +
 results/.../MURU_E2B_FULLFRONT_REPLAY_PROVENANCE.json | 23 +
 scripts/run_e2b_fullfront_replay.py                 |   36 +-
 9 files changed, 7816 insertions(+), 8 deletions(-)
```

Eight of the nine paths are **output artifacts produced by the run itself**. Exactly
one source file changed: `scripts/run_e2b_fullfront_replay.py` (+29 / −7).

**The scientific core is byte-identical across the freeze:**

```
$ git diff dabcb4b 6b18dd8 -- src/muru/ | wc -c
0
```

`src/muru/paper_benchmark/` — which contains `g2_contract.py` (the G2-correctness
definition), `rc5_selection.py` (retention + cross-seed voting), `generator.py`
and `registry.py` — has **zero** changed bytes. The frozen evaluator
`scripts/e2b_direct_evaluator.py` likewise does not appear in the diff; its SHA-256
is `ee285a8b…9743` at `dabcb4b`, at `6b18dd8`, and in the working tree.

## 2. Line-by-line classification of the 36 changed lines

| Hunk | Location | Change | Class |
|---|---|---|---|
| 1 | new `_to_json_safe()` | adds a cell→JSON-native converter with a `str()` fallback | `SERIALIZATION_ONLY` |
| 2 | `_serialize_front()` inner loop | replaces 5 inline conversion lines with `_to_json_safe(val)` | `SERIALIZATION_ONLY` |
| 3 | `_json_default()` docstring | comment reworded | `REPORTING_ONLY` |
| 4 | `_json_default()` tail | `raise TypeError(...)` → `return str(obj)` | `SERIALIZATION_ONLY` |

```
SCIENTIFIC_CHANGED_LINES = 0
UNKNOWN_CHANGED_LINES    = 0
```

Every changed line lives inside `_serialize_front` / `_to_json_safe` / `_json_default`.

## 3. The patch executes strictly *after* the search is complete

`_serialize_front(equations, …)` takes the **already-materialised** PySR
`equations_` DataFrame as its argument. It is called from `persist_front_atomic`,
after the PySR/Julia search has returned. The patched code therefore cannot reach
any of the following, all of which are decided upstream inside PySR/Julia and the
unchanged `src/muru` modules:

```
RNG                     search               candidate generation
candidate ranking       loss                 score
complexity              selection_count      representative
termination             simplification
```

There is no feedback path: `_serialize_front` returns a list of dicts that is
written to disk and never read back within the run.

## 4. Machine-checked proof that the persisted values are byte-identical

The patch changes which *branch* a cell takes, so branch-equality is not enough —
the emitted bytes must be shown equal. `serialization_equivalence_proof.py`
reimplements both the pre-patch and post-patch converters verbatim from the diff
and compares `json.dumps` output.

The one genuinely subtle case: **`np.float64` subclasses Python `float`**, so
`score` and `loss` take the *new* `isinstance(val,(str,int,float,bool))` early
return and are emitted **unconverted**, whereas the pre-patch code called
`.item()`. The Python type therefore differs on every single float — but the
serialized bytes do not:

```json
{
  "float64": {"tested": 300009, "json_differs": 0, "value_differs": 0,
              "python_type_differs": 300009},
  "int64":   {"tested": 100004, "json_differs": 0},
  "str":     {"tested": 6,      "json_differs": 0},
  "bool":    {"tested": 4,      "json_differs": 0},
  "TOTAL_JSON_DIFFERENCES_ON_CLASSIFIER_RELEVANT_TYPES": 0,
  "VERDICT": "IDENTICAL"
}
```

The 300,009 float64 samples are drawn from **uniform random 64-bit patterns**,
so they span the whole IEEE-754 double space — subnormals, ±0, and both extremes —
not a friendly decimal subset. `json.dumps` uses `float.__repr__` for `float`
subclasses, and `float.__repr__` is exact round-trip, which is why the byte output
is invariant. `np.int64` does *not* subclass `int`, so `complexity` takes the
identical `.item()` branch on both sides.

**Only two columns change representation at all:** `sympy_format` and
`lambda_format`, which pre-patch raised `TypeError` (the defect) and post-patch
become `str(val)`.

## 5. Those two columns have no consumer anywhere

```
$ grep -rn "sympy_format\|lambda_format" --include=*.py scripts/ src/ audit/ \
    | grep -v run_e2b_fullfront_replay.py
(no matches)
```

The only columns read by any classifier are `equation` and `score`:

- `scripts/e2b_direct_evaluator.py:189` → `row.get("equation", "")`
- `scripts/e2b_direct_evaluator.py:175` → `row.get("score", float("-inf"))`
- `src/muru/paper_benchmark/rc5_selection.py:172` → `equations["score"].idxmax()`
- `audit/…/agent4_independent_evaluator.py:141,143` → `equation`, `score`

Both are proven byte-identical in §4. `complexity` and `loss` are likewise
identical, though only `loss` is consulted (by `rc5_selection`'s finiteness guard).

## 6. Corpus-wide structural confirmation

Every persisted row was re-read and checked (51,411 rows across 4,320 files):

```
rows missing 'equation' : 0        non-str equation  : 0
rows missing 'score'    : 0        non-numeric score : 0
non-finite score        : 0
sympy_format non-str    : 0        lambda_format non-str : 0
row-key union: _case_id _case_index _search_index _seed _seed_ordinal
               complexity equation lambda_format loss score sympy_format
```

The stringification is confined exactly where predicted, and no classifier-relevant
field is missing, null, mistyped, or non-finite anywhere in the corpus.

## 7. Corroborating (not sole) evidence

The replay reproduced the sealed macOS result exactly — `selection_count` 144/144
and cross-seed `representative` 144/144, recomputed here directly from the raw
`selection_count_sealed` vs `selection_count_replayed` and `representative_sealed`
vs `representative_replayed` fields rather than trusting the report's own summary
counters. A serializer defect that perturbed any scientific quantity could not
leave 288/288 comparisons exact. This is treated as corroboration only; §3–§6
are the proof.

## 8. Conclusion

```
POST_FREEZE_LINES_CHANGED            = 36  (29 added, 7 removed, 1 file)
SERIALIZATION_ONLY                   = 33
REPORTING_ONLY                       = 3
SCIENTIFIC                           = 0
UNKNOWN                              = 0
POST_FREEZE_PATCH_SCIENTIFICALLY_NEUTRAL = YES
```

The 4,320-search corpus **must not be regenerated**. Defect A is observational.
