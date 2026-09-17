"""CE interface adjudication, P4 step 1: MassSpecGym 1.5 scalar metadata columns only, by HTTP range reads of
Hugging Face's parquet conversion of data/MassSpecGym1.5.tsv.

Same access pattern as scripts/comparator_feasibility/02_fetch_massspecgym_identity.py:
  - the parquet is re-resolved through the HF parquet API (convert/parquet ref), probed with a one-byte range,
  - the footer is parsed, the byte interval of every mzs / intensities column chunk is computed,
  - every range request that would overlap one of those intervals is refused BEFORE it is sent,
  - after the read, every logged range is re-checked against the forbidden intervals and classified
    (byte-0 probe / footer tail / chunk of a requested column); an unclassifiable range fails the run.

Modes:
  --schema-only   read only the footer; write the schema JSON (no column chunk is read)
  (default)       read identifier + METADATA_COLUMNS (+ any scalar source/library-like column found in the schema,
                  disclosed in the record)

Outputs (artifacts/ce_interface_adjudication/):
  massspecgym15_schema.json
  massspecgym15_metadata_columns.parquet
  massspecgym15_metadata_columns_fetch_record.json   (or massspecgym15_schema_probe_fetch_record.json)
  downloads_register.jsonl                           (appended, one JSON line per fetched object)
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts/ce_interface_adjudication"
REGISTER = OUT / "downloads_register.jsonl"
SCRIPT = "scripts/ce_interface_adjudication/01_fetch_massspecgym_metadata_columns.py"
DATASET = "roman-bushuiev/MassSpecGym"
PARQUET_API = f"https://huggingface.co/api/datasets/{DATASET}/parquet/main/val/0.parquet"
CONVERT_REF_API = f"https://huggingface.co/api/datasets/{DATASET}/revision/refs%2Fconvert%2Fparquet"
KEY_COLUMN = "identifier"
METADATA_COLUMNS = ["precursor_mz", "parent_mass", "formula", "precursor_formula", "smiles"]
IDENTITY_COLUMNS = {"identifier", "inchikey", "fold", "simulation_challenge", "adduct", "instrument_type",
                    "collision_energy"}
SOURCE_LIKE = re.compile(r"(source|librar|database|origin|dataset|collection|provenance)", re.I)
FORBIDDEN = {"mzs", "intensities"}
EXPECTED_ROWS = 231_104
MAX_BYTES = 60_000_000
PRIOR_RECORD = ROOT / "artifacts/comparator_feasibility/massspecgym15_identity_fetch_record.json"


class RangeFile:
    """Minimal seekable read-only file over HTTP range requests, with a byte log and content hashes."""

    def __init__(self, url: str):
        req = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
        with urllib.request.urlopen(req) as r:
            assert r.status == 206, r.status
            self.url = r.geturl()
            self.size = int(r.headers["Content-Range"].split("/")[-1])
            self.etag = r.headers.get("ETag")
            first = r.read()
        self.pos, self.log = 0, [[0, 0]]
        self.retries: list[list] = []
        self.resolve = None
        self.hash = hashlib.sha256(first)          # sha256 of all transferred bytes, in transfer order
        self.chunk_sha: list[str] = [hashlib.sha256(first).hexdigest()]
        self.forbidden: list[tuple[int, int]] = []

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
        data = None
        for attempt in range(6):   # transient TLS EOFs were seen on the CDN; retry the identical range only
            try:
                req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{end}"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    assert r.status == 206, r.status
                    data = r.read()
                break
            except (urllib.error.URLError, ConnectionError, TimeoutError) as exc:
                self.retries.append([self.pos, end, attempt, repr(exc)[:200]])
                if isinstance(exc, urllib.error.HTTPError) and exc.code in (401, 403) and self.resolve is not None:
                    self.url = self.resolve()   # signed CDN URL expired: re-resolve through the HF API
                time.sleep(2 * (attempt + 1))
        if data is None:
            raise RuntimeError(f"range {self.pos}-{end} failed after retries")
        assert len(data) == end - self.pos + 1, (len(data), self.pos, end)
        self.log.append([self.pos, end])
        self.hash.update(data)
        self.chunk_sha.append(hashlib.sha256(data).hexdigest())
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


def chunk_intervals(md, names: set[str]) -> dict[str, list[tuple[int, int]]]:
    out: dict[str, list[tuple[int, int]]] = {}
    for rg in range(md.num_row_groups):
        for c in range(md.num_columns):
            col = md.row_group(rg).column(c)
            if col.path_in_schema.split(".")[0] in names:
                start = col.dictionary_page_offset if col.has_dictionary_page else col.data_page_offset
                out.setdefault(col.path_in_schema, []).append((start, start + col.total_compressed_size - 1))
    return out


def schema_record(pf) -> dict:
    md = pf.metadata
    per_col_bytes: dict[str, int] = {}
    for rg in range(md.num_row_groups):
        for c in range(md.num_columns):
            col = md.row_group(rg).column(c)
            per_col_bytes[col.path_in_schema] = per_col_bytes.get(col.path_in_schema, 0) + col.total_compressed_size
    kv = md.metadata or {}
    return {
        "num_rows": md.num_rows, "num_row_groups": md.num_row_groups, "num_leaf_columns": md.num_columns,
        "created_by": md.created_by, "format_version": md.format_version,
        "arrow_fields": [{"name": fl.name, "type": str(fl.type), "nullable": fl.nullable} for fl in pf.schema_arrow],
        "parquet_leaf_columns": [md.schema.column(i).path for i in range(md.num_columns)],
        "compressed_bytes_per_leaf_column": per_col_bytes,
        "key_value_metadata": {k.decode(): (v.decode()[:4000]) for k, v in kv.items()},
    }


def register(entry: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with REGISTER.open("a") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema-only", action="store_true")
    args = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    mode = "schema_only" if args.schema_only else "metadata_columns"

    ref_bytes = urllib.request.urlopen(CONVERT_REF_API).read()
    convert_ref = json.loads(ref_bytes)
    f = RangeFile(PARQUET_API)
    f.resolve = resolve_url
    try:
        return _run(args, now, mode, ref_bytes, convert_ref, f)
    except BaseException as exc:
        # Persist whatever was transferred before the failure, so every byte is accounted for in the register.
        n = int(sum(e - s + 1 for s, e in f.log))
        register({"fetched_utc": now, "name": "MassSpecGym1.5 HF parquet conversion val/0.parquet (partial: HTTP range "
                  "reads) FAILED RUN, no output written", "source_url": PARQUET_API, "size_bytes": n,
                  "sha256": f.hash.hexdigest(), "sha256_definition": "sha256 over all transferred bytes in transfer order",
                  "byte_ranges": f.log, "retries": f.retries, "error": repr(exc)[:500],
                  "forbidden_overlaps": [[s, e] for s, e in f.log for a, b in f.forbidden if s <= b and e >= a],
                  "script": SCRIPT, "mode": mode + "_failed"})
        register({"fetched_utc": now, "name": "refs%2Fconvert%2Fparquet revision API response (JSON, not stored)",
                  "source_url": CONVERT_REF_API, "size_bytes": len(ref_bytes),
                  "sha256": hashlib.sha256(ref_bytes).hexdigest(), "script": SCRIPT, "mode": mode + "_failed"})
        raise


def _run(args, now, mode, ref_bytes, convert_ref, f) -> int:
    # pre_buffer=False: pyarrow's default pre-buffering coalesces adjacent column chunks into one range, which on a
    # first attempt (2026-09-14, logged in downloads_register.jsonl) pulled unrequested non-spectral column chunks
    # lying between requested ones. With it off, each request is one chunk of a requested column.
    pf = pq.ParquetFile(pa.PythonFile(f, mode="r"), pre_buffer=False)
    md = pf.metadata
    names = pf.schema_arrow.names
    assert FORBIDDEN <= set(names), names
    assert md.num_rows == EXPECTED_ROWS, md.num_rows
    forb = chunk_intervals(md, FORBIDDEN)
    f.forbidden = sorted(iv for ivs in forb.values() for iv in ivs)
    assert f.forbidden
    schema = schema_record(pf)
    prior = json.loads(PRIOR_RECORD.read_text())
    same_file_as_prior = {
        "size_equal": f.size == prior["source_parquet_size_bytes"],
        "url_path_equal": f.url.split("?")[0] == prior["source_parquet_url"].split(" ")[0],
        "convert_revision_equal": convert_ref.get("sha") == prior["convert_parquet_revision_sha"],
        "forbidden_intervals_equal": [list(x) for x in f.forbidden] == prior["forbidden_intervals_never_read"],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "massspecgym15_schema.json").write_text(json.dumps(
        {"source_parquet_url": f.url.split("?")[0], "source_parquet_size_bytes": f.size,
         "convert_parquet_revision_sha": convert_ref.get("sha"), "same_file_as_identity_fetch": same_file_as_prior,
         **schema}, indent=1) + "\n")

    table = None
    if args.schema_only:
        cols: list[str] = []
        extra: list[str] = []
    else:
        nonscalar = {fl.name for fl in pf.schema_arrow
                     if pa.types.is_list(fl.type) or pa.types.is_large_list(fl.type) or pa.types.is_struct(fl.type)
                     or pa.types.is_map(fl.type)}
        missing = [c for c in METADATA_COLUMNS if c not in names]
        assert not missing, f"metadata columns absent from schema: {missing}"
        extra = sorted(n for n in names if SOURCE_LIKE.search(n) and n not in nonscalar and n not in FORBIDDEN
                       and n not in METADATA_COLUMNS and n not in IDENTITY_COLUMNS)
        cols = [KEY_COLUMN] + METADATA_COLUMNS + extra
        assert not FORBIDDEN & set(cols)
        assert not nonscalar & set(cols), nonscalar & set(cols)
        table = pf.read(columns=cols, use_threads=False)
        assert not FORBIDDEN & set(table.column_names)
        assert table.num_rows == EXPECTED_ROWS

    overlaps = [[s, e] for s, e in f.log for a, b in f.forbidden if s <= b and e >= a]
    assert not overlaps, f"logged ranges overlapping spectrum chunks: {overlaps}"
    all_chunks = chunk_intervals(md, set(names))
    last_chunk_end = max(iv[1] for ivs in all_chunks.values() for iv in ivs)
    allowed = chunk_intervals(md, set(cols)) if cols else {}
    classified = []
    for (s, e), sha in zip(f.log, f.chunk_sha):
        owners = sorted({c for c, ivs in all_chunks.items() for a, b in ivs if s <= b and e >= a})
        if s == 0 and e == 0:
            kind = "probe_byte0_magic"
        elif s > last_chunk_end:
            kind = "footer_tail"
        elif owners and set(owners) <= set(allowed):
            kind = "requested_column_chunk"
        elif owners and not (set(owners) & FORBIDDEN) and set(owners) & set(allowed):
            kind = "coalesced_nonspectral_chunks"
        else:
            kind = "other"
        classified.append({"range": [s, e], "bytes": e - s + 1, "kind": kind, "columns": owners, "sha256": sha})
    other = [c for c in classified if c["kind"] == "other"]
    assert not other, f"ranges outside footer/requested columns: {other[:5]}"
    bytes_transferred = int(sum(e - s + 1 for s, e in f.log))

    record = {
        "created_utc": now, "mode": mode, "script": SCRIPT,
        "source_parquet_api": PARQUET_API, "source_parquet_url": f.url.split("?")[0] + " (signed query string removed)",
        "source_parquet_size_bytes": f.size, "source_etag": f.etag,
        "convert_parquet_revision_sha": convert_ref.get("sha"),
        "convert_parquet_last_modified": convert_ref.get("lastModified"),
        "convert_ref_api_response_sha256": hashlib.sha256(ref_bytes).hexdigest(),
        "hf_config_data_files": "data/MassSpecGym1.5.tsv (dataset card configs)",
        "same_file_as_identity_fetch": same_file_as_prior,
        "num_rows": md.num_rows, "schema_columns": names,
        "columns_read": cols, "columns_never_read": sorted(FORBIDDEN),
        "columns_in_schema_not_read": sorted(set(names) - set(cols)),
        "extra_source_like_columns_read": extra,
        "forbidden_intervals_never_read": [list(x) for x in f.forbidden],
        "bytes_transferred": bytes_transferred, "sha256_of_transferred_bytes_in_order": f.hash.hexdigest(),
        "range_retries": f.retries,
        "bytes_by_kind": {k: sum(c["bytes"] for c in classified if c["kind"] == k)
                          for k in sorted({c["kind"] for c in classified})},
        "byte_ranges": classified,
    }
    if table is not None:
        out_path = OUT / "massspecgym15_metadata_columns.parquet"
        pq.write_table(table, out_path)
        record["output_parquet"] = str(out_path.relative_to(ROOT))
        record["output_sha256"] = hashlib.sha256(out_path.read_bytes()).hexdigest()
        record["output_size_bytes"] = out_path.stat().st_size
    rec_name = ("massspecgym15_schema_probe_fetch_record.json" if args.schema_only
                else "massspecgym15_metadata_columns_fetch_record.json")
    (OUT / rec_name).write_text(json.dumps(record, indent=1) + "\n")

    register({"fetched_utc": now, "name": "refs%2Fconvert%2Fparquet revision API response (JSON, not stored)",
              "source_url": CONVERT_REF_API, "size_bytes": len(ref_bytes),
              "sha256": hashlib.sha256(ref_bytes).hexdigest(), "script": SCRIPT, "mode": mode})
    register({"fetched_utc": now,
              "name": "MassSpecGym1.5 HF parquet conversion val/0.parquet (partial: HTTP range reads, "
                      + ("footer only" if args.schema_only else "footer + scalar metadata column chunks") + ")",
              "source_url": PARQUET_API, "resolved_url": record["source_parquet_url"],
              "source_file_size_bytes": f.size, "size_bytes": bytes_transferred,
              "sha256": f.hash.hexdigest(), "sha256_definition": "sha256 over all transferred bytes in transfer order",
              "n_ranges": len(f.log), "bytes_by_kind": record["bytes_by_kind"],
              "columns_read": cols, "columns_never_read": sorted(FORBIDDEN),
              "stored_as": record.get("output_parquet", "artifacts/ce_interface_adjudication/massspecgym15_schema.json"),
              "stored_sha256": record.get("output_sha256"),
              "fetch_record": f"artifacts/ce_interface_adjudication/{rec_name}", "script": SCRIPT, "mode": mode})
    print(json.dumps({k: v for k, v in record.items() if k not in ("byte_ranges", "forbidden_intervals_never_read")},
                     indent=1))
    return 0


def resolve_url() -> str:
    req = urllib.request.Request(PARQUET_API, headers={"Range": "bytes=0-0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        r.read()
        return r.geturl()


if __name__ == "__main__":
    raise SystemExit(main())
