#!/usr/bin/env python3
"""D-INST: E2a instrument diagnostic.

Implements audit/muru_v2_reentry_20260819/MURU_V2_E2A_INSTRUMENT_DIAGNOSTIC_PROTOCOL.md
(SHA-256 5b2d2ae549241fbef993b928807a52122a7c8bc7cba73dff4eb63ee9ca71b646), frozen
before this ran.

ZERO new symbolic search. Recomputes G2-correctness for the front rows whose
canonicalization was ABANDONED by the wall-clock cap, using g2_contract's own
unmodified primitives, each in a dedicated subprocess with a generous budget.
A budget exhaustion yields UNRESOLVED and is NEVER converted into a class.
"""
from __future__ import annotations
import argparse, json, glob, os, sqlite3, subprocess, sys, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "audit" / "muru_v2_reentry_20260819"
CKPT = OUT / "_ckpt_dinst"
CACHE = os.path.expanduser("~/e2_x86_cache/classify_cache.sqlite3")
ESCALATION_SECONDS = 1800
CORRECT, INCORRECT, UNRESOLVED = "CORRECT", "INCORRECT", "UNRESOLVED"


def timed_out_expressions() -> set[str]:
    con = sqlite3.connect(f"file:{CACHE}?mode=ro", uri=True)
    return {e for e, rj in con.execute("select expression_string,result_json from classify_cache")
            if json.loads(rj).get("canonicalization_status") == "SIMPLIFY_TIMEOUT"}


def load_corpus():
    stage, meta = {}, {}
    for f in glob.glob(str(ROOT / "results/e2/run_x86_e2a_v1/worlds_shard_*.jsonl")):
        for l in open(f):
            if l.strip():
                d = json.loads(l)
                stage[d["world_id"]] = d["first_loss_stage"]
                meta[d["world_id"]] = d
    rows = collections.defaultdict(list)
    for f in glob.glob(str(ROOT / "results/e2/run_x86_e2a_v1/candidates_shard_*.jsonl")):
        for l in open(f):
            if l.strip():
                d = json.loads(l)
                rows[d["world_id"]].append(d)
    return stage, meta, rows


def eval_one(world_meta: dict, expr: str) -> tuple[str, float]:
    """One (world, expression) pair, in its own process, generous budget."""
    code = (
        "import sys,json,time;"
        f"sys.path.insert(0,{str(ROOT/'src')!r});"
        "from muru.v2_calibration import e2_worlds;"
        "from muru.paper_benchmark.g2_contract import ("
        " extract_effective_support, classify_discovered_family, classify_support,"
        " classify_family_match, evaluate_g2_event, G2Event);"
        f"w=e2_worlds.build_world({world_meta['family']!r},{world_meta['regime']!r},"
        f"{world_meta['noise_level']!r},{int(world_meta['replicate'])});"
        "ts=w.truth.support if hasattr(w,'truth') else None;"
        "tf=w.truth.family if hasattr(w,'truth') else None;"
        f"e={expr!r};"
        "t0=time.time();"
        "ev=evaluate_g2_event(classify_support(extract_effective_support(e),ts),"
        " classify_family_match(classify_discovered_family(e),tf));"
        "print('VERDICT'+json.dumps({'correct':ev==G2Event.SUCCESS,'wall':time.time()-t0}))"
    )
    try:
        p = subprocess.run([sys.executable, "-u", "-c", code], capture_output=True, text=True,
                           timeout=ESCALATION_SECONDS,
                           env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
    except subprocess.TimeoutExpired:
        return UNRESOLVED, float(ESCALATION_SECONDS)
    for line in (p.stdout or "").splitlines():
        if line.startswith("VERDICT"):
            d = json.loads(line[len("VERDICT"):])
            return (CORRECT if d["correct"] else INCORRECT), d["wall"]
    return UNRESOLVED, 0.0   # crash/OOM/kill -> UNRESOLVED, never a class


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()
    CKPT.mkdir(parents=True, exist_ok=True)

    timeout = timed_out_expressions()
    stage, meta, rows = load_corpus()
    work = []
    for w, rs in rows.items():
        for d in rs:
            if d.get("expression_string") in timeout:
                work.append((w, d["seed_ordinal_k"], d["front_rank"],
                             bool(d.get("retained_by_argmax_score")), d["expression_string"]))
    print(f"[D-INST] {len(work)} timed-out front rows across {len({w for w,*_ in work})} worlds "
          f"(sealed stages: {dict(collections.Counter(stage[w] for w,*_ in work))})", flush=True)

    from concurrent.futures import ThreadPoolExecutor, as_completed
    def run(item):
        w, k, rank, ret, expr = item
        ck = CKPT / f"{w.replace('|','_')}__{k}_{rank}.json"
        if ck.exists():
            try: return json.loads(ck.read_text())
            except json.JSONDecodeError: ck.unlink()
        verdict, wall = eval_one(meta[w], expr)
        rec = {"world_id": w, "seed_ordinal_k": k, "front_rank": rank,
               "retained_by_argmax_score": ret, "expression_string": expr,
               "verdict": verdict, "wall_seconds": round(wall, 1),
               "sealed_stage": stage[w]}
        ck.write_text(json.dumps(rec))
        return rec

    done = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for fut in as_completed([ex.submit(run, it) for it in work]):
            r = fut.result(); done += 1
            if r["verdict"] == CORRECT or done % 25 == 0:
                print(f"[{done}/{len(work)}] {r['verdict']:10} {r['sealed_stage']} "
                      f"{r['world_id']} k={r['seed_ordinal_k']} ({r['wall_seconds']}s)", flush=True)
    print(f"[D-INST] evaluation complete: {done} pairs", flush=True)


if __name__ == "__main__":
    main()
