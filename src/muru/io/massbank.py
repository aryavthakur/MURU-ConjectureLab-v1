"""MassBank Record Format 2.6.0 parser.

Specification:
    https://github.com/MassBank/MassBank-web/blob/master/Documentation/MassBankRecordFormat.md

Governing rule (project field guide, "MURU parsing rule"):
    Never throw away the raw metadata representation after parsing.

So every record keeps `raw_lines` and a `fields` map of tag -> list of raw
strings, alongside any convenience accessor. Convenience accessors return None
when a field is absent; they never invent, coerce, or default a value. A record
that cannot be parsed is returned with `parse_status="FAILED"` and a reason,
never silently dropped.

Record grammar as encountered:

    TAG: value                      simple field
    TAG: SUBTAG value               subtagged field (COMMENT, CH$LINK, AC$*, MS$*)
    TAG: header                     block header, followed by
      indented data line            continuation lines (2-space indent)
    //                              end of record
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Tags whose value is "SUBTAG rest-of-line" rather than a bare value.
SUBTAGGED = {
    "COMMENT",
    "CH$LINK",
    "AC$MASS_SPECTROMETRY",
    "AC$CHROMATOGRAPHY",
    "AC$GENERAL",
    "MS$FOCUSED_ION",
    "MS$DATA_PROCESSING",
    "PK$ANNOTATION",
}

# Tags introducing an indented data block.
BLOCK_TAGS = {"PK$PEAK", "PK$ANNOTATION"}

TAG_RE = re.compile(r"^(?P<tag>[A-Z][A-Z0-9$_/]*):\s?(?P<rest>.*)$")
ACCESSION_RE = re.compile(r"^MSBNK-LCSB-LU(?P<internal_id>\d{4})(?P<slot>\d{2})$")


@dataclass
class Peak:
    """One entry of PK$PEAK. `rel_intensity` is MassBank's 0-999 scaling."""

    mz: float
    intensity: float
    rel_intensity: float


@dataclass
class MassBankRecord:
    """A parsed record with its raw representation retained in full."""

    accession: str | None
    path: str
    raw_text: str
    # tag -> list of raw value strings, in file order, duplicates preserved.
    fields: dict[str, list[str]] = field(default_factory=dict)
    # (tag, subtag) -> list of raw value strings.
    subfields: dict[tuple[str, str], list[str]] = field(default_factory=dict)
    peaks: list[Peak] = field(default_factory=list)
    annotation_rows: list[str] = field(default_factory=list)
    parse_status: str = "OK"
    warnings: list[str] = field(default_factory=list)

    # -- raw accessors ----------------------------------------------------
    def get(self, tag: str) -> str | None:
        """First raw value for `tag`, or None. Never defaults."""
        v = self.fields.get(tag)
        return v[0] if v else None

    def get_all(self, tag: str) -> list[str]:
        return list(self.fields.get(tag, []))

    def sub(self, tag: str, subtag: str) -> str | None:
        """First raw value for `tag: subtag`, or None. Never defaults."""
        v = self.subfields.get((tag, subtag))
        return v[0] if v else None

    def sub_all(self, tag: str, subtag: str) -> list[str]:
        return list(self.subfields.get((tag, subtag), []))

    # -- derived identity -------------------------------------------------
    @property
    def internal_id(self) -> int | None:
        """RMassBank internal compound ID from the accession, not the COMMENT.

        Both are recorded; T1.6 asserts they agree rather than trusting either.
        """
        if not self.accession:
            return None
        m = ACCESSION_RE.match(self.accession)
        return int(m.group("internal_id")) if m else None

    @property
    def slot(self) -> str | None:
        if not self.accession:
            return None
        m = ACCESSION_RE.match(self.accession)
        return m.group("slot") if m else None

    @property
    def inchikey(self) -> str | None:
        """InChIKey from CH$LINK, raw. None if the record does not carry one."""
        return self.sub("CH$LINK", "INCHIKEY")

    @property
    def num_peak_declared(self) -> int | None:
        v = self.get("PK$NUM_PEAK")
        if v is None:
            return None
        try:
            return int(v.strip())
        except ValueError:
            return None


def parse_record(text: str, path: str = "<memory>") -> MassBankRecord:
    """Parse one MassBank record. Never raises on malformed input."""
    rec = MassBankRecord(accession=None, path=path, raw_text=text)
    current_block: str | None = None

    for lineno, line in enumerate(text.splitlines(), start=1):
        if line.strip() == "//":
            current_block = None
            continue
        if not line.strip():
            continue

        # Indented line -> continuation of the block most recently opened.
        if line[:1] in (" ", "\t"):
            if current_block == "PK$PEAK":
                _consume_peak(rec, line, lineno)
            elif current_block == "PK$ANNOTATION":
                rec.annotation_rows.append(line.strip())
            else:
                rec.warnings.append(
                    f"line {lineno}: indented line outside a known block"
                )
            continue

        m = TAG_RE.match(line)
        if not m:
            rec.warnings.append(f"line {lineno}: unparseable line")
            current_block = None
            continue

        tag, rest = m.group("tag"), m.group("rest")
        rec.fields.setdefault(tag, []).append(rest)

        if tag == "ACCESSION":
            rec.accession = rest.strip()

        if tag in SUBTAGGED:
            parts = rest.split(None, 1)
            if parts:
                subtag = parts[0]
                value = parts[1] if len(parts) > 1 else ""
                rec.subfields.setdefault((tag, subtag), []).append(value.strip())

        current_block = tag if tag in BLOCK_TAGS else None

    _validate(rec)
    return rec


def _consume_peak(rec: MassBankRecord, line: str, lineno: int) -> None:
    parts = line.split()
    if len(parts) < 3:
        rec.warnings.append(f"line {lineno}: peak line has {len(parts)} fields, need 3")
        return
    try:
        rec.peaks.append(
            Peak(mz=float(parts[0]), intensity=float(parts[1]),
                 rel_intensity=float(parts[2]))
        )
    except ValueError:
        rec.warnings.append(f"line {lineno}: non-numeric peak values: {line.strip()!r}")


def _validate(rec: MassBankRecord) -> None:
    """Structural checks. Sets parse_status; does not repair anything."""
    if rec.accession is None:
        rec.parse_status = "FAILED"
        rec.warnings.append("no ACCESSION field")
        return
    if not ACCESSION_RE.match(rec.accession):
        rec.warnings.append(f"accession {rec.accession!r} off the LCSB-LU pattern")

    declared = rec.num_peak_declared
    if declared is None:
        rec.warnings.append("PK$NUM_PEAK missing or non-integer")
    elif declared != len(rec.peaks):
        # BLOCKER-class: a peak list that does not match its own declared count
        # means the parser or the record is losing peaks.
        rec.parse_status = "FAILED"
        rec.warnings.append(
            f"PK$NUM_PEAK={declared} but parsed {len(rec.peaks)} peaks"
        )

    if not rec.peaks and rec.parse_status == "OK":
        rec.warnings.append("record carries zero peaks")


def parse_file(path: str | Path) -> MassBankRecord:
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="strict")
    return parse_record(text, path=str(p))


def iter_records(directory: str | Path, pattern: str = "*.txt"):
    """Yield parsed records in sorted filename order (deterministic)."""
    for p in sorted(Path(directory).glob(pattern)):
        yield parse_file(p)
