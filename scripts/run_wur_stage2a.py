"""CLI: execute Stage 2A once. See MURU_WUR_STAGE2A_EXECUTION_PROTOCOL.md."""
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muru.wur_stage2.run2a import main  # noqa: E402

if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    main(data_dir)
