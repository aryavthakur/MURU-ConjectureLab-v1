from __future__ import annotations

import argparse
import json
from pathlib import Path

from muru.paper_benchmark.governance import ImplementationLock
from muru.paper_benchmark.preflight import run_preflight


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_preflight(args.artifacts, ImplementationLock.pending())
    args.output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n")
    print(f"development preflight: {report.case_count} cases; engine={report.engine_status}")


if __name__ == "__main__":
    main()
