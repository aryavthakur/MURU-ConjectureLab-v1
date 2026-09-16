"""S3-C03 independent verification pass (metadata only, no model run, no spectra download).

Re-checks the C03 screen (artifacts/ce_interface_adjudication/screen/c03_massbank_hcd) without reusing its summary:

 1. recomputes the design-row / compound / exclusion headline counts straight from records.parquet and the P5 key lists;
 2. re-derives the MassSpecGym 1.5 CE arm for five named accessions by hand (raw NCE vs NCE*precursor_mz/500);
 3. verifies the MassBank-data tag 2023.11 -> commit object;
 4. re-fetches three MassBank export-service JSON-LD responses live and compares sha256 with the cached aggregate;
 5. audits every post-2023.11 commit that touches the six contributor directories: additions/deletions stats, and for
    the ChemOnt/CHEBI commits a per-changed-line MassBank field-tag histogram (line CONTENT is never printed or stored,
    only the tag name at the start of each changed line), to bound whether AC$MASS_SPECTROMETRY: COLLISION_ENERGY or
    RECORD_TITLE lines could have changed between the tag and the strings observable today;
 6. samples record files per directory and lists which post-tag commits touched them.

Writes artifacts/ce_interface_adjudication/screen/c03_massbank_hcd/s3_verification_record.json and appends one line per
network fetch to artifacts/ce_interface_adjudication/downloads_register.jsonl.

Deliberately NOT fetched: any MassBank record .txt blob, any release asset (MSP/JSON/SQL), /records/{accession}, and the
file patches of the release-merge commits (those add whole new record files, so their patches carry peak lines).
"""
from __future__ import annotations

import collections
import gzip
import hashlib
import json
import re
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
ADJ = ROOT / "artifacts/ce_interface_adjudication"
OUT = ADJ / "screen/c03_massbank_hcd"
EXC = ADJ / "exclusion"
REGISTER = ADJ / "downloads_register.jsonl"
SCRIPT = "scripts/ce_interface_adjudication/screen_c03_massbank_hcd_verify.py"
TASK = "S3-C03-verify"
PROTON = 1.007276466812
TAG_COMMIT = "9dc52cb29b7ade23e81befc3ce9eb001477ce393"
DIRS = ["AAFC", "Eawag", "Eawag_Additional_Specs", "HBM4EU", "NaToxAq", "UFZ"]
# post-2023.11 commits touching the six directories (from the screen's commit lists)
METADATA_COMMITS = ["2909674", "f224a5c", "74f840a", "dbc9063"]  # ChemOnt / CHEBI: safe to read patches
OTHER_COMMITS = ["fd8fb15", "2d07d24", "c421681", "06338d1", "d257cab", "6275b60", "500fd21", "12b1ea6",
                 "4398ef3", "90fdf6f", "6be0d51", "58f4e12", "3f57a1f", "563cce0"]  # stats only, patches not read


def now():
    return datetime.now(timezone.utc).isoformat()


def register(name, url, data: bytes, kind, extra=None):
    rec = {"fetched_utc": now(), "task": TASK, "name": name, "kind": kind, "source_url": url,
           "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
           "stored_as": None, "script": SCRIPT}
    if extra:
        rec.update(extra)
    with open(REGISTER, "a") as fh:
        fh.write(json.dumps(rec) + "\n")


def gh(path: str) -> bytes:
    r = subprocess.run(["gh", "api", path], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"gh api {path}: {r.stderr.decode()[:200]}")
    register(f"gh api {path}", "https://api.github.com/" + path, r.stdout, "GitHub API metadata response")
    return r.stdout


def keys(name: str) -> set[str]:
    return {l.strip() for l in (EXC / name).read_text().splitlines() if l.strip()}


def main():
    res: dict = {"written_utc": now(), "task": TASK, "verifies": "screen/c03_massbank_hcd"}

    # ---- 1. headline recomputation ----
    rec = pd.read_parquet(OUT / "records.parquet")
    d = rec[rec["design_row"]]
    cd = d.groupby("compound_id").agg(rk=("recorded_key14", "first"), pk=("parent_key", "first"),
                                      sg=("scaffold_group", "first"))
    msg = keys("msg15_keys_all.txt") | keys("msg15_parent_keys_all.txt")
    sim = keys("msg15_simchallenge_keys_all.txt")
    reg = keys("muru_exposure_registry_keys.txt")
    dev = keys("muru_exposure_registry_population_V2-DEVELOPMENT-POPULATION_keys.txt")
    pr7 = keys("msnlib_study2_population_keys.txt")
    cmp_ = keys("comparator_common_population_keys.txt")

    def hit(s):
        return int(((cd.rk.isin(s)) | (cd.pk.isin(s))).sum())

    allx = msg | reg | pr7 | cmp_
    rem = cd[~((cd.rk.isin(allx)) | (cd.pk.isin(allx)))]
    sg_ex = (keys("msg15_scaffold_groups_all.txt") | keys("muru_exposure_registry_scaffold_groups.txt")
             | keys("msnlib_study2_population_scaffold_groups.txt")
             | keys("comparator_common_population_scaffold_groups.txt"))
    rem2 = rem[~rem.sg.isin(sg_ex)]
    nce = d.groupby("compound_id")["nce_first_number"].nunique()
    mh = d.groupby("compound_id")["mz_MH_theoretical"].first()
    res["recomputed"] = {
        "records_2023_11": int(len(rec)), "records_per_dir": rec.groupby("dir").size().to_dict(),
        "records_positive": int(rec.is_positive.sum()), "records_positive_MH": int((rec.is_positive & rec.is_MH).sum()),
        "records_esi_orbitrap": int(rec.is_esi_orbitrap.sum()),
        "design_rows": int(len(d)), "design_rows_per_dir": d.groupby("dir").size().to_dict(),
        "design_compounds": int(len(cd)),
        "design_compounds_in_msg15_any_fold": hit(msg), "design_compounds_in_msg15_simchallenge": hit(sim),
        "design_compounds_in_muru_registry": hit(reg), "design_compounds_in_muru_v2_development": hit(dev),
        "design_compounds_in_pr7": hit(pr7), "design_compounds_in_comparator": hit(cmp_),
        "design_compounds_after_key_exclusions": int(len(rem)), "scaffold_groups_after_key_exclusions": int(rem.sg.nunique()),
        "design_compounds_after_key_and_scaffold_exclusions": int(len(rem2)),
        "scaffold_groups_after_key_and_scaffold_exclusions": int(rem2.sg.nunique()),
        "distinct_nce_per_design_compound": {"median": float(nce.median()), "q25": float(nce.quantile(.25)),
                                             "q75": float(nce.quantile(.75)), "n_ge_4": int((nce >= 4).sum())},
        "design_MH_mz_range": [float(mh.min()), float(mh.max())],
    }
    res["recomputed_matches_summary_json"] = {}
    s = json.loads((OUT / "summary.json").read_text())
    allrow = next(x for x in s["per_dir"] if x["dir"] == "ALL")
    for a, b in (("records_2023_11", allrow["records_2023_11"]), ("design_rows", allrow["records_design_rows"]),
                 ("design_compounds", allrow["compounds_design"]),
                 ("design_compounds_after_key_exclusions", allrow["design_compounds_after_key_exclusion"]),
                 ("scaffold_groups_after_key_exclusions", allrow["design_scaffold_groups_after_key_exclusion"])):
        res["recomputed_matches_summary_json"][a] = (res["recomputed"][a] == b)

    # ---- 2. hand-checked CE arm for named accessions ----
    m15 = pd.read_parquet(ADJ / "massspecgym15_identity_metadata_joined.parquet",
                          columns=["identifier", "inchikey", "adduct", "instrument_type", "collision_energy",
                                   "precursor_mz", "fold", "simulation_challenge"])
    spot = []
    for acc in ["MSBNK-AAFC-AC000001", "MSBNK-NaToxAq-NA000438", "MSBNK-Eawag-EQ330851", "MSBNK-Eawag-EA034202",
                "MSBNK-HBM4EU-HB003696"]:
        r = rec[rec.accession == acc].iloc[0]
        mz = r.mono_mass + PROTON
        g = m15[(m15.inchikey == r.recorded_key14) & (m15.instrument_type == "Orbitrap")
                & m15.collision_energy.notna() & (m15.precursor_mz - mz).abs().le(0.02)]
        conv = g[(g.collision_energy - r.nce_first_number * g.precursor_mz / 500.0).abs() <= 1e-6]
        raw = g[(g.collision_energy - r.nce_first_number).abs() <= 1e-9]
        spot.append({"accession": acc, "title": r.title, "record_ce_number": float(r.nce_first_number),
                     "msg_rows_same_key_and_precursor": int(len(g)), "n_converted_match": int(len(conv)),
                     "n_raw_match": int(len(raw)),
                     "example_converted_ce": float(conv.collision_energy.iloc[0]) if len(conv) else None,
                     "example_raw_ce": float(raw.collision_energy.iloc[0]) if len(raw) else None})
    res["ce_arm_spot_checks"] = spot

    # ---- 3. tag -> commit ----
    ref = json.loads(gh("repos/MassBank/MassBank-data/git/ref/tags/2023.11"))
    tag = json.loads(gh(f"repos/MassBank/MassBank-data/git/tags/{ref['object']['sha']}"))
    res["tag_2023_11"] = {"tag_object": ref["object"]["sha"], "commit": tag["object"]["sha"],
                          "tagger_date": tag["tagger"]["date"], "matches_screen_commit": tag["object"]["sha"] == TAG_COMMIT}

    # ---- 4. live JSON-LD vs cache ----
    cache = {}
    want = {"MSBNK-AAFC-AC000001", "MSBNK-NaToxAq-NA000438", "MSBNK-UFZ-UF402004"}
    with gzip.open(OUT / "downloads/massbank_export_jsonld/export_metadata_jsonld.jsonl.gz", "rt") as fh:
        for line in fh:
            r = json.loads(line)
            if r["accession"] in want:
                cache[r["accession"]] = r
    live = []
    for acc, c in cache.items():
        url = f"https://massbank.eu/MassBank-export/metadata/{acc}"
        req = urllib.request.Request(url, headers={"Accept": "application/ld+json",
                                                   "User-Agent": "metadata-screen/1.0 (no spectra requested)"})
        b = urllib.request.urlopen(req, timeout=60).read()
        register(f"MassBank export JSON-LD {acc} (live re-check, compared then discarded)", url, b,
                 "MassBank export-service JSON-LD structured metadata (no peaks)")
        ds = next(x for x in json.loads(b) if x.get("@type") == "Dataset")
        live.append({"accession": acc, "identical_to_cache": hashlib.sha256(b).hexdigest() == c["sha256"],
                     "live_title": ds.get("name")})
    res["jsonld_live_recheck"] = live
    api = json.loads((OUT / "downloads/massbank_api/metadata.json").read_text())
    res["massbank_server_release_served"] = {"version": api.get("version"), "timestamp": api.get("timestamp"),
                                             "note": "JSON-LD titles reflect this release, NOT 2023.11"}

    # ---- 5. post-tag commit audit ----
    stats = {}
    for sha in METADATA_COMMITS + OTHER_COMMITS:
        c = json.loads(gh(f"repos/MassBank/MassBank-data/commits/{sha}"))
        stats[c["sha"][:7]] = {"date": c["commit"]["committer"]["date"][:10],
                               "message": c["commit"]["message"].splitlines()[0][:80],
                               "additions": c["stats"]["additions"], "deletions": c["stats"]["deletions"],
                               "patches_read": sha in METADATA_COMMITS}
        if sha in METADATA_COMMITS:
            tags = collections.Counter()
            numeric = 0
            for f in c.get("files", []):
                for ln in (f.get("patch") or "").splitlines():
                    if ln[:1] in "+-" and ln[1:2] not in ("+", "-"):
                        body = ln[1:]
                        m = re.match(r"^([A-Z]+\$?[A-Z_]*)", body)
                        t = m.group(1) if m else ("<numeric>" if re.match(r"^\s*\d", body) else "<other>")
                        tags[t] += 1
                        numeric += t == "<numeric>"
            stats[c["sha"][:7]]["changed_line_tags_page1"] = dict(tags.most_common(10))
            stats[c["sha"][:7]]["numeric_changed_lines_page1"] = numeric
            stats[c["sha"][:7]]["dirs_page1"] = dict(collections.Counter(f["filename"].split("/")[0]
                                                                        for f in c.get("files", [])).most_common(6))
    res["post_tag_commit_audit"] = stats

    # ---- 6. which post-tag commits touch sampled record files ----
    import random
    random.seed(11)
    touch = {}
    for dd in DIRS:
        accs = rec[rec.dir == dd].accession.tolist()
        cnt = collections.Counter()
        for a in random.sample(accs, 8):
            cs = json.loads(gh(f"repos/MassBank/MassBank-data/commits?path={dd}/{a}.txt&sha=dev"
                               f"&since=2023-11-28T13:26:24Z&per_page=100"))
            for c in cs:
                cnt[c["commit"]["message"].splitlines()[0][:60]] += 1
        touch[dd] = {"files_sampled": 8, "commit_messages": dict(cnt)}
    res["sampled_record_file_commits_since_tag"] = touch

    (OUT / "s3_verification_record.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: res[k] for k in ("recomputed_matches_summary_json", "tag_2023_11", "jsonld_live_recheck",
                                          "massbank_server_release_served")}, indent=1))


if __name__ == "__main__":
    main()
