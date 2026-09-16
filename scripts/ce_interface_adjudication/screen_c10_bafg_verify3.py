"""S10-C10 verification, part 3: peak-COUNT (PK$NUM_PEAK) and PRECURSOR_TYPE census for BAFG.

Only the integer peak COUNT and the precursor-type string are taken from the record headers; no m/z and no intensity
value is fetched, printed or stored (any line that looks like a peak row is dropped before anything is kept).
The counts are joined to the per-record CE from c10_records_identity.csv, so the CE dependence of the recorded peak
count can be described without ever touching a peak.

Why this matters for the screen: MURU's quantity is fragmentation extent, which is estimated from the peak
distribution of a spectrum. A library whose records carry a handful of peaks cannot support that estimate, however
well its CE ladder is documented.
"""
import hashlib
import json
import re
import subprocess
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
ADJ = ROOT / "artifacts/ce_interface_adjudication"
OUT = ADJ / "screen/c10_bafg"
REGISTER = ADJ / "downloads_register.jsonl"
SCRIPT = "scripts/ce_interface_adjudication/screen_c10_bafg_verify3.py"
TASK = "S10-C10-verify"

PEAK_LINE = re.compile(r"^\s*\d+(\.\d+)?\s+\d")
NUM_PEAK = re.compile(r"PK\$NUM_PEAK:\s*(\d+)")
PREC_TYPE = re.compile(r"PRECURSOR_TYPE\s+(\S+)")
PREC_MZ = re.compile(r"PRECURSOR_M/Z\s+([\d.]+)")


def register(name, url, payload, stored_as):
    rec = {
        "fetched_utc": datetime.now(timezone.utc).isoformat(),
        "task": TASK,
        "name": name,
        "kind": "GitHub code search response with text-match fragments; peak-looking lines dropped before storage; "
                "only PK$NUM_PEAK integers, PRECURSOR_TYPE and PRECURSOR_M/Z are extracted (never a peak row)",
        "source_url": url,
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "stored_as": stored_as,
        "script": SCRIPT,
    }
    with REGISTER.open("a") as fh:
        fh.write(json.dumps(rec) + "\n")


rows = {}
pages, dropped = 0, 0
q = 'PRECURSOR_TYPE repo:MassBank/MassBank-data path:BAFG'
for page in range(1, 11):
    url = f"search/code?q={urllib.parse.quote(q)}&per_page=100&page={page}"
    r = subprocess.run(
        ["gh", "api", "-H", "Accept: application/vnd.github.text-match+json", url],
        capture_output=True,
    )
    if r.returncode != 0:
        print("stop at page", page, r.stderr.decode()[:200])
        break
    register(f"code search PRECURSOR_TYPE page {page}", "https://api.github.com/" + url, r.stdout,
             "artifacts/ce_interface_adjudication/screen/c10_bafg/s10_peak_count_census.json")
    d = json.loads(r.stdout)
    items = d.get("items", [])
    if not items:
        break
    pages += 1
    for it in items:
        acc = Path(it["path"]).stem
        np_, pt, pmz = None, None, None
        for tm in it.get("text_matches", []):
            for ln in tm.get("fragment", "").split("\n"):
                if PEAK_LINE.match(ln):
                    dropped += 1
                    continue
                m = NUM_PEAK.search(ln)
                if m:
                    np_ = int(m.group(1))
                m = PREC_TYPE.search(ln)
                if m:
                    pt = m.group(1)
                m = PREC_MZ.search(ln)
                if m:
                    pmz = float(m.group(1))
        rows[acc] = {"accession": acc, "num_peak": np_, "precursor_type": pt, "precursor_mz": pmz}
    time.sleep(7)

samp = pd.DataFrame(list(rows.values()))
df = pd.read_csv(OUT / "c10_records_identity.csv", low_memory=False)
j = samp.merge(df[["accession", "ion_mode", "ce_value", "key", "parent_charge", "mh_mz_from_parent",
                   "in_tree_2023_11"]], on="accession", how="left")

out = {
    "query": q,
    "pages_fetched": pages,
    "records_sampled": int(len(j)),
    "dropped_peak_lines": dropped,
    "sampling_note": "GitHub code-search best-match order over the BAFG directory; NOT a random sample of the "
                     "20,658 records. Treat the distribution as indicative, not as a population estimate.",
    "num_peak_available": int(j["num_peak"].notna().sum()),
    "precursor_type_distribution": {str(k): int(v) for k, v in j["precursor_type"].value_counts().items()},
    "precursor_type_by_ion_mode": {
        f"{m}|{t}": int(n) for (m, t), n in j.groupby(["ion_mode", "precursor_type"]).size().items()
    },
}
if j["num_peak"].notna().any():
    npk = j["num_peak"].dropna()
    out["num_peak_summary"] = {
        "min": int(npk.min()), "p10": float(npk.quantile(0.10)), "median": float(npk.median()),
        "p90": float(npk.quantile(0.90)), "max": int(npk.max()), "mean": float(npk.mean()),
        "share_le_5_peaks": float((npk <= 5).mean()),
        "share_le_10_peaks": float((npk <= 10).mean()),
        "share_ge_20_peaks": float((npk >= 20).mean()),
    }
    by_ce = j.dropna(subset=["num_peak", "ce_value"]).groupby("ce_value")["num_peak"].agg(
        ["size", "median", "mean", "max"])
    out["num_peak_by_ce"] = {str(k): {kk: float(vv) for kk, vv in v.items()} for k, v in by_ce.iterrows()}
    by_mode = j.dropna(subset=["num_peak"]).groupby("ion_mode")["num_peak"].agg(["size", "median", "mean"])
    out["num_peak_by_ion_mode"] = {str(k): {kk: float(vv) for kk, vv in v.items()} for k, v in by_mode.iterrows()}

(OUT / "s10_peak_count_census.json").write_text(json.dumps(out, indent=1))
j.to_csv(OUT / "s10_peak_count_sample.csv", index=False)
print(json.dumps(out, indent=1)[:6000])
