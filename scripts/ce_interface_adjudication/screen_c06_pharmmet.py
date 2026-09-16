"""C06 screen (CE interface adjudication, task S6): PharmMet DB parent drugs (Metabolomics Workbench ST003991,
Jeon et al. 2025 Drug Metab Dispos, PMC12923290). Metadata only.

Subcommands
  fetch   transfer metadata objects into artifacts/.../screen/c06_pharmmet/downloads and append one line per object to
          downloads_register.jsonl. Objects:
            - Europe PMC full-text XML of the paper (article text, no data)
            - Metabolomics Workbench REST: study summary JSON, analysis JSON
            - mwTab text of analysis AN006575 (study metadata + sample factors; its MS_METABOLITE_DATA block is a
              one-row placeholder named "Test")
            - Metabolomics Workbench raw-data download page and archive contents listing (file names and sizes only)
            - GitHub ClinicalBiomarkersLaborabory/PharmMet: PharmMet_app.R (source code) and the PRECURSOR BLOCK of
              PharmMet_DB_v1.0.csv by HTTP range reads. The CSV is 104,774,483 bytes, above the ~50 MB policy cap, so it
              is never transferred whole: ranges of 262,144 bytes are read from byte 0 only until the first complete
              non-precursor row is parsed. Only precursor rows are persisted (parsed CSV); the tail of the last chunk
              (metabolite rows) is discarded.
            - PubChem PUG REST property responses for a fixed random sample of 25 "Parent ID" values (to test the
              INFERRED reading that Parent ID is a PubChem CID). Stored as one JSON file.
          Never requested: ST003991_PharmMet.zip (.raw), ST003991_mzml.zip (.mzML), any per-sample raw/mzML file.
  screen  compute MURU keys/scaffold groups and all overlap/feasibility counts from the persisted metadata.

No ICEBERG, GLACIER, FIORA or MURU prediction is run.
"""
from __future__ import annotations

import ast
import collections
import csv
import datetime as dt
import hashlib
import io
import json
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

W = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
A = W / "artifacts/ce_interface_adjudication"
OUT = A / "screen/c06_pharmmet"
DL = OUT / "downloads"
EXC = A / "exclusion"
REG = A / "downloads_register.jsonl"
SCRIPT = "scripts/ce_interface_adjudication/screen_c06_pharmmet.py"
TASK = "S6-C06"
UA = {"User-Agent": "Mozilla/5.0 (metadata screen)"}

GH_COMMIT = "88eeb0a0e395a88fac631b91c73f068d6a9ded85"
CSV_URL = f"https://raw.githubusercontent.com/ClinicalBiomarkersLaborabory/PharmMet/{GH_COMMIT}/PharmMet_DB_v1.0.csv"
APP_URL = f"https://raw.githubusercontent.com/ClinicalBiomarkersLaborabory/PharmMet/{GH_COMMIT}/PharmMet_app.R"
CHUNK = 262_144
CAP = 50_000_000

PROTON = 1.007276467

# Identity defects found by reading structures (VERIFIED in this screen, not caught by the PubChem name route because
# PubChem's own misspelled synonym entry carries the same wrong isomer):
MANUAL_IDENTITY_DEFECTS = {
    "PM0000264": {"db_name": "Cinnarazine", "db_key": "SSKFWBSXNIWCBH",
                  "reason": "DB SMILES C1CN(CCN1C=CCC2=CC=CC=C2)C(c)c is the N-CH=CH-CH2-Ph enamine isomer (PubChem CID 5353532 "
                            "'Cinnarazine'); cinnarizine is N-CH2-CH=CH-Ph, key DERZBLKQOCDDDZ, which is in "
                            "exclusion/msg15_keys_all.txt",
                  "true_key": "DERZBLKQOCDDDZ"},
}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def register(entry: dict) -> None:
    entry = {"fetched_utc": now(), "task": TASK, "script": SCRIPT, **entry}
    with REG.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def get(url: str, rng: tuple[int, int] | None = None, cap: int = CAP) -> tuple[int, dict, bytes]:
    h = dict(UA)
    if rng:
        h["Range"] = f"bytes={rng[0]}-{rng[1]}"
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=300) as r:
        cl = r.headers.get("Content-Length")
        if cl is not None and int(cl) > cap:
            raise RuntimeError(f"refusing {url}: Content-Length {cl} above cap")
        data = r.read(cap + 1)
        if len(data) > cap:
            raise RuntimeError(f"refusing {url}: body above cap")
        return r.status, dict(r.headers), data


def save_simple(name: str, url: str, desc: str) -> Path:
    p = DL / name
    status, headers, data = get(url)
    p.write_bytes(data)
    register({"name": f"{name} ({desc})", "source_url": url, "size_bytes": len(data), "sha256": sha(data),
              "stored_as": str(p.relative_to(W)), "http_status": status})
    print("saved", name, len(data))
    return p


def fetch() -> None:
    DL.mkdir(parents=True, exist_ok=True)
    save_simple("europepmc_PMC12923290_fullTextXML.xml",
                "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12923290/fullTextXML",
                "Europe PMC full-text XML of Jeon et al. 2025 DMD 53:100183; article text only")
    save_simple("mw_ST003991_summary.json", "https://www.metabolomicsworkbench.org/rest/study/study_id/ST003991/summary",
                "Metabolomics Workbench REST study summary")
    save_simple("mw_ST003991_analysis.json",
                "https://www.metabolomicsworkbench.org/rest/study/study_id/ST003991/analysis",
                "Metabolomics Workbench REST analysis metadata")
    save_simple("mw_AN006575_mwtab.txt", "https://www.metabolomicsworkbench.org/rest/study/analysis_id/AN006575/mwtab/txt",
                "mwTab metadata of analysis AN006575 incl. SUBJECT_SAMPLE_FACTORS; no spectra")
    save_simple("mw_ST003991_rawdata_download_page.html",
                "https://www.metabolomicsworkbench.org/data/DRCCStudySummary.php?Mode=SetupRawDataDownload&StudyID=ST003991",
                "MW raw-data download page: archive names, sizes, checksums; archives NOT downloaded")
    save_simple("mw_ST003991_archive_contents.html",
                "https://www.metabolomicsworkbench.org/data/show_archive_contents.php?STUDY_ID=ST003991",
                "MW archive contents listing (7-Zip listing of file names and sizes); no file content")
    save_simple("github_PharmMet_app.R", APP_URL, f"PharmMet Shiny app source at commit {GH_COMMIT}")
    fetch_csv()


def fetch_csv() -> None:
    """Attempt 2 rule (attempt 1 wrongly also required biosystem == 'Precursor', which stopped at PM0000464, a parent
    whose biosystem field is 'Human'): a precursor row is a row with metaboliteID == precursorID."""
    DL.mkdir(parents=True, exist_ok=True)
    # precursor block of the DB CSV by range reads
    _, headers, _ = get(CSV_URL, (0, 0))
    total = int(headers["Content-Range"].split("/")[-1])
    buf = b""
    ranges: list[dict] = []
    hasher = hashlib.sha256()
    boundary = None
    header: list[str] = []
    prec_rows: list[list[str]] = []
    after: list[tuple[str, str, str]] = []
    start = 0
    while boundary is None:
        end = min(start + CHUNK - 1, total - 1)
        st, _, data = get(CSV_URL, (start, end))
        assert st == 206, st
        ranges.append({"range": [start, end], "n_bytes": len(data)})
        hasher.update(data)
        buf += data
        start = end + 1
        text = buf.decode("utf-8-sig", errors="replace")
        cut = text.rfind("\n")
        rows = list(csv.reader(io.StringIO(text[:cut])))
        header = rows[0]
        ip, im, ib = header.index("precursorID"), header.index("metaboliteID"), header.index("biosystem")
        prec_rows, after, boundary = [], [], None
        for k, r in enumerate(rows[1:]):
            if len(r) != len(header):
                if k == len(rows) - 2:
                    break  # last, possibly incomplete row
                raise RuntimeError(f"malformed row {k}")
            is_prec = r[im] == r[ip]
            if boundary is None and is_prec:
                prec_rows.append(r)
            else:
                if boundary is None:
                    boundary = k
                after.append((r[ip], r[im], r[ib]))
        if boundary is not None and len(after) < 50 and start < total:
            boundary = None  # read one more chunk so at least 50 post-boundary rows are checked for stray precursors
            continue
        if start >= total or sum(x["n_bytes"] for x in ranges) > 20_000_000:
            raise RuntimeError("no boundary within 20 MB; stop")
    stray = [a for a in after if a[0] == a[1]]
    p = DL / "pharmmet_db_v1_0_precursor_rows.csv"
    with p.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(header)
        wr.writerows(prec_rows)
    stored = p.read_bytes()
    rec = {"name": "PharmMet_DB_v1.0.csv (partial: HTTP range reads of the leading precursor block only; attempt 2, rule metaboliteID == precursorID)",
           "source_url": CSV_URL, "source_file_size_bytes": total, "n_ranges": len(ranges), "ranges": ranges,
           "size_bytes": sum(x["n_bytes"] for x in ranges), "sha256": hasher.hexdigest(),
           "sha256_definition": "sha256 over all transferred bytes in transfer order (excludes the 1-byte size probe)",
           "size_probe": {"range": [0, 0], "n_bytes": 1},
           "n_precursor_rows": len(prec_rows), "n_post_boundary_rows_checked": len(after),
           "stray_precursor_rows_after_boundary": len(stray), "first_post_boundary_rows": after[:5],
           "note": "whole file (104.8 MB) exceeds the ~50 MB cap and was never transferred; only the leading precursor "
                   "block plus a checking margin was read; metabolite rows were discarded, not persisted",
           "stored_as": str(p.relative_to(W)), "stored_sha256": sha(stored)}
    (DL / "pharmmet_db_csv_range_fetch_record.json").write_text(json.dumps(rec, indent=1))
    register(rec)
    print("precursor rows", len(prec_rows), "bytes", rec["size_bytes"], "post-boundary checked", len(after), "stray", len(stray))

    # PubChem CID check on a fixed random sample
    ipid, ism = header.index("Parent ID"), header.index("SMILES")
    rnd = random.Random(20260914)
    cand = [(r[ip], r[ipid]) for r in prec_rows if r[ipid].isdigit()]
    sample = rnd.sample(cand, 25)
    biosys = collections.Counter(r[ib] for r in prec_rows)
    rec["biosystem_values_in_precursor_rows"] = dict(biosys)
    (DL / "pharmmet_db_csv_range_fetch_record.json").write_text(json.dumps(rec, indent=1))
    resp = []
    for pm, cid in sample:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/InChIKey,Title,MolecularFormula/JSON"
        try:
            st, _, data = get(url)
            resp.append({"precursorID": pm, "cid": cid, "url": url, "status": st, "body": json.loads(data)})
        except Exception as e:  # noqa: BLE001
            resp.append({"precursorID": pm, "cid": cid, "url": url, "error": repr(e)})
        time.sleep(0.3)
    p = DL / "pubchem_cid_sample_check.json"
    b = json.dumps(resp, indent=1).encode()
    p.write_bytes(b)
    register({"name": "pubchem_cid_sample_check.json (25 PubChem PUG REST property responses, concatenated)",
              "source_url": "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/<CID>/property/InChIKey,Title,MolecularFormula/JSON",
              "request_urls": [x["url"] for x in resp], "size_bytes": len(b), "sha256": sha(b),
              "sha256_definition": "sha256 of the stored concatenated JSON", "stored_as": str(p.relative_to(W)),
              "n_parent_id_numeric": len(cand)})



def fetch_names() -> None:
    """Name-route identity check for every precursor whose DB-SMILES key is absent from MassSpecGym 1.5 (both routes).
    Motivation: the DB SMILES for Cinnarazine (PM0000264) encodes an enamine isomer (key SSKFWBSXNIWCBH) instead of
    cinnarizine (DERZBLKQOCDDDZ, which IS in MassSpecGym), so DB-SMILES novelty can be an identity defect.
    One PubChem PUG REST name -> property request per drug name; all responses stored in one JSON file."""
    import urllib.parse
    rows = list(csv.DictReader((DL / "pharmmet_db_v1_0_precursor_rows.csv").open()))
    sys.path.insert(0, str(W / "scripts/ce_interface_adjudication"))
    import scaffold_key as SK
    msg = load_set("msg15_keys_all.txt") | load_set("msg15_parent_keys_all.txt")
    todo = []
    for r in rows:
        k, _ = SK.key_and_group(r["SMILES"])
        from rdkit import Chem
        from rdkit.Chem import inchi
        m0 = Chem.MolFromSmiles(r["SMILES"])
        rk = inchi.MolToInchiKey(m0).split("-")[0] if m0 is not None else None
        if not ({k, rk} - {None}) & msg:
            todo.append((r["precursorID"], r["name"]))
    resp = []
    for pm, name in todo:
        url = ("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/" + urllib.parse.quote(name, safe="")
               + "/property/InChIKey,IsomericSMILES,Title/JSON")
        try:
            st, _, data = get(url)
            resp.append({"precursorID": pm, "name": name, "url": url, "status": st, "body": json.loads(data)})
        except Exception as e:  # noqa: BLE001
            resp.append({"precursorID": pm, "name": name, "url": url, "error": repr(e)[:300]})
        time.sleep(0.25)
    p = DL / "pubchem_name_route_check.json"
    b = json.dumps(resp, indent=1).encode()
    p.write_bytes(b)
    register({"name": "pubchem_name_route_check.json (PubChem PUG REST name->InChIKey/SMILES property responses for the "
                      "MassSpecGym-novel precursors, concatenated)",
              "source_url": "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/<drug name>/property/InChIKey,IsomericSMILES,Title/JSON",
              "n_requests": len(resp), "n_errors": sum("error" in x for x in resp), "size_bytes": len(b), "sha256": sha(b),
              "sha256_definition": "sha256 of the stored concatenated JSON", "stored_as": str(p.relative_to(W))})
    print("name requests", len(resp), "errors", sum("error" in x for x in resp))


# ----------------------------------------------------------------------------------------------------------------------

def load_set(name: str) -> set[str]:
    return {l.strip() for l in (EXC / name).read_text().splitlines() if l.strip()}


def parse_listlit(s: str):
    if s in ("", "N/A", "NA"):
        return []
    try:
        v = ast.literal_eval(s)
    except Exception:  # noqa: BLE001
        return None
    flat = []

    def rec(x):
        if isinstance(x, list):
            for y in x:
                rec(y)
        else:
            flat.append(x)
    rec(v)
    return flat


def screen() -> None:
    sys.path.insert(0, str(W / "scripts/ce_interface_adjudication"))
    import pandas as pd
    from rdkit import Chem, rdBase
    from rdkit.Chem import Descriptors, inchi
    import scaffold_key as SK

    rows = list(csv.DictReader((DL / "pharmmet_db_v1_0_precursor_rows.csv").open()))

    mwtab = (DL / "mw_AN006575_mwtab.txt").read_text()
    subj_full: dict[str, str | None] = collections.OrderedDict()
    subj_modes: dict = collections.defaultdict(collections.Counter)
    n_sample_rows = 0
    for line in mwtab.splitlines():
        if line.startswith("SUBJECT_SAMPLE_FACTORS"):
            parts = line.split("\t")
            n_sample_rows += 1
            m = re.search(r"Sample source:(.*?)\s+Human S9 Fraction", parts[3])
            subj_full.setdefault(parts[1], m.group(1).strip() if m else None)
            subj_modes[parts[1]][parts[2].rsplit("_", 1)[-1]] += 1
    # base id = PM number without the -1/-2/-3 suffix used for repeated incubations of one drug
    subj: dict[str, str | None] = collections.OrderedDict()
    for sid, nm in subj_full.items():
        subj.setdefault(sid.split("-")[0], nm)
    tot_subjects_decl = re.search(r"ST:TOTAL_SUBJECTS\s+(\d+)", mwtab)
    arch = (DL / "mw_ST003991_archive_contents.html").read_text(errors="replace")
    files: dict = collections.defaultdict(lambda: collections.defaultdict(set))
    fsize: collections.Counter = collections.Counter()
    unmatched = 0
    for line in re.sub(r"<[^>]+>", "\n", arch).splitlines():
        if not re.search(r"\.(raw|mzML)\s*$", line.strip()):
            continue
        m = re.search(r"(\d+)\s+(\d+)\s+(?:[^\s]*\\)?(PM\d{7})(?:-\d+)?_(\d+hr)_(\d+)_([A-Za-z0-9]+)\.(raw|mzML)\s*$", line.strip())
        if not m:
            unmatched += 1
            continue
        usz, _, pm, t, rep, mode, ext = m.groups()
        files[pm][(ext, mode.lower())].add((t, rep))
        fsize[ext] += int(usz)
    n_files: collections.Counter = collections.Counter()
    for pm, d in files.items():
        for (ext, mode), s in d.items():
            n_files[(ext, mode)] += len(s)

    S = {
        "msg15_recorded_all": load_set("msg15_keys_all.txt"),
        "msg15_parent_all": load_set("msg15_parent_keys_all.txt"),
        "msg15_recorded_train": load_set("msg15_keys_train.txt"),
        "msg15_parent_train": load_set("msg15_parent_keys_train.txt"),
        "msg15_simchallenge_recorded_all": load_set("msg15_simchallenge_keys_all.txt"),
        "muru_registry": load_set("muru_exposure_registry_keys.txt"),
        "muru_registry_direct": load_set("muru_exposure_registry_keys_direct_reason.txt"),
        "muru_exposed_union": load_set("muru_exposed_union_keys.txt"),
        "study2_pop": load_set("msnlib_study2_population_keys.txt"),
        "comparator_pop": load_set("comparator_common_population_keys.txt"),
        "msnlib_v1_4lib": load_set("msnlib_v1_0_4lib_keys.txt"),
        "msnlib_9lib": load_set("msnlib_9lib_keys.txt"),
    }
    dev_pop = load_set("muru_exposure_registry_population_V2-DEVELOPMENT-POPULATION_keys.txt")
    exposed_pops: set[str] = set()
    for p in EXC.glob("muru_exposure_registry_population_*_keys.txt"):
        exposed_pops |= load_set(p.name)
    S["muru_exposed_populations"] = exposed_pops
    regc = pd.read_csv(W / "artifacts/wur_v2_confirmation_v2/exposure_registry/excluded_compounds.csv",
                       usecols=["key", "scaffold_group_census"])
    exposed_pop_groups = set(regc.loc[regc["key"].isin(exposed_pops), "scaffold_group_census"].dropna())
    G = {
        "muru_exposed_populations": exposed_pop_groups,
        "muru_registry": load_set("muru_exposure_registry_scaffold_groups.txt"),
        "study2_pop": load_set("msnlib_study2_population_scaffold_groups.txt"),
        "comparator_pop": load_set("comparator_common_population_scaffold_groups.txt"),
        "msg15_all": load_set("msg15_scaffold_groups_all.txt"),
    }
    rk = pd.read_parquet(EXC / "msg_row_msnlib_membership.parquet", columns=["identifier", "parent_key14", "simulation_challenge", "adduct", "instrument_type"])
    rk_cols = list(rk.columns)
    pcol = "parent_key14" if "parent_key14" in rk.columns else None
    msg_parent_sim = set(rk.loc[rk["simulation_challenge"] == True, pcol].dropna()) if (pcol and "simulation_challenge" in rk.columns) else None
    msg_orbi_mh = None
    if pcol and {"instrument_type", "adduct"} <= set(rk.columns):
        msg_orbi_mh = set(rk.loc[(rk["instrument_type"] == "Orbitrap") & (rk["adduct"] == "[M+H]+"), pcol].dropna())

    out = []
    for r in rows:
        pm = r["precursorID"]
        smi = r["SMILES"]
        k, g = SK.key_and_group(smi)
        m0 = Chem.MolFromSmiles(smi) if smi else None
        raw_key = None
        if m0 is not None:
            ik = inchi.MolToInchiKey(m0)
            raw_key = ik.split("-")[0] if ik else None
        par = SK.parent_mol(smi) if m0 is not None else None
        charge = Chem.GetFormalCharge(par) if par is not None else None
        n_frag = len(Chem.GetMolFrags(m0)) if m0 is not None else None
        mono = Descriptors.ExactMolWt(par) if par is not None else None
        mh = (mono + PROTON) if (mono is not None and charge == 0) else None
        elements = sorted({a.GetSymbol() for a in par.GetAtoms()}) if par is not None else []
        feats = {c: parse_listlit(r[c]) for c in ("adduct", "mz", "rt", "mode")}
        ok_align = all(v is not None for v in feats.values()) and len({len(v) for v in feats.values()}) == 1
        mh_modes = sorted({mo for a, mo in zip(feats["adduct"], feats["mode"]) if a == "M+H"}) if ok_align else []
        fm = files.get(pm, {})
        keys = {k, raw_key} - {None}
        rec = {
            "precursorID": pm, "name": r["name"], "drug_group": r["drug_group"], "drug_class": r["drug_class"],
            "formula_db": r["molecular_formula"], "mono_mass_db": r["monoisotopic Mass"], "parent_id": r["Parent ID"],
            "smiles_db": smi, "key": k, "raw_key14": raw_key, "scaffold_group": g, "n_fragments_raw": n_frag,
            "parent_formal_charge": charge, "parent_mono_mass": mono, "mh_mz": mh, "elements": ";".join(elements),
            "mw_subject_name": subj.get(pm), "in_mw_subjects": pm in subj,
            "hilicpos_raw_files": len(fm.get(("raw", "hilicpos"), ())),
            "hilicpos_0hr_raw_files": sum(1 for t, _ in fm.get(("raw", "hilicpos"), ()) if t == "0hr"),
            "c18pos_raw_files": len(fm.get(("raw", "c18pos"), ())),
            "feature_lists_aligned": ok_align, "db_MH_feature_modes": ";".join(mh_modes),
            "db_MH_in_hilicpos": "hilicpos" in mh_modes, "db_MH_in_any_pos": any(x.endswith("pos") for x in mh_modes),
        }
        for nm, s in S.items():
            rec[f"in_{nm}"] = bool(keys & s)
        rec["in_muru_dev_population"] = bool(keys & dev_pop)
        rec["in_msg15_parent_simchallenge"] = bool(keys & msg_parent_sim) if msg_parent_sim is not None else None
        rec["in_msg15_orbitrap_MH_parent"] = bool(keys & msg_orbi_mh) if msg_orbi_mh is not None else None
        for nm, s in G.items():
            rec[f"scaffold_in_{nm}"] = (g in s) if g else None
        out.append(rec)
    df = pd.DataFrame(out)
    # name-route identity check (PubChem name lookup) for DB-SMILES-novel precursors
    nm_path = DL / "pubchem_name_route_check.json"
    name_info = {}
    msg_any = S["msg15_recorded_all"] | S["msg15_parent_all"]
    if nm_path.exists():
        for x in json.loads(nm_path.read_text()):
            props = x.get("body", {}).get("PropertyTable", {}).get("Properties", []) if "body" in x else []
            ks = set()
            for pr in props:
                ik = pr.get("InChIKey")
                if ik:
                    ks.add(ik.split("-")[0])
                smi2 = pr.get("IsomericSMILES") or pr.get("SMILES")
                if smi2:
                    pk2, _ = SK.key_and_group(smi2)
                    if pk2:
                        ks.add(pk2)
            name_info[x["precursorID"]] = {"resolved": bool(ks), "keys": ks, "n_cids": len(props),
                                           "titles": [pr.get("Title") for pr in props][:3]}
    def nflag(pm, key, rkey):
        info = name_info.get(pm)
        if info is None:
            return pd.Series({"name_checked": False, "name_resolved": None, "name_key_matches_db": None,
                              "name_route_in_msg15": None, "name_keys": None})
        return pd.Series({"name_checked": True, "name_resolved": info["resolved"],
                          "name_key_matches_db": (bool({key, rkey} & info["keys"]) if info["resolved"] else None),
                          "name_route_in_msg15": bool(info["keys"] & msg_any),
                          "name_keys": ";".join(sorted(info["keys"]))})
    df = pd.concat([df, df.apply(lambda r: nflag(r["precursorID"], r["key"], r["raw_key14"]), axis=1)], axis=1)
    df.to_csv(OUT / "c06_compounds_screen.csv", index=False)

    def cnt(d):
        return {"rows": int(len(d)), "keys": int(d["key"].nunique()), "scaffold_groups": int(d["scaffold_group"].nunique()),
                "scaffold_groups_ring_only": int(d.loc[~d["scaffold_group"].fillna("").str.startswith("__"), "scaffold_group"].nunique()),
                "acyclic_keys": int(d.loc[d["scaffold_group"].fillna("").str.startswith("__ACYCLIC__"), "key"].nunique())}

    ok = df[df["key"].notna()]
    summ: dict = {"script": SCRIPT, "rdkit": rdBase.rdkitVersion, "generated_utc": now(), "msg_row_table": "exclusion/msg_row_msnlib_membership.parquet", "msg_row_table_columns_used": rk_cols}
    summ["db_precursor_rows"] = int(len(df))
    summ["db_precursor_ids_unique"] = int(df["precursorID"].nunique())
    summ["smiles_missing_or_unparsed"] = int(df["key"].isna().sum())
    summ["unparsed_examples"] = df.loc[df["key"].isna(), ["precursorID", "name", "smiles_db"]].head(10).to_dict("records")
    summ["parseable_with_key"] = int(len(ok))
    summ["unique_keys"] = int(ok["key"].nunique())
    summ["duplicate_key_rows"] = int(len(ok) - ok["key"].nunique())
    summ["mw_sample_factor_rows"] = n_sample_rows
    summ["mw_declared_total_subjects"] = int(tot_subjects_decl.group(1)) if tot_subjects_decl else None
    summ["mw_subject_ids_distinct"] = len(subj_full)
    summ["mw_subject_ids_with_suffix"] = sorted(k for k in subj_full if "-" in k)
    summ["mw_samples_by_mode"] = dict(sum((c for c in subj_modes.values()), collections.Counter()))
    summ["mw_subjects"] = len(subj)
    summ["mw_subjects_not_in_db_precursors"] = sorted(set(subj) - set(df["precursorID"]))
    summ["db_precursors_not_in_mw_subjects_n"] = len(set(df["precursorID"]) - set(subj))
    summ["db_precursors_not_in_mw_subjects_examples"] = sorted(set(df["precursorID"]) - set(subj))[:20]
    summ["name_mismatch_db_vs_mw_n"] = int(sum(1 for x in out if x["in_mw_subjects"] and (x["mw_subject_name"] or "").strip().lower()
                                           != x["name"].strip().lower()))
    summ["archive_file_counts"] = {f"{e}:{m}": v for (e, m), v in sorted(n_files.items())}
    summ["archive_file_lines_unmatched"] = unmatched
    summ["archive_uncompressed_bytes_by_ext"] = dict(fsize)
    summ["archive_pm_ids"] = len(files)
    summ["drugs_with_any_hilicpos_raw"] = int((df["hilicpos_raw_files"] > 0).sum())
    summ["drugs_with_hilicpos_0hr_raw"] = int((df["hilicpos_0hr_raw_files"] > 0).sum())
    summ["drugs_with_c18pos_raw"] = int((df["c18pos_raw_files"] > 0).sum())
    summ["feature_lists_unaligned"] = int((~df["feature_lists_aligned"]).sum())
    summ["db_MH_in_hilicpos_all"] = int(df["db_MH_in_hilicpos"].sum())
    summ["multi_fragment_smiles"] = int((df["n_fragments_raw"].fillna(1) > 1).sum())
    summ["parent_permanent_charge_nonzero"] = int((df["parent_formal_charge"].fillna(0) != 0).sum())
    summ["overlap_keys"] = {nm: int(ok.groupby("key")[f"in_{nm}"].any().sum()) for nm in S}
    summ["overlap_keys"]["muru_dev_population"] = int(ok.groupby("key")["in_muru_dev_population"].any().sum())
    if msg_parent_sim is not None:
        summ["overlap_keys"]["msg15_parent_simchallenge"] = int(ok.groupby("key")["in_msg15_parent_simchallenge"].any().sum())
    if msg_orbi_mh is not None:
        summ["overlap_keys"]["msg15_orbitrap_MH_parent"] = int(ok.groupby("key")["in_msg15_orbitrap_MH_parent"].any().sum())
    summ["overlap_scaffold_groups"] = {nm: int(ok.loc[ok[f"scaffold_in_{nm}"] == True, "scaffold_group"].nunique()) for nm in G}

    msg = ok["in_msg15_recorded_all"] | ok["in_msg15_parent_all"]
    muru = ok["in_muru_registry"]
    pr7 = ok["in_study2_pop"]
    comp = ok["in_comparator_pop"]
    summ["overlap_keys"]["msg15_any_route"] = int(ok[msg]["key"].nunique())

    def inrange(d):
        return d[(d["parent_formal_charge"] == 0) & d["mh_mz"].between(100.0, 1000.0) & d["mh_mz"].between(70.0, 1042.6)]

    tiers: dict = collections.OrderedDict()
    tiers["T0_all_keyed"] = ok
    tiers["T1_minus_MSG15_all_folds_keys"] = ok[~msg]
    t2 = ok[~msg & ~muru & ~pr7 & ~comp]
    tiers["T2_minus_MSG15_MURUregistry_PR7_comparator_keys"] = t2
    t3 = t2[~(t2["scaffold_in_muru_registry"] == True) & ~(t2["scaffold_in_study2_pop"] == True)
            & ~(t2["scaffold_in_comparator_pop"] == True)]
    tiers["T3_also_MURU_PR7_comparator_scaffold_groups"] = t3
    t4 = inrange(t3)
    tiers["T4_neutral_parent_MH_in_scan_100_1000"] = t4
    t5 = t4[t4["hilicpos_0hr_raw_files"] > 0]
    tiers["T5_has_hilicpos_0hr_raw_file"] = t5
    t6 = t5[t5["db_MH_in_hilicpos"]]
    tiers["T6_PharmMet_MS1_MH_feature_in_hilicpos_proxy"] = t6
    tiers["T7_T6_minus_MSnLib_9lib_keys"] = t6[~t6["in_msnlib_9lib"]]
    tiers["T8_T6_scaffold_group_absent_from_MSG15"] = t6[~(t6["scaffold_in_msg15_all"] == True)]
    # moderate MURU exclusion (P5 section 2.1 scope caution): exposed-population keys and their scaffold groups instead of
    # the full MSnLib-centred registry
    expo = ok["in_muru_exposed_populations"]
    m2 = ok[~msg & ~expo & ~pr7 & ~comp]
    tiers["M2_minus_MSG15_MURUexposedpops_PR7_comparator_keys"] = m2
    m3 = m2[~(m2["scaffold_in_muru_exposed_populations"] == True) & ~(m2["scaffold_in_study2_pop"] == True)
            & ~(m2["scaffold_in_comparator_pop"] == True)]
    tiers["M3_also_exposedpops_PR7_comparator_scaffold_groups"] = m3
    m4 = inrange(m3)
    tiers["M4_neutral_parent_MH_in_scan_100_1000"] = m4
    m5 = m4[m4["hilicpos_0hr_raw_files"] > 0]
    tiers["M5_has_hilicpos_0hr_raw_file"] = m5
    m6 = m5[m5["db_MH_in_hilicpos"]]
    tiers["M6_PharmMet_MS1_MH_feature_in_hilicpos_proxy"] = m6
    tiers["M7_M6_scaffold_group_absent_from_MSG15"] = m6[~(m6["scaffold_in_msg15_all"] == True)]
    # identity-robust variant: also drop rows whose drug NAME resolves (PubChem) to a key in MassSpecGym 1.5, and rows whose
    # name resolves but to no key equal to the DB SMILES key (identity defect; true compound uncertain)
    def idrobust(d):
        bad = ((d["name_route_in_msg15"] == True) | (d["name_key_matches_db"] == False)
               | d["precursorID"].isin(list(MANUAL_IDENTITY_DEFECTS))
               | (d["in_mw_subjects"] & (d["mw_subject_name"].fillna("").str.lower() != d["name"].str.lower())))
        return d[~bad]
    summ["manual_identity_defects"] = MANUAL_IDENTITY_DEFECTS
    summ["db_vs_mw_name_mismatches"] = df.loc[df["in_mw_subjects"] & (df["mw_subject_name"].fillna("").str.lower()
                                              != df["name"].str.lower()), ["precursorID", "name", "mw_subject_name"]].to_dict("records")
    pos_all = inrange(ok)
    pos_all = pos_all[pos_all["hilicpos_0hr_raw_files"] > 0]
    summ["positive_mode_deposited_no_exclusions"] = {**cnt(pos_all), "db_MH_in_hilicpos": int(pos_all["db_MH_in_hilicpos"].sum()),
        "mh_mz_quantiles_0_10_50_90_100": [round(float(v), 2) for v in pos_all["mh_mz"].quantile([0, .1, .5, .9, 1])],
        "eV_35mz500_quantiles_0_10_50_90_100": [round(float(v), 2) for v in (35 * pos_all["mh_mz"] / 500).quantile([0, .1, .5, .9, 1])]}
    tiers["M6R_M6_identity_robust_name_route"] = idrobust(m6)
    tiers["T6R_T6_identity_robust_name_route"] = idrobust(t6)
    tiers["T1R_T1_identity_robust_name_route"] = idrobust(tiers["T1_minus_MSG15_all_folds_keys"])
    chk = df[df["name_checked"] == True]
    summ["name_route_check"] = {"checked": int(len(chk)), "resolved": int((chk["name_resolved"] == True).sum()),
                                "unresolved": int((chk["name_resolved"] == False).sum()),
                                "db_key_matches_name": int((chk["name_key_matches_db"] == True).sum()),
                                "db_key_differs_from_name": int((chk["name_key_matches_db"] == False).sum()),
                                "name_route_in_msg15": int((chk["name_route_in_msg15"] == True).sum()),
                                "differs_examples": chk.loc[chk["name_key_matches_db"] == False, ["precursorID", "name", "key", "name_keys", "name_route_in_msg15"]].head(40).to_dict("records")}
    summ["M6R_names"] = sorted(tiers["M6R_M6_identity_robust_name_route"]["name"].tolist())
    summ["T6R_names"] = sorted(tiers["T6R_T6_identity_robust_name_route"]["name"].tolist())
    summ["tiers"] = {nm: cnt(d) for nm, d in tiers.items()}
    summ["M6_names"] = sorted(m6["name"].tolist())
    summ["M6_scaffold_group_size_hist"] = {int(a): int(b) for a, b in m6.groupby("scaffold_group").size().value_counts().sort_index().items()} if len(m6) else {}
    summ["M6_drug_group_counts"] = m6["drug_group"].value_counts().to_dict() if len(m6) else {}
    summ["T5_names"] = sorted(t5["name"].tolist())
    summ["tiers_alt"] = {
        "A1_no_MSG_exclusion_minus_MURU_PR7_comparator_keys_neutral_MH_range_hilicpos0hr": cnt(
            (lambda d: d[d["hilicpos_0hr_raw_files"] > 0])(inrange(ok[~muru & ~pr7 & ~comp]))),
        "A2_T1_neutral_MH_range_hilicpos0hr_MHfeature": cnt(
            (lambda d: d[(d["hilicpos_0hr_raw_files"] > 0) & d["db_MH_in_hilicpos"]])(inrange(ok[~msg]))),
    }
    ms = ok["mh_mz"].dropna()
    summ["mh_mz_all_keyed"] = {"n": int(len(ms)), "min": float(ms.min()), "p10": float(ms.quantile(.1)),
                               "median": float(ms.median()), "p90": float(ms.quantile(.9)), "max": float(ms.max()),
                               "below_100": int((ms < 100).sum()), "above_1000": int((ms > 1000).sum())}
    for nm, d in (("T1", tiers["T1_minus_MSG15_all_folds_keys"]), ("T6", t6)):
        if len(d.dropna(subset=["mh_mz"])):
            m6 = d["mh_mz"].dropna()
            summ[f"mh_mz_{nm}"] = {"n": int(len(m6)), "min": float(m6.min()), "median": float(m6.median()), "max": float(m6.max()),
                                   "eV_if_35_times_mz_over_500": {"min": 35 * float(m6.min()) / 500,
                                                                  "median": 35 * float(m6.median()) / 500,
                                                                  "max": 35 * float(m6.max()) / 500}}
    summ["T6_scaffold_group_size_hist"] = {int(a): int(b) for a, b in t6.groupby("scaffold_group").size().value_counts().sort_index().items()} if len(t6) else {}
    summ["T6_top_scaffold_groups"] = t6["scaffold_group"].value_counts().head(10).to_dict() if len(t6) else {}
    summ["T6_drug_group_counts"] = t6["drug_group"].value_counts().to_dict() if len(t6) else {}
    summ["T1_names"] = sorted(tiers["T1_minus_MSG15_all_folds_keys"]["name"].tolist())
    summ["T6_names"] = sorted(t6["name"].tolist())
    pc = json.loads((DL / "pubchem_cid_sample_check.json").read_text())
    agree, tot, bad = 0, 0, []
    for x in pc:
        props = x.get("body", {}).get("PropertyTable", {}).get("Properties", [])
        if not props:
            continue
        tot += 1
        row = df[df["precursorID"] == x["precursorID"]].iloc[0]
        pk = props[0].get("InChIKey", "").split("-")[0]
        if pk in {row["key"], row["raw_key14"]}:
            agree += 1
        else:
            bad.append((x["precursorID"], row["name"], props[0].get("Title")))
    summ["pubchem_cid_sample"] = {"n_with_props": tot, "inchikey14_agree_with_db_smiles": agree, "disagreements": bad}
    (OUT / "c06_screen_summary.json").write_text(json.dumps(summ, indent=1, default=str))
    print(json.dumps({k: v for k, v in summ.items() if k not in ("T1_names",)}, indent=1, default=str))
    print("T1 names:", summ["T1_names"])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "screen"
    {"fetch": fetch, "screen": screen, "fetch_csv": fetch_csv, "fetch_names": fetch_names}[cmd]()
