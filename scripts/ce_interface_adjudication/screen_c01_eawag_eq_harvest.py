"""S1 screen C01, step 2: harvest MassBank record HEADER lines for Eawag EQ records via GitHub code search.

Metadata only. GitHub code search (legacy REST search/code with text-match fragments) indexes the default branch
(dev) of MassBank/MassBank-data. Each result carries the indexed blob SHA and short text fragments around the matched
terms. Only lines whose tag is a header tag (KEEP) are kept; every other line (in particular any PK$ line or peak
row) is discarded in memory and never written. No record file (which contains PK$PEAK) is downloaded.

Targets: files from step 1 (eawag_eq_tree_blobs.csv) whose first_ref is in --first-refs, plus optional --extra-uchem
compound ids (all their files). Queries are split by file-name prefix so that each query matches at most --cap files
of the dev tree (the API returns at most 1,000 results per query).

Passes (term pairs, each giving a different header neighbourhood):
  S  "SMILES IUPAC"                -> CH$FORMULA, CH$EXACT_MASS, CH$SMILES, CH$IUPAC, CH$LINK
  C  "CONFIDENCE LICENSE"          -> RECORD_TITLE, DATE, AUTHORS, LICENSE, COPYRIGHT, COMMENT
  E  "INCHIKEY COLLISION_ENERGY"   -> CH$LINK INCHIKEY, AC$MASS_SPECTROMETRY COLLISION_ENERGY, FRAGMENTATION_MODE
  P  "PRECURSOR_TYPE ION_MODE"     -> MS$FOCUSED_ION PRECURSOR_TYPE / PRECURSOR_M/Z, ION_MODE, MS_TYPE
  I  "INSTRUMENT_TYPE RESOLUTION"  -> AC$INSTRUMENT, AC$INSTRUMENT_TYPE, RESOLUTION
Output: <outdir>/codesearch_<pass>.json
"""
import argparse
import collections
import datetime as dt
import json
import math
import re
import subprocess
import time
from pathlib import Path

import pandas as pd

TERMS = {"S": "SMILES IUPAC", "C": "CONFIDENCE LICENSE", "E": "INCHIKEY COLLISION_ENERGY",
         "P": "PRECURSOR_TYPE ION_MODE", "I": "INSTRUMENT_TYPE RESOLUTION"}
KEEP = re.compile(r"^(RECORD_TITLE|DATE|AUTHORS|LICENSE|COPYRIGHT|PUBLICATION|COMMENT|"
                  r"CH\$(NAME|COMPOUND_CLASS|FORMULA|EXACT_MASS|SMILES|IUPAC|LINK)|"
                  r"AC\$INSTRUMENT|AC\$INSTRUMENT_TYPE|AC\$MASS_SPECTROMETRY|AC\$CHROMATOGRAPHY|"
                  r"MS\$FOCUSED_ION|MS\$DATA_PROCESSING): ")
DROP = re.compile(r"^PK\$")


def groups(prefix, fs, cap, targets):
    if len(fs) <= cap or not (set(fs) - targets):
        return [(prefix, fs)]
    by = collections.defaultdict(list)
    for f in fs:
        by[f[:len(prefix) + 1]].append(f)
    out = []
    for p, s in sorted(by.items()):
        out += groups(p, s, cap, targets)
    return out


def search(q, page):
    last = ""
    for attempt in range(8):
        r = subprocess.run(["gh", "api", "-X", "GET", "search/code", "-f", f"q={q}", "-f", "per_page=100",
                            "-f", f"page={page}", "-H", "Accept: application/vnd.github.text-match+json"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return json.loads(r.stdout), len(r.stdout.encode())
        last = r.stderr[:300]
        time.sleep(45 + 15 * attempt)
    raise RuntimeError(last)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--passes", default="S,C,E,P,I")
    ap.add_argument("--first-refs", default="2024.06,2024.11,2025.10,dev")
    ap.add_argument("--extra-uchem", default="")
    ap.add_argument("--label", default="")
    ap.add_argument("--files", default="", help="optional text file with one target file name per line (added)")
    ap.add_argument("--cap", type=int, default=400)
    ap.add_argument("--sleep", type=float, default=6.5)
    a = ap.parse_args()
    t = pd.read_csv(a.tree)
    allf = sorted(t["file"])
    tg = t[t["first_ref"].isin(a.first_refs.split(","))] if a.first_refs else t.iloc[0:0]
    targets = set(tg["file"])
    if a.extra_uchem:
        ids = {int(x) for x in a.extra_uchem.split(",")}
        targets |= set(t[t["uchem_id"].isin(ids)]["file"])
    if a.files:
        targets |= set(Path(a.files).read_text().split())
    gs = [(p, fs) for p, fs in groups("MSBNK-Eawag-EQ", allf, a.cap, targets) if targets & set(fs)]
    print("targets", len(targets), "groups", len(gs), "est pages/pass", sum(math.ceil(len(fs) / 100) for _, fs in gs),
          flush=True)
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    for ps in a.passes.split(","):
        recs, queries, nbytes = {}, [], 0
        n_dropped_nonheader = 0
        for prefix, fs in gs:
            q = f"repo:MassBank/MassBank-data filename:{prefix} {TERMS[ps]}"
            for page in range(1, 11):
                js, nb = search(q, page)
                nbytes += nb
                time.sleep(a.sleep)
                items = js.get("items", [])
                queries.append({"q": q, "page": page, "total_count": js.get("total_count"),
                                "incomplete_results": js.get("incomplete_results"), "n_items": len(items),
                                "n_tree_files_with_prefix": len(fs)})
                for it in items:
                    fn = it["path"].split("/")[-1]
                    if not it["path"].startswith("Eawag/") or fn not in targets:
                        continue
                    r = recs.setdefault(fn, {"sha": it["sha"], "lines": []})
                    lines = set(r["lines"])
                    for tm in it.get("text_matches", []):
                        for ln in tm.get("fragment", "").split("\n"):
                            if KEEP.match(ln) and not DROP.match(ln):
                                lines.add(ln)
                            elif ln.strip():
                                n_dropped_nonheader += 1
                    r["lines"] = sorted(lines)
                if len(items) < 100:
                    break
            print(ps, prefix, len(fs), "harvested", len(recs), flush=True)
        doc = {"pass": ps, "terms": TERMS[ps], "repo": "MassBank/MassBank-data (default branch dev, as indexed)",
               "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "n_targets": len(targets),
               "n_harvested": len(recs), "api_response_bytes_total": nbytes,
               "n_nonheader_fragment_lines_discarded_unwritten": n_dropped_nonheader,
               "keep_regex": KEEP.pattern, "queries": queries, "records": recs}
        fn = out / f"codesearch_{ps}{a.label}.json"
        fn.write_text(json.dumps(doc, indent=0, sort_keys=True))
        print("DONE", ps, len(targets), len(recs), fn, flush=True)


if __name__ == "__main__":
    main()
