#!/usr/bin/env python3
"""Design A step 40: score every population record against every (model, mapping) prediction.

Study: "MURU CE interface adjudication Design A" (study id muru-ce-interface-adjudication-design-a).

This step is the join. For every record of the frozen population and every (model, mapping) pair it
pairs the model's predicted spectrum for that record's (compound, NCE) cell with the record's observed
spectrum, computes the two frozen similarity endpoints, and writes one row of
artifacts/ce_interface_adjudication/design_a/scores/record_scores.csv, the table that step 50 consumes.

Nothing in this module defines, tunes or second-guesses a similarity convention. Every convention lives
in scripts/ce_interface_adjudication/design_a/spectrum_similarity.py and is used exactly as frozen: the
public endpoints are called with their default keyword arguments only, allow_override is never passed,
and the module refuses to run if that module's FROZEN_CONFIG sha256 differs from the value pinned here
as SIMILARITY_FROZEN_CONFIG_SHA256.

Observed intensity column
-------------------------
A MassBank PK$PEAK block carries triplets "m/z int. rel.int.". This step FREEZES the second column, the
ABSOLUTE intensity ("int."), as the observed intensity. Both endpoints are scale invariant, so the
choice between the absolute and the relative column cannot change any result: the cosine endpoint is a
ratio that is unchanged by a positive rescale of either side, the Jensen-Shannon endpoint L1 normalises
each side to a probability distribution, and the frozen layer additionally max normalises both sides
before either endpoint sees them. The column is frozen anyway, because a convention that cannot change a
number still has to be stated once and never chosen again. One caveat, stated so it is on the record:
MassBank's relative column is conventionally a rounded integer copy of the absolute column scaled to 999,
so it is a rounded rather than an exact positive multiple; the absolute column is the unrounded quantity
and is therefore the one frozen here.

Parent mass
-----------
The parent mass handed to the frozen mass-cutoff convention is the population's theoretical [M+H]+
(design_a_records.csv column theoretical_mh), never the record's deposited PRECURSOR_M/Z. The deposited
value is parsed and reported for provenance and is used in no computation whatsoever, so a record whose
PRECURSOR_M/Z is absent or unparseable is NOT dropped for that reason: dropping on it would be a filter
the preregistration has not fixed.

The single documented square inverse
------------------------------------
ms-pred stores predicted intensities on a sqrt scale. The frozen layer inverts that by squaring the
PREDICTION side exactly once (pred_inverse_transform="square") and applies no transform at all to the
observed side (obs_inverse_transform="identity"). This module therefore hands the prediction's stored
intensities to the layer untouched. It never squares, never square roots and never renormalises anything
itself.

Mechanical drop rule
--------------------
A record that cannot be read, or whose peak block is absent or malformed, or that yields zero peaks, and
a (model, mapping) cell whose prediction is missing or empty, produce a row carrying a fixed drop_reason
string and NO similarity values. There are exactly six drop reasons, all mechanical; see DROP_REASONS.
There is no quality judgement anywhere: no minimum peak count, no intensity threshold, no noise filter,
no deduplication, no exclusion on anything the preregistration has not fixed.

Governance
----------
run() refuses, with a hard exit, unless all of

  1. MURU_CE_ADJUDICATION_EXECUTE=1 is set in the environment (the same variable the step 30 prediction
     harness uses),
  2. the freeze ref refs/muru-freeze/muru-ce-interface-adjudication-design-a resolves in git,
  3. design_a_records.csv matches its sha256 recorded in design_a_manifest_sha256.json,
  4. spectrum_similarity.frozen_config_sha256() equals SIMILARITY_FROZEN_CONFIG_SHA256.

The observed-record directory and every expected prediction dump must exist; a missing record directory
or a missing dump file means the step was never run and is a refusal, not a drop.

Determinism
-----------
Row order is (population record_id, model, mapping) with model and mapping taken in their frozen tuple
order. All arithmetic is float64. Similarity columns are written with repr(), the shortest decimal that
round-trips a binary64, so nothing is rounded away. The output is byte identical across runs.

Usage:
  MURU_CE_ADJUDICATION_EXECUTE=1 /opt/miniconda3/bin/python3 \
      scripts/ce_interface_adjudication/design_a/40_score_spectra.py --records-dir <dir>

Style note: ordinary hyphens only, no em dashes or en dashes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

STUDY_ID = "muru-ce-interface-adjudication-design-a"
FREEZE_REF = f"refs/muru-freeze/{STUDY_ID}"
EXECUTE_ENV_VAR = "MURU_CE_ADJUDICATION_EXECUTE"
RECORDS_DIR_ENV_VAR = "MURU_CE_ADJUDICATION_RECORDS_DIR"

RECORDS_CSV_REL = "artifacts/ce_interface_adjudication/design_a/population/design_a_records.csv"
POP_MANIFEST_REL = "artifacts/ce_interface_adjudication/design_a/population/design_a_manifest_sha256.json"
PRED_DIR_REL = "artifacts/ce_interface_adjudication/design_a/prediction_outputs"
SCORES_REL = "artifacts/ce_interface_adjudication/design_a/scores/record_scores.csv"
SIDECAR_NAME = "record_scores_manifest.json"

# Default location of the MassBank record text files, one file per accession, named by the population's
# source_file column. Nothing under it is read until every governance gate above has passed.
DEFAULT_RECORDS_DIR_REL = "data/massbank/MassBank-data/Eawag"

# ------------------------------------------------------------------------------------------------
# The frozen similarity layer, loaded by path because the sibling step scripts are numbered modules.
# ------------------------------------------------------------------------------------------------

SIMILARITY_MODULE_PATH = HERE / "spectrum_similarity.py"


def _load_similarity_module():
    spec = importlib.util.spec_from_file_location(
        "ce_design_a_spectrum_similarity", SIMILARITY_MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SS = _load_similarity_module()

# Pinned here and nowhere else. A change to any frozen similarity convention changes this digest and
# this step refuses to run until the change is deliberate and the pin is updated with it.
SIMILARITY_FROZEN_CONFIG_SHA256 = "655436863b02262585609d5582f43a73a0f51f84d04d0bba0da9c2b3db252848"

# ------------------------------------------------------------------------------------------------
# Frozen identities
# ------------------------------------------------------------------------------------------------

# (step 30 harness model key, step 50 analysis model label), in the frozen row order.
MODEL_KEYS = (
    ("iceberg_2_1_msg_simulation", "ICEBERG_2_1"),
    ("glacier_msg", "GLACIER"),
)
MAPPINGS = ("K1", "K2", "K3")
NCE_CELLS = (30, 60)

# Step 50 requires a unique record_id per row, and the row grid is (record, model, mapping), so the row
# key is the population record id joined to the model label and the mapping id by this separator. The
# separator is the one the step 30 harness already uses for its (model, mapping) output tags.
ROW_ID_SEP = "__"

OUTPUT_COLUMNS = ("record_id", "compound_id", "scaffold_group", "nce", "model", "mapping",
                  "cosine", "js", "drop_reason")

# ------------------------------------------------------------------------------------------------
# The six mechanical drop reasons. Fixed strings, no others, no free text anywhere.
# ------------------------------------------------------------------------------------------------

DROP_UNREADABLE_RECORD = "unreadable_record"
"""The record file is absent, is not readable, is not decodable as UTF-8 text, or carries no single
ACCESSION line. Nothing about its content is guessed."""

DROP_MISSING_PK_PEAK_BLOCK = "missing_pk_peak_block"
"""The record carries no PK$PEAK header line at all."""

DROP_MALFORMED_PEAK_LINE = "malformed_peak_line"
"""The PK$PEAK block exists but does not conform: a non canonical column header, a peak line that is not
exactly three whitespace separated finite numbers, a missing or non integer PK$NUM_PEAK, a PK$NUM_PEAK
that disagrees with the number of peak lines actually parsed, or a duplicated PK$PEAK or PK$NUM_PEAK
line. Every structural defect INSIDE the block reports this reason; the block's total absence reports
missing_pk_peak_block instead."""

DROP_ZERO_PEAKS = "zero_peaks_after_parsing"
"""The block is well formed and self consistent but declares and contains no peaks."""

DROP_MISSING_PREDICTION = "missing_prediction"
"""The spec id is absent from the (model, mapping) prediction dump, or its dump entry cannot be read as
two equal length numeric peak arrays."""

DROP_EMPTY_PREDICTION = "empty_prediction"
"""The dump entry is readable and its peak arrays are empty."""

DROP_REASONS = (
    DROP_UNREADABLE_RECORD,
    DROP_MISSING_PK_PEAK_BLOCK,
    DROP_MALFORMED_PEAK_LINE,
    DROP_ZERO_PEAKS,
    DROP_MISSING_PREDICTION,
    DROP_EMPTY_PREDICTION,
)

# ------------------------------------------------------------------------------------------------
# MassBank record format, as frozen by this step
# ------------------------------------------------------------------------------------------------

# A MassBank tag line: an upper case tag, optionally with $ _ / and digits, then a colon. Peak lines
# never match, because they begin with a digit.
TAG_RE = re.compile(r"^([A-Z][A-Za-z0-9$_/]*):(.*)$")

ACCESSION_TAG = "ACCESSION"
PEAK_TAG = "PK$PEAK"
NUM_PEAK_TAG = "PK$NUM_PEAK"
FOCUSED_ION_TAG = "MS$FOCUSED_ION"
PRECURSOR_SUBTAG = "PRECURSOR_M/Z"
RECORD_TERMINATOR = "//"

PEAK_HEADER_TOKENS = ("m/z", "int.", "rel.int.")
"""The canonical PK$PEAK column header. A block whose header differs is malformed rather than silently
scored on a column whose meaning is not the frozen one."""

OBSERVED_INTENSITY_COLUMN_INDEX = 1
"""Column 1 of the triplet, the absolute intensity. See the module docstring."""


class ScoringRefusal(SystemExit):
    """A frozen precondition of the scoring step is not met. Hard exit, never a partial score table."""


class RecordParseError(ValueError):
    """A record could not be parsed. Carries exactly one of the fixed drop reasons."""

    def __init__(self, reason: str, detail: str = ""):
        if reason not in DROP_REASONS:
            raise AssertionError(f"undeclared drop reason {reason!r}")
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


class PredictionError(ValueError):
    """A prediction could not be used. Carries exactly one of the fixed drop reasons."""

    def __init__(self, reason: str, detail: str = ""):
        if reason not in DROP_REASONS:
            raise AssertionError(f"undeclared drop reason {reason!r}")
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


# ------------------------------------------------------------------------------------------------
# Observed spectrum reader
# ------------------------------------------------------------------------------------------------

def normalise_lines(text: str) -> list[str]:
    """Split a record into lines, line-ending agnostic.

    CRLF and CR are folded to LF, so a record deposited with Windows line endings parses identically to
    the same record with Unix line endings. Nothing else about the text is altered.
    """
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def _tag_lines(lines: list[str]) -> list[tuple[int, str, str]]:
    """Every MassBank tag line as (line index, tag, raw value). Leading and trailing whitespace on the
    line is ignored, so a record padded with spaces parses identically."""
    out = []
    for i, raw in enumerate(lines):
        m = TAG_RE.match(raw.strip())
        if m:
            out.append((i, m.group(1), m.group(2)))
    return out


def _parse_float(token: str) -> float:
    """Strict float parse. Rejects non finite tokens, which float() itself would accept."""
    value = float(token)
    if not math.isfinite(value):
        raise ValueError(f"non finite numeric token {token!r}")
    return value


def parse_massbank_record(text: str) -> dict:
    """Parse one MassBank record text into its frozen observed spectrum.

    Returns a dict with keys accession, deposited_precursor_mz (float or None), n_peak_declared (int),
    mz, intensity and relative_intensity (lists of float, all the same length, in the file's own peak
    order). Raises RecordParseError carrying one of the fixed drop reasons on any defect. Never guesses,
    never repairs, never returns a partial spectrum.

    Frozen parse rules, in order:
      1. exactly one ACCESSION line, else unreadable_record;
      2. exactly one PK$PEAK line, else missing_pk_peak_block when there is none and
         malformed_peak_line when there is more than one;
      3. the PK$PEAK column header must be exactly "m/z int. rel.int.", else malformed_peak_line;
      4. the peak block runs from the line after PK$PEAK to the first blank line, record terminator //,
         tag line, or end of file; every line in it must split into exactly three whitespace separated
         finite numbers, else malformed_peak_line;
      5. exactly one PK$NUM_PEAK line holding an integer, else malformed_peak_line;
      6. PK$NUM_PEAK must equal the number of peak lines parsed, else malformed_peak_line;
      7. zero peaks is zero_peaks_after_parsing.
    MS$FOCUSED_ION PRECURSOR_M/Z is parsed for provenance only and gates nothing.
    """
    lines = normalise_lines(text)
    tags = _tag_lines(lines)

    accessions = [v.strip() for _, t, v in tags if t == ACCESSION_TAG]
    if len(accessions) != 1 or not accessions[0]:
        raise RecordParseError(DROP_UNREADABLE_RECORD,
                               f"expected exactly one non empty ACCESSION line, found {len(accessions)}")
    accession = accessions[0]

    precursor = None
    for _, tag, value in tags:
        if tag != FOCUSED_ION_TAG:
            continue
        tokens = value.split()
        if len(tokens) >= 2 and tokens[0] == PRECURSOR_SUBTAG:
            try:
                precursor = _parse_float(tokens[1])
            except ValueError:
                precursor = None
            break

    peak_headers = [(i, v) for i, t, v in tags if t == PEAK_TAG]
    if not peak_headers:
        raise RecordParseError(DROP_MISSING_PK_PEAK_BLOCK, "no PK$PEAK line")
    if len(peak_headers) > 1:
        raise RecordParseError(DROP_MALFORMED_PEAK_LINE,
                               f"{len(peak_headers)} PK$PEAK lines, expected exactly one")
    header_index, header_value = peak_headers[0]
    if tuple(header_value.split()) != PEAK_HEADER_TOKENS:
        raise RecordParseError(
            DROP_MALFORMED_PEAK_LINE,
            f"PK$PEAK column header {header_value.strip()!r} is not {' '.join(PEAK_HEADER_TOKENS)!r}")

    mz: list[float] = []
    intensity: list[float] = []
    relative: list[float] = []
    for raw in lines[header_index + 1:]:
        stripped = raw.strip()
        if stripped == "" or stripped == RECORD_TERMINATOR or TAG_RE.match(stripped):
            break
        tokens = stripped.split()
        if len(tokens) != 3:
            raise RecordParseError(DROP_MALFORMED_PEAK_LINE,
                                   f"peak line {stripped!r} has {len(tokens)} fields, expected 3")
        try:
            a, b, c = (_parse_float(t) for t in tokens)
        except ValueError as exc:
            raise RecordParseError(DROP_MALFORMED_PEAK_LINE,
                                   f"peak line {stripped!r}: {exc}") from None
        mz.append(a)
        intensity.append(b)
        relative.append(c)

    declared = [v.strip() for _, t, v in tags if t == NUM_PEAK_TAG]
    if len(declared) != 1:
        raise RecordParseError(DROP_MALFORMED_PEAK_LINE,
                               f"expected exactly one PK$NUM_PEAK line, found {len(declared)}")
    try:
        n_declared = int(declared[0])
    except ValueError:
        raise RecordParseError(DROP_MALFORMED_PEAK_LINE,
                               f"PK$NUM_PEAK {declared[0]!r} is not an integer") from None
    if n_declared != len(mz):
        raise RecordParseError(
            DROP_MALFORMED_PEAK_LINE,
            f"PK$NUM_PEAK declares {n_declared} peaks, the block holds {len(mz)}")
    if not mz:
        raise RecordParseError(DROP_ZERO_PEAKS, "PK$NUM_PEAK 0 and no peak lines")

    return {"accession": accession, "deposited_precursor_mz": precursor,
            "n_peak_declared": n_declared, "mz": mz, "intensity": intensity,
            "relative_intensity": relative}


def read_record(path: Path) -> dict:
    """Read and parse one record file. A missing or undecodable file is unreadable_record."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise RecordParseError(DROP_UNREADABLE_RECORD, f"{path}: {exc}") from None
    return parse_massbank_record(text)


def observed_spectrum(parsed: dict) -> tuple[list[float], list[float]]:
    """The frozen observed spectrum: m/z against the ABSOLUTE intensity column."""
    column = (parsed["mz"], parsed["intensity"], parsed["relative_intensity"])[
        OBSERVED_INTENSITY_COLUMN_INDEX]
    return list(parsed["mz"]), list(column)


# ------------------------------------------------------------------------------------------------
# Prediction dump reader
# ------------------------------------------------------------------------------------------------

# The dump is produced inside the ms-pred container by
# scripts/comparator_benchmark/container/mspred_h5_to_json.py, which walks the PredSpecDB HDF5 and emits
# a JSON LIST of objects. This step uses exactly three of the keys it writes:
#   "name"            the spec id of the input TSV row, which the native predictor stores with a
#                     "pred_" prefix (stripped here, exactly as the frozen comparator verification does
#                     at scripts/comparator_benchmark/verify_predictions.py:125),
#   "masses_float32"  the stored fragment m/z values, float32 as written, listed as JSON numbers,
#   "intens_float32"  the stored intensities, float32 as written, on ms-pred's SQRT scale and left on
#                     it here, because inverting that scale is the frozen similarity layer's single
#                     documented square and belongs to the layer alone.
# Everything else the dump carries (remark, collision_key, stored_collision_energy,
# root_canonical_smiles, adduct, natoms, is_root_fragment, frag_popcount) is untouched by this step.
PRED_NAME_PREFIX = "pred_"
PRED_MASS_KEY = "masses_float32"
PRED_INTENSITY_KEY = "intens_float32"


def spec_id(compound_id: str, nce: int) -> str:
    """The step 30 spec id for a (compound, NCE) cell, 30_run_predictions.py:196-198."""
    return f"{compound_id}_NCE{int(nce)}"


def dump_filename(model_key: str, mapping: str) -> str:
    """The step 30 execute-mode dump name, 30_run_predictions.py:534-536."""
    return f"{model_key}{ROW_ID_SEP}{mapping}_spectra.json"


def load_prediction_dump(path: Path) -> dict[str, dict]:
    """Index one prediction dump by spec id.

    A missing or unparseable dump FILE, or a dump that names the same spec id twice, is a refusal: the
    prediction step either ran or it did not, and an ambiguous join cannot be resolved mechanically.
    Defects of an individual ENTRY are not inspected here, so that they surface as per-row drop reasons.
    """
    path = Path(path)
    if not path.is_file():
        raise ScoringRefusal(
            f"refusing: prediction dump {path} does not exist. Run step 30 in execute mode first; a "
            f"dump that was never produced is not a per-record drop.")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScoringRefusal(f"refusing: prediction dump {path} is not readable JSON: {exc}")
    if not isinstance(payload, list):
        raise ScoringRefusal(
            f"refusing: prediction dump {path} is a {type(payload).__name__}, expected a JSON list")
    index: dict[str, dict] = {}
    for position, entry in enumerate(payload):
        if not isinstance(entry, dict) or "name" not in entry:
            raise ScoringRefusal(
                f"refusing: prediction dump {path} entry {position} carries no 'name' key")
        name = str(entry["name"])
        if name.startswith(PRED_NAME_PREFIX):
            name = name[len(PRED_NAME_PREFIX):]
        if name in index:
            raise ScoringRefusal(
                f"refusing: prediction dump {path} names spec id {name!r} more than once")
        index[name] = entry
    return index


def prediction_spectrum(entry: dict) -> tuple[list[float], list[float]]:
    """The predicted spectrum of one dump entry, on ms-pred's stored sqrt scale, untouched.

    Raises PredictionError(missing_prediction) when the entry cannot be read as two equal length numeric
    arrays and PredictionError(empty_prediction) when those arrays are empty.
    """
    masses = entry.get(PRED_MASS_KEY)
    intens = entry.get(PRED_INTENSITY_KEY)
    if not isinstance(masses, list) or not isinstance(intens, list):
        raise PredictionError(DROP_MISSING_PREDICTION,
                              f"{PRED_MASS_KEY}/{PRED_INTENSITY_KEY} are not both JSON lists")
    if len(masses) != len(intens):
        raise PredictionError(DROP_MISSING_PREDICTION,
                              f"{len(masses)} masses against {len(intens)} intensities")
    if not masses:
        raise PredictionError(DROP_EMPTY_PREDICTION, "the dump entry holds no peaks")
    try:
        mz = [float(v) for v in masses]
        it = [float(v) for v in intens]
    except (TypeError, ValueError) as exc:
        raise PredictionError(DROP_MISSING_PREDICTION, f"non numeric peak array: {exc}") from None
    return mz, it


# ------------------------------------------------------------------------------------------------
# Population
# ------------------------------------------------------------------------------------------------

REQUIRED_RECORD_COLUMNS = ("record_id", "compound_id", "scaffold_group", "nce", "theoretical_mh",
                           "source_file")


def read_population(records_csv: Path) -> list[dict]:
    """Read the frozen record population. Deterministic order: lexicographic by record_id."""
    records_csv = Path(records_csv)
    if not records_csv.is_file():
        raise ScoringRefusal(f"refusing: population record table not found at {records_csv}")
    with open(records_csv, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ScoringRefusal(f"refusing: population record table {records_csv} holds no rows")
    missing = [c for c in REQUIRED_RECORD_COLUMNS if c not in rows[0]]
    if missing:
        raise ScoringRefusal(
            f"refusing: population record table is missing required column(s): {', '.join(missing)}")
    out = []
    seen: set[str] = set()
    for row in rows:
        record_id = str(row["record_id"]).strip()
        if record_id in seen:
            raise ScoringRefusal(f"refusing: duplicate record_id {record_id!r} in {records_csv}")
        seen.add(record_id)
        try:
            nce_float = float(row["nce"])
            mh = float(row["theoretical_mh"])
        except (TypeError, ValueError) as exc:
            raise ScoringRefusal(f"refusing: record {record_id} has a non numeric nce or "
                                 f"theoretical_mh: {exc}")
        nce = int(nce_float)
        if nce != nce_float or nce not in NCE_CELLS:
            raise ScoringRefusal(
                f"refusing: record {record_id} declares nce {row['nce']!r}, not one of {NCE_CELLS}")
        if not math.isfinite(mh) or mh <= 0.0:
            raise ScoringRefusal(
                f"refusing: record {record_id} declares theoretical_mh {row['theoretical_mh']!r}")
        out.append({
            "record_id": record_id,
            "compound_id": str(row["compound_id"]).strip(),
            "scaffold_group": str(row["scaffold_group"]),
            "nce": nce,
            "theoretical_mh": mh,
            "source_file": str(row["source_file"]).strip(),
        })
    out.sort(key=lambda r: r["record_id"])
    return out


# ------------------------------------------------------------------------------------------------
# Governance
# ------------------------------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def require_execute_env(env: dict | None = None) -> None:
    env = os.environ if env is None else env
    value = env.get(EXECUTE_ENV_VAR)
    if value != "1":
        raise ScoringRefusal(
            f"refusing to score: missing precondition 1 of 4, environment variable "
            f"{EXECUTE_ENV_VAR}=1 (observed: {value!r}).")


def require_freeze_ref(root: Path) -> str:
    proc = subprocess.run(["git", "rev-parse", "--verify", "--quiet", FREEZE_REF],
                          cwd=str(root), capture_output=True, text=True)
    sha = proc.stdout.strip() if proc.returncode == 0 else ""
    if not sha:
        raise ScoringRefusal(
            f"refusing to score: missing precondition 2 of 4, the study freeze ref {FREEZE_REF} does "
            f"not resolve in {root}.")
    return sha


def require_population_hash(root: Path) -> dict:
    root = Path(root)
    manifest_path = root / POP_MANIFEST_REL
    if not manifest_path.is_file():
        raise ScoringRefusal(
            f"refusing to score: missing precondition 3 of 4, no population manifest at "
            f"{POP_MANIFEST_REL}.")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScoringRefusal(
            f"refusing to score: population manifest {POP_MANIFEST_REL} is not readable JSON: {exc}")
    recorded = (manifest.get("outputs_written") or {}).get(RECORDS_CSV_REL)
    if not recorded:
        raise ScoringRefusal(
            f"refusing to score: missing precondition 3 of 4, {RECORDS_CSV_REL} has no recorded "
            f"sha256 in {POP_MANIFEST_REL}.")
    records_path = root / RECORDS_CSV_REL
    if not records_path.is_file():
        raise ScoringRefusal(f"refusing to score: population file missing at {RECORDS_CSV_REL}")
    observed = sha256_file(records_path)
    if observed != recorded:
        raise ScoringRefusal(
            f"refusing to score: missing precondition 3 of 4, sha256 mismatch for {RECORDS_CSV_REL} "
            f"(recorded {recorded}, observed {observed}).")
    return {"path": RECORDS_CSV_REL, "sha256_recorded": recorded, "sha256_observed": observed}


def require_similarity_config() -> str:
    observed = SS.frozen_config_sha256()
    if observed != SIMILARITY_FROZEN_CONFIG_SHA256:
        raise ScoringRefusal(
            f"refusing to score: missing precondition 4 of 4, spectrum_similarity FROZEN_CONFIG "
            f"sha256 is {observed}, the pinned value is {SIMILARITY_FROZEN_CONFIG_SHA256}. A frozen "
            f"similarity convention has changed.")
    return observed


def governance_checks(root: Path, env: dict | None = None) -> dict:
    """All four gates, in order. Nothing is read or written before they all pass."""
    require_execute_env(env)
    freeze_sha = require_freeze_ref(root)
    population = require_population_hash(root)
    config_sha = require_similarity_config()
    return {
        "study_id": STUDY_ID,
        "execute_env_var": EXECUTE_ENV_VAR,
        "freeze_ref": FREEZE_REF,
        "freeze_ref_sha": freeze_sha,
        "population": population,
        "similarity_frozen_config_sha256": config_sha,
        "similarity_frozen_config_sha256_pinned": SIMILARITY_FROZEN_CONFIG_SHA256,
    }


# ------------------------------------------------------------------------------------------------
# Scoring
# ------------------------------------------------------------------------------------------------

def row_id(record_id: str, model_label: str, mapping: str) -> str:
    """The step 50 row key. Unique per row, which step 50 enforces."""
    return f"{record_id}{ROW_ID_SEP}{model_label}{ROW_ID_SEP}{mapping}"


def score_pair(pred: tuple[list[float], list[float]], obs: tuple[list[float], list[float]],
               parent_mass: float) -> tuple[float, float]:
    """Both frozen endpoints, called with their frozen defaults only.

    No convention is passed, no convention is overridden, allow_override is never used. parent_mass is
    the population's theoretical [M+H]+ and feeds the frozen mass-cutoff convention.
    """
    cosine = SS.cosine_similarity_untransformed(pred, obs, parent_mass=parent_mass)
    js = SS.jensen_shannon_similarity(pred, obs, parent_mass=parent_mass)
    return float(cosine), float(js)


def score_rows(population: list[dict], records_dir: Path,
               dumps: dict[tuple[str, str], dict[str, dict]]) -> list[dict]:
    """One row per (population record, model, mapping), in the frozen order.

    Each record is read and parsed exactly once and reused across the six cells, so a parse defect
    reports the same reason in all six of that record's rows.
    """
    records_dir = Path(records_dir)
    rows: list[dict] = []
    for rec in population:
        try:
            parsed = read_record(records_dir / rec["source_file"])
            obs = observed_spectrum(parsed)
            record_reason = ""
        except RecordParseError as exc:
            parsed, obs, record_reason = None, None, exc.reason
        for _model_key, model_label in MODEL_KEYS:
            for mapping in MAPPINGS:
                row = {
                    "record_id": row_id(rec["record_id"], model_label, mapping),
                    "compound_id": rec["compound_id"],
                    "scaffold_group": rec["scaffold_group"],
                    "nce": rec["nce"],
                    "model": model_label,
                    "mapping": mapping,
                    "cosine": None,
                    "js": None,
                    "drop_reason": record_reason,
                }
                if record_reason:
                    rows.append(row)
                    continue
                entry = dumps[(model_label, mapping)].get(spec_id(rec["compound_id"], rec["nce"]))
                if entry is None:
                    row["drop_reason"] = DROP_MISSING_PREDICTION
                    rows.append(row)
                    continue
                try:
                    pred = prediction_spectrum(entry)
                except PredictionError as exc:
                    row["drop_reason"] = exc.reason
                    rows.append(row)
                    continue
                cosine, js = score_pair(pred, obs, rec["theoretical_mh"])
                row["cosine"] = cosine
                row["js"] = js
                rows.append(row)
    return rows


def format_value(value: float | None) -> str:
    """Full precision, no rounding: repr() of a binary64 is the shortest decimal that round-trips it."""
    return "" if value is None else repr(float(value))


def write_scores(rows: list[dict], out_path: Path) -> str:
    """Write the score table. Byte identical across runs; returns its sha256."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(OUTPUT_COLUMNS)
        for row in rows:
            writer.writerow([
                row["record_id"], row["compound_id"], row["scaffold_group"], str(int(row["nce"])),
                row["model"], row["mapping"], format_value(row["cosine"]),
                format_value(row["js"]), row["drop_reason"],
            ])
    return sha256_file(out_path)


def drop_reason_counts(rows: list[dict]) -> dict:
    counts = {reason: 0 for reason in DROP_REASONS}
    for row in rows:
        if row["drop_reason"]:
            counts[row["drop_reason"]] += 1
    return counts


# ------------------------------------------------------------------------------------------------
# Run
# ------------------------------------------------------------------------------------------------

def default_records_dir(root: Path, env: dict | None = None) -> Path:
    env = os.environ if env is None else env
    override = env.get(RECORDS_DIR_ENV_VAR)
    return Path(override) if override else Path(root) / DEFAULT_RECORDS_DIR_REL


def run(root: Path = ROOT, env: dict | None = None, records_dir: Path | None = None,
        predictions_dir: Path | None = None, out_path: Path | None = None,
        sidecar_path: Path | None = None, write: bool = True) -> dict:
    root = Path(root)
    gov = governance_checks(root, env)

    records_dir = Path(records_dir) if records_dir is not None else default_records_dir(root, env)
    if not records_dir.is_dir():
        raise ScoringRefusal(
            f"refusing to score: the observed-record directory {records_dir} does not exist. A record "
            f"set that was never provisioned is not a per-record drop.")
    predictions_dir = Path(predictions_dir) if predictions_dir is not None else root / PRED_DIR_REL
    out_path = Path(out_path) if out_path is not None else root / SCORES_REL
    sidecar_path = Path(sidecar_path) if sidecar_path is not None else out_path.with_name(SIDECAR_NAME)

    population = read_population(root / RECORDS_CSV_REL)

    dumps: dict[tuple[str, str], dict[str, dict]] = {}
    dump_sha: dict[str, str] = {}
    for model_key, model_label in MODEL_KEYS:
        for mapping in MAPPINGS:
            name = dump_filename(model_key, mapping)
            path = predictions_dir / name
            dumps[(model_label, mapping)] = load_prediction_dump(path)
            dump_sha[name] = sha256_file(path)

    rows = score_rows(population, records_dir, dumps)

    result = {
        "rows": rows,
        "governance": gov,
        "counts": {
            "n_population_records": len(population),
            "n_models": len(MODEL_KEYS),
            "n_mappings": len(MAPPINGS),
            "n_rows": len(rows),
            "n_rows_scored": sum(1 for r in rows if not r["drop_reason"]),
            "n_rows_dropped": sum(1 for r in rows if r["drop_reason"]),
        },
        "drop_reason_counts": drop_reason_counts(rows),
    }
    if not write:
        return result

    scores_sha = write_scores(rows, out_path)
    sidecar = {
        "study_id": STUDY_ID,
        "step": "40_score_spectra",
        "governance": gov,
        "script": {
            "path": _rel(Path(__file__).resolve(), root),
            "sha256": sha256_file(Path(__file__).resolve()),
        },
        "similarity_layer": {
            "path": _rel(SIMILARITY_MODULE_PATH, root),
            "sha256": sha256_file(SIMILARITY_MODULE_PATH),
            "frozen_config_sha256": gov["similarity_frozen_config_sha256"],
            "frozen_config_sha256_pinned": SIMILARITY_FROZEN_CONFIG_SHA256,
            "endpoints": ["cosine_similarity_untransformed", "jensen_shannon_similarity"],
            "called_with": "frozen defaults only; no convention passed, allow_override never used",
        },
        "inputs": {
            "population_records_csv": {"path": RECORDS_CSV_REL,
                                       "sha256": gov["population"]["sha256_observed"]},
            "population_manifest": {"path": POP_MANIFEST_REL,
                                    "sha256": sha256_file(root / POP_MANIFEST_REL)},
            "records_dir": str(records_dir),
            "prediction_dumps": {"dir": str(predictions_dir), "sha256": dump_sha},
        },
        "outputs": {"score_table": {"path": _rel(out_path, root), "sha256": scores_sha}},
        "schema": {"columns": list(OUTPUT_COLUMNS),
                   "row_key": f"record_id = population record_id + '{ROW_ID_SEP}' + model + "
                              f"'{ROW_ID_SEP}' + mapping, unique per row as step 50 requires"},
        "conventions": {
            "observed_intensity_column": "PK$PEAK column 1, the absolute intensity (m/z int. rel.int.)",
            "observed_intensity_column_index": OBSERVED_INTENSITY_COLUMN_INDEX,
            "scale_invariance": "both endpoints are scale invariant, so the absolute/relative choice "
                                "cannot change any result",
            "parent_mass_source": "population theoretical_mh (theoretical [M+H]+), never the record's "
                                  "deposited PRECURSOR_M/Z",
            "prediction_inverse_transform": "applied to the prediction side only, exactly once, by the "
                                            "frozen similarity layer",
            "spec_id_rule": "f'{compound_id}_NCE{nce}', with the dump's 'pred_' name prefix stripped",
            "row_order": "population record_id ascending, then model, then mapping, in frozen order",
            "float_format": "repr(float), the shortest round-tripping decimal; nothing is rounded",
        },
        "counts": result["counts"],
        "drop_reason_counts": result["drop_reason_counts"],
        "drop_reason_constants": list(DROP_REASONS),
    }
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    sidecar_path.write_text(json.dumps(sidecar, indent=1, sort_keys=False) + "\n", encoding="utf-8")

    result["out_path"] = str(out_path)
    result["sidecar_path"] = str(sidecar_path)
    result["score_table_sha256"] = scores_sha
    return result


def _rel(path: Path, root: Path) -> str:
    path, root = Path(path), Path(root)
    return str(path.relative_to(root)) if path.is_relative_to(root) else str(path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--records-dir", type=Path, default=None,
                    help="directory of MassBank record text files, named by the population's "
                         "source_file column")
    ap.add_argument("--predictions-dir", type=Path, default=None,
                    help="directory of the step 30 prediction dumps")
    ap.add_argument("--out", type=Path, default=None, help="score table path")
    args = ap.parse_args(argv)
    res = run(records_dir=args.records_dir, predictions_dir=args.predictions_dir, out_path=args.out)
    print(json.dumps({"out_path": res["out_path"], "sidecar_path": res["sidecar_path"],
                      "score_table_sha256": res["score_table_sha256"],
                      "counts": res["counts"], "drop_reason_counts": res["drop_reason_counts"]},
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
