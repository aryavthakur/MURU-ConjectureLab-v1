"""Design B sourcing screen, step 1: fetch vendor catalogue identity metadata from PubChem vendor deposits.

Catalogue metadata only: SID, vendor catalogue ID (PubChem RegistryID), standardized CID, and CID-level
SMILES, InChIKey, formula, charge, monoisotopic mass and title. No spectrum, no model, no MS/MS outcome.
Raw payloads go to design_b/sourcing/downloads/ (untracked) and are registered in downloads_register.jsonl.
"""
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
A = REPO / "artifacts/ce_interface_adjudication"
DL = A / "design_b/sourcing/downloads"
DL.mkdir(parents=True, exist_ok=True)
PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
SOURCES = ["MedChemexpress MCE", "TargetMol", "Selleck Chemicals"]
PROPS = "SMILES,InChIKey,MolecularFormula,Charge,MonoisotopicMass,Title"


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def req(url, data=None, tries=6):
    for i in range(tries):
        try:
            r = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode() if data else None)
            with urllib.request.urlopen(r, timeout=300) as f:
                b = f.read()
            time.sleep(0.25)
            return b
        except urllib.error.HTTPError as e:
            if e.code == 404:  # PUGREST.NotFound: no item in this chunk has the requested field
                time.sleep(0.25)
                return None
            print("  retry", i, url[:90], e, flush=True)
            time.sleep(3 * (i + 1))
        except Exception as e:  # noqa: BLE001
            print("  retry", i, url[:90], e, flush=True)
            time.sleep(3 * (i + 1))
    raise SystemExit(f"failed {url}")


def register(name, url, path):
    b = path.read_bytes()
    with open(A / "downloads_register.jsonl", "a") as fh:
        fh.write(json.dumps({"task": "design-b-sourcing-screen", "name": name, "source_url": url,
                             "size_bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(),
                             "stored_as": str(path.relative_to(REPO)), "fetched_utc": now(),
                             "registered_utc": now(), "mode": "live"}) + "\n")


def main():
    import _scope_gate  # project-scope closure 2026-09-19: Design B cancelled, never executes
    _scope_gate.refuse()
    rows = []
    for src in SOURCES:
        tag = src.split()[0].lower()
        out = DL / f"{tag}_sid_registry_cid.csv"
        if out.exists():
            rows.append(pd.read_csv(out)); continue
        url = f"{PUG}/substance/sourceall/{urllib.parse.quote(src)}/sids/TXT"
        sids = [int(x) for x in req(url).decode().split()]
        print(src, len(sids), "SIDs", flush=True)
        reg, cid = {}, {}
        for i in range(0, len(sids), 2000):
            chunk = ",".join(map(str, sids[i:i + 2000]))
            b = req(f"{PUG}/substance/sid/xrefs/RegistryID/JSON", {"sid": chunk})
            for it in (json.loads(b)["InformationList"]["Information"] if b else []):
                reg[it["SID"]] = ";".join(it.get("RegistryID", []))
            b = req(f"{PUG}/substance/sid/cids/JSON?cids_type=standardized", {"sid": chunk})
            for it in (json.loads(b)["InformationList"]["Information"] if b else []):
                cid[it["SID"]] = it.get("CID", [None])[0]
            print(f"  {src} {i + 2000}/{len(sids)}", flush=True)
        d = pd.DataFrame({"source": src, "sid": sids, "catalogue_id": [reg.get(s) for s in sids],
                          "cid": [cid.get(s) for s in sids]})
        d.to_csv(out, index=False)
        register(out.name, url + " (+ sid xrefs/RegistryID and standardized cids)", out)
        rows.append(d)
    allr = pd.concat(rows, ignore_index=True)
    cids = sorted({int(c) for c in allr["cid"].dropna()})
    out = DL / "cid_properties.csv"
    if not out.exists():
        parts = []
        for i in range(0, len(cids), 1000):
            b = req(f"{PUG}/compound/cid/property/{PROPS}/CSV", {"cid": ",".join(map(str, cids[i:i + 1000]))})
            parts.append(pd.read_csv(pd.io.common.BytesIO(b)))
            print(f"  props {i + 1000}/{len(cids)}", flush=True)
        pd.concat(parts, ignore_index=True).to_csv(out, index=False)
        register(out.name, f"{PUG}/compound/cid/property/{PROPS}/CSV (POST, {len(cids)} CIDs)", out)
    print("done", len(allr), "SIDs", len(cids), "CIDs", now())


if __name__ == "__main__":
    main()
