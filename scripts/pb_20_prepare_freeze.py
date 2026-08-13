from __future__ import annotations

import argparse
import json
from pathlib import Path

from muru.paper_benchmark.freeze import prepare_content_freeze
from muru.paper_benchmark.governance import ImplementationLock


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    preflight_path = args.artifacts / "paper_benchmark_preflight.json"
    preflight = json.loads(preflight_path.read_text()) if preflight_path.exists() else {"complete": False}
    prepared = prepare_content_freeze(args.artifacts, ImplementationLock.pending(), preflight)
    args.output.write_text(json.dumps(prepared.to_dict(), indent=2, sort_keys=True) + "\n")
    print(prepared.status)


if __name__ == "__main__":
    main()
