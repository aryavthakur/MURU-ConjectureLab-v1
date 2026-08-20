"""The RC5 authorized-delta ledger stays honest.

This is a standing integrity guard, not a mirror of the tree.  It asserts the
properties that make the ledger meaningful:

* it describes the tree it transcribes (a stale pin is itself a failure),
* every pre-change hash really is the engineering parent's bytes,
* it authorizes nothing outside the paths RC5 legitimately touches,
* it is closed -- no duplicate path, no glob, no prefix,
* every consuming script sees the union of all three ledgers, and
* each path is attributed to the ledger that actually authorizes it, so an
  A3.5 implementation can never be read as a defect repair.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import pb_rc4_2_authorized_delta as rc4_2  # noqa: E402
import pb_rc5_a3_5_authorized_delta as rc5  # noqa: E402
import pb_v2_calibration_authorized_delta as v2c  # noqa: E402

BASE = "69e33c778efb14362439941d25ebbfcfb1068284"

#: RC5 may touch implementation, tests, and integrity tooling.  It may not
#: touch benchmark content, calibration output, or configuration.
FORBIDDEN_PREFIXES = ("artifacts/", "calibration/", "configs/", "inputs/", "truth/")


def _frozen_bytes(path: str) -> bytes | None:
    result = subprocess.run(
        ["git", "show", f"{BASE}:{path}"], cwd=ROOT, capture_output=True
    )
    return result.stdout if result.returncode == 0 else None


# -----------------------------------------------------------------------
# The ledger describes the tree
# -----------------------------------------------------------------------

def test_every_pinned_post_change_hash_matches_the_working_tree():
    report = rc5.verify_ledger_against_tree(ROOT)
    assert report == {"mismatched": [], "missing": []}, (
        "the RC5 ledger no longer describes the tree it transcribes; refresh the "
        "pinned new_sha256/new_blob_sha1 for the listed paths"
    )


#: The one entry whose ``old_sha256`` is deliberately NOT the engineering
#: parent's bytes.  ``pb_34``/``pb_35`` check ``pb_33`` against pre-RC4.2.1
#: baselines, and a ledger entry matches one (old, new) pair, so covering those
#: baselines requires the pre-RC4.2.1 digest -- which makes this entry's span
#: RC4.2.1's tooling edit *and* RC5's, composed. That is stated in the entry
#: itself; it is asserted here so the exception can never become implicit.
_COMPOSED_TOOLING_PATH = "scripts/pb_33_amendment_a3_1_integrity.py"
_PRE_RC4_2_1_PB33_SHA256 = (
    "d9b40cb6d8fbcfd35cff43dca87190fa1984401508e2f646f2a14043038ebac3"
)


@pytest.mark.parametrize(
    "entry", rc5.RC5_MODIFIED_DELTA, ids=lambda e: e.path
)
def test_every_pre_change_hash_is_a_real_frozen_baseline(entry):
    frozen = _frozen_bytes(entry.path)
    assert frozen is not None, f"{entry.path} does not exist at the engineering parent"
    at_parent = hashlib.sha256(frozen).hexdigest()

    if entry.path == _COMPOSED_TOOLING_PATH:
        # The composed entry: its old bytes are the baseline the consuming
        # scripts actually compare against, which is earlier than the parent.
        assert entry.old_sha256 == _PRE_RC4_2_1_PB33_SHA256
        assert entry.old_sha256 != at_parent
        for baseline in ("c8938e8", "1194fcb", "be23b80"):
            probe = subprocess.run(
                ["git", "show", f"{baseline}:{entry.path}"],
                cwd=ROOT, capture_output=True,
            )
            assert probe.returncode == 0
            assert hashlib.sha256(probe.stdout).hexdigest() == entry.old_sha256, (
                f"{entry.path} is not {entry.old_sha256[:12]} at {baseline}, so the "
                f"composed entry would not cover that consuming script's baseline"
            )
        assert "RC4.2.1" in entry.defect_id and "RC5" in entry.defect_id, (
            "a composed entry must name both edits rather than attributing both "
            "to RC5"
        )
        return

    assert at_parent == entry.old_sha256


def test_only_the_documented_tooling_entry_departs_from_the_parent_baseline():
    departures = [
        entry.path
        for entry in rc5.RC5_MODIFIED_DELTA
        if hashlib.sha256(_frozen_bytes(entry.path) or b"").hexdigest()
        != entry.old_sha256
    ]
    assert departures == [_COMPOSED_TOOLING_PATH]


@pytest.mark.parametrize("entry", rc5.RC5_ADDED_DELTA, ids=lambda e: e.path)
def test_every_additive_entry_really_is_absent_at_the_engineering_parent(entry):
    assert entry.old_sha256 is None
    assert entry.old_blob_sha1 is None
    assert _frozen_bytes(entry.path) is None, (
        f"{entry.path} is recorded as purely additive but exists at the parent"
    )


# -----------------------------------------------------------------------
# The ledger is closed and bounded
# -----------------------------------------------------------------------

def test_the_ledger_has_no_duplicate_path():
    paths = [entry.path for entry in rc5.RC5_AUTHORIZED_DELTA]
    assert len(paths) == len(set(paths))
    assert len(rc5.RC5_AUTHORIZED_BY_PATH) == len(rc5.RC5_AUTHORIZED_DELTA)


def test_the_ledger_authorizes_no_benchmark_content_or_calibration_artifact():
    for entry in rc5.RC5_AUTHORIZED_DELTA:
        assert not entry.path.startswith(FORBIDDEN_PREFIXES), (
            f"{entry.path} is outside what RC5 may touch: no calibration artifact, "
            f"threshold table, or benchmark content is in RC5's delta"
        )


def test_every_entry_carries_a_defect_id_and_a_semantic_scope():
    for entry in rc5.RC5_AUTHORIZED_DELTA:
        assert entry.defect_id.strip()
        assert len(entry.semantic_scope.strip()) > 40, entry.path
        assert len(entry.new_sha256) == 64
        assert len(entry.new_blob_sha1) == 40


def test_the_ledger_is_a_tuple_not_a_mutable_or_globbing_container():
    assert isinstance(rc5.RC5_AUTHORIZED_DELTA, tuple)
    assert isinstance(rc5.RC5_MODIFIED_DELTA, tuple)
    assert isinstance(rc5.RC5_ADDED_DELTA, tuple)
    for entry in rc5.RC5_AUTHORIZED_DELTA:
        assert "*" not in entry.path and not entry.path.endswith("/")


# -----------------------------------------------------------------------
# Composition and attribution
# -----------------------------------------------------------------------

def test_the_union_view_contains_all_three_ledgers():
    union = rc4_2.ALL_AUTHORIZED_BY_PATH
    for path in rc4_2.AUTHORIZED_BY_PATH:
        assert path in union
    for path in rc4_2.RC4_2_1_TOOLING_BY_PATH:
        assert path in union
    for path in rc5.RC5_AUTHORIZED_BY_PATH:
        assert path in union


def test_each_path_is_attributed_to_the_ledger_that_authorizes_it():
    for path in rc4_2.AUTHORIZED_BY_PATH:
        if path in rc5.RC5_AUTHORIZED_BY_PATH:
            continue  # a later ledger legitimately supersedes an earlier pin
        assert rc4_2.ledger_owner(path) == "RC4.2_R1_R4_defect_repair"
    for path in rc5.RC5_AUTHORIZED_BY_PATH:
        if path in v2c.V2_CALIBRATION_AUTHORIZED_BY_PATH:
            continue  # rc5_authorization.py: see test_a_superseded_pin_... below
        assert rc4_2.ledger_owner(path) == "RC5_A3_5_implementation"
    for path in v2c.V2_CALIBRATION_AUTHORIZED_BY_PATH:
        assert rc4_2.ledger_owner(path) == "v2_calibration_stage1_launch_remediation"
    assert rc4_2.ledger_owner("no/such/path.py") is None


def test_a_superseded_pin_is_shadowed_by_the_later_ledger_not_silently_dropped():
    """pb_33 is pinned by both RC4.2.1's tooling ledger and RC5's.

    The RC5 entry must win in the union (it describes the current bytes), and
    RC4.2.1's entry must still be present in its own tuple as the record of the
    intermediate state.
    """
    path = "scripts/pb_33_amendment_a3_1_integrity.py"
    assert path in rc4_2.RC4_2_1_TOOLING_BY_PATH
    assert path in rc5.RC5_AUTHORIZED_BY_PATH
    assert rc4_2.ALL_AUTHORIZED_BY_PATH[path] is rc5.RC5_AUTHORIZED_BY_PATH[path]
    # The two entries describe different spans, and the RC5 one reaches further.
    assert (
        rc4_2.RC4_2_1_TOOLING_BY_PATH[path].new_sha256
        != rc5.RC5_AUTHORIZED_BY_PATH[path].new_sha256
    )
    assert (
        rc4_2.RC4_2_1_TOOLING_BY_PATH[path].old_sha256
        == rc5.RC5_AUTHORIZED_BY_PATH[path].old_sha256
    )


def test_rc5_authorization_pin_is_shadowed_by_the_v2_calibration_ledger():
    """rc5_authorization.py is pinned by both RC5's own ledger and the
    v2-calibration ledger; the v2-calibration entry must win in the union (it
    describes the current, post-A3.6 bytes) while RC5's own entry stays
    exactly as RC5 froze it -- a record of the pre-A3.6 state, not something
    this later ledger is allowed to edit.

    This is the documented, disclosed gap named in
    ``audit/MURU_HELDOUT_SUPERSESSION_LEDGER.md`` section 5: A3.6 changed a
    file RC5 had pinned without an A3.6 ledger entry ever being written. The
    v2-calibration ledger is that instrument (see its module docstring), and
    is why ``test_every_pinned_post_change_hash_matches_the_working_tree``
    above is a pre-existing, already-disclosed failure for RC5's own tuple in
    isolation -- RC5's ledger is frozen at its own bytes by design, and only
    the union (``ALL_AUTHORIZED_BY_PATH``, checked here) describes the
    current tree.
    """
    path = "src/muru/paper_benchmark/rc5_authorization.py"
    assert path in rc5.RC5_AUTHORIZED_BY_PATH
    assert path in v2c.V2_CALIBRATION_AUTHORIZED_BY_PATH
    assert rc4_2.ALL_AUTHORIZED_BY_PATH[path] is v2c.V2_CALIBRATION_AUTHORIZED_BY_PATH[path]
    assert (
        rc5.RC5_AUTHORIZED_BY_PATH[path].new_sha256
        != v2c.V2_CALIBRATION_AUTHORIZED_BY_PATH[path].new_sha256
    )
    # The v2-calibration entry's pinned bytes match the current working tree
    # (this is the entry that actually classifies the file today).
    report = v2c.verify_ledger_against_tree(ROOT)
    assert path not in report["mismatched"] and path not in report["missing"]


# -----------------------------------------------------------------------
# Recognition is by bytes, not by path
# -----------------------------------------------------------------------

def test_a_further_edit_to_a_ledgered_path_is_not_authorized():
    """The property that makes the ledger stricter than an allowlist."""
    entry = rc5.RC5_AUTHORIZED_BY_PATH["src/muru/paper_benchmark/preflight.py"]
    frozen = _frozen_bytes(entry.path)
    drifted = (ROOT / entry.path).read_bytes() + b"\n# a further edit\n"
    classification, errors = rc4_2.classify_path(
        entry.path, frozen_bytes=frozen, current_bytes=drifted
    )
    assert classification == "UNAUTHORIZED_DRIFT"
    assert errors


def test_the_exact_ledgered_bytes_are_authorized():
    entry = rc5.RC5_AUTHORIZED_BY_PATH["src/muru/paper_benchmark/preflight.py"]
    classification, errors = rc4_2.classify_path(
        entry.path,
        frozen_bytes=_frozen_bytes(entry.path),
        current_bytes=(ROOT / entry.path).read_bytes(),
    )
    assert classification == "AUTHORIZED_RC4_2_DELTA"
    assert errors == []


def test_an_unledgered_path_is_never_authorized():
    classification, errors = rc4_2.classify_path(
        "src/muru/paper_benchmark/generator.py",
        frozen_bytes=b"old",
        current_bytes=b"new",
    )
    assert classification == "UNAUTHORIZED_DRIFT"
    assert errors


def test_split_unexpected_changed_reports_the_owning_ledger():
    """Regression for the KeyError this composition originally would have hit."""
    still, authorized = rc4_2.split_unexpected_changed(
        ["src/muru/paper_benchmark/preflight.py"], frozen_commit=BASE, root=ROOT
    )
    assert still == []
    assert len(authorized) == 1
    assert authorized[0]["path"] == "src/muru/paper_benchmark/preflight.py"
    assert authorized[0]["ledger"] == "RC5_A3_5_implementation"
