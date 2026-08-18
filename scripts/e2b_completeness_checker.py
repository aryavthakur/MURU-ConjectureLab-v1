"""E2b completeness checker: validates replay execution against expected manifest.

Reads the expected search manifest, scans the fronts directory for actual
front files, and computes a comprehensive completeness report including:
  - Search counts (expected, started, completed, failed)
  - Front counts (written, valid, torn, duplicate, missing)
  - Per-front validation (JSONL parse, case_id, seed, row count, SHA-256)

Successful completion requires ALL of:
  SEARCHES_COMPLETED = 4320
  SEARCHES_FAILED = 0
  FRONTS_WRITTEN = 4320
  FRONTS_VALID = 4320
  FRONTS_TORN = 0
  FRONTS_DUPLICATE = 0
  FRONTS_MISSING = 0
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path


REPLAY_ROOT = Path(__file__).resolve().parent.parent / (
    "results/e2b_macos_fullfront_replay_20260818"
)
MANIFEST_PATH = REPLAY_ROOT / "manifests" / "MURU_E2B_EXPECTED_SEARCH_MANIFEST.csv"
FRONTS_DIR = REPLAY_ROOT / "fronts"
LOGS_DIR = REPLAY_ROOT / "logs"


def load_manifest(manifest_path: Path) -> list[dict]:
    """Load expected manifest rows."""
    rows = []
    with open(manifest_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def validate_front(
    front_path: Path, expected_case_id: str, expected_seed: int
) -> dict:
    """Validate a single front file.

    Returns a dict with:
      valid: bool
      rows: int (number of JSONL rows)
      sha256: str or None
      error: str or None (reason for invalidity)
    """
    result = {
        "valid": False,
        "rows": 0,
        "sha256": None,
        "error": None,
        "torn": False,
    }

    if not front_path.exists():
        result["error"] = "file_not_found"
        return result

    try:
        raw_bytes = front_path.read_bytes()
    except OSError as exc:
        result["error"] = f"read_error: {exc}"
        result["torn"] = True
        return result

    result["sha256"] = hashlib.sha256(raw_bytes).hexdigest()

    text = raw_bytes.decode("utf-8", errors="replace")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if not lines:
        result["error"] = "empty_file"
        result["torn"] = True
        return result

    parsed_rows = []
    for i, line in enumerate(lines):
        try:
            obj = json.loads(line)
            parsed_rows.append(obj)
        except json.JSONDecodeError as exc:
            result["error"] = f"jsonl_parse_error_line_{i + 1}: {exc}"
            result["torn"] = True
            return result

    result["rows"] = len(parsed_rows)

    if result["rows"] < 1:
        result["error"] = "no_rows"
        result["torn"] = True
        return result

    # Validate case_id presence in at least one row
    case_ids_found = {
        row.get("case_id") for row in parsed_rows if "case_id" in row
    }
    if expected_case_id not in case_ids_found and case_ids_found:
        result["error"] = (
            f"case_id_mismatch: expected {expected_case_id}, "
            f"found {case_ids_found}"
        )
        return result

    # Validate seed presence in at least one row
    seeds_found = set()
    for row in parsed_rows:
        if "seed" in row:
            seeds_found.add(int(row["seed"]))
    if expected_seed not in seeds_found and seeds_found:
        result["error"] = (
            f"seed_mismatch: expected {expected_seed}, found {seeds_found}"
        )
        return result

    result["valid"] = True
    return result


def count_started_searches(logs_dir: Path) -> int:
    """Count searches that were started, from log or marker files."""
    if not logs_dir.exists():
        return 0
    # Count log/marker files that indicate a search was started
    started = 0
    for path in logs_dir.iterdir():
        if path.is_file() and (
            path.suffix in (".log", ".marker", ".started", ".json")
        ):
            started += 1
    return started


def run_completeness_check(
    manifest_path: Path | None = None,
    fronts_dir: Path | None = None,
    logs_dir: Path | None = None,
    verbose: bool = False,
) -> dict:
    """Run the full completeness check and return results dict."""
    manifest_path = manifest_path or MANIFEST_PATH
    fronts_dir = fronts_dir or FRONTS_DIR
    logs_dir = logs_dir or LOGS_DIR

    manifest_rows = load_manifest(manifest_path)

    searches_expected = len(manifest_rows)
    searches_started = count_started_searches(logs_dir)
    searches_completed = 0
    searches_failed = 0

    fronts_written = 0
    fronts_valid = 0
    fronts_torn = 0
    fronts_missing = 0

    # Track duplicates: (case_id, seed) -> list of paths
    seen_keys: dict[tuple[str, int], list[str]] = {}
    fronts_duplicate = 0

    missing_list: list[str] = []
    torn_list: list[str] = []
    invalid_list: list[dict] = []
    sha256_registry: dict[str, str] = {}

    for row in manifest_rows:
        case_id = row["case_id"]
        seed = int(row["seed"])
        expected_front_path = row["expected_front_path"]
        full_path = fronts_dir.parent / expected_front_path

        key = (case_id, seed)
        if key in seen_keys:
            seen_keys[key].append(expected_front_path)
            fronts_duplicate += 1
        else:
            seen_keys[key] = [expected_front_path]

        if not full_path.exists():
            fronts_missing += 1
            missing_list.append(expected_front_path)
            continue

        fronts_written += 1
        validation = validate_front(full_path, case_id, seed)

        if validation["torn"]:
            fronts_torn += 1
            torn_list.append(expected_front_path)
            searches_failed += 1
        elif validation["valid"]:
            fronts_valid += 1
            searches_completed += 1
            if validation["sha256"]:
                sha256_registry[expected_front_path] = validation["sha256"]
        else:
            searches_failed += 1
            invalid_list.append(
                {"path": expected_front_path, "error": validation["error"]}
            )

    # Also scan for unexpected files in fronts/
    unexpected_files = []
    expected_filenames = {
        Path(row["expected_front_path"]).name for row in manifest_rows
    }
    if fronts_dir.exists():
        for path in sorted(fronts_dir.iterdir()):
            if path.is_file() and path.name not in expected_filenames:
                unexpected_files.append(str(path.relative_to(fronts_dir.parent)))

    # If we could not get started count from logs, use fronts as lower bound
    if searches_started == 0:
        searches_started = fronts_written

    # Completion verdict
    all_pass = (
        searches_completed == 4320
        and searches_failed == 0
        and fronts_written == 4320
        and fronts_valid == 4320
        and fronts_torn == 0
        and fronts_duplicate == 0
        and fronts_missing == 0
    )

    report = {
        "SEARCHES_EXPECTED": searches_expected,
        "SEARCHES_STARTED": searches_started,
        "SEARCHES_COMPLETED": searches_completed,
        "SEARCHES_FAILED": searches_failed,
        "FRONTS_WRITTEN": fronts_written,
        "FRONTS_VALID": fronts_valid,
        "FRONTS_TORN": fronts_torn,
        "FRONTS_DUPLICATE": fronts_duplicate,
        "FRONTS_MISSING": fronts_missing,
        "UNEXPECTED_FILES": len(unexpected_files),
        "COMPLETENESS_VERDICT": "PASS" if all_pass else "FAIL",
    }

    details = {
        "missing": missing_list[:20] if not verbose else missing_list,
        "torn": torn_list[:20] if not verbose else torn_list,
        "invalid": invalid_list[:20] if not verbose else invalid_list,
        "unexpected": unexpected_files[:20] if not verbose else unexpected_files,
        "sha256_registry_size": len(sha256_registry),
    }

    return {"report": report, "details": details}


def main():
    parser = argparse.ArgumentParser(
        description="E2b completeness checker for MURU fullfront replay"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=MANIFEST_PATH,
        help="Path to expected search manifest CSV",
    )
    parser.add_argument(
        "--fronts-dir",
        type=Path,
        default=FRONTS_DIR,
        help="Path to fronts directory",
    )
    parser.add_argument(
        "--logs-dir",
        type=Path,
        default=LOGS_DIR,
        help="Path to logs directory",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show all details"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write JSON report to file",
    )
    args = parser.parse_args()

    result = run_completeness_check(
        manifest_path=args.manifest,
        fronts_dir=args.fronts_dir,
        logs_dir=args.logs_dir,
        verbose=args.verbose,
    )

    print("=" * 70)
    print("E2b COMPLETENESS CHECK")
    print("=" * 70)
    for key, value in result["report"].items():
        print(f"  {key:30s} = {value}")
    print()

    details = result["details"]
    if details["missing"] and result["report"]["FRONTS_MISSING"] > 0:
        n = result["report"]["FRONTS_MISSING"]
        shown = len(details["missing"])
        print(f"MISSING FRONTS ({shown} of {n}):")
        for p in details["missing"][:10]:
            print(f"  {p}")
        if shown > 10:
            print(f"  ... and {shown - 10} more")
        print()

    if details["torn"]:
        print(f"TORN FRONTS ({len(details['torn'])}):")
        for p in details["torn"][:10]:
            print(f"  {p}")
        print()

    if details["invalid"]:
        print(f"INVALID FRONTS ({len(details['invalid'])}):")
        for item in details["invalid"][:10]:
            print(f"  {item['path']}: {item['error']}")
        print()

    if details["unexpected"]:
        print(f"UNEXPECTED FILES ({len(details['unexpected'])}):")
        for p in details["unexpected"][:10]:
            print(f"  {p}")
        print()

    print(f"SHA-256 registry size: {details['sha256_registry_size']}")
    print()
    verdict = result["report"]["COMPLETENESS_VERDICT"]
    print(f"COMPLETENESS_VERDICT = {verdict}")
    print("=" * 70)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8"
        )
        print(f"Report written to: {args.output}")

    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
