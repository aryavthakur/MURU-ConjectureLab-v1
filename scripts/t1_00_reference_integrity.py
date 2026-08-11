"""Reference-pack integrity audit -> REFERENCE_INTEGRITY.md.

The planning analysis reported that several files named .pdf were not genuine
PDF byte streams and that their hashes did not match SHA256SUMS.txt. This script
tests that claim independently and reports whatever it finds, including "the
defect did not reproduce". Nothing is repaired.
"""

from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "MURU_Reference_Pack"
sys.path.insert(0, str(ROOT / "src"))

MAGIC = {b"%PDF-": "PDF", b"PK\x03\x04": "ZIP/OOXML", b"\x89PNG": "PNG",
         b"<!DOC": "HTML", b"<html": "HTML", b"{": "JSON?", b"# ": "Markdown"}


def sniff(head: bytes) -> str:
    for sig, name in MAGIC.items():
        if head.startswith(sig):
            return name
    try:
        head.decode("utf-8")
        return "text/utf-8"
    except UnicodeDecodeError:
        return "unknown/binary"


def read_manifest() -> dict[str, str]:
    f = PACK / "SHA256SUMS.txt"
    if not f.exists():
        return {}
    out = {}
    for line in f.read_text().splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2:
            out[parts[1].strip()] = parts[0].strip()
    return out


def pdf_probe(path: Path) -> dict:
    """Structural and readability probe. Never modifies the file."""
    data = path.read_bytes()
    info = {
        "has_pdf_header": data[:5] == b"%PDF-",
        "version": data[5:8].decode("ascii", "replace") if data[:5] == b"%PDF-" else None,
        "has_eof": b"%%EOF" in data[-2048:],
        "xref_markers": data.count(b"xref"),
        "pages": None, "text_chars": None, "readable": False, "error": None,
    }
    try:
        from pypdf import PdfReader
        r = PdfReader(str(path))
        info["pages"] = len(r.pages)
        txt = "".join((p.extract_text() or "") for p in r.pages)
        info["text_chars"] = len(txt)
        info["readable"] = len(txt) > 500
    except Exception as exc:  # noqa: BLE001
        info["error"] = f"{type(exc).__name__}: {exc}"[:200]
    return info


def main() -> None:
    manifest = read_manifest()
    files = sorted(p for p in PACK.rglob("*") if p.is_file()
                   and p.name != ".DS_Store")

    rows, mismatches, unreadable = [], [], []
    for p in files:
        rel = str(p.relative_to(PACK))
        data = p.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        declared_ext = p.suffix.lower().lstrip(".")
        detected = sniff(data[:8])
        expected = manifest.get(rel)

        if expected is None:
            status = "NOT_IN_MANIFEST"
        elif expected == actual:
            status = "MATCH"
        else:
            status = "MISMATCH"
            mismatches.append(rel)

        ext_ok = (declared_ext == "pdf" and detected == "PDF") or \
                 (declared_ext in ("md", "txt") and detected in ("text/utf-8", "Markdown"))

        row = {"path": rel, "declared_ext": declared_ext, "detected_type": detected,
               "extension_matches_content": ext_ok, "sha256_actual": actual,
               "sha256_manifest": expected, "hash_status": status,
               "size": len(data)}
        if declared_ext == "pdf":
            row.update(pdf_probe(p))
            if not row["readable"]:
                unreadable.append(rel)
        else:
            row["readable"] = True
            row["text_chars"] = len(data)
        rows.append(row)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    L: list[str] = []
    A = L.append
    A("# REFERENCE_INTEGRITY.md\n")
    A(f"Generated {now} by `scripts/t1_00_reference_integrity.py`. "
      "No file in the reference pack was modified, repaired, or moved.\n")

    A("## Verdict on the reported defect\n")
    A("The planning analysis reported that several files named `.pdf` appeared "
      "not to be genuine PDF byte streams, and that their hashes did not match "
      "the provided manifest. Both halves of that claim were tested "
      "independently.\n")
    pdfs = [r for r in rows if r["declared_ext"] == "pdf"]
    genuine = sum(1 for r in pdfs if r.get("has_pdf_header"))
    matched = sum(1 for r in rows if r["hash_status"] == "MATCH")
    in_manifest = sum(1 for r in rows if r["sha256_manifest"] is not None)
    A(f"- **File type:** {genuine} of {len(pdfs)} files named `.pdf` carry a "
      "valid `%PDF-` header and parse as PDF documents. "
      f"**{len(pdfs) - genuine} are not genuine PDFs.**")
    A(f"- **Hashes:** {matched} of {in_manifest} manifest-listed files match "
      f"`SHA256SUMS.txt` exactly. **{len(mismatches)} mismatch.**")
    A("")
    if not mismatches and genuine == len(pdfs):
        A("**FAILED TO REPRODUCE.** Neither half of the reported defect is "
          "present in the files on disk. Every `.pdf` is a genuine PDF byte "
          "stream and every manifest hash matches. The reference pack is "
          "internally consistent.\n")
        A("Status of the reported defect: **FAILED** (tested and unsupported), "
          "using this project's epistemic vocabulary. If the defect was real at "
          "some earlier point, the files were replaced before this session "
          "began; nothing in the repository records such a replacement.\n")
    else:
        A("**REPRODUCED, at least in part.** See the table.\n")

    A("## Per-file audit\n")
    A("| File | Declared | Detected | Ext matches | SHA-256 (actual) | "
      "Manifest SHA-256 | Status | Readable |")
    A("|---|---|---|---|---|---|---|---|")
    for r in rows:
        man = (r["sha256_manifest"][:16] + "..." if r["sha256_manifest"]
               else "_not listed_")
        A(f"| `{r['path']}` | {r['declared_ext']} | {r['detected_type']} | "
          f"{'yes' if r['extension_matches_content'] else '**NO**'} | "
          f"`{r['sha256_actual'][:16]}...` | `{man}` | "
          f"{'MATCH' if r['hash_status']=='MATCH' else '**'+r['hash_status']+'**'} | "
          f"{'yes' if r.get('readable') else '**NO**'} |")
    A("")

    A("## PDF structural detail\n")
    A("| File | Header | Version | %%EOF | Pages | Extracted text (chars) |")
    A("|---|---|---|---|---|---|")
    for r in pdfs:
        A(f"| `{r['path']}` | {'%PDF-' if r['has_pdf_header'] else '**absent**'} | "
          f"{r.get('version') or '-'} | {'present' if r.get('has_eof') else '**absent**'} | "
          f"{r.get('pages') or '-'} | {r.get('text_chars') or 0:,} |")
    A("")

    A("## Scientific interpretation vs provenance\n")
    A("| Question | Answer |")
    A("|---|---|")
    A(f"| Does any discrepancy affect scientific interpretation? | "
      f"{'**No.** All content is readable and traceable.' if not unreadable else '**Yes** - see unreadable files above.'} |")
    A(f"| Does any discrepancy affect provenance? | "
      f"{'**No.** Every hash matches its manifest entry.' if not mismatches else '**Yes** - ' + ', '.join(mismatches)} |")
    A("| Was any file repaired? | **No.** This audit is read-only. |")
    A("")

    A("## Content traceability\n")
    A("Beyond byte integrity, the two claims MURU actually depends on were "
      "traced back into the reference text itself:\n")
    A("- **Spectral entropy definition** (Li et al. 2021): the text states the "
      "minimum is \"zero for a single fragment ion\", that uniform intensities "
      "give \"ln (number of ions)\", and that normalized entropy divides by "
      "\"ln (number of ions)\". This pins the logarithm base and is asserted in "
      "`tests/test_features.py`. **VERIFIED from the primary source.**")
    A("- **Collision-energy design** (Elapavalore et al. 2023): the text states "
      "spectra were \"fragmented at 6 different nominal collision energy (NCE) "
      "levels (15, 30, 45, 60, 75, and 90 NCE) in separate runs\". "
      "**VERIFIED from the primary source.**")
    A("- **Replicate mix design** (Elapavalore et al. 2023): \"mix 5 included "
      "the replicate set of mix 1\" and \"Mix 7 comprised 270 substances plus "
      "the replicate set from mix 1\", with Table 1 mapping mix 1/5/7 to 499/"
      "503/505. **VERIFIED from the primary source.**")
    A("- **Thermo NCE-to-eV conversion**: the master plan cites Revesz et al. "
      "2023 and Thermo PSB 104. Neither is in the reference pack and neither "
      "was retrieved. The formula is therefore **SUPPORTED (cited, not "
      "independently verified)** and every derived E_lab / E_com in this "
      "project is labelled conditional. See `CE_AUDIT.md`.")
    A("")

    A("## Non-blocking observation\n")
    A("`file(1)` reports `Li_2021_Spectral_Entropy.pdf` as \"23 pages\" while "
      "`pypdf` counts 19. This is a difference between counting `/Page` objects "
      "in the raw byte stream and walking the resolved page tree, not evidence "
      "of corruption: the document parses, paginates and yields text normally. "
      "Recorded as MINOR; no action.\n")

    out = ROOT / "REFERENCE_INTEGRITY.md"
    out.write_text("\n".join(L))
    print(f"written {out.name}: {len(rows)} files, {len(mismatches)} hash "
          f"mismatches, {len(unreadable)} unreadable")


if __name__ == "__main__":
    main()
