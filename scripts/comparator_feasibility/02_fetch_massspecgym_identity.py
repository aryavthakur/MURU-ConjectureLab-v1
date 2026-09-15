"""Comparator feasibility audit: MassSpecGym 1.5 identity columns only, by HTTP range reads of Hugging Face's parquet
conversion of data/MassSpecGym1.5.tsv.

Only the parquet footer and the column chunks of IDENTITY_COLUMNS are transferred. The mzs and intensities columns
are never requested, so no MassSpecGym spectrum (including any MSnLib spectrum of a PR #7 compound) is downloaded.
Every byte range read is logged.
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts/comparator_feasibility"
DATASET = "roman-bushuiev/MassSpecGym"
PARQUET_API = f"https://huggingface.co/api/datasets/{DATASET}/parquet/main/val/0.parquet"
CONVERT_REF_API = f"https://huggingface.co/api/datasets/{DATASET}/revision/refs%2Fconvert%2Fparquet"
IDENTITY_COLUMNS = ["identifier", "inchikey", "fold", "simulation_challenge", "adduct", "instrument_type",
                    "collision_energy"]
FORBIDDEN = {"mzs", "intensities"}
EXPECTED_ROWS = 231_104
MAX_BYTES = 60_000_000


class RangeFile:
    """Minimal seekable read-only file over HTTP range requests, with a byte log."""

    def __init__(self, url: str):
        # A one-byte range probe (never a plain GET, which would fetch the whole file with its spectra columns).
        req = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
        with urllib.request.urlopen(req) as r:
            assert r.status == 206, r.status
            self.url = r.geturl()
            self.size = int(r.headers["Content-Range"].split("/")[-1])
            r.read()
        self.pos, self.log = 0, [[0, 0]]
        self.forbidden: list[tuple[int, int]] = []   # byte intervals of the mzs/intensities column chunks

    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else (self.pos + offset if whence == 1 else self.size + offset)
        return self.pos

    def tell(self):
        return self.pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        if n == 0 or self.pos >= self.size:
            return b""
        end = min(self.pos + n, self.size) - 1
        for a, b in self.forbidden:
            if self.pos <= b and end >= a:
                raise RuntimeError(f"refusing range {self.pos}-{end}: overlaps a spectrum column chunk {a}-{b}")
        if sum(e - s + 1 for s, e in self.log) + (end - self.pos + 1) > MAX_BYTES:
            raise RuntimeError("byte budget exceeded")
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{end}"})
        with urllib.request.urlopen(req) as r:
            assert r.status == 206, r.status
            data = r.read()
        self.log.append([self.pos, end])
        self.pos += len(data)
        return data

    def readable(self):
        return True

    def seekable(self):
        return True

    def close(self):
        pass

    @property
    def closed(self):
        return False


def main() -> int:
    assert not FORBIDDEN & set(IDENTITY_COLUMNS)
    with urllib.request.urlopen(CONVERT_REF_API) as r:
        convert_ref = json.load(r)
    f = RangeFile(PARQUET_API)
    pf = pq.ParquetFile(pa.PythonFile(f, mode="r"))
    schema_names = pf.schema_arrow.names
    assert FORBIDDEN <= set(schema_names), schema_names
    assert pf.metadata.num_rows == EXPECTED_ROWS, pf.metadata.num_rows
    md = pf.metadata
    for rg in range(md.num_row_groups):
        for c in range(md.num_columns):
            col = md.row_group(rg).column(c)
            if col.path_in_schema in FORBIDDEN:
                start = col.dictionary_page_offset if col.has_dictionary_page else col.data_page_offset
                f.forbidden.append((start, start + col.total_compressed_size - 1))
    assert f.forbidden
    table = pf.read(columns=IDENTITY_COLUMNS, use_threads=False)
    assert not FORBIDDEN & set(table.column_names)
    overlaps = [[s, e] for s, e in f.log for a, b in f.forbidden if s <= b and e >= a]
    assert not overlaps, f"logged ranges overlapping spectrum chunks: {overlaps}"
    OUT.mkdir(parents=True, exist_ok=True)
    out_path = OUT / "massspecgym15_identity.parquet"
    pq.write_table(table, out_path)
    record = {
        "source_parquet_url": f.url.split("?")[0], "source_parquet_size_bytes": f.size,
        "convert_parquet_revision_sha": convert_ref.get("sha"),
        "convert_parquet_last_modified": convert_ref.get("lastModified"),
        "hf_config_data_files": "data/MassSpecGym1.5.tsv (dataset card configs)",
        "tsv_lfs_sha256": "50cfdd1d22f79543c59555f9ce43c6893bd788a19a42b21fb4e2e3a54673c06a",
        "num_rows": pf.metadata.num_rows, "columns_read": IDENTITY_COLUMNS, "columns_never_read": sorted(FORBIDDEN),
        "forbidden_intervals_never_read": f.forbidden, "bytes_transferred": int(sum(e - s + 1 for s, e in f.log)), "byte_ranges": f.log,
        "output_sha256": hashlib.sha256(out_path.read_bytes()).hexdigest(),
    }
    (OUT / "massspecgym15_identity_fetch_record.json").write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps({k: v for k, v in record.items() if k not in ("byte_ranges", "forbidden_intervals_never_read")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
