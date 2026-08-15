"""RC5 authorized A3.5-implementation delta ledger.

What this closes
----------------
RC5 implements the frozen A3.5 science contract.  Three of its obligations
(sections 6.9.3, 6.9.4, and implementation obligations 13, 14, 17, 18, 19)
cannot be discharged without editing files that seven frozen integrity scripts
byte-pin, and one mechanical generalisation touches an eighth.  Every one of
those scripts correctly flags the change -- **that detection is working as
designed, not a bug** -- and none of them is modified to stop flagging.

This module is the same kind of object RC4.2.1 built for R1-R4: a closed,
hash-pinned ledger of exactly the paths RC5 touches, each entry binding

* the exact path,
* the A3.5 obligation or RC5 delta item it implements,
* the exact SHA-256 of the pre-change (historical-freeze) bytes,
* the exact SHA-256 of the post-change (RC5-frozen) bytes,
* a one-line statement of the allowed semantic scope.

A path/byte pair that is not *exactly* one of these entries is never treated as
authorized, no matter how small the further drift.  The check compares hashes,
not just paths, so renaming, re-touching, or extending any of these files
beyond the pinned change is rejected identically to an entirely new
unauthorized change.

Nothing here is a new scientific choice.  This ledger transcribes what
MURU_PAPER_BENCHMARK_AMENDMENT_A3_5.md (commit
560bf28568e2762c60edc994aac7f2b6de14081f, tag
benchmark-content-freeze-a3-5) already binds and what
audit/MURU_RC5_POST_A3_5_FREEZE_RECONCILIATION.md already classified, so
that scripts written before A3.5 existed can recognize the implementation
without their own frozen historical-byte-identity assertions being edited,
weakened, or disabled.

Baseline
--------
Every old_sha256 below was computed against the RC5 engineering parent,
69e33c778efb14362439941d25ebbfcfb1068284.  Each modified file was verified
byte-identical at **every** freeze baseline where it exists (d94d2c9,
03cc4d3, 80a7803, c8938e8, 1194fcb, 71f5369, be23b80,
69e33c7), so one entry per file is correct for all seven consuming scripts
rather than one entry per (file, baseline) pair.

What this module deliberately does NOT do
------------------------------------------
* It does not change what any script's historical byte-identity check means.
  A caller that does not consult this ledger still requires bit-for-bit
  identity to its frozen commit.
* It does not touch RECORDED_PROTECTED_AGGREGATE or any other historical
  digest.
* It does not authorize a further file, or a different byte pattern for any of
  these.  Both tuples are closed, not prefixes or globs.
* It does not authorize anything under artifacts/, calibration/,
  configs/, inputs/ or truth/: no calibration artifact, threshold
  table, or benchmark content is in RC5's delta at all.
"""
from __future__ import annotations

import hashlib
import pathlib
from typing import NamedTuple

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: The engineering parent every old_sha256 below was computed against.
RC5_BASE_COMMIT = "69e33c778efb14362439941d25ebbfcfb1068284"
RC5_BASE_TAG = "engineering-rc4-2-1-integrity-closure"

#: The frozen science contract RC5 implements.
A3_5_SCIENCE_FREEZE_COMMIT = "560bf28568e2762c60edc994aac7f2b6de14081f"
A3_5_SCIENCE_FREEZE_TAG = "benchmark-content-freeze-a3-5"
A3_5_SCIENCE_FREEZE_TAG_OBJECT = "533777b73748e3c45dd1ecbda07098ba9837c587"

RC5_RECONCILIATION_MD = "audit/MURU_RC5_POST_A3_5_FREEZE_RECONCILIATION.md"
RC5_RECONCILIATION_JSON = "audit/muru_rc5_post_a3_5_freeze_reconciliation.json"


class AuthorizedChange(NamedTuple):
    path: str
    defect_id: str
    #: SHA-256 of the pre-change bytes. None means the path did not exist
    #: at the engineering parent (a purely additive file).
    old_sha256: str | None
    #: SHA-256 of the exact RC5-frozen post-change bytes.
    new_sha256: str
    semantic_scope: str
    old_blob_sha1: str | None
    new_blob_sha1: str


_MODIFIED = (
    AuthorizedChange(
        path='src/muru/paper_benchmark/preflight.py',
        defect_id='RC5-MECH-1 (partition-aware preflight)',
        old_sha256='4ead750b4fec8990b80745946fa8ee115a08bd05f3d215122fdde87bd58076cb',
        new_sha256='13b41e02a3715be1733d5f28e5002f6d86085be114cc47634703af1e3be3a8c4',
        semantic_scope=(
            'run_preflight takes a partition, defaulting to "development", and reads the expected case count from the frozen registry instead of the literal 80. The default call is unchanged field for field; held_out_accessed reports the truth rather than a constant. No scientific behaviour, no authorisation logic, no threshold.'
        ),
        old_blob_sha1='76767ecac84970791a68a0dfb5ad5948d8618f4e',
        new_blob_sha1='c60f6ee73fad8e984e3d288bdadf031693e36108',
    ),
    AuthorizedChange(
        path='src/muru/paper_benchmark/structural_acceptance.py',
        defect_id='RC5-D1+D3 (A3.5 obligations 14, 17, 18)',
        old_sha256='ab4a54b11b1012d1f08f09a6fc1bdac4631fb9d486fc409121cc7640ea0c602a',
        new_sha256='3e0ff3c3bf7aaa32c203efec58a20f73c0e1d710766d83ae5d5929625f5b226c',
        semantic_scope=(
            "Gate 7's waiver gains the candidate_test_r2 >"
            'null_threshold[min(complexity,20)] conjunct and StructuralCandidate gains that field; F5_SCAFFOLD_HOLDOUT is dropped from FalsificationRung; REQUIRED_FALSIFICATION_RUNGS becomes REQUIRED_HARD_GATES = {F1,F4,F7,F10}; check_falsification_harness becomes the fail-closed check_gate8 (result != PASS). CEILING_FRACTION_GATE=0.80, CEILING_WAIVER_THRESHOLD=0.05, STABILITY_GATE=20, STABILITY_DENOMINATOR=30, MAX_COMPLEXITY=20, MAX_INVALID_FRACTION=0.005 and Gates 1-6 are all unchanged.'
        ),
        old_blob_sha1='71d48361858e0661fe8fb1dcba124bba5be8635d',
        new_blob_sha1='1527004a21aea920629bc84b1f04812bb2a47c95',
    ),
    AuthorizedChange(
        path='src/muru/paper_benchmark/rc3_record.py',
        defect_id='RC5-D4 (A3.5 obligation 19)',
        old_sha256='a1359e1e96ba268396dec7c21cfddffdc4110d817b4ddeb70b0b86161e7c0ff7',
        new_sha256='3947f22667f047c76505d58cdee1531ec66e71548799d232cb650252d900bf15',
        semantic_scope=(
            'RECORD_SCHEMA_VERSION bumped to muru-rc5-case-record-2.0.0, with record_schema_generation refusing to read a legacy record as current; HARD_GATE_ORDER narrows to the four hard gates; candidate_test_r2, f9_stress_test_result, f9_stress_test_metric and f9_acceptance_calibration_status added; __post_init__ requires the hard gates and the F9 pair exactly when the case reached Gate 8, and refuses them otherwise. Canonical serialization, digest convention and the provenance-sidecar split are unchanged.'
        ),
        old_blob_sha1='fbd81ec7b1655a27f4d4aaaf64a11827d28dcd49',
        new_blob_sha1='47f7d8643c43a4be629bf79cb1ce78d66fc186e6',
    ),
    AuthorizedChange(
        path='src/muru/paper_benchmark/rc3_acceptance.py',
        defect_id='RC5-D2 (A3.5 obligation 13)',
        old_sha256='882c12f6e0e312075aa6d94541d288456e0f69aae682c1007f6d8131d94de93b',
        new_sha256='bf10b44ee7f2582c9aa8805639b8186f4a0ad233fb9bedfed61990cbec13526b',
        semantic_scope=(
            'candidate_from_record projects candidate_test_r2 and'
            "TRUTH_BLIND_FIELDS names it, so Gate 7's waiver floor is re-"
            'derivable from the record alone. No truth field is added; the projection still carries no planted truth.'
        ),
        old_blob_sha1='0458e12478a258b5cb3057a55cf88b94c4017e40',
        new_blob_sha1='127693754f212f005370590b7f10932f0cfaebc9',
    ),
    AuthorizedChange(
        path='src/muru/paper_benchmark/rc3_ceiling.py',
        defect_id='RC5-D1 (A3.5 obligation 17)',
        old_sha256='bf8574c0a13cb7aa3c6648e20c2380846a3b985064af0880b3bf2dbebd8ecbf0',
        new_sha256='c634fb9b44e5778c961ae1467a2479f1ffec4da33aaf03ce0ff9597183c304c4',
        semantic_scope=(
            'Removes the SUPERSEDED Gate-7 verdict. Obligation 17 names this '
            "module's previous unconditional-waiver form as precisely what must "
            'NOT be implemented, yet ceiling_satisfied (= gate_passed or '
            'waiver_applied) was still live and exported, and was '
            'acceptance-favouring wherever the candidate floor fails. '
            'ceiling_satisfied is deleted and waiver_applied is renamed '
            'waiver_regime, because it is only the CEILING half of the amended '
            'waiver. Gate 7 is now decided solely by '
            'evaluate_structural_acceptance, which has the threshold table and '
            'the complexity this module deliberately does not. The estimator, '
            'its frozen hyperparameters, the sklearn pin, the train/score '
            'partitions, ceiling_r2, candidate_r2, ceiling_fraction and '
            'gate_passed are all unchanged.'
        ),
        old_blob_sha1='0341b0e6d31e0d7cc4d5be0a28760acc5a824c44',
        new_blob_sha1='2d2fbb775d5f3ade601663c6bbd93d6b51f89edb',
    ),
    AuthorizedChange(
        path='tests/test_rc3_ceiling.py',
        defect_id='RC5-D1 tests',
        old_sha256='daac303500dafb790e340daa667628871c0818a59a2d6789f6c2ec7d223dcb49',
        new_sha256='b029560c81f4df013e310feea7d56b5c9dc2dc826eaeb12fc05aeb91bcf7302f',
        semantic_scope=(
            'The test that entrenched the superseded rule (assert '
            'estimate.ceiling_satisfied) is replaced by three that pin the '
            'amended contract: the low-ceiling REGIME is detected but decides '
            'nothing, no Gate-7 verdict is offered by this module at all, and '
            'the regime with a failing floor still yields REJECTED_CEILING. No '
            'test weakened, skipped or xfailed.'
        ),
        old_blob_sha1='3d5fcd693cbade51e7fda685fe64b3e853cd180d',
        new_blob_sha1='9080e74a531c09aa69f2261ca895f5923eba23ec',
    ),
    AuthorizedChange(
        path='tests/test_a3_1_structural_acceptance.py',
        defect_id='RC5-D1+D3 tests',
        old_sha256='f9388034a0ab04b711f79b872bec065162cdd72e254605ca67e7caca2ec87855',
        new_sha256='2db69f92beb89770ca2aede1ecbe6c463d4a4ce4f4037bb8aae6a25e797ee440',
        semantic_scope=(
            'Gate-7 waiver tests gain floor-pass, floor-fail, strictness and capped-index cases; Gate-8 tests re-parametrise over the four hard gates and add missing-rung, NOT_APPLICABLE-blocks, F5-not-gating and F9-not-gating assertions. No test weakened, skipped or xfailed.'
        ),
        old_blob_sha1='780fd254836f4eebccf95e691893d7029d00ae65',
        new_blob_sha1='7cc9190d25482cb54b1d5b7008d393677e2e13ca',
    ),
    AuthorizedChange(
        path='tests/test_rc3_record.py',
        defect_id='RC5-D4 tests',
        old_sha256='eb2588555fb06c340dd6bc2cc9ece17fe0c65c5acd622d734472998da4d910f7',
        new_sha256='057573483d15957c8c7e6ae28349bfa95a9238f5d0ab33a158ae7fc89a837f43',
        semantic_scope=(
            'Six-rung assertions become four-rung; new coverage for the F9 secondary fields, the non-hard-gate refusal, the reached-Gate-8 conditionality, the schema version bump and legacy-record identification.'
        ),
        old_blob_sha1='c77b222b4ac4be76e5668d50267b34f3d603d12a',
        new_blob_sha1='c174777ac5fca8e5f3d28a0aa2d9e99c2e1aa045',
    ),
    AuthorizedChange(
        path='tests/test_rc3_acceptance.py',
        defect_id='RC5-D2 tests',
        old_sha256='4500eb9f563debe4f45ac8f065a39eb35017ced197d462d15a67fe40271674a6',
        new_sha256='78d0156f4014af38208c5da07b37e821899733fb7d1509b077aa1a4312e9b04b',
        semantic_scope=(
            'The no-candidate fixture is corrected to carry no rung results (it'
            "never reached Gate 8), and a new test proves Gate 7's waiver floor"
            'is reproducible from the record alone.'
        ),
        old_blob_sha1='fd4fb8ceb0101a162732eed9f828d9e6e6d76a11',
        new_blob_sha1='a4316e7d3db0d08ea1d51ae1aaf62b9eb6276097',
    ),
)

_ADDED = (
    AuthorizedChange(
        path='src/muru/paper_benchmark/identity_contract.py',
        defect_id='RC5 provenance-preserved import (A3.5 section 14.1)',
        old_sha256=None,
        new_sha256='faeff55fcc9a13cc349008964226971ccb3c6e47b2b325b7e5a5a3e2cc7eba1f',
        semantic_scope=(
            'imported byte-identical from the A3.5 science freeze 560bf28568e2762c60edc994aac7f2b6de14081f, blob 151867cbee4cf60189afc5c393d0c8f3ca77c6a0: the frozen positive- scale-invariant cross-seed identity contract'
        ),
        old_blob_sha1=None,
        new_blob_sha1='151867cbee4cf60189afc5c393d0c8f3ca77c6a0',
    ),
    AuthorizedChange(
        path='src/muru/paper_benchmark/seed_band_registry.py',
        defect_id='RC5 provenance-preserved import (A3.5 section 8.1)',
        old_sha256=None,
        new_sha256='1409b203f8b18737178d64242573e5c875f8ededbf0e41fb50301b316da4e0b7',
        semantic_scope=(
            'imported byte-identical from 560bf28568e2762c60edc994aac7f2b6de14081f, blob b6b127ef11fc7f2c46379acd089755057f5ee7cb: the frozen seed-band governance registry'
        ),
        old_blob_sha1=None,
        new_blob_sha1='b6b127ef11fc7f2c46379acd089755057f5ee7cb',
    ),
    AuthorizedChange(
        path='src/muru/paper_benchmark/rc5_seeds.py',
        defect_id='RC5-D6',
        old_sha256=None,
        new_sha256='1e655385c2d032e72d26f88803a7248d37acd16be5b04d95805861a8697a2506',
        semantic_scope=(
            "new, purely additive: A3.5 section 8.1's injective ordinal"
            'search_seed plus the mandatory verify_search_seed_invariants'
        ),
        old_blob_sha1=None,
        new_blob_sha1='e58719af0c97bc8a8722c79eb025af54be8c4fc6',
    ),
    AuthorizedChange(
        path='src/muru/paper_benchmark/rc5_estimate.py',
        defect_id='RC5-D14',
        old_sha256=None,
        new_sha256='e198e3fad40100e396f244c1055fe65b977b20e05ac98d3dbd0901d507c0d0f4',
        semantic_scope=(
            'new, purely additive: the two-stage Phi/g fit at E_REF=45.0, the raw-g search target, and invalid_fraction over denominator 30'
        ),
        old_blob_sha1=None,
        new_blob_sha1='48530b5a434fda173dbed118b0773c34443b176c',
    ),
    AuthorizedChange(
        path='src/muru/paper_benchmark/rc5_adapter.py',
        defect_id='RC5-D12',
        old_sha256=None,
        new_sha256='fa58f696fc69c4553f70048a48adec27879d191922d2568098fc50cef5351753',
        semantic_scope=(
            'new, purely additive: the case-to-search design and Gate-2 input provenance from the calibration path'
        ),
        old_blob_sha1=None,
        new_blob_sha1='230e6b440cdc57ee72f7a00d944121078c708952',
    ),
    AuthorizedChange(
        path='src/muru/paper_benchmark/rc5_selection.py',
        defect_id='RC5-D11+D13',
        old_sha256=None,
        new_sha256='a27257dd5c4d1fa3a33cb5361458b012b6261bc5bbd644575a9adf0a2621a05c',
        semantic_scope=(
            'new, purely additive: per-seed retention, cross-seed grouping by the frozen identity contract, selection_count and representative selection'
        ),
        old_blob_sha1=None,
        new_blob_sha1='e930412c4e689ec674831278d84fe0764e7e8f4c',
    ),
    AuthorizedChange(
        path='src/muru/paper_benchmark/rc5_falsify.py',
        defect_id='RC5-D7',
        old_sha256=None,
        new_sha256='0dfaeb56da8e81aa530aaf8609c33da9c6559c0e987fa64b5e7b1ee05494df8c',
        semantic_scope=(
            'new, purely additive: the five per-case falsification procedures under A3.5 section 6 as amended by 6.9'
        ),
        old_blob_sha1=None,
        new_blob_sha1='56dc86a96c566fd4d8129dd7d23827f691b4fe8f',
    ),
    AuthorizedChange(
        path='src/muru/paper_benchmark/rc5_g1_bridge.py',
        defect_id='RC5-D8',
        old_sha256=None,
        new_sha256='7d76b00005880af174cbfa463e24a20fa23213f1b8910e9331c3000c48a60ac7',
        semantic_scope=(
            "new, purely additive: G1's leave-one-energy-out trajectory bridge"
            'under A1.2/A1.3/A1.4'
        ),
        old_blob_sha1=None,
        new_blob_sha1='ff32a4363336a95993e8644d2ccdabe99431dd33',
    ),
    AuthorizedChange(
        path='src/muru/paper_benchmark/rc5_manifest.py',
        defect_id='RC5-D9',
        old_sha256=None,
        new_sha256='5a8f102f6f16de0c5ec0a9dc43000562693960666419a8774f68ad19fac90354',
        semantic_scope=(
            'new, purely additive: the two-layer pre-execution manifest of A3.5 section 8.4'
        ),
        old_blob_sha1=None,
        new_blob_sha1='32c3e054973e92d222946e4cd25b9dfbb210167d',
    ),
    AuthorizedChange(
        path='src/muru/paper_benchmark/rc5_store.py',
        defect_id='RC5 mechanical',
        old_sha256=None,
        new_sha256='8a20e62205cd932cea299a0e1042cd98cf53d2f9515dcbc6dfc42c6326f9188c',
        semantic_scope=(
            'new, purely additive: the case-scoped seed store, atomic case- record writes and deterministic resume'
        ),
        old_blob_sha1=None,
        new_blob_sha1='53e088146fb2e39d04821100db340f9a0ee9ddd1',
    ),
    AuthorizedChange(
        path='src/muru/paper_benchmark/rc5_case_scoring.py',
        defect_id='RC5 mechanical + D10',
        old_sha256=None,
        new_sha256='fad92299443a63355e368d20ca00a775391ff0860bcb240d4efd757615db80f5',
        semantic_scope=(
            "new, purely additive: per-case wiring of A3.4's frozen scorers and"
            'the sole G3 authority'
        ),
        old_blob_sha1=None,
        new_blob_sha1='67eeb8bd39fd2a33eae6bf25cd572dc9b64b8f9d',
    ),
    AuthorizedChange(
        path='src/muru/paper_benchmark/rc5_runner.py',
        defect_id='RC5 runner',
        old_sha256=None,
        new_sha256='bacb9b96409f8fdd5818ff3a4a2293b3f4bf2cd68329d8060a82c96c38cdd377',
        semantic_scope=(
            'new, purely additive: the production case runner, composition only'
        ),
        old_blob_sha1=None,
        new_blob_sha1='f940115782f93e788d524eb19c54f484a9c29183',
    ),
)


#: RC5's OWN integrity-tooling delta, kept separate from the implementation
#: delta above exactly as RC4.2.1 kept its tooling change separate from RC4.2's
#: R1-R4 repair.
#:
#: Bootstrapping note, identical in shape to RC4.2.1's.  A3.1 declared its own
#: integrity script one of its protected-forever paths (``pb_34``'s
#: ``A3_1_PROTECTED_PATHS``), so teaching ``pb_33`` to recognize a ledger that
#: did not exist when it was written necessarily changes its bytes.  This
#: repairs no defect and touches no science surface (``scripts/``, not
#: ``src/muru/paper_benchmark/`` or ``tests/test_a3_*``): it swaps one import
#: from the RC4.2-only dict to the union view, so a path authorized by ANY
#: ledger is recognized.  The classification rule -- both old and new bytes
#: must match an entry exactly -- is untouched, and no protected path's
#: required identity is relaxed.
#:
#: **The entry below spans TWO successive authorized tooling changes, and says
#: so.**  ``pb_34`` and ``pb_35`` check ``pb_33`` against ``c8938e8`` /
#: ``1194fcb`` / ``be23b80``, where its bytes are ``d9b40cb6...`` -- the
#: *pre-RC4.2.1* state.  A ledger entry is keyed by path and matches one
#: (old, new) pair, so covering those baselines requires ``old_sha256`` to be
#: the pre-RC4.2.1 digest, which makes this entry's span
#: ``d9b40cb6 -> 3b8be3d7``: RC4.2.1's edit **and** RC5's, composed.  RC4.2.1's
#: own entry (``d9b40cb6 -> a8355fd4``) is deliberately left in place in
#: ``RC4_2_1_TOOLING_DELTA`` as the record of the intermediate state; it simply
#: stops matching once the current bytes move past it.  Attributing both edits
#: to RC5 would be false, so both are named here.
_TOOLING = (
    AuthorizedChange(
        path='scripts/pb_33_amendment_a3_1_integrity.py',
        defect_id='RC4.2.1 + RC5 tooling, composed (integrity, not a science change)',
        old_sha256='d9b40cb6d8fbcfd35cff43dca87190fa1984401508e2f646f2a14043038ebac3',
        new_sha256='3b8be3d70a48b6d1b4aa602152da6033c25cad3578f30ff2e2032878c2a8c589',
        semantic_scope=(
            'Two composed tooling edits, neither a science change. RC4.2.1: '
            'check_protected_paths returns (errors, authorized_delta_paths) '
            'instead of just errors and consults a delta ledger at all. RC5: '
            'that consultation moves from the RC4.2-only AUTHORIZED_BY_PATH to '
            'the union ALL_AUTHORIZED_BY_PATH, so a path authorized by any '
            'ledger is recognized instead of being reported as unauthorized '
            "drift. No protected path's required identity, no amendment logic, "
            'and no science surface is touched by either.'
        ),
        old_blob_sha1='ed17113065c975e37c2c1276145e5a160a2f8fef',
        new_blob_sha1='62e41d75d68a3b0f0aa8ba75c60e77388ac48a4e',
    ),
)

#: Modified protected paths.  Each was byte-identical at every freeze baseline
#: where it exists, so one entry serves every consuming script.
RC5_MODIFIED_DELTA: tuple[AuthorizedChange, ...] = _MODIFIED + _TOOLING

#: Purely additive paths under the protected tree.  Consulted by the drift
#: checks that compare the current tree against the RC4 parent.
RC5_ADDED_DELTA: tuple[AuthorizedChange, ...] = _ADDED

RC5_AUTHORIZED_DELTA: tuple[AuthorizedChange, ...] = RC5_MODIFIED_DELTA + RC5_ADDED_DELTA

RC5_AUTHORIZED_BY_PATH: dict[str, AuthorizedChange] = {
    change.path: change for change in RC5_AUTHORIZED_DELTA
}

if len(RC5_AUTHORIZED_BY_PATH) != len(RC5_AUTHORIZED_DELTA):  # pragma: no cover
    raise ImportError("the RC5 delta ledger contains a duplicate path")


def authorized_paths() -> frozenset[str]:
    return frozenset(RC5_AUTHORIZED_BY_PATH)


def verify_ledger_against_tree(root: pathlib.Path = ROOT) -> dict[str, list[str]]:
    """Recompute every pinned new_sha256 from the working tree.

    Returned rather than asserted, so a caller can record the *computed*
    result instead of a hardcoded True.  A non-empty mismatched or
    missing means the ledger no longer describes the tree it transcribes,
    which is itself an integrity failure.
    """
    mismatched: list[str] = []
    missing: list[str] = []
    for change in RC5_AUTHORIZED_DELTA:
        candidate = root / change.path
        if not candidate.is_file():
            missing.append(change.path)
            continue
        if hashlib.sha256(candidate.read_bytes()).hexdigest() != change.new_sha256:
            mismatched.append(change.path)
    return {"mismatched": sorted(mismatched), "missing": sorted(missing)}


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(verify_ledger_against_tree(), indent=2))
