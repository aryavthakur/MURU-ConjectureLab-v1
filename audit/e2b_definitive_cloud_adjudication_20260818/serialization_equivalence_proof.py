#!/usr/bin/env python3
"""AGENT_2 machine-checkable proof that the post-freeze serialization patch
(dabcb4b -> 6b18dd8, scripts/run_e2b_fullfront_replay.py) is scientifically neutral.

Strategy: reimplement BOTH the pre-patch and post-patch cell-conversion functions
verbatim from the git diff, then show that for every column the classifiers
actually read, the two paths emit BYTE-IDENTICAL JSON.

Run:  python audit/.../serialization_equivalence_proof.py
"""
import json, random, struct, sys
import numpy as np

# ---- verbatim PRE-PATCH conversion (dabcb4b, _serialize_front inner loop) ----
def pre_patch(val):
    if hasattr(val, "item"):
        val = val.item()
    elif isinstance(val, (bytes, bytearray)):
        val = val.decode("utf-8", errors="replace")
    return val

# ---- verbatim POST-PATCH conversion (6b18dd8, _to_json_safe) ----
def post_patch(val):
    if val is None:
        return None
    if isinstance(val, (str, int, float, bool)):
        return val
    if isinstance(val, (bytes, bytearray)):
        return val.decode("utf-8", errors="replace")
    if hasattr(val, "item"):
        return val.item()
    return str(val)

def main():
    random.seed(20260818)
    report = {}

    # --- score / loss : np.float64 (SUBCLASSES float -> takes a DIFFERENT branch) ---
    fvals = []
    while len(fvals) < 300000:
        b = random.getrandbits(64)
        f = struct.unpack("<d", struct.pack("<Q", b))[0]
        if f != f or f in (float("inf"), float("-inf")):
            continue
        fvals.append(np.float64(f))
    fvals += [np.float64(x) for x in (0.0, -0.0, 5e-324, 1e-320, 2.2250738585072014e-308,
                                      1.7976931348623157e308, 0.1, 1/3, -0.0)]
    bad = [v for v in fvals if json.dumps(pre_patch(v)) != json.dumps(post_patch(v))]
    badv = [v for v in fvals if float(pre_patch(v)) != float(post_patch(v))]
    report["float64"] = {"tested": len(fvals), "json_differs": len(bad), "value_differs": len(badv),
                         "python_type_differs": sum(1 for v in fvals if type(pre_patch(v)) is not type(post_patch(v)))}

    # --- complexity : np.int64 (does NOT subclass int -> same branch both sides) ---
    ivals = [np.int64(random.randint(-2**62, 2**62)) for _ in range(100000)]
    ivals += [np.int64(0), np.int64(1), np.int64(-1), np.int64(2**62)]
    report["int64"] = {"tested": len(ivals),
                       "json_differs": sum(1 for v in ivals if json.dumps(pre_patch(v)) != json.dumps(post_patch(v)))}

    # --- equation : str (the ONLY column feeding G2 classification) ---
    svals = ["x0", "sqrt(x0) * 0.062147498", "(x0 + x1)/2", "exp(-x0)*sin(x1)", "", "x0**2 + 1e-9"]
    report["str"] = {"tested": len(svals),
                     "json_differs": sum(1 for v in svals if json.dumps(pre_patch(v)) != json.dumps(post_patch(v)))}

    # --- bool ---
    bvals = [np.bool_(True), np.bool_(False), True, False]
    report["bool"] = {"tested": len(bvals),
                      "json_differs": sum(1 for v in bvals if json.dumps(pre_patch(v)) != json.dumps(post_patch(v)))}

    total_json_diff = sum(r["json_differs"] for r in report.values())
    report["TOTAL_JSON_DIFFERENCES_ON_CLASSIFIER_RELEVANT_TYPES"] = total_json_diff
    report["VERDICT"] = "IDENTICAL" if total_json_diff == 0 else "DIVERGENT"
    print(json.dumps(report, indent=2))
    return 0 if total_json_diff == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
