"""E2b identity comparator: validates replay results against sealed evidence.

Loads the sealed evidence from commit cc6c8b9 (the pre-registered
G2_SELECTION_COUNT_AND_REPRESENTATIVE_144.json) and compares it against
the new replay results. For all 144 G2 cases, both selection_count and
cross_seed_representative_expression must be EXACT (byte-identical string
for the expression, integer-identical for the count).

If either match count is not 144/144:
    REPLAY_INTEGRITY = FAIL
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SEALED_COMMIT = "cc6c8b9"
SEALED_PATH = "results/e2b_heldout/G2_SELECTION_COUNT_AND_REPRESENTATIVE_144.json"
REPLAY_ROOT = (
    REPO_ROOT / "results" / "e2b_macos_fullfront_replay_20260818"
)
SUMMARIES_DIR = REPLAY_ROOT / "summaries"


def load_sealed_evidence(
    commit: str = SEALED_COMMIT,
    path: str = SEALED_PATH,
) -> dict[str, dict]:
    """Load sealed evidence from the specified git commit.

    Returns a dict keyed by case_id with:
      selection_count: int
      cross_seed_representative_expression: str
    """
    try:
        result = subprocess.run(
            ["git", "show", f"{commit}:{path}"],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(REPO_ROOT),
        )
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: could not retrieve sealed evidence: {exc.stderr}")
        sys.exit(2)

    data = json.loads(result.stdout)
    evidence = {}
    for case in data["cases"]:
        evidence[case["case_id"]] = {
            "selection_count": int(case["selection_count"]),
            "cross_seed_representative_expression": str(
                case["cross_seed_representative_expression"]
            ),
        }
    return evidence


def load_replay_results(summaries_dir: Path) -> dict[str, dict]:
    """Load replay results from per-case summary files.

    Expects either:
    1. Individual JSON files per case in summaries_dir, each containing
       case_id, selection_count, cross_seed_representative_expression
    2. A single combined JSON file (e2b_replay_g2_summary.json) in the
       summaries dir

    Returns a dict keyed by case_id.
    """
    results = {}

    # Try combined file first
    combined = summaries_dir / "e2b_replay_g2_summary.json"
    if combined.exists():
        data = json.loads(combined.read_text(encoding="utf-8"))
        cases = data.get("cases", data) if isinstance(data, dict) else data
        if isinstance(cases, list):
            for case in cases:
                results[case["case_id"]] = {
                    "selection_count": int(case["selection_count"]),
                    "cross_seed_representative_expression": str(
                        case.get(
                            "cross_seed_representative_expression",
                            case.get("representative_expression", ""),
                        )
                    ),
                }
            return results

    # Try individual case files
    if summaries_dir.exists():
        for path in sorted(summaries_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                case_id = data.get("case_id")
                if case_id:
                    results[case_id] = {
                        "selection_count": int(data["selection_count"]),
                        "cross_seed_representative_expression": str(
                            data.get(
                                "cross_seed_representative_expression",
                                data.get("representative_expression", ""),
                            )
                        ),
                    }
            except (json.JSONDecodeError, KeyError, TypeError):
                continue

    return results


def compare(
    sealed: dict[str, dict],
    replay: dict[str, dict],
    verbose: bool = False,
) -> dict:
    """Compare sealed evidence against replay results.

    Returns a structured report.
    """
    total_cases = len(sealed)
    selection_count_exact = 0
    representative_exact = 0
    selection_count_mismatches = []
    representative_mismatches = []
    missing_in_replay = []

    for case_id in sorted(sealed):
        sealed_entry = sealed[case_id]

        if case_id not in replay:
            missing_in_replay.append(case_id)
            continue

        replay_entry = replay[case_id]

        # selection_count: exact integer match
        sealed_count = sealed_entry["selection_count"]
        replay_count = replay_entry["selection_count"]
        if sealed_count == replay_count:
            selection_count_exact += 1
        else:
            selection_count_mismatches.append(
                {
                    "case_id": case_id,
                    "sealed": sealed_count,
                    "replay": replay_count,
                    "delta": replay_count - sealed_count,
                }
            )

        # representative: byte-identical string match
        sealed_repr = sealed_entry["cross_seed_representative_expression"]
        replay_repr = replay_entry["cross_seed_representative_expression"]
        if sealed_repr == replay_repr:
            representative_exact += 1
        else:
            representative_mismatches.append(
                {
                    "case_id": case_id,
                    "sealed": sealed_repr,
                    "replay": replay_repr,
                }
            )

    integrity = (
        selection_count_exact == total_cases
        and representative_exact == total_cases
        and len(missing_in_replay) == 0
    )

    report = {
        "TOTAL_CASES": total_cases,
        "REPLAY_CASES_FOUND": len(replay),
        "MISSING_IN_REPLAY": len(missing_in_replay),
        "SELECTION_COUNT_EXACT_CASES": f"{selection_count_exact} / {total_cases}",
        "REPRESENTATIVE_EXACT_CASES": f"{representative_exact} / {total_cases}",
        "SELECTION_COUNT_MISMATCHES": len(selection_count_mismatches),
        "REPRESENTATIVE_MISMATCHES": len(representative_mismatches),
        "REPLAY_INTEGRITY": "PASS" if integrity else "FAIL",
    }

    details = {
        "missing_in_replay": (
            missing_in_replay[:20] if not verbose else missing_in_replay
        ),
        "selection_count_mismatches": (
            selection_count_mismatches[:20]
            if not verbose
            else selection_count_mismatches
        ),
        "representative_mismatches": (
            representative_mismatches[:20]
            if not verbose
            else representative_mismatches
        ),
    }

    return {"report": report, "details": details}


def main():
    parser = argparse.ArgumentParser(
        description="E2b identity comparator: sealed evidence vs replay"
    )
    parser.add_argument(
        "--sealed-commit",
        default=SEALED_COMMIT,
        help="Git commit containing sealed evidence",
    )
    parser.add_argument(
        "--sealed-path",
        default=SEALED_PATH,
        help="Path within the commit to the sealed JSON",
    )
    parser.add_argument(
        "--summaries-dir",
        type=Path,
        default=SUMMARIES_DIR,
        help="Path to replay summaries directory",
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

    print("Loading sealed evidence from git...")
    sealed = load_sealed_evidence(args.sealed_commit, args.sealed_path)
    print(f"  Sealed cases: {len(sealed)}")

    print("Loading replay results...")
    replay = load_replay_results(args.summaries_dir)
    print(f"  Replay cases: {len(replay)}")

    if not replay:
        print()
        print("WARNING: No replay results found yet.")
        print(
            "  The replay has not yet written summaries. Run this script "
            "after the replay completes."
        )
        print()
        print("  Expected summaries location:")
        print(f"    {args.summaries_dir}")
        print()
        print("  Expected format: either")
        print("    1. e2b_replay_g2_summary.json (combined)")
        print("    2. Per-case JSON files in the summaries directory")
        print()

    result = compare(sealed, replay, verbose=args.verbose)

    print()
    print("=" * 70)
    print("E2b IDENTITY REPLAY VALIDATION")
    print("=" * 70)
    for key, value in result["report"].items():
        print(f"  {key:40s} = {value}")
    print()

    details = result["details"]
    if details["missing_in_replay"]:
        n = len(details["missing_in_replay"])
        print(f"MISSING IN REPLAY ({n}):")
        for cid in details["missing_in_replay"][:10]:
            print(f"  {cid}")
        if n > 10:
            print(f"  ... and {n - 10} more")
        print()

    if details["selection_count_mismatches"]:
        n = len(details["selection_count_mismatches"])
        print(f"SELECTION COUNT MISMATCHES ({n}):")
        for m in details["selection_count_mismatches"][:10]:
            print(
                f"  {m['case_id']}: sealed={m['sealed']}, "
                f"replay={m['replay']}, delta={m['delta']}"
            )
        print()

    if details["representative_mismatches"]:
        n = len(details["representative_mismatches"])
        print(f"REPRESENTATIVE MISMATCHES ({n}):")
        for m in details["representative_mismatches"][:10]:
            print(f"  {m['case_id']}:")
            print(f"    sealed: {m['sealed']}")
            print(f"    replay: {m['replay']}")
        print()

    integrity = result["report"]["REPLAY_INTEGRITY"]
    print(f"REPLAY_INTEGRITY = {integrity}")
    print("=" * 70)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8"
        )
        print(f"Report written to: {args.output}")

    return 0 if integrity == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
