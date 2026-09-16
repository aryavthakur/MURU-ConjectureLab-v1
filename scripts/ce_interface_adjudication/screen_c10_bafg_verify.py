"""S10-C10 independent verification pass for the MassBank BAFG SCIEX TripleTOF CE ladders.

Metadata only. No model run, no spectra download, no peak row is fetched, printed or stored.

This does NOT reuse c10_screen_summary.json for any number it reports. It re-derives everything from
  - c10_records_identity.csv  (the per-record identity table of the first C10 pass: accession, title, ion mode,
    SMILES/InChI, tree membership) - but the compound key and scaffold group are RECOMPUTED here from the SMILES with
    scaffold_key.py rather than read from that file's key/scaffold_group columns;
  - the P5 exclusion key and scaffold-group lists in artifacts/ce_interface_adjudication/exclusion/;
  - the MassSpecGym 1.5 identity parquet (all folds).

Network work (all registered in downloads_register.jsonl):
  A. GitHub code search with text matches for the MassBank AC$ header fields, separately for the pre-2023.11
     accession block (CSL231*) and the post-2023.11 increment (CSL250*), so the CE semantics claim is checked on
     BOTH blocks. Any line that looks like a peak row (number whitespace number) is dropped before storage.
  B. A live re-fetch of three MassBank export-service JSON-LD metadata objects, compared byte-for-byte (sha256)
     against the cached aggregate, so the cached titles used for the CE unit claim are shown to be genuine.
  C. git tag 2023.11 -> commit -> BAFG tree sha, to confirm which tree the "in MassBank 2023.11" flag was computed on.

Writes artifacts/ce_interface_adjudication/screen/c10_bafg/s10_verification_record.json.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
ADJ = ROOT / "artifacts/ce_interface_adjudication"
OUT = ADJ / "screen/c10_bafg"
EXC = ADJ / "exclusion"
REGISTER = ADJ / "downloads_register.jsonl"
SCRIPT = "scripts/ce_interface_adjudication/screen_c10_bafg_verify.py"
TASK = "S10-C10-verify"

sys.path.insert(0, str(ROOT / "scripts/ce_interface_adjudication"))
import scaffold_key as SK  # noqa: E402

PEAK_LINE = re.compile(r"^\s*\d+(\.\d+)?\s+\d")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def register(name: str, kind: str, url: str, payload: bytes, stored_as: str | None) -> dict:
    rec = {
        "fetched_utc": now(),
        "task": TASK,
        "name": name,
        "kind": kind,
        "source_url": url,
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "stored_as": stored_as,
        "script": SCRIPT,
    }
    with REGISTER.open("a") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def gh(path: str, accept: str | None = None) -> bytes:
    cmd = ["gh", "api"]
    if accept:
        cmd += ["-H", f"Accept: {accept}"]
    cmd.append(path)
    return subprocess.run(cmd, capture_output=True, check=True).stdout


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "muru-ce-interface-adjudication/S10-verify"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def read_keys(fname: str) -> set[str]:
    return {ln.strip() for ln in (EXC / fname).read_text().splitlines() if ln.strip()}


def main() -> None:
    rec: dict = {"task": TASK, "written_utc": now(), "rdkit": SK.rdBase.rdkitVersion, "checks": {}}

    # ---------------------------------------------------------------- A. records table, keys recomputed from SMILES
    df = pd.read_csv(OUT / "c10_records_identity.csv", low_memory=False)
    rec["checks"]["records_table"] = {
        "file": "c10_records_identity.csv",
        "sha256": hashlib.sha256((OUT / "c10_records_identity.csv").read_bytes()).hexdigest(),
        "rows": int(len(df)),
        "distinct_accessions": int(df["accession"].nunique()),
        "ion_mode": {k: int(v) for k, v in df["ion_mode"].value_counts().items()},
        "title_instrument_type": {k: int(v) for k, v in df["title_instrument_type"].value_counts(dropna=False).items()},
        "ce_unit": {str(k): int(v) for k, v in df["ce_unit"].value_counts(dropna=False).items()},
        "in_tree_2023_11": int(df["in_tree_2023_11"].sum()),
        "post_2023_11": int((~df["in_tree_2023_11"].astype(bool)).sum()),
        "license": {str(k): int(v) for k, v in df["license"].value_counts(dropna=False).items()},
    }

    # title CE unit: parse the record title tail independently of the first pass
    tail = df["title"].astype(str).str.rsplit(";", n=1).str[-1].str.strip()
    rec["checks"]["title_ce_tail"] = {
        "pattern_number_space_V": int(tail.str.fullmatch(r"\d+(\.\d+)? V").sum()),
        "examples": tail.head(5).tolist(),
        "distinct_units_in_tail": sorted({t.split(" ")[-1] for t in tail.head(20000)})[:10],
    }

    # recompute key + scaffold group from SMILES with the MURU definition (independent of the stored columns)
    smis = df["smiles"].astype(str)
    uniq = sorted(set(smis))
    kg = {s: SK.key_and_group(s) for s in uniq}
    df["key_recomputed"] = [kg[s][0] for s in smis]
    df["sg_recomputed"] = [kg[s][1] for s in smis]
    agree_key = int((df["key_recomputed"] == df["key"]).sum())
    agree_sg = int((df["sg_recomputed"] == df["scaffold_group"]).sum())
    rec["checks"]["key_recomputation"] = {
        "distinct_smiles": len(uniq),
        "rows_key_agree_with_first_pass": agree_key,
        "rows_scaffold_agree_with_first_pass": agree_sg,
        "rows": int(len(df)),
        "keys_recomputed_distinct": int(df["key_recomputed"].nunique()),
        "null_keys": int(df["key_recomputed"].isna().sum()),
    }

    pos = df[df["ion_mode"] == "POSITIVE"].copy()
    neg = df[df["ion_mode"] == "NEGATIVE"].copy()

    # per-compound CE ladder, positive mode
    g = pos.groupby("key_recomputed")
    comp = pd.DataFrame({
        "records": g.size(),
        "n_distinct_ce": g["ce_value"].nunique(),
        "ce_min": g["ce_value"].min(),
        "ce_max": g["ce_value"].max(),
        "any_in_2023_11": g["in_tree_2023_11"].any(),
        "all_in_2023_11": g["in_tree_2023_11"].all(),
        "mh_mz": g["mh_mz_from_parent"].first(),
        "parent_charge": g["parent_charge"].first(),
        "sg": g["sg_recomputed"].first(),
    })
    rec["checks"]["positive_compounds"] = {
        "keys": int(len(comp)),
        "records": int(len(pos)),
        "scaffold_groups": int(comp["sg"].nunique()),
        "keys_ge_2_ce": int((comp["n_distinct_ce"] >= 2).sum()),
        "keys_ge_10_ce": int((comp["n_distinct_ce"] >= 10).sum()),
        "keys_full_15_point_ladder": int((comp["n_distinct_ce"] >= 15).sum()),
        "median_n_distinct_ce": float(comp["n_distinct_ce"].median()),
        "keys_parent_charge_nonzero": int((comp["parent_charge"] != 0).sum()),
    }
    rec["checks"]["negative_mode"] = {
        "records": int(len(neg)),
        "keys": int(neg["key_recomputed"].nunique()),
        "keys_also_positive": int(len(set(neg["key_recomputed"]) & set(pos["key_recomputed"]))),
    }

    # ---------------------------------------------------------------- B. exclusion overlap, recomputed
    sets = {
        "msg15_all": read_keys("msg15_keys_all.txt"),
        "msg15_parent_all": read_keys("msg15_parent_keys_all.txt"),
        "msg15_train": read_keys("msg15_keys_train.txt"),
        "msg15_simchallenge_all": read_keys("msg15_simchallenge_keys_all.txt"),
        "muru_registry": read_keys("muru_exposure_registry_keys.txt"),
        "muru_exposed_union": read_keys("muru_exposed_union_keys.txt"),
        "pr7": read_keys("msnlib_study2_population_keys.txt"),
        "comparator": read_keys("comparator_common_population_keys.txt"),
        "msnlib_9lib": read_keys("msnlib_9lib_keys.txt"),
    }
    pop_files = sorted(EXC.glob("muru_exposure_registry_population_*_keys.txt"))
    exposed_pop = set()
    for f in pop_files:
        exposed_pop |= {ln.strip() for ln in f.read_text().splitlines() if ln.strip()}
    sets["muru_exposed_populations"] = exposed_pop
    sg_sets = {
        "msg15": read_keys("msg15_scaffold_groups_all.txt"),
        "muru_registry": read_keys("muru_exposure_registry_scaffold_groups.txt"),
        "pr7": read_keys("msnlib_study2_population_scaffold_groups.txt"),
        "comparator": read_keys("comparator_common_population_scaffold_groups.txt"),
    }
    rec["checks"]["exclusion_set_sizes"] = {k: len(v) for k, v in sets.items()}
    rec["checks"]["exclusion_sg_set_sizes"] = {k: len(v) for k, v in sg_sets.items()}

    pk = set(comp.index)
    msg_any = sets["msg15_all"] | sets["msg15_parent_all"]
    ov = {
        "positive_keys": len(pk),
        "in_msg15_any_route": len(pk & msg_any),
        "in_msg15_recorded_all": len(pk & sets["msg15_all"]),
        "in_msg15_train": len(pk & sets["msg15_train"]),
        "in_msg15_simulation_challenge": len(pk & sets["msg15_simchallenge_all"]),
        "in_muru_registry": len(pk & sets["muru_registry"]),
        "in_muru_exposed_populations": len(pk & exposed_pop),
        "in_muru_exposed_union": len(pk & sets["muru_exposed_union"]),
        "in_pr7": len(pk & sets["pr7"]),
        "in_comparator": len(pk & sets["comparator"]),
        "in_msnlib_9lib": len(pk & sets["msnlib_9lib"]),
    }
    sgs = set(comp["sg"].dropna())
    ov_sg = {
        "positive_scaffold_groups": len(sgs),
        "sg_in_msg15": len(sgs & sg_sets["msg15"]),
        "sg_in_muru_registry": len(sgs & sg_sets["muru_registry"]),
        "sg_in_pr7": len(sgs & sg_sets["pr7"]),
        "sg_in_comparator": len(sgs & sg_sets["comparator"]),
    }
    rec["checks"]["overlap_positive"] = ov
    rec["checks"]["overlap_positive_scaffold"] = ov_sg

    # ---------------------------------------------------------------- C. exclusion cascade, recomputed
    step = comp.copy()
    cascade = []

    def snap(label: str, d: pd.DataFrame) -> None:
        cascade.append({
            "label": label,
            "keys": int(len(d)),
            "scaffold_groups": int(d["sg"].nunique()),
            "records": int(d["records"].sum()),
            "keys_ge_2_ce": int((d["n_distinct_ce"] >= 2).sum()),
            "keys_ge_10_ce": int((d["n_distinct_ce"] >= 10).sum()),
            "singleton_scaffold_groups": int((d["sg"].value_counts() == 1).sum()),
        })

    snap("V0 all positive-mode BAFG compounds", step)
    step = step[step["parent_charge"] == 0]
    snap("V1 charge-neutral parent", step)
    step = step[~step.index.isin(msg_any)]
    snap("V2 = V1 minus MassSpecGym 1.5 (all folds, either key route)", step)
    step = step[~step.index.isin(sets["muru_exposed_union"] | sets["muru_registry"])]
    snap("V3 = V2 minus MURU exposure registry / exposed union (criteria 1-3 by key)", step)
    step = step[~step["sg"].isin(sg_sets["muru_registry"] | sg_sets["pr7"] | sg_sets["comparator"])]
    snap("V4 = V3 minus MURU/PR7/comparator scaffold groups", step)
    v4 = step.copy()
    step = step[~step["sg"].isin(sg_sets["msg15"])]
    snap("V5 = V4 minus every MassSpecGym 1.5 scaffold group (strict)", step)
    v5 = step.copy()
    v6 = v4[(v4["n_distinct_ce"] >= 2) & (v4["mh_mz"] >= 70) & (v4["mh_mz"] <= 1042.6)]
    snap("V6 = V4 with >=2 CE and [M+H]+ in 70-1042.6", v6)
    v7 = v5[(v5["n_distinct_ce"] >= 2) & (v5["mh_mz"] >= 70) & (v5["mh_mz"] <= 1042.6)]
    snap("V7 = V5 with >=2 CE and [M+H]+ in 70-1042.6", v7)
    rec["checks"]["exclusion_cascade"] = cascade
    rec["checks"]["v6_keys"] = sorted(v6.index.tolist())
    rec["checks"]["v6_scaffold_groups"] = sorted(set(v6["sg"]))

    # ---------------------------------------------------------------- D. header-field verification via code search
    def code_search(name: str, q: str, per_page: int = 5) -> dict:
        url = f"search/code?q={urllib.parse.quote(q)}&per_page={per_page}"
        raw = gh(url, accept="application/vnd.github.text-match+json")
        d = json.loads(raw)
        hits, dropped = [], 0
        for it in d.get("items", []):
            frs = []
            for tm in it.get("text_matches", []):
                lines = tm.get("fragment", "").split("\n")
                keep = []
                for ln in lines:
                    if PEAK_LINE.match(ln):
                        dropped += 1
                        continue
                    keep.append(ln.strip())
                frs.append([l for l in keep if l])
            hits.append({"path": it["path"], "fragments": frs})
        out = {
            "query": q,
            "url": "https://api.github.com/" + url,
            "total_count": d.get("total_count"),
            "incomplete_results": d.get("incomplete_results"),
            "hits": hits,
            "dropped_peak_lines": dropped,
        }
        register(
            f"code search (text-match) {name}",
            "GitHub code search response with text-match fragments; any peak-looking line dropped before storage",
            out["url"],
            raw,
            f"artifacts/ce_interface_adjudication/screen/c10_bafg/s10_verification_record.json :: checks.header_fields.{name}",
        )
        return out

    queries = {
        "ce_pre2023_CSL231": 'COLLISION_ENERGY repo:MassBank/MassBank-data path:BAFG filename:MSBNK-BAFG-CSL231',
        "ce_post2023_CSL250": 'COLLISION_ENERGY repo:MassBank/MassBank-data path:BAFG filename:MSBNK-BAFG-CSL250',
        "record_title": 'RECORD_TITLE repo:MassBank/MassBank-data path:BAFG',
        "instrument_line": '"AC$INSTRUMENT:" repo:MassBank/MassBank-data path:BAFG',
        "precursor_type": 'PRECURSOR_TYPE repo:MassBank/MassBank-data path:BAFG',
        "license_line": '"COPYRIGHT" repo:MassBank/MassBank-data path:BAFG',
    }
    hdr = {}
    for name, q in queries.items():
        try:
            hdr[name] = code_search(name, q)
        except subprocess.CalledProcessError as e:
            hdr[name] = {"query": q, "error": e.stderr.decode()[:300]}
    rec["checks"]["header_fields"] = hdr

    # ---------------------------------------------------------------- E. JSON-LD cache authenticity
    cache = OUT / "downloads/massbank_export_jsonld/bafg_export_metadata_jsonld.jsonl.gz"
    cached = {}
    with gzip.open(cache, "rt") as fh:
        for line in fh:
            o = json.loads(line)
            acc = o.get("accession") or o.get("identifier") or ""
            cached[str(acc)] = o
    probe = ["MSBNK-BAFG-CSL2311096", "MSBNK-BAFG-CSL2500001", sorted(cached)[0] if cached else ""]
    jl = []
    for acc in probe:
        if not acc:
            continue
        url = f"https://massbank.eu/MassBank-export/metadata/{acc}"
        try:
            raw = http_get(url)
        except Exception as e:  # noqa: BLE001
            jl.append({"accession": acc, "error": str(e)[:200]})
            continue
        register(
            f"MassBank export JSON-LD live re-fetch {acc}",
            "MassBank export-service JSON-LD structured metadata (title, compound identity; no peaks)",
            url,
            raw,
            "not stored separately; compared against the cached aggregate",
        )
        live = json.loads(raw)
        c = cached.get(acc)
        cbody = c.get("body") if isinstance(c, dict) else None
        def dataset_node(body):
            if isinstance(body, list):
                for n in body:
                    if isinstance(n, dict) and n.get("@type") == "Dataset":
                        return n
            return body if isinstance(body, dict) else {}
        lnode = dataset_node(live)
        jl.append({
            "accession": acc,
            "live_sha256": hashlib.sha256(raw).hexdigest(),
            "in_cached_aggregate": c is not None,
            "cached_body_equals_live": (json.dumps(cbody, sort_keys=True) == json.dumps(live, sort_keys=True))
            if cbody is not None else None,
            "live_name_field": str(lnode.get("name", ""))[:200],
            "live_datePublished": str(lnode.get("datePublished", ""))[:40],
            "live_license": str(lnode.get("license", ""))[:120],
            "live_description": str(lnode.get("description", ""))[:220],
        })
    rec["checks"]["jsonld_live_recheck"] = {"cached_records": len(cached), "probes": jl}

    # ---------------------------------------------------------------- F. tag -> tree provenance
    prov = {}
    for tag in ["2023.11", "2025.05.1"]:
        try:
            t = json.loads(gh(f"repos/MassBank/MassBank-data/git/ref/tags/{tag}"))
            obj = t["object"]
            if obj["type"] == "tag":
                ann = json.loads(gh(f"repos/MassBank/MassBank-data/git/tags/{obj['sha']}"))
                commit_sha = ann["object"]["sha"]
            else:
                commit_sha = obj["sha"]
            c = json.loads(gh(f"repos/MassBank/MassBank-data/commits/{commit_sha}"))
            tree = json.loads(gh(f"repos/MassBank/MassBank-data/git/trees/{c['commit']['tree']['sha']}"))
            bafg = [e for e in tree["tree"] if e["path"] == "BAFG"]
            prov[tag] = {
                "commit": commit_sha,
                "date": c["commit"]["committer"]["date"],
                "bafg_tree_sha": bafg[0]["sha"] if bafg else None,
            }
        except subprocess.CalledProcessError as e:
            prov[tag] = {"error": e.stderr.decode()[:200]}
    rec["checks"]["tag_provenance"] = prov
    refs_used = json.loads((OUT / "downloads/github_trees/refs_used.json").read_text())
    rec["checks"]["refs_used_first_pass"] = refs_used

    # ---------------------------------------------------------------- G. MSG QTOF CE-ladder shape (criterion 11)
    msg = pd.read_parquet(ADJ.parent / "comparator_feasibility/massspecgym15_identity.parquet")
    q = msg[msg["instrument_type"] == "QTOF"]
    ladder = q[q["collision_energy"].isin([float(x) for x in range(10, 160, 10)])]
    rec["checks"]["msg_qtof"] = {
        "msg_rows": int(len(msg)),
        "qtof_rows": int(len(q)),
        "qtof_keys": int(q["inchikey"].nunique()),
        "qtof_rows_on_10_150_step10_grid": int(len(ladder)),
        "qtof_rows_ce_ge_110": int((q["collision_energy"] >= 110).sum()),
        "qtof_keys_ce_ge_110": int(q.loc[q["collision_energy"] >= 110, "inchikey"].nunique()),
        "qtof_keys_ce_ge_110_that_are_bafg_positive_keys": int(
            len(set(q.loc[q["collision_energy"] >= 110, "inchikey"]) & pk)
        ),
        "qtof_ce_max": float(q["collision_energy"].max()),
        "bafg_positive_keys_in_msg_with_qtof_rows": int(len(set(q["inchikey"]) & pk)),
    }
    bafg_msg = msg[msg["inchikey"].isin(pk)]
    rec["checks"]["msg_rows_for_bafg_keys"] = {
        "rows": int(len(bafg_msg)),
        "keys": int(bafg_msg["inchikey"].nunique()),
        "by_instrument": {str(k): int(v) for k, v in bafg_msg["instrument_type"].value_counts(dropna=False).items()},
        "by_fold": {str(k): int(v) for k, v in bafg_msg["fold"].value_counts(dropna=False).items()},
        "by_adduct_top": {str(k): int(v) for k, v in bafg_msg["adduct"].value_counts().head(6).items()},
        "simulation_challenge_rows": int(bafg_msg["simulation_challenge"].sum()),
    }

    (OUT / "s10_verification_record.json").write_text(json.dumps(rec, indent=1, default=str))
    print(json.dumps({k: v for k, v in rec["checks"].items() if k != "header_fields"}, indent=1, default=str)[:12000])
    print("\nHEADER FIELD FRAGMENTS")
    print(json.dumps(rec["checks"]["header_fields"], indent=1)[:6000])


if __name__ == "__main__":
    main()
