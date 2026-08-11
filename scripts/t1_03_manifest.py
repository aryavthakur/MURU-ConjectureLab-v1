"""T1.3 -- manifest every acquired MassBank record with SHA-256."""
import sys, yaml
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from muru.io.manifest import Manifest

ROOT = Path(__file__).resolve().parents[1]
cfg = yaml.safe_load((ROOT / "configs" / "dataset.yaml").read_text())["massbank"]
lcsb = ROOT / "data" / "massbank" / "MassBank-data" / "LCSB"
files = sorted(lcsb.glob("MSBNK-LCSB-LU*.txt"))
m = Manifest.build(
    source=cfg["source_repository"],
    pin={"release_tag": cfg["release_tag"], "commit": cfg["commit"],
         "directory": cfg["contributor_directory"],
         "release_published": cfg["release_published"]},
    root=lcsb, paths=files,
)
out = m.write(ROOT / "artifacts" / "MANIFEST_massbank.json")
print(f"files={len(m.files)} bytes={m.total_bytes:,} digest={m.corpus_digest()[:16]}...")
print(f"written: {out.relative_to(ROOT)}")
