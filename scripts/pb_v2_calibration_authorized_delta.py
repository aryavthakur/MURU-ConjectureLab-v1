"""v2-calibration authorized delta ledger (Stage 1 launch remediation).

What this closes
-----------------
`scripts/pb_37_environment_closure.py` flags `SCIENCE_DRIFT_VS_RC4_PARENT` for
ten files under `src/muru/paper_benchmark/` that differ from the RC4 parent
commit (`c800e7a59eca904ee32231e43ce3d1ddda4a26ee`) and are not present in any
of the three existing ledgers (`pb_rc4_2_authorized_delta.AUTHORIZED_DELTA`,
`RC4_2_1_TOOLING_DELTA`, `pb_rc5_a3_5_authorized_delta.RC5_AUTHORIZED_DELTA`).
That detection is correct, not a bug: none of the ten postdates RC4.2/RC4.2.1/
RC5 in a way any existing ledger was built to recognize.

This module is the same kind of object those three are: a closed, hash-pinned
ledger, each entry binding path, exact old/new SHA-256, exact old/new git blob
SHA-1, and a semantic-scope statement -- authored per the owner's 2026-08-20
"OWNER DECISION: CLOSE PB_37 FAST, THEN LAUNCH STAGE 1" instruction (see
Provenance below), following an independent file-by-file provenance
adjudication against the RC4 parent commit, not a self-declared "no science
changed" flag.

Provenance
----------
Owner instruction (verbatim, this session, 2026-08-20), authorizing exactly
this remediation:

    "OWNER DECISION: CLOSE PB_37 FAST, THEN LAUNCH STAGE 1 ... 3. RESOLVE THE
    10 SCIENCE_DRIFT_VS_RC4_PARENT FILES BY AUDIT, NOT ASSUMPTION ... 4. USE
    THE EXISTING AUTHORIZED-DELTA PRECEDENT ... If and only if all 10 flagged
    files are demonstrated to be legitimate pre-existing v2 changes that were
    made before the relevant results and are already supported by repository
    history, construct the narrowest possible v2 authorized-delta ledger
    using the same hash-pinned semantics as the prior accepted ledgers ...
    If even one file cannot be justified from the historical record, stop
    that file and report it explicitly rather than forcing the ledger to
    pass."

Issued before any Stage 1 result exists (`results/v2_calibration_surface/
INTEGRITY_WATCH.json`: `checkpoints_present: 0` at authoring time) --
satisfies this project's "condition A".

Independent adjudication basis
-------------------------------
Each entry below was verified independently (not merely cited from a
self-declaration) via `git log`, `git diff`, `git show` against the RC4
parent commit for every one of the ten files, cross-referenced against the
dedicated audit documents each change is already recorded in:
`audit/muru_v2_reentry_20260819/V3_REPAIR_LEDGER.md`,
`audit/muru_v2_reentry_20260819/V2C_PROTOCOL_FREEZE_MANIFEST.json`,
`audit/MURU_HELDOUT_RESTORATION_FINAL_DISPOSITION.md`,
`audit/MURU_HELDOUT_RESTORATION_HOSTILE_REVIEW.md`,
`audit/MURU_HELDOUT_SUPERSESSION_LEDGER.md`,
`audit/MURU_RC5_1_FINAL_HOSTILE_REVIEW.md`,
`audit/MURU_HELDOUT_RESCUE_AUTHORITY_MATRIX.md`. Nine of the ten files were
found byte-identical to the exact bytes those audit documents already pin as
frozen. The tenth (`rc5_authorization.py`) required composing this ledger's
entry across two prior, independently-disclosed changes (RC5's original
addition and the A3.6/RC5.1 partition amendment) because no ledger entry for
its current bytes existed anywhere -- a gap the project's own audit trail
already named three times (see that entry below) but never closed with an
instrument. This ledger closes it.

**One caveat carried forward, not silently dropped**: the commit that
created `calibration_seed_band.py`/`calibration_surface.py` (`61375e08`)
self-discloses an adjacent process violation concerning a *different*
instrument (Stage 0/D-INST re-run after inspecting a prior failure). It does
not describe either of these two files' own content. D-INST is a diagnostic,
not a gate, per the protocol's own text: "This is a diagnostic, not a gate.
It licenses nothing." (`audit/muru_v2_reentry_20260819/
MURU_V2_E2A_INSTRUMENT_DIAGNOSTIC_PROTOCOL.md`, line 17 -- verified directly
against that file's current text; a prior draft of this ledger cited a
nonexistent file, `DINST_NONBLOCKING_DETERMINATION.md`, for this point, which
is corrected here). It is recorded here for anyone auditing this ledger
later, exactly because it is the closest thing to a red flag found in the
whole set.

What this module deliberately does NOT do
------------------------------------------
* It does not change what any script's historical byte-identity check means
  for any path outside this ten-entry, closed tuple.
* It does not touch `RECORDED_PROTECTED_AGGREGATE` or any other historical
  digest, and does not modify any of the three prior ledgers' own entries.
* It does not authorize an eleventh file or a different byte pattern for any
  of these ten. The tuple is closed, not a prefix or a glob.
* It does not authorize anything under `artifacts/`, `calibration/`,
  `configs/`, `inputs/`, or `truth/`.
"""
from __future__ import annotations

import hashlib
import pathlib
from typing import NamedTuple

ROOT = pathlib.Path(__file__).resolve().parent.parent

RC4_PARENT_COMMIT = "c800e7a59eca904ee32231e43ce3d1ddda4a26ee"


class AuthorizedChange(NamedTuple):
    path: str
    defect_id: str
    old_sha256: str | None
    new_sha256: str
    semantic_scope: str
    old_blob_sha1: str | None
    new_blob_sha1: str


#: All ten files are purely additive relative to the RC4 parent commit (none
#: existed at c800e7a5; verified via `git cat-file -e`). old_sha256/
#: old_blob_sha1 are therefore None for every entry, per the same convention
#: `pb_rc4_2_authorized_delta.py` and `pb_rc5_a3_5_authorized_delta.py` use
#: for their own purely-additive entries.
V2_CALIBRATION_AUTHORIZED_DELTA: tuple[AuthorizedChange, ...] = (
    AuthorizedChange(
        path="src/muru/paper_benchmark/calibration_seed_band.py",
        defect_id="V2C-DEF-C1 (verify_band overlap-check repair)",
        old_sha256=None,
        new_sha256="1b9e097a963757938bc1b13763f381ffd7e96a90474b7768cac001c057620597",
        semantic_scope=(
            "Created 61375e08 (2026-08-19), edited faad279f (2026-08-19, "
            "'Protocol v3: all 45 v2 defects dispositioned'), unchanged since. "
            "Population/seed-disjointness declaration, module docstring states "
            "'ENTIRELY OUTSIDE the byte-frozen benchmark files', not a "
            "benchmark partition. faad279f's edit makes verify_band() also "
            "check unacknowledged_overlaps() (previously checked only "
            "find_overlaps(), the wrong registry function -- a strictly "
            "stricter fix, not a loosening; disclosed and dispositioned as "
            "DEF-M7/G20 in V3_REPAIR_LEDGER.md). Byte-pinned in "
            "V2C_PROTOCOL_FREEZE_MANIFEST.json since faad279f; "
            "V2C_TUNING_LEDGER.json empty since. Not touched by any later "
            "protocol round (v4-v6, ending 899d9b0 'BOTH hostile reviews PASS "
            "after six rounds')."
        ),
        old_blob_sha1=None,
        new_blob_sha1="a65b9201f63ccfecd4cf5f9267b27dabeca01d24",
    ),
    AuthorizedChange(
        path="src/muru/paper_benchmark/calibration_surface.py",
        defect_id="V2C-DEF-M7 (derived-predicate family check)",
        old_sha256=None,
        new_sha256="8aa667338b4a22f3acb1429bc30b205adb9b1373d553e4b0ce92710fe251f000",
        semantic_scope=(
            "Created 61375e08, edited faad279f, unchanged since (same commit "
            "pair as calibration_seed_band.py). Replaces a hand-transcribed "
            "literal family tuple with a predicate derived from frozen "
            "registry fields, asserting the derived result still equals the "
            "original literal and refusing to import on drift (fail-closed). "
            "Byte-pinned in V2C_PROTOCOL_FREEZE_MANIFEST.json; disclosed as "
            "DEF-M7 in V3_REPAIR_LEDGER.md, cross-checked in "
            "CRITIC_SCIENCE_V3_REVIEW.md / CRITIC_GOVERNANCE_V3_REVIEW.md."
        ),
        old_blob_sha1=None,
        new_blob_sha1="5ffa8e7833ff778edb2e7a056ad3c42dac071aaa",
    ),
    AuthorizedChange(
        path="src/muru/paper_benchmark/heldout_contract_analysis.py",
        defect_id="Held-out restoration (calls frozen scorers, no reimplementation)",
        old_sha256=None,
        new_sha256="84f4a22fb94ce9033d03f9c70eb9ef556f04a277ef9417c2ff7be534a5f1639f",
        semantic_scope=(
            "Single commit 1f5b9076 (2026-08-16, 'RESTORATION OF "
            "ALREADY-FROZEN ANALYSIS CONTRACT'), never touched again. "
            "Replaces a superseded self-reimplementing analysis layer with "
            "one that calls the already-frozen scorers; commit states `git "
            "diff 8d87143 HEAD -- src/` empty for all frozen scorer modules, "
            "no search rerun, evidence root untouched. Documented in "
            "MURU_HELDOUT_RESTORATION_REQUIREMENT_MAP.md, "
            "MURU_HELDOUT_RESTORATION_HOSTILE_REVIEW.md (7 lenses, 66 checks, "
            "0 failures, 13 mutation tests proving each lens can fail), "
            "MURU_HELDOUT_RESTORATION_FINAL_DISPOSITION.md (hash table "
            "matches exactly), MURU_HELDOUT_SUPERSESSION_LEDGER.md. "
            "Post-hoc-tuning check in the hostile review (§7): agreement "
            "reproduces sealed evidence b750d5c0 fixed before this commit "
            "existed; every correction moves the reported verdict against "
            "the reporting party's own interest (permissive -> failure)."
        ),
        old_blob_sha1=None,
        new_blob_sha1="3fa421993f8e9f6be41d2166e0f088cfd6e9ff84",
    ),
    AuthorizedChange(
        path="src/muru/paper_benchmark/heldout_endpoint_populations.py",
        defect_id="Held-out restoration (calls frozen scorers, no reimplementation)",
        old_sha256=None,
        new_sha256="2aaa0541090f2e0da50fe8f93ad7aac09d661e24e11ec07bbaa69a47dd14ae93",
        semantic_scope=(
            "Same commit (1f5b9076) and evidentiary basis as "
            "heldout_contract_analysis.py above; see that entry."
        ),
        old_blob_sha1=None,
        new_blob_sha1="fb7e24cdbf3200d214ee811f9a681f3cb25d35f7",
    ),
    AuthorizedChange(
        path="src/muru/paper_benchmark/heldout_g1_recovery.py",
        defect_id="Held-out restoration (calls frozen scorers, no reimplementation)",
        old_sha256=None,
        new_sha256="92b9cdc9bf217a9e5efb49ed84d86b315c1f061e5f22f1bda71e0a157fe6adcb",
        semantic_scope=(
            "Same commit (1f5b9076) and evidentiary basis as "
            "heldout_contract_analysis.py above; see that entry."
        ),
        old_blob_sha1=None,
        new_blob_sha1="005e5c6e0fbd3ab07c09ee11c1d65244b15a5f58",
    ),
    AuthorizedChange(
        path="src/muru/paper_benchmark/heldout_hostile_lenses.py",
        defect_id="Held-out restoration (calls frozen scorers, no reimplementation)",
        old_sha256=None,
        new_sha256="3fcd44e575f4907c4b319fbda0515e532c6be03061803b707fcff4857b1af279",
        semantic_scope=(
            "Same commit (1f5b9076) and evidentiary basis as "
            "heldout_contract_analysis.py above; see that entry."
        ),
        old_blob_sha1=None,
        new_blob_sha1="8e640c1eabe31120609eef1010b2aee3f27b9b4c",
    ),
    AuthorizedChange(
        path="src/muru/paper_benchmark/heldout_independent_scoring.py",
        defect_id="Held-out restoration (calls frozen scorers, no reimplementation)",
        old_sha256=None,
        new_sha256="305051a45991bf370d0103d84e9f8cd38d77ed4b042227e397c77d54ec1f875a",
        semantic_scope=(
            "Same commit (1f5b9076) and evidentiary basis as "
            "heldout_contract_analysis.py above; see that entry."
        ),
        old_blob_sha1=None,
        new_blob_sha1="131c419de3579a1987ea26470f609a88cd82d9a9",
    ),
    AuthorizedChange(
        path="src/muru/paper_benchmark/post_execution_sealer.py",
        defect_id="Held-out restoration (calls frozen scorers, no reimplementation)",
        old_sha256=None,
        new_sha256="37eab2f7799cac24c368d5d93e4d472520908819e91ff1d42b0cb272714009dc",
        semantic_scope=(
            "Same commit (1f5b9076) and evidentiary basis as "
            "heldout_contract_analysis.py above; see that entry."
        ),
        old_blob_sha1=None,
        new_blob_sha1="488a9e353a563ae9e9ab49ec51e9daa32a638777",
    ),
    AuthorizedChange(
        path="src/muru/paper_benchmark/rc5_record_payload.py",
        defect_id="Held-out restoration (calls frozen scorers, no reimplementation)",
        old_sha256=None,
        new_sha256="407cc3a5728a0435f009cdbea785ef1f83e9cf97735b4a7b3e8a2cec3cd284cf",
        semantic_scope=(
            "Same commit (1f5b9076) and evidentiary basis as "
            "heldout_contract_analysis.py above; see that entry."
        ),
        old_blob_sha1=None,
        new_blob_sha1="7f068991dd6169f2953b36b7d3f5a7166862e9a7",
    ),
    AuthorizedChange(
        path="src/muru/paper_benchmark/rc5_authorization.py",
        defect_id="RC5 addition + A3.6/RC5.1 partition amendment, composed",
        old_sha256=None,
        new_sha256="e8fc53c50fb8873cc4989db03e49ec5beb33872967f7cc1c4f5a14be8272ed2c",
        semantic_scope=(
            "Composed span, both halves independently disclosed: (1) RC5's "
            "original addition, commit 97b28d38 (2026-08-15), already pinned "
            "in pb_rc5_a3_5_authorized_delta.RC5_AUTHORIZED_BY_PATH as "
            "old_sha256=None -> new_sha256=fd1dfe74... "
            "('the frozen partition authorization contract enforcing "
            "development partition exclusivity'); (2) commit 8d87143 "
            "(2026-08-16, 'MURU Engineering RC5.1: Amendment A3.6 "
            "implementation and freeze'), whose sole semantic edit to this "
            "file is `AUTHORISED_PARTITIONS = frozenset({\"development\"})` "
            "-> `frozenset({\"development\", \"held_out\"})` -- no endpoint, "
            "gate, falsification, scoring, registry, selection, or manifest "
            "module modified (verified in "
            "audit/MURU_HELDOUT_RESCUE_AUTHORITY_MATRIX.md: 'authorization-"
            "only. Verified, not assumed.'). Disclosed independently in "
            "MURU_RC5_1_FINAL_ENGINEERING_DECISION.md, "
            "MURU_RC5_1_FINAL_HOSTILE_REVIEW.md ('UNANIMOUS PASS 4/4 "
            "lenses'), and rediscovered from a separate worktree in "
            "MURU_CHALLENGE_BLIND_ADJUDICATION.md. This is the exact gap "
            "MURU_HELDOUT_SUPERSESSION_LEDGER.md §5 names explicitly: "
            "'A3.6 legitimately changed AUTHORISED_PARTITIONS ... but did so "
            "on a file pinned by the A3.5 ledger without recording that in "
            "an A3.6 ledger ... Not repaired here, deliberately ... The "
            "correct instrument is an A3.6 ledger or erratum.' This entry is "
            "that instrument."
        ),
        old_blob_sha1=None,
        new_blob_sha1="4ff7a24adeeeeb5391b8f0d6a8efecc610091d91",
    ),
)

V2_CALIBRATION_AUTHORIZED_BY_PATH: dict[str, AuthorizedChange] = {
    change.path: change for change in V2_CALIBRATION_AUTHORIZED_DELTA
}

if len(V2_CALIBRATION_AUTHORIZED_BY_PATH) != len(V2_CALIBRATION_AUTHORIZED_DELTA):  # pragma: no cover
    raise ImportError("the v2-calibration delta ledger contains a duplicate path")


def authorized_paths() -> frozenset[str]:
    return frozenset(V2_CALIBRATION_AUTHORIZED_BY_PATH)


def verify_ledger_against_tree(root: pathlib.Path = ROOT) -> dict[str, list[str]]:
    """Recompute every pinned new_sha256 from the working tree.

    Returned rather than asserted, so a caller can record the *computed*
    result instead of a hardcoded True.
    """
    mismatched: list[str] = []
    missing: list[str] = []
    for change in V2_CALIBRATION_AUTHORIZED_DELTA:
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
