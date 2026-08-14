# MURU A3.4 Frozen Metadata Attestation Advisory

**Status:** `IMMUTABLE_HISTORICAL_PROVENANCE_ATTESTATION_DISCREPANCY`

**Classification:** additive, outcome-blind advisory; not a science amendment

**Scientific change:** none

**Outcome inspection:** none

## Purpose and scope

This advisory records one immutable historical provenance-attestation discrepancy
and one historical serialization convention/ambiguity in frozen A3.4 metadata.
It does not replace, amend, regenerate, or edit Amendment A3.4. It makes no
scientific definition, reference distribution, threshold, denominator,
selection, metric, or outcome change.

The evidence source is limited to read-only Git objects, Git tree metadata, and
the frozen A3.4 artifact map. The advisory does not materialize or rehash any
of the 31 listed protected-path blobs. No calibration record, Development
result, Held-out result, Confirmation result, or other outcome-bearing payload
was opened or inspected.

## Frozen source identity

| Item | Immutable Git identity |
| --- | --- |
| A3.4 creation commit | `d0ea5d4b0309e4e95dcab4035b9be66e166765b1` |
| A3.4 freeze commit | `be23b80d63fbd30227f0ab8f200dddc2121f3bfe` |
| A3.4 freeze tag | annotated `benchmark-content-freeze-a3-4`, tag object `326727d5f17943b22f014262dcf42f5cf043ba42`, resolving to `be23b80d63fbd30227f0ab8f200dddc2121f3bfe` |
| Frozen A3.4 document | `MURU_PAPER_BENCHMARK_AMENDMENT_A3_4.md`, SHA-256 `c699230ab8995461b73a6db2b3fecab661f744e937f40ebe2db34fa8c8c11ada` |
| Frozen reference-covariate digest | SHA-256 `4fef2379ae33a10d089bd66794fdd21418b2b30c656fd801bc619f55c3fe7a44` |

The freeze commit is the source of each factual comparison below. The advisory
adds new audit files only; it changes no frozen path.

## Finding 1 — A3.3 parent literal is not a Git object

Both frozen A3.4 records—`MURU_PAPER_BENCHMARK_AMENDMENT_A3_4.md` and
`artifacts/paper_benchmark_amendment_a3_4.json` at
`be23b80d63fbd30227f0ab8f200dddc2121f3bfe`—record
`parent_a3_3_commit` as:

```text
71f53697e8894df6469ad0ff7150a049fa531b74
```

That literal is not a local Git commit object: the exact check
`git cat-file -e 71f53697e8894df6469ad0ff7150a049fa531b74^{commit}` returns
nonzero. The actual tagged A3.3 commit is
`71f5369c8aa9e5c47f951bd894d744af70956616`: the annotated
`benchmark-content-freeze-a3-3` tag (tag object
`363e1c5a64cdf235712900fc2a14409fa6ec3e1e`) resolves to that commit, and it
is also the Git parent of the A3.4 creation commit:

```text
d0ea5d4b0309e4e95dcab4035b9be66e166765b1^
  = 71f5369c8aa9e5c47f951bd894d744af70956616
```

This advisory does not substitute the actual commit into either frozen A3.4
record. The recorded literal remains byte-preserved historical provenance.

## Finding 2 — protected-path aggregate serialization convention

At `be23b80d63fbd30227f0ab8f200dddc2121f3bfe`, the A3.4
`protected_sha256` map has 31 listed paths and 31 SHA-256 entries. The
accompanying regression check compares only Git blob metadata—mode, object
type, object ID, and path—for each listed path at the freeze commit and the
test-run `HEAD`. It requires all 31 metadata records to match and deliberately
does not materialize or rehash the protected blobs.

The artifact records aggregate digest:

```text
d24cc91698a562acfe61c8bab65a9f33ccc517b284411c65c66e394fe7a6d1b8
```

The historical aggregate is exactly reproduced by this serialization:

1. Sort relative paths in lexicographic ascending order.
2. Serialize each UTF-8 entry as `{relative_path}:{sha256}`.
3. Join adjacent entries with `\n`, with no terminal newline after the final
   entry.
4. Apply SHA-256 to the resulting byte stream.

That exact no-terminal-newline convention recomputes the recorded value
`d24cc91698a562acfe61c8bab65a9f33ccc517b284411c65c66e394fe7a6d1b8`.

An alternate, equally explicit serialization appends `\n` after every UTF-8
`{relative_path}:{sha256}` entry, including the final entry. It instead
recomputes:

```text
55ebd0b92ba07ad828983f4e7add5163f49377255dfcf47bdd9f1af98174f16a
```

The frozen artifact does not state whether a terminal newline is required. The
two values therefore express a historical serialization convention/ambiguity,
not a content-integrity defect: `d24cc…` is not incorrect, and this advisory
does not replace it.

## Scientific effect and preservation

Neither discrepancy changes A3.4's scientific definitions or its frozen
reference-covariate digest
`4fef2379ae33a10d089bd66794fdd21418b2b30c656fd801bc619f55c3fe7a44`.
The live annotated `benchmark-content-freeze-a3-4` tag remains a Git tag object
that dereferences to `be23b80d63fbd30227f0ab8f200dddc2121f3bfe`. The A3.4
document and artifact remain identified by their frozen Git blobs, and the
metadata-only regression check requires every listed protected-path blob ID to
match from `be23` through test-run `HEAD`. This is an immutable historical
provenance-attestation record, not an operational correction or new science
amendment.

## Canonical advisory binding

`audit/muru_a3_4_frozen_metadata_attestation_advisory.json` is the binding
ledger for this advisory. Its `canonical_attestation` object is serialized as
UTF-8 JSON with recursive lexicographic object-key ordering, compact `,` and
`:` separators, `ensure_ascii=false`, `allow_nan=false`, and no trailing
newline; its SHA-256 is recorded in `canonical_binding.content_sha256`.
The same canonical object records this Markdown file's SHA-256, binding the
human-readable projection without changing frozen A3.4 content.
