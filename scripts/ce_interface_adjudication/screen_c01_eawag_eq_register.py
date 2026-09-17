"""S1 screen C01: append one downloads_register.jsonl line per file fetched by this screen (metadata only)."""
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "artifacts/ce_interface_adjudication"
D = A / "screen/c01_eawag_eq/downloads"
REG = A / "downloads_register.jsonl"
SCRIPT_H = "scripts/ce_interface_adjudication/screen_c01_eawag_eq_harvest.py"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    lines = []
    for ps in "SCEPI":
        p = D / f"codesearch_{ps}.json"
        doc = json.loads(p.read_text())
        lines.append({
            "fetched_utc": doc["retrieved_utc"], "registered_utc": now, "task": "S1-C01",
            "name": f"codesearch_{ps}.json (GitHub code-search text-match fragments, MassBank-data Eawag EQ record "
                    f"HEADER lines only, terms '{doc['terms']}'; PK$ lines and all non-header lines discarded in memory, "
                    f"never written; no record file downloaded)",
            "source_url": "https://api.github.com/search/code?q=repo:MassBank/MassBank-data+filename:<prefix>+" + doc["terms"].replace(" ", "+"),
            "n_api_requests": len(doc["queries"]), "api_response_bytes_total": doc["api_response_bytes_total"],
            "n_records_harvested": doc["n_harvested"], "n_targets": doc["n_targets"],
            "stored_as": str(p.relative_to(ROOT)), "size_bytes": p.stat().st_size, "sha256": sha(p),
            "sha256_definition": "sha256 of the stored filtered JSON (raw API responses were not persisted)",
            "content_class": "metadata_only", "script": SCRIPT_H})
    extra = [
        ("RMassBank_inst_RMB_options.ini", "https://api.github.com/repos/MassBank/RMassBank/contents/inst/RMB_options.ini (blob 22dc0fd8f7eb3a67fb6e2176f0583eed77694bdf, last commit 0a69fbc 2023-08-16)",
         "RMassBank settings template (source code config; defines record CE annotation strings)"),
        ("MassBank-web_Documentation_MassBankRecordFormat.md", "https://api.github.com/repos/MassBank/MassBank-web/contents/Documentation/MassBankRecordFormat.md (blob 3de1e8859d4a642acc15d10453b8dd69aaf24222, last commit 61d21ae 2025-07-18)",
         "MassBank record format documentation"),
        ("massbank_data_pulls_258_263_319_398.jsonl", "https://api.github.com/repos/MassBank/MassBank-data/pulls/{258,263,319,398}",
         "PR metadata (dates, file counts; no file contents)"),
    ]
    for fn, url, what in extra:
        p = D / fn
        lines.append({"fetched_utc": now, "registered_utc": now, "task": "S1-C01", "name": f"{fn} ({what})",
                      "source_url": url, "stored_as": str(p.relative_to(ROOT)), "size_bytes": p.stat().st_size,
                      "sha256": sha(p), "content_class": "metadata_only"})
    with REG.open("a") as f:
        for ln in lines:
            f.write(json.dumps(ln, sort_keys=True) + "\n")
    print(len(lines), "lines appended to", REG)


if __name__ == "__main__":
    main()
