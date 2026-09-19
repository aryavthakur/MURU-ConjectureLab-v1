"""Design B step 35: mechanical procurement walk over the frozen ordered queues.

Input: procurement/ordered_queues.csv (frozen) and procurement/verification_log.csv (append-only, one row per
verification decision; the last row per parent_key is the decision). Strata are walked in the fixed priority
N -> H -> L. Within a stratum candidates are taken strictly in rank order until 66 are accepted. A candidate is
passed over ONLY for a reason in design_b_constants.SKIP_REASONS. A candidate with no decision stops the walk
(PENDING): acceptance never skips ahead. Price is not an input and cannot influence acceptance.

Outputs: procurement/walk_trace.csv (every candidate reached, with its outcome), procurement/walk_status.json,
and, only when all three strata reach 66, procurement/procurement_manifest.csv plus its sha256 and a full
re-verification of the original exclusion rules.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import design_b_constants as C  # noqa: E402

ROOT = HERE.parents[2]
P = ROOT / "artifacts/ce_interface_adjudication/design_b/procurement"
LOG_COLUMNS = ["parent_key", "stratum", "decision", "reason_code", "vendor", "catalogue_id", "purity_percent",
               "pack", "quantity_mg", "lot", "evidence", "decided_utc"]
FAIL_CODES = {"NO_SUPPLY", "PURITY_LT_95", "IDENTITY_MISMATCH", "INSUFFICIENT_QUANTITY"}


class LogError(ValueError):
    pass


def load_log(path: Path) -> dict:
    if not path.exists():
        return {}
    log = pd.read_csv(path, dtype=str).fillna("")
    missing = [c for c in LOG_COLUMNS if c not in log.columns]
    if missing:
        raise LogError(f"verification log missing columns {missing}")
    out = {}
    for r in log.to_dict("records"):
        d = r["decision"]
        if d == "PASS":
            if float(r["purity_percent"] or "nan") < 95.0 or not float(r["purity_percent"] or "nan") >= 95.0:
                raise LogError(f"{r['parent_key']}: PASS requires stated purity >= 95")
            if not float(r["quantity_mg"] or "nan") >= C.MIN_QUANTITY_MG:
                raise LogError(f"{r['parent_key']}: PASS requires quantity_mg >= {C.MIN_QUANTITY_MG}")
            if not r["vendor"] or not r["catalogue_id"] or not r["evidence"]:
                raise LogError(f"{r['parent_key']}: PASS requires vendor, catalogue_id and evidence")
        elif d == "FAIL":
            if r["reason_code"] not in FAIL_CODES:
                raise LogError(f"{r['parent_key']}: FAIL reason {r['reason_code']!r} is not a preregistered reason")
            if not r["evidence"]:
                raise LogError(f"{r['parent_key']}: FAIL requires evidence")
        else:
            raise LogError(f"{r['parent_key']}: decision must be PASS or FAIL")
        out[r["parent_key"]] = r
    return out


def walk(queues: pd.DataFrame, decisions: dict, target: int = C.PROCUREMENT_TARGET_PER_STRATUM):
    trace, accepted, taken_scaffolds, status = [], {}, set(), {}
    blocked = False
    for s in C.STRATUM_PRIORITY:
        acc = []
        q = queues[queues["stratum"] == s].sort_values("rank")
        state = "COMPLETE"
        for r in q.to_dict("records"):
            if len(acc) == target:
                break
            base = {"stratum": s, "rank": r["rank"], "parent_key": r["parent_key"], "scaffold_group": r["scaffold_group"]}
            if r["scaffold_group"] in taken_scaffolds:
                trace.append({**base, "outcome": "SKIP", "reason_code": "SCAFFOLD_ALREADY_ACCEPTED"})
                continue
            if blocked:
                state = "BLOCKED_BY_HIGHER_PRIORITY_STRATUM"
                break
            d = decisions.get(r["parent_key"])
            if d is None:
                trace.append({**base, "outcome": "PENDING", "reason_code": ""})
                state = "PENDING"
                break
            if d["decision"] == "FAIL":
                trace.append({**base, "outcome": "SKIP", "reason_code": d["reason_code"]})
                continue
            trace.append({**base, "outcome": "ACCEPT", "reason_code": ""})
            acc.append(r["parent_key"])
            taken_scaffolds.add(r["scaffold_group"])
        else:
            if len(acc) < target:
                state = "EXHAUSTED"
        if len(acc) == target:
            state = "COMPLETE"
        accepted[s] = acc
        status[s] = {"state": state, "accepted": len(acc)}
        if state != "COMPLETE":
            blocked = True   # a lower-priority stratum cannot finalise before this one's scaffolds are fixed
    return pd.DataFrame(trace), accepted, status


def reverify(man: pd.DataFrame) -> dict:
    """Re-apply the sourcing screen's structural and identity rules to the accepted population."""
    spec = importlib.util.spec_from_file_location("screen", HERE / "20_sourcing_screen.py")
    S = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(S)
    problems = []
    for r in man.to_dict("records"):
        v = S.per_structure(r["parent_smiles"])
        lo, hi = C.STRATA[r["stratum"]]
        ok = (v.get("parse_ok") and v["parent_key"] == r["parent_key"] and lo <= v["mh"] <= hi and v["single_unit"]
              and not v["permanent_charge"] and not v["isotope_labelled"] and v["elements_ok"]
              and v["heavy_atoms"] <= S.MAX_ATOM_CT and v["mh"] <= S.PRECURSOR_BOUND)
        if not ok:
            problems.append(f"{r['parent_key']}: structural rule failure on re-verification")
    ex = {n: set((S.EX / f).read_text().split()) for n, f in {
        "msg_recorded": "msg15_keys_all.txt", "msg_parent": "msg15_parent_keys_all.txt",
        "comparator": "comparator_common_population_keys.txt"}.items()}
    lab = pd.read_csv(S.MSPRED_LABELS, sep="\t", usecols=["smiles", "inchikey"])
    ex["mspred_recorded"] = set(lab["inchikey"].dropna().map(lambda k: k.split("-")[0]))
    ex["mspred_parent"] = {S.SK.parent_connectivity_key(s) for s in lab["smiles"].dropna().unique()} - {None}
    ex["design_a"] = set(pd.read_csv(S.DESIGN_A)["compound_id"])
    for n, keys in ex.items():
        hit = sorted(set(man["parent_key"]) & keys)
        if hit:
            problems.append(f"exclusion set {n} contains {hit}")
    forms = set(man["formula"])
    mm = pd.read_parquet(S.A / "massspecgym15_metadata_columns.parquet", columns=["smiles"]).drop_duplicates()
    ref = set(mm["smiles"]) | set(lab["smiles"].dropna())
    msg_taut = set()
    for s in ref:
        pm = S.SK.parent_mol(s)
        if pm is not None and S.Chem.rdMolDescriptors.CalcMolFormula(pm) in forms:
            t = S.taut_key(s)
            if t:
                msg_taut.add(t)
    th = [k for k, s in zip(man["parent_key"], man["parent_smiles"]) if S.taut_key(s) in msg_taut]
    if th:
        problems.append(f"tautomer route hits {th}")
    return {"n_checked": int(len(man)), "problems": problems, "pass": not problems}


def main() -> int:
    import _scope_gate  # project-scope closure 2026-09-19: Design B cancelled, never executes
    _scope_gate.refuse()
    qpath = P / "ordered_queues.csv"
    queues = pd.read_csv(qpath)
    decisions = load_log(P / "verification_log.csv")
    trace, accepted, status = walk(queues, decisions)
    trace.to_csv(P / "walk_trace.csv", index=False)
    out = {"ordered_queues_sha256": hashlib.sha256(qpath.read_bytes()).hexdigest(), "status": status,
           "skips_by_reason": trace[trace["outcome"] == "SKIP"]["reason_code"].value_counts().to_dict() if len(trace) else {},
           "complete": all(v["state"] == "COMPLETE" for v in status.values())}
    if out["complete"]:
        keep = {k for v in accepted.values() for k in v}
        man = queues[queues["parent_key"].isin(keep)].copy()
        log = pd.DataFrame(decisions.values()).set_index("parent_key")
        for c in ("vendor", "catalogue_id", "purity_percent", "pack", "quantity_mg", "lot", "evidence"):
            man[c] = man["parent_key"].map(log[c])
        man = man.sort_values(["stratum", "rank"])
        assert man.groupby("stratum").size().to_dict() == {s: C.PROCUREMENT_TARGET_PER_STRATUM for s in C.STRATA}
        assert not man["scaffold_group"].duplicated().any(), "scaffold duplication"
        man.to_csv(P / "procurement_manifest.csv", index=False)
        out["manifest_sha256"] = hashlib.sha256((P / "procurement_manifest.csv").read_bytes()).hexdigest()
        out["scaffold_duplicates"] = int(man["scaffold_group"].duplicated().sum())
        out["reverification"] = reverify(man)
    (P / "walk_status.json").write_text(json.dumps(out, indent=1, default=int) + "\n")
    print(json.dumps(out, indent=1, default=int))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
