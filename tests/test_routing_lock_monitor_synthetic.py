"""Demonstrates routing_lock_monitor.py end-to-end against SYNTHETIC,
schema-faithful world-outcome files -- never against the live E2a run's
real (incomplete) output. Mirrors the outcome-blind interim
characterization's own step 9 precedent (dry run on synthetic data).

Two scenarios: (1) a fabricated count distribution engineered to prove a
LOCKED_EXECUTE_E4A state fires with the CLI printing no per-stage counts,
and (2) a fabricated distribution engineered to stay FULL_RUN_REQUIRED
(A-dominant-looking, unratified exoneration) even at full synthetic
"completion". World IDs and stage labels here are entirely made up.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO_SRC = Path(__file__).resolve().parents[1] / "src"
CLI = Path(__file__).resolve().parents[1] / "scripts" / "e2_rescue_v2" / "routing_lock_monitor.py"


def _write_synthetic(tmp_dir: Path, stage_counts: dict[str, int]) -> None:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    path = tmp_dir / "worlds_shard_000.jsonl"
    i = 0
    with path.open("w") as fh:
        for stage, n in stage_counts.items():
            for _ in range(n):
                fh.write(json.dumps({
                    "world_id": f"SYNTH|world|{i:04d}",
                    "first_loss_stage": stage,
                }) + "\n")
                i += 1


def _run_cli(tmp_dir: Path, total: int) -> str:
    out = subprocess.run(
        [sys.executable, str(CLI), "--world-outcome-dir", str(tmp_dir), "--total", str(total)],
        capture_output=True, text=True, check=True,
    )
    return out.stdout


def test_synthetic_execute_lock(tmp_path):
    # 540 synthetic cases, B overwhelming -> LOCKED_EXECUTE_E4A, and the
    # printed output must contain no A/B/C/D count anywhere.
    _write_synthetic(tmp_path, {"A": 5, "B": 500, "C": 10, "D": 10, "E": 15})
    stdout = _run_cli(tmp_path, total=540)
    assert "LOCKED_EXECUTE_E4A" in stdout
    assert "N_CLASSIFIED: 540/540" in stdout
    assert "R_REMAINING: 0" in stdout
    for forbidden in ("500", "\"A\":", "\"B\":", "\"C\":", "\"D\":"):
        assert forbidden not in stdout


def test_synthetic_a_dominant_stays_full_run_required(tmp_path):
    # A totally dominant, 540/540 synthetic completion, but since the
    # exoneration branch is unratified, this MUST remain FULL_RUN_REQUIRED
    # -- proves the CLI never silently promotes an A-dominant read into a
    # route decision.
    _write_synthetic(tmp_path, {"A": 480, "B": 10, "C": 20, "D": 20, "E": 10})
    stdout = _run_cli(tmp_path, total=540)
    assert "FULL_RUN_REQUIRED" in stdout
    assert "LOCKED" not in stdout.split("FULL_RUN_REQUIRED")[0].replace("ROUTING_LOCK_STATE: ", "")


def test_synthetic_partial_completion_unlocked(tmp_path):
    _write_synthetic(tmp_path, {"A": 5, "B": 10, "C": 2, "D": 2, "E": 3})  # 22/540, nowhere near locked
    stdout = _run_cli(tmp_path, total=540)
    assert "ROUTING_LOCK_STATE: FULL_RUN_REQUIRED" in stdout
    assert "N_CLASSIFIED: 22/540" in stdout
    assert "R_REMAINING: 518" in stdout


def test_synthetic_duplicate_world_id_deduplicated(tmp_path):
    # Two files, same world_id repeated with the same stage (byte-identical
    # duplicate, matching the real §16 duplicate-recomputation pattern) --
    # must count once, not twice.
    d1 = tmp_path / "d1"
    d1.mkdir(parents=True)
    (d1 / "worlds_shard_000.jsonl").write_text(
        json.dumps({"world_id": "SYNTH|w|0000", "first_loss_stage": "B"}) + "\n"
        + json.dumps({"world_id": "SYNTH|w|0000", "first_loss_stage": "B"}) + "\n"
    )
    stdout = _run_cli(d1, total=540)
    assert "N_CLASSIFIED: 1/540" in stdout


if __name__ == "__main__":
    import tempfile
    import traceback

    tests = [
        test_synthetic_execute_lock,
        test_synthetic_a_dominant_stays_full_run_required,
        test_synthetic_partial_completion_unlocked,
        test_synthetic_duplicate_world_id_deduplicated,
    ]
    failed = 0
    for t in tests:
        with tempfile.TemporaryDirectory() as td:
            try:
                t(Path(td) / "case")
                print(f"PASS {t.__name__}")
            except Exception:
                failed += 1
                print(f"FAIL {t.__name__}")
                traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
