"""C06 screen, second pass (CE interface adjudication, task S6): PharmMet DB parent drugs.

Companion to screen_c06_pharmmet.py. That script screened the 1,007 rows of the DB CSV's leading precursor block.
This one closes two gaps it left open:
  (i)  699 drugs have deposited raw/mzML files (MW archive listing) but 40 of them have NO row in the precursor block,
       so they were never keyed. Here they are identified through PubChem by their mwTab sample-source name.
  (ii) the paper reports 1114 drugs and the DB precursor IDs run PM0000001-PM0001123 with 116 IDs absent from the
       precursor block. Supplemental Table 1 of the paper (Europe PMC supplementary-file zip) is the authoritative list.

Subcommands
  fetch_suppl    Europe PMC supplementary-file zip of PMC12923290 (xlsx tables only; no spectra)
  fetch_missing  one PubChem PUG REST name->property request per deposited drug with no DB precursor row
  addendum       recompute identity, MURU key/scaffold group and exclusion membership for those drugs, cross-check the
                 supplemental drug list, and write c06_addendum.json

Every transfer is appended to artifacts/ce_interface_adjudication/downloads_register.jsonl. No spectra file is
requested. No ICEBERG, GLACIER, FIORA or MURU prediction is run.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import hashlib
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

W = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
A = W / "artifacts/ce_interface_adjudication"
OUT = A / "screen/c06_pharmmet"
DL = OUT / "downloads"
EXC = A / "exclusion"
REG = A / "downloads_register.jsonl"
SCRIPT = "scripts/ce_interface_adjudication/screen_c06_pharmmet_b.py"
TASK = "S6-C06"
UA = {"User-Agent": "Mozilla/5.0 (metadata screen)"}
CAP = 50_000_000
PROTON = 1.007276467


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def register(entry: dict) -> None:
    entry = {"fetched_utc": now(), "task": TASK, "script": SCRIPT, **entry}
    with REG.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def get(url: str, cap: int = CAP) -> tuple[int, dict, bytes]:
    req = urllib.request.Request(url, headers=dict(UA))
    with urllib.request.urlopen(req, timeout=300) as r:
        cl = r.headers.get("Content-Length")
        if cl is not None and int(cl) > cap:
            raise RuntimeError(f"refusing {url}: Content-Length {cl} above cap")
        data = r.read(cap + 1)
        if len(data) > cap:
            raise RuntimeError(f"refusing {url}: body above cap")
        return r.status, dict(r.headers), data


def load_set(name: str) -> set[str]:
    return {l.strip() for l in (EXC / name).read_text().splitlines() if l.strip()}


def mwtab_subjects() -> "collections.OrderedDict[str, str | None]":
    subj_full: collections.OrderedDict = collections.OrderedDict()
    for line in (DL / "mw_AN006575_mwtab.txt").read_text().splitlines():
        if line.startswith("SUBJECT_SAMPLE_FACTORS"):
            parts = line.split("\t")
            m = re.search(r"Sample source:(.*?)\s+Human S9 Fraction", parts[3])
            subj_full.setdefault(parts[1], m.group(1).strip() if m else None)
    subj: collections.OrderedDict = collections.OrderedDict()
    for sid, nm in subj_full.items():
        subj.setdefault(sid.split("-")[0], nm)
    return subj


def archive_files() -> dict:
    arch = (DL / "mw_ST003991_archive_contents.html").read_text(errors="replace")
    files: dict = collections.defaultdict(lambda: collections.defaultdict(set))
    for line in re.sub(r"<[^>]+>", "\n", arch).splitlines():
        s = line.strip()
        if not re.search(r"\.(raw|mzML)$", s):
            continue
        m = re.search(r"(\d+)\s+(\d+)\s+(?:[^\s]*\\)?(PM\d{7})(?:-\d+)?_(\d+hr)_(\d+)_([A-Za-z0-9]+)\.(raw|mzML)$", s)
        if m:
            _, _, pm, t, rep, mode, ext = m.groups()
            files[pm][(ext, mode.lower())].add((t, rep))
    return files


def fetch_suppl() -> None:
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12923290/supplementaryFiles"
    st, _, data = get(url)
    p = DL / "europepmc_PMC12923290_SupplementaryFiles.zip"
    p.write_bytes(data)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        members = [{"name": i.filename, "size": i.file_size} for i in z.infolist()]
    register({"name": "europepmc_PMC12923290_SupplementaryFiles.zip (paper supplementary files: Supplemental Table 1, "
                      "spreadsheet drug list; no spectra)", "source_url": url, "size_bytes": len(data),
              "sha256": sha(data), "stored_as": str(p.relative_to(W)), "http_status": st, "zip_members": members})
    print("suppl bytes", len(data), members)


def fetch_missing() -> None:
    rows = list(csv.DictReader((DL / "pharmmet_db_v1_0_precursor_rows.csv").open()))
    have = {r["precursorID"] for r in rows}
    todo = [(pm, nm) for pm, nm in mwtab_subjects().items() if pm not in have]
    resp = []
    for pm, name in todo:
        url = ("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/" + urllib.parse.quote(name or "", safe="")
               + "/property/InChIKey,IsomericSMILES,Title,MolecularFormula/JSON")
        try:
            st, _, data = get(url)
            resp.append({"precursorID": pm, "name": name, "url": url, "status": st, "body": json.loads(data)})
        except Exception as e:  # noqa: BLE001
            resp.append({"precursorID": pm, "name": name, "url": url, "error": repr(e)[:300]})
        time.sleep(0.25)
    p = DL / "pubchem_missing_precursor_name_check.json"
    b = json.dumps(resp, indent=1).encode()
    p.write_bytes(b)
    register({"name": "pubchem_missing_precursor_name_check.json (PubChem PUG REST name->property responses for the "
                      "deposited drugs with no row in the DB precursor block, concatenated)",
              "source_url": "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/<drug name>/property/"
                            "InChIKey,IsomericSMILES,Title,MolecularFormula/JSON",
              "request_urls": [x["url"] for x in resp], "n_requests": len(resp),
              "n_errors": sum("error" in x for x in resp), "size_bytes": len(b), "sha256": sha(b),
              "sha256_definition": "sha256 of the stored concatenated JSON", "stored_as": str(p.relative_to(W))})
    print("missing-name requests", len(resp), "errors", sum("error" in x for x in resp))


def addendum() -> None:
    import pandas as pd
    from rdkit import Chem, rdBase
    from rdkit.Chem import Descriptors
    sys.path.insert(0, str(W / "scripts/ce_interface_adjudication"))
    import scaffold_key as SK

    out: dict = {"script": SCRIPT, "rdkit": rdBase.rdkitVersion, "generated_utc": now()}
    files = archive_files()
    scr = pd.read_csv(OUT / "c06_compounds_screen.csv")

    zp = DL / "europepmc_PMC12923290_SupplementaryFiles.zip"
    if zp.exists():
        with zipfile.ZipFile(zp) as z:
            xls = [i.filename for i in z.infolist() if i.filename.lower().endswith((".xlsx", ".xls"))]
            sup = pd.read_excel(io.BytesIO(z.read(xls[0]))) if xls else None
        if sup is not None:
            info = {"member": xls[0], "rows": int(len(sup)), "columns": list(map(str, sup.columns)),
                    "head": sup.head(3).astype(str).to_dict("records")}
            cand = [c for c in sup.columns if re.search(r"name|drug|compound", str(c), re.I)]
            if cand:
                col = cand[0]
                sup_names = {str(x).strip().lower() for x in sup[col].dropna()}
                db_names = {str(x).strip().lower() for x in scr["name"].dropna()}
                mw_names = {str(x).strip().lower() for x in mwtab_subjects().values() if x}
                info.update({"name_column": str(col), "unique_names": len(sup_names),
                             "db_precursor_names_in_suppl": len(db_names & sup_names),
                             "n_suppl_names_not_in_db_precursor_block": len(sup_names - db_names),
                             "suppl_names_not_in_db_precursor_block": sorted(sup_names - db_names),
                             "n_suppl_names_with_deposited_files_by_name": len(sup_names & mw_names)})
            out["suppl_table"] = info

    S = {k: load_set(f) for k, f in {
        "msg15_recorded_all": "msg15_keys_all.txt", "msg15_parent_all": "msg15_parent_keys_all.txt",
        "muru_registry": "muru_exposure_registry_keys.txt", "study2_pop": "msnlib_study2_population_keys.txt",
        "comparator_pop": "comparator_common_population_keys.txt", "msnlib_9lib": "msnlib_9lib_keys.txt"}.items()}
    exposed: set[str] = set()
    for p in EXC.glob("muru_exposure_registry_population_*_keys.txt"):
        exposed |= load_set(p.name)
    S["muru_exposed_populations"] = exposed
    regc = pd.read_csv(W / "artifacts/wur_v2_confirmation_v2/exposure_registry/excluded_compounds.csv",
                       usecols=["key", "scaffold_group_census"])
    G = {"muru_exposed_populations": set(regc.loc[regc["key"].isin(exposed), "scaffold_group_census"].dropna()),
         "muru_registry": load_set("muru_exposure_registry_scaffold_groups.txt"),
         "study2_pop": load_set("msnlib_study2_population_scaffold_groups.txt"),
         "comparator_pop": load_set("comparator_common_population_scaffold_groups.txt"),
         "msg15_all": load_set("msg15_scaffold_groups_all.txt")}

    recs = []
    mp = DL / "pubchem_missing_precursor_name_check.json"
    if mp.exists():
        for x in json.loads(mp.read_text()):
            props = x.get("body", {}).get("PropertyTable", {}).get("Properties", []) if "body" in x else []
            pm = x["precursorID"]
            fm = files.get(pm, {})
            r = {"precursorID": pm, "name": x["name"], "resolved": bool(props), "n_cids": len(props),
                 "hilicpos_0hr_raw_files": sum(1 for t, _ in fm.get(("raw", "hilicpos"), ()) if t == "0hr"),
                 "raw_files_any_mode": sum(len(v) for k, v in fm.items() if k[0] == "raw")}
            if props:
                smi = props[0].get("IsomericSMILES") or props[0].get("SMILES")
                r["pubchem_title"] = props[0].get("Title")
                r["smiles"] = smi
                k, g = SK.key_and_group(smi) if smi else (None, None)
                r["key"], r["scaffold_group"] = k, g
                par = SK.parent_mol(smi) if smi else None
                if par is not None:
                    ch = Chem.GetFormalCharge(par)
                    r["parent_formal_charge"] = ch
                    r["mh_mz"] = (Descriptors.ExactMolWt(par) + PROTON) if ch == 0 else None
                for nm2, s in S.items():
                    r[f"in_{nm2}"] = (k in s) if k else None
                for nm2, s in G.items():
                    r[f"scaffold_in_{nm2}"] = (g in s) if g else None
            recs.append(r)
    ad = pd.DataFrame(recs)
    if len(ad):
        ad.to_csv(OUT / "c06_addendum_missing_precursors.csv", index=False)
        res = ad[ad["resolved"] == True]
        novel = res[(res["in_msg15_recorded_all"] == False) & (res["in_msg15_parent_all"] == False)]
        keep = novel[(novel["in_muru_exposed_populations"] == False) & (novel["in_study2_pop"] == False)
                     & (novel["in_comparator_pop"] == False) & (novel["scaffold_in_muru_exposed_populations"] != True)
                     & (novel["scaffold_in_study2_pop"] != True) & (novel["scaffold_in_comparator_pop"] != True)]
        keep_av = keep[(keep["parent_formal_charge"] == 0) & keep["mh_mz"].between(100.0, 1000.0)
                       & (keep["hilicpos_0hr_raw_files"] > 0)]
        db_groups = set(scr.loc[scr["key"].notna(), "scaffold_group"].dropna())
        out["missing_precursors"] = {
            "n": int(len(ad)), "resolved": int(len(res)), "unresolved_names": sorted(ad.loc[ad["resolved"] == False, "name"].dropna()),
            "with_hilicpos_0hr_raw": int((ad["hilicpos_0hr_raw_files"] > 0).sum()),
            "absent_from_msg15_both_routes": int(len(novel)),
            "also_absent_from_MURU_exposed_pops_PR7_comparator_keys_and_groups": int(len(keep)),
            "and_neutral_MH_in_100_1000_with_hilicpos_0hr_raw": int(len(keep_av)),
            "added_names": sorted(keep_av["name"].dropna().tolist()),
            "added_keys": sorted(keep_av["key"].dropna().tolist()),
            "added_scaffold_groups": sorted(set(keep_av["scaffold_group"].dropna())),
            "added_groups_already_present_in_db_precursor_block": sorted(set(keep_av["scaffold_group"].dropna()) & db_groups),
            "also_in_msnlib_9lib": int((keep_av["in_msnlib_9lib"] == True).sum()),
            "also_in_muru_full_registry": int((keep_av["in_muru_registry"] == True).sum()),
            "all_names": sorted(x for x in ad["name"].dropna().tolist()),
        }
    (OUT / "c06_addendum.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: v for k, v in out.items()}, indent=1, default=str)[:6000])


if __name__ == "__main__":
    {"fetch_suppl": fetch_suppl, "fetch_missing": fetch_missing, "addendum": addendum}[sys.argv[1]]()
