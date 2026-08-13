"""Build prospective paper benchmark content without evaluating outcomes."""
from __future__ import annotations

import argparse
from pathlib import Path

from muru.paper_benchmark.artifacts import build_all


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts"))
    parser.add_argument("--quiet-held-out", action="store_true")
    args = parser.parse_args()
    receipts = build_all(args.output)
    for partition, receipt in receipts.items():
        print(f"{partition}: {receipt.case_count} cases")
    print(f"verified artifacts: {len(next(iter(receipts.values())).hashes)}")


if __name__ == "__main__":
    main()
