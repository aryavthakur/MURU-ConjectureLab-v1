# Defect A: Post-Freeze Serialization Patch — Scientific Equivalence

**Agent:** AGENT_2 / SERIALIZATION_EQUIVALENCE (coordinator-executed)
**Baseline:** `dabcb4b` (execution freeze commit)
**Compared against:** `6b18dd8` (the commit containing the executed 4,320-front replay results, parent = `dabcb4b`)
**Method:** `git diff dabcb4b 6b18dd8 -- scripts/ src/` (full repository diff, not a sample)

## 1. The complete post-freeze diff

`git diff --stat dabcb4b 6b18dd8` touches exactly one source file:
`scripts/run_e2b_fullfront_replay.py` (+29/-7 lines). No file under `src/muru/paper_benchmark/`
changed at all (`git diff --stat dabcb4b 6b18dd8 -- src/` is empty — independently reconfirmed
above, not merely quoted from the earlier AGENT_2 draft report). Every other change in the
`6b18dd8` diff is new result artifacts (manifest, fronts, gate JSON, provenance) — data, not code.

The full code diff (verbatim):

```diff
+def _to_json_safe(val: Any) -> Any:
+    """Convert a single cell value to a JSON-serialisable Python native. ..."""
+    if val is None:
+        return None
+    if isinstance(val, (str, int, float, bool)):
+        return val
+    if isinstance(val, (bytes, bytearray)):
+        return val.decode("utf-8", errors="replace")
+    if hasattr(val, "item"):
+        return val.item()
+    return str(val)
+
 def _serialize_front(...):
     ...
     for col in equations.columns:
         val = equations[col].iloc[iloc_pos]
-        if hasattr(val, "item"):
-            val = val.item()
-        elif isinstance(val, (bytes, bytearray)):
-            val = val.decode("utf-8", errors="replace")
-        row_dict[col] = val
+        row_dict[col] = _to_json_safe(val)
     ...

 def _json_default(obj):
     ...
-    raise TypeError(f"Object of type {type(obj)} is not JSON serializable: {obj!r}")
+    return str(obj)     # was: raise TypeError(...)
```

## 2. What the patch does

Before the patch, `_serialize_front` only handled two cases (`.item()` for numpy scalars,
`.decode()` for bytes) and left everything else — in particular `sympy_format` (a `sympy.Expr`)
and `lambda_format` (a `CallableEquation`) — unconverted, which made `json.dumps` fall through to
`_json_default`, which then raised `TypeError` for exactly those two column types. The patch adds
`_to_json_safe`, which stringifies (`str(val)`) anything that isn't already a JSON-native type, and
changes `_json_default`'s fallback from "raise" to "stringify" as defense in depth.

## 3. Where in the pipeline this executes

`PersistingBackend.search()` (unchanged by this diff, and unchanged since the freeze):

```python
def search(self, design, seed):
    outcome = self.inner.search(design, seed)   # the real, unmodified PySRCaseBackend
    self.last_equations = outcome.equations      # captured BY REFERENCE, not copied
    return outcome                                # returned UNCHANGED
```

`self.inner` is `PySRCaseBackend` from `src/muru/paper_benchmark/`, confirmed byte-identical to
`d6f607a` (see `AGENT_2_SCIENTIFIC_EQUIVALENCE_REPORT.json`, independently re-verified above via
`git diff --stat dabcb4b 6b18dd8 -- src/` = empty). The wrapper never mutates `outcome` or
`outcome.equations`; it returns the identical `SeedSearchOutcome` the unwrapped backend would have
produced. `_serialize_front`/`_to_json_safe`/`_json_default` are called only from
`persist_front_atomic`, which runs strictly **after** `outcome = self.inner.search(...)` has
already returned — i.e., after PySR search, candidate generation, and the engine's own scoring are
complete. There is no code path from `_to_json_safe`/`_json_default` back into `design`, `seed`,
the regressor, or any subsequent seed's search: they are one-way, write-only formatting of an
already-finalized `equations_` frame to disk.

## 4. Why it cannot affect RNG / search / ranking / selection / classification

- **RNG / search / candidate generation**: untouched — the diff is entirely inside
  `run_e2b_fullfront_replay.py`'s persistence helpers; `PersistingBackend.search()`'s call into the
  unmodified `src/muru/paper_benchmark/` search path is unchanged by this diff (identical before
  and after, confirmed above), and nothing in `_to_json_safe`/`_json_default` executes before or
  during `self.inner.search(design, seed)`.
- **Candidate ranking / loss / score / complexity**: `complexity` (`np.int64`), `loss`
  (`np.float64`), and `score` (`np.float64`) all take the `hasattr(val, "item")` branch in both the
  old and new code — `val.item()` — byte-for-byte identical numeric conversion before and after the
  patch. The patch changes nothing for these three columns.
- **`equation`** (the string every downstream classifier and evaluator reads — both
  `scripts/e2b_direct_evaluator.py` and this audit's independent replication key on `row["equation"]`,
  never on `sympy_format`/`lambda_format`) is already a Python `str`, so it takes the
  `isinstance(val, (str, int, float, bool))` branch **before and after** the patch — identical,
  untouched.
- **`sympy_format`/`lambda_format`**: these are the two columns whose serialization the patch
  changes (`str(val)` instead of an uncaught `TypeError`). Neither the frozen evaluator
  (`scripts/e2b_direct_evaluator.py::is_row_g2_correct`, which reads `row["equation"]`) nor this
  audit's independent classifier reads either column for G2-correctness, retention, or selection.
  They are carried through purely as informational/debugging columns.
- **`selection_count` / representative selection**: computed downstream (by
  `rc5_selection.select_row_label`/`group_and_select`, or by the frozen evaluator's own
  argmax-over-`score` loop) from `equation` and `score`, both unaffected as shown above. Selection
  and cross-seed voting run over the persisted JSONL after the fact (evaluator/replication code
  paths); they never see `sympy_format`/`lambda_format` at all.
- **Termination / simplification**: `simplify()` (in `g2_contract.py`, called only at
  evaluation time — after persistence, in a wholly separate process/script — from the `equation`
  string) never touches `sympy_format`/`lambda_format` either; it re-parses `equation` fresh via
  `sympify`, independent of whatever `str(sympy.Expr)` produced during persistence.

## 5. Corroborating (not sole) evidence

The 144/144 selection_count and representative-expression identity match against the sealed
`cc6c8b9` evidence (independently recomputed by the coordinator directly from
`E2B_FULLFRONT_REPLAY_REPORT.json`'s `comparison_details`, cross-referenced against
`git show cc6c8b9:results/e2b_heldout/G2_SELECTION_COUNT_AND_REPRESENTATIVE_144.json` — see
`FRONT_CORPUS_INTEGRITY.json` and the coordinator's identity re-check) is consistent with, but is
not being used as the sole proof of, neutrality: selection_count/representative depend only on
`equation`/`score`, which sections 3-4 above show are unaffected by the patch independent of any
identity-match outcome.

## 6. Classification

| Changed line group | Classification |
|---|---|
| `_to_json_safe` (new function) | SERIALIZATION_ONLY |
| `_serialize_front` body (delegates to `_to_json_safe`) | SERIALIZATION_ONLY |
| `_json_default` fallback (raise → stringify) | SERIALIZATION_ONLY |

```
SCIENTIFIC_CHANGED_LINES = 0
UNKNOWN_CHANGED_LINES    = 0
SERIALIZATION_ONLY_LINES = 29 (+22 new, +7 modified, -7 removed — all inside the two
                                 persistence helper functions and one exception-fallback branch)
```

## 7. Verdict

```
POST_FREEZE_PATCH_SCIENTIFICALLY_NEUTRAL = YES
```

No new search is required. The 4,320-front corpus persisted under this patch is scientifically
equivalent to what an un-patched (but functioning) persistence layer would have written for the
columns that matter (`equation`, `complexity`, `loss`, `score`); the only columns whose on-disk
representation the patch changes (`sympy_format`, `lambda_format`) are not read by any
classification, selection, or gate computation in this audit or in the frozen evaluator.
