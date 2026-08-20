"""RC4.2 authorized engineering-defect-repair delta ledger.

Problem this closes (RC4.2.1, Issue 1)
---------------------------------------
RC4.2 (`audit/MURU_RC4_2_CORE_DEFECT_REPAIR.md`, tag
`engineering-rc4-2-core-defect-repair`) repaired four independently-confirmed
implementation defects (R1-R4) inside files multiple frozen integrity scripts
byte-pin: `pb_30` (A1), `pb_32` (A2.1), `pb_35` (A3.4), and `pb_37`
(environment closure, via a science-drift-vs-RC4-parent check). Every one of
those scripts correctly flagged the six touched protected files as changed --
that detection is *working as designed*, not a bug -- and none of them was
modified to stop flagging. What was missing was a place for current-lineage
verification to know the difference between "an unlisted, unauthorized
change" and "the one specific, adjudicated, byte-pinned repair this project
already froze".

This module is that place. It is a closed, hash-pinned ledger of exactly the
eight files RC4.2 touched (six protected-path modifications plus two purely
additive new test files), each entry binding:

* the exact path,
* the defect ID it repairs (matching R1-R4 in the RC4.2 audit),
* the exact SHA-256 of the pre-repair (historical-freeze) bytes,
* the exact SHA-256 of the post-repair (RC4.2-frozen) bytes,
* a one-line statement of the allowed semantic scope.

A path/byte pair that is not *exactly* one of these entries is never treated
as authorized, no matter how small the further drift. This is deliberately
narrower than a path-name allowlist: renaming, re-touching, or extending any
of these eight files beyond the byte-pinned repair is rejected identically to
an entirely new unauthorized change, because the check compares hashes, not
just paths.

Nothing here is a new scientific choice. This ledger does not decide what is
authorized; it transcribes what `audit/MURU_RC4_2_CORE_DEFECT_REPAIR.md` and
`audit/muru_rc4_2_core_defect_repair.json` already recorded as frozen, so
that scripts written before RC4.2 existed can recognize it without their own
frozen historical-byte-identity assertions being edited, weakened, or
disabled.

What this module deliberately does NOT do
-------------------------------------------
* It does not change what any script's historical byte-identity check means.
  A caller that does not import this module still requires bit-for-bit
  identity to its frozen commit, exactly as before RC4.2.1.
* It does not touch `RECORDED_PROTECTED_AGGREGATE` or any other historical
  digest. Those aggregates still describe the historical frozen bytes; this
  module is consulted only for the *current* tree, as a second, independent
  question ("is the live divergence from that history exactly the one
  authorized delta?").
* It does not authorize a ninth file, or a different byte pattern for any of
  the eight. `AUTHORIZED_DELTA` is a tuple, not a prefix or a glob.
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent.parent

#: The RC4.2 freeze this ledger transcribes, recorded for provenance. The
#: entries below were computed against this exact commit; the ledger itself
#: is a static transcription, not re-derived from it at import time.
RC4_2_BASE_COMMIT = "a605120242594d23a5fc36d2e622d7d3084356fb"
RC4_2_FREEZE_TAG = "engineering-rc4-2-core-defect-repair"
RC4_2_AUDIT_MD = "audit/MURU_RC4_2_CORE_DEFECT_REPAIR.md"
RC4_2_AUDIT_JSON = "audit/muru_rc4_2_core_defect_repair.json"


class AuthorizedChange(NamedTuple):
    path: str
    defect_id: str
    #: SHA-256 of the pre-repair bytes. ``None`` means the path did not exist
    #: at any historical freeze point RC4.2 predates (purely additive file).
    old_sha256: str | None
    #: SHA-256 of the exact RC4.2-frozen post-repair bytes.
    new_sha256: str
    #: One-line statement of what changed and, as important, what did not.
    semantic_scope: str
    #: git blob SHA-1 (``git hash-object``), reproduced from the published
    #: RC4.2 report table for independent cross-reference. Not used for
    #: comparison (SHA-256 of raw content is what every caller here already
    #: computes); kept only so this ledger and the audit document can be
    #: diffed against each other by inspection.
    old_blob_sha1: str | None
    new_blob_sha1: str


AUTHORIZED_DELTA: tuple[AuthorizedChange, ...] = (
    AuthorizedChange(
        path="src/muru/paper_benchmark/protocol.py",
        defect_id="R1/DEFECT_A",
        old_sha256="63c77d5732f0c339b99c20f7d91953324d053d4bb970ec08f10fac4666d85cf5",
        new_sha256="cb35289f68767036b8c4e96ce4763ede75b3fa146e5d51a18da704712110ed36",
        semantic_scope=(
            "estimate_one: log_g = clip(residual, *support) replacing "
            "clip(-residual, *support) -- removes an anti-monotone sign "
            "inversion against the frozen M0 law. Fold-locality, the "
            "(-2.0, 2.0) clip range, the estimator domain, and G1's "
            "thresholds (0.80 Spearman, 0.70 Wilson lower bound) unchanged."
        ),
        old_blob_sha1="a913a71ef17f41fba3c102b898cf2536b2b740f8",
        new_blob_sha1="8a8e3c548c8e6f25ab21974bd0a1be9159f5093b",
    ),
    AuthorizedChange(
        path="src/muru/paper_benchmark/g3_contract.py",
        defect_id="R2/DEFECT_B3",
        old_sha256="c09d849cf69bae0c183ba793a0ef117e27655defcdcc4145b12f457aee2f5a95",
        new_sha256="dcf5382ed5fac4236bd1c39755ac992436220d48ca50e8b314e0855e1eba866e",
        semantic_scope=(
            "adds classify_f07_event (structurally identical to "
            "classify_f19a_event/classify_f19b_event) and wires it as the "
            "dispatcher's first branch, replacing a ValueError for variant "
            "'F07'. classify_f19a_event through classify_f20c_event, "
            "G3_HELD_OUT_DENOMINATOR=36, G3_WILSON_UPPER_GATE=0.15 unchanged."
        ),
        old_blob_sha1="a2b2bc75a517f580af0ead97287b360b081b5693",
        new_blob_sha1="f327ad709f131f65253abb36efa2947e4b7ae16c",
    ),
    AuthorizedChange(
        path="src/muru/paper_benchmark/g2_contract.py",
        defect_id="R3/DEFECT_C + R4/DEFECT_D",
        old_sha256="502b1a65705d9c2d13c7680c3bbc4d307593185e8f60e5706150e6e092727fb5",
        new_sha256="29af866c5ff980de9149b137b6c9290b12e75092210772f37215a53f389d0817",
        semantic_scope=(
            "R3: binds square/cube/inv in _safe_parse's sympify locals "
            "(reproduced verbatim from grammar.py::_SYMPY_LOCALS) and aliases "
            "x{i} to the frozen GRAMMAR_PRIMITIVES Symbol objects, fixing "
            "cancellation/reordering and making unmapped raw symbols fail "
            "closed. R4: adds truth_support_for_case, a mechanical reader of "
            "TruthRecord.active_variables/symbolic_truth_kind, supplying the "
            "truth_support operand classify_support always required. "
            "GRAMMAR_PRIMITIVES, classify_support, evaluate_g2_event, "
            "G2_HELD_OUT_DENOMINATOR=144, G2_WILSON_LOWER_GATE=0.70 "
            "unchanged; discovery/equivalence.py not imported or duplicated."
        ),
        old_blob_sha1="3abc095ee58bce3bd5630a5680104c6f1220f765",
        new_blob_sha1="d2ee5ebc77c55498c94cb4c06256b6ab308f1562",
    ),
    AuthorizedChange(
        path="tests/test_paper_benchmark_protocol.py",
        defect_id="R1/DEFECT_A tests",
        old_sha256="4ee7ccbdca755d17373f0bcb13d6e19684c3c3ec3f052b9b557edda450f3f644",
        new_sha256="0919378a3ec6566796dc4d94c44cb2c3d300461bab14a1ba0eb7e1d40bf7f730",
        semantic_scope="6 new hand-built canary tests for R1's sign correction; no case_id/registry/generate_case/partition anywhere in the file.",
        old_blob_sha1="804bc13c9b0a206c8d83a5c63843eb88107f5abe",
        new_blob_sha1="63b1f7443fdeadc21a8a97bcf2f3f64d1ca35874",
    ),
    AuthorizedChange(
        path="tests/test_a3_1_g3_contract.py",
        defect_id="R2/DEFECT_B3 tests",
        old_sha256="bcbc51afeebd5db93865343fca043a04a7de2bbf62df361f3487b48cd95fc3eb",
        new_sha256="7fe99f8071599ea34725d4bb6cbc9e749d045e2dde76f0d45e56760339870dfc",
        semantic_scope="TestF07 (5 unit tests) + 3 dispatch tests + 'F07' added to the existing test_all_variants loop.",
        old_blob_sha1="fd9e4fbb9d2e56279928b6a949a74b529304a2e8",
        new_blob_sha1="49ffff2fa305df0effd06e9921f52035ca6e4360",
    ),
    AuthorizedChange(
        path="tests/test_a3_1_g2_contract.py",
        defect_id="R3/DEFECT_C tests",
        old_sha256="a74c6fa08575baf53200501064b9bfac425a0aa62ca1b5f9d696886033b138ba",
        new_sha256="16c90fb4298fc69863f9498f27cc69af4d4004f516299fcfd7b585300f4dd15c",
        semantic_scope="TestR3ParserSupportFeatureMapping (20 tests): the mission-mandated parser/support/feature-mapping fixture set.",
        old_blob_sha1="d156c128e1e1e7eb3c275cd5ba4e8a078fee61b8",
        new_blob_sha1="835323660555a7ecfbdc9a12909952997e5b52e2",
    ),
    AuthorizedChange(
        path="tests/test_g3_f07_dispatcher_equivalence.py",
        defect_id="R2/DEFECT_B3 tests (new file)",
        old_sha256=None,
        new_sha256="6e6b05d5b7e5ed6da0650e4bf0f251053fe7727d8510054822e54c2deda63d05",
        semantic_scope="new, purely additive: proves classify_f07_event, the dispatcher, and analysis.classify_negative_control agree.",
        old_blob_sha1=None,
        new_blob_sha1="95d4b57609e69134f8ac82524765885fb5ca4b1c",
    ),
    AuthorizedChange(
        path="tests/test_r4_g2_truth_support.py",
        defect_id="R4/DEFECT_D tests (new file)",
        old_sha256=None,
        new_sha256="e22595073b9586fa05a39ef7d88361ba9efe0e18e2193598c6c8c94eb5cf2875",
        semantic_scope="new, purely additive: hand-built + generate_case(development) cross-checks of truth_support_for_case.",
        old_blob_sha1=None,
        new_blob_sha1="7b534971bbc5c08624fdd3d8660af65a1097f7b2",
    ),
)

AUTHORIZED_BY_PATH: dict[str, AuthorizedChange] = {c.path: c for c in AUTHORIZED_DELTA}


# ---------------------------------------------------------------------------
# RC4.2.1's OWN tooling delta
# ---------------------------------------------------------------------------
#
# Bootstrapping note: A3.1 declared its own integrity script
# (`scripts/pb_33_amendment_a3_1_integrity.py`) one of its 11 protected-forever
# paths (`pb_34_rc3_integrity.py::A3_1_PROTECTED_PATHS`), byte-pinned by
# `pb_34`'s `check_protected_paths`/`check_a3_2_governance`. Teaching pb_33
# and pb_34 to recognize the RC4.2 ledger above requires editing pb_33 itself
# (adding the import and changing `check_protected_paths`'s return shape) --
# which necessarily changes its bytes. This is RC4.2.1's own authorized,
# byte-pinned, engineering-only tooling change, kept in a SEPARATE ledger
# from RC4.2's R1-R4 science-defect repair above: it repairs no defect and
# touches no science surface (scripts/, not src/muru/paper_benchmark/ or
# tests/test_a3_*), only teaches an existing frozen checker about a delta
# ledger that did not exist when it was written.
RC4_2_1_TOOLING_DELTA: tuple[AuthorizedChange, ...] = (
    AuthorizedChange(
        path="scripts/pb_33_amendment_a3_1_integrity.py",
        defect_id="RC4.2.1 Issue 1 (integrity tooling, not a science defect)",
        old_sha256="d9b40cb6d8fbcfd35cff43dca87190fa1984401508e2f646f2a14043038ebac3",
        new_sha256="a8355fd400c303d8677d96d64c4140af6fbdaf5c8296386be66a8861148d4074",
        semantic_scope=(
            "check_protected_paths now returns (errors, rc4_2_authorized_delta_paths) "
            "instead of just errors, and imports pb_rc4_2_authorized_delta.AUTHORIZED_BY_PATH "
            "to recognize the RC4.2 ledger for protocol.py. No protected path's required "
            "identity, no amendment logic, no science surface touched."
        ),
        old_blob_sha1="ed17113065c975e37c2c1276145e5a160a2f8fef",
        new_blob_sha1="545e94f20e05aa088e11f5002149975461174771",
    ),
)

RC4_2_1_TOOLING_BY_PATH: dict[str, AuthorizedChange] = {c.path: c for c in RC4_2_1_TOOLING_DELTA}


# ---------------------------------------------------------------------------
# RC5's OWN A3.5-implementation delta
# ---------------------------------------------------------------------------
#
# RC5 implements the frozen A3.5 science contract, whose implementation
# obligations 13/14/17/18/19 cannot be discharged without editing files these
# same scripts byte-pin. That ledger lives in its own module -- kept SEPARATE
# from RC4.2's R1-R4 repair and from RC4.2.1's tooling change, so an A3.5
# implementation can never be read as a defect repair or as an engineering
# exemption -- and is composed in HERE, at the one point every consuming
# script already imports from, so all seven learn about it by construction
# rather than by seven copies staying in sync. That is the same rationale
# `pb_engineering_paths` states for its own single declaration point.
#
# Nothing about the classification rules below changes: an RC5-ledgered path
# is still recognized only when BOTH its old and its new bytes match exactly.
from pb_rc5_a3_5_authorized_delta import (  # noqa: E402
    RC5_AUTHORIZED_BY_PATH,
    RC5_AUTHORIZED_DELTA,
)

# ---------------------------------------------------------------------------
# v2-calibration Stage 1 launch-remediation delta
# ---------------------------------------------------------------------------
#
# Ten files under src/muru/paper_benchmark/ postdate RC4.2, RC4.2.1, and RC5,
# so none of the three ledgers above was ever built to recognize them; pb_37
# flagging them as SCIENCE_DRIFT_VS_RC4_PARENT was correct detection, not a
# bug. This ledger is composed in HERE, at the one point every consuming
# script already imports from, exactly like RC5's own ledger was -- so all
# seven learn about it by construction. See pb_v2_calibration_authorized_delta
# for the full provenance record, owner-instruction citation, and per-file
# adjudication this ledger transcribes.
from pb_v2_calibration_authorized_delta import (  # noqa: E402
    V2_CALIBRATION_AUTHORIZED_BY_PATH,
    V2_CALIBRATION_AUTHORIZED_DELTA,
)

#: Union view for callers that want to recognize any ledger by path+hash
#: without caring which one authorized the change. Later ledgers win on a
#: duplicate path key (rc5_authorization.py: the v2-calibration ledger's
#: entry composes RC5's own addition with the subsequent A3.6/RC5.1 edit, so
#: it correctly supersedes RC5's now-stale pin for current-tree
#: classification -- see that entry's semantic_scope).
ALL_AUTHORIZED_BY_PATH: dict[str, AuthorizedChange] = {
    **AUTHORIZED_BY_PATH,
    **RC4_2_1_TOOLING_BY_PATH,
    **RC5_AUTHORIZED_BY_PATH,
    **V2_CALIBRATION_AUTHORIZED_BY_PATH,
}

_LEDGER_OWNER: dict[str, str] = {
    **{c.path: "RC4.2_R1_R4_defect_repair" for c in AUTHORIZED_DELTA},
    **{c.path: "RC4.2.1_integrity_tooling" for c in RC4_2_1_TOOLING_DELTA},
    **{c.path: "RC5_A3_5_implementation" for c in RC5_AUTHORIZED_DELTA},
    **{c.path: "v2_calibration_stage1_launch_remediation" for c in V2_CALIBRATION_AUTHORIZED_DELTA},
}


def ledger_owner(path: str) -> str | None:
    """Which ledger authorizes ``path``, for transparent reporting."""
    return _LEDGER_OWNER.get(path)


def authorized_paths() -> frozenset[str]:
    return frozenset(AUTHORIZED_BY_PATH)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_show_bytes(root: Path, commit: str, relative_path: str) -> bytes | None:
    result = subprocess.run(
        ("git", "show", f"{commit}:{relative_path}"),
        cwd=root,
        capture_output=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def classify_path(
    path: str,
    *,
    frozen_bytes: bytes | None,
    current_bytes: bytes | None,
) -> tuple[str, list[str]]:
    """Classify one path's current bytes against a historical frozen baseline.

    Returns ``(classification, errors)``. ``classification`` is one of:

    * ``UNCHANGED_FROM_FREEZE`` -- bit-identical to the historical baseline.
    * ``AUTHORIZED_RC4_2_DELTA`` -- differs, but the (old, new) pair is
      exactly the ledgered RC4.2 repair for this path.
    * ``AUTHORIZED_RC4_2_DELTA_NEW_FILE`` -- did not exist at the historical
      baseline, and current bytes exactly match the ledgered new file.
    * ``MISSING`` -- the path does not exist in the current tree.
    * ``NOT_AT_FREEZE`` -- the path did not exist at the historical baseline
      and is not a ledgered new file (out of scope for this ledger; the
      caller's own historical check owns this case).
    * ``UNAUTHORIZED_DRIFT`` -- differs from the baseline and is not the
      ledgered delta (wrong path, wrong old bytes, or wrong new bytes: any
      further drift beyond the exact authorized repair lands here too).

    Only ``errors`` should gate a script's pass/fail; ``classification`` is
    for transparent reporting.
    """
    if current_bytes is None:
        return "MISSING", [f"MISSING: {path}"]
    entry = ALL_AUTHORIZED_BY_PATH.get(path)
    if frozen_bytes is None:
        if (
            entry is not None
            and entry.old_sha256 is None
            and sha256_bytes(current_bytes) == entry.new_sha256
        ):
            return "AUTHORIZED_RC4_2_DELTA_NEW_FILE", []
        return "NOT_AT_FREEZE", [f"NOT_AT_FREEZE: {path}"]
    if current_bytes == frozen_bytes:
        return "UNCHANGED_FROM_FREEZE", []
    if (
        entry is not None
        and entry.old_sha256 == sha256_bytes(frozen_bytes)
        and entry.new_sha256 == sha256_bytes(current_bytes)
    ):
        return "AUTHORIZED_RC4_2_DELTA", []
    return "UNAUTHORIZED_DRIFT", [f"UNAUTHORIZED_DRIFT: {path}"]


def classify_path_against_commit(root: Path, commit: str, relative_path: str) -> tuple[str, list[str]]:
    """Convenience wrapper: read both sides from disk/git for one path."""
    current_path = root / relative_path
    current_bytes = current_path.read_bytes() if current_path.is_file() else None
    frozen_bytes = git_show_bytes(root, commit, relative_path)
    return classify_path(relative_path, frozen_bytes=frozen_bytes, current_bytes=current_bytes)


def check_byte_identity_lineage_aware(
    root: Path,
    commit: str,
    paths: list[str] | tuple[str, ...],
    *,
    label: str,
) -> tuple[list[str], list[dict[str, str]]]:
    """Drop-in, stricter-superset replacement for a plain byte-identity check.

    Behaves identically to a plain "current must equal frozen" check for
    every path with no ledger entry, or whose current bytes are unchanged.
    For a path that differs AND matches a ledgered entry exactly, the
    difference is reported (second return value) instead of erroring.
    Anything else -- unlisted path, wrong old bytes, wrong new bytes -- is
    still an error. Enforcement is not weakened for any file outside the
    eight-entry ledger, and not weakened for these eight beyond their exact
    pinned bytes.
    """
    errors: list[str] = []
    authorized: list[dict[str, str]] = []
    marker = label.upper()
    for relative_path in sorted(set(paths)):
        current_path = root / relative_path
        if not current_path.is_file():
            errors.append(f"MISSING_{marker}: {relative_path}")
            continue
        frozen = git_show_bytes(root, commit, relative_path)
        if frozen is None:
            errors.append(f"NOT_AT_{marker}: {relative_path}")
            continue
        current = current_path.read_bytes()
        if current == frozen:
            continue
        entry = ALL_AUTHORIZED_BY_PATH.get(relative_path)
        if (
            entry is not None
            and entry.old_sha256 == sha256_bytes(frozen)
            and entry.new_sha256 == sha256_bytes(current)
        ):
            authorized.append({
                "path": relative_path,
                "defect_id": entry.defect_id,
                "semantic_scope": entry.semantic_scope,
            })
            continue
        errors.append(f"UNAUTHORIZED_MODIFIED_{marker}: {relative_path}")
    return errors, authorized


def classify_blob_sha1(path: str, frozen_blob_sha1: str, current_blob_sha1: str) -> str:
    """Same classification as ``classify_path``, keyed on git blob SHA-1.

    Some callers (git ``ls-tree``/``diff --name-only``-based checks) compare
    git's own blob object IDs rather than a SHA-256 of raw content. Every
    ledger entry records both so either caller can use the ledger without
    rehashing bytes it does not otherwise need to read.
    """
    if frozen_blob_sha1 == current_blob_sha1:
        return "UNCHANGED_FROM_FREEZE"
    entry = ALL_AUTHORIZED_BY_PATH.get(path)
    if (
        entry is not None
        and entry.old_blob_sha1 == frozen_blob_sha1
        and entry.new_blob_sha1 == current_blob_sha1
    ):
        return "AUTHORIZED_RC4_2_DELTA"
    return "UNAUTHORIZED_DRIFT"


def split_unexpected_changed(
    unexpected_changed: list[str],
    *,
    frozen_commit: str,
    root: Path = ROOT,
) -> tuple[list[str], list[dict[str, str]]]:
    """Split a caller's own 'changed - allowed' set into real vs. ledgered.

    For scripts (pb_30, pb_31, pb_32) that already compute their own
    ``changed`` set by diffing the *entire* frozen tree against a reference
    commit and subtracting an amendment-specific allowlist, this re-checks
    each still-unexplained path against the RC4.2 ledger using that same
    reference commit, so the two classification paths cannot disagree about
    what "changed" means.
    """
    still_unexpected: list[str] = []
    authorized: list[dict[str, str]] = []
    for path in sorted(unexpected_changed):
        classification, _ = classify_path_against_commit(root, frozen_commit, path)
        if classification in ("AUTHORIZED_RC4_2_DELTA", "AUTHORIZED_RC4_2_DELTA_NEW_FILE"):
            # Look the entry up in the SAME dict ``classify_path`` classified
            # against. Reading it out of the RC4.2-only dict would raise
            # KeyError for a path authorized by either of the other two
            # ledgers, turning a recognized change into a crash.
            entry = ALL_AUTHORIZED_BY_PATH[path]
            authorized.append({
                "path": path,
                "defect_id": entry.defect_id,
                "semantic_scope": entry.semantic_scope,
                "ledger": ledger_owner(path) or "UNKNOWN",
            })
        else:
            still_unexpected.append(path)
    return still_unexpected, authorized
