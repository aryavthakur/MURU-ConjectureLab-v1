"""T1.11 -- acquire the Phase 1 raw mzML subset from MassIVE MSV000091754.

Subset rationale (master plan W1.5): mixes 499, 503, 505 are the only mixes
sharing a replicate compound set, and they are the only route to a repeatability
estimate because the curated MassBank layer holds one record per compound.

Campaign: 20200303 ONLY. MSV000091754 also contains a 20190812 campaign; the
MassBank records cite COMMENT: DATASET 20200303_*, so mixing campaigns would
compare different injections.

Positive mode only -- positive is the primary experiment and K3 needs one
endpoint to clear one gate.

Every file is hashed on arrival. Downloads are resumable and skip files already
present with the right size.
"""

from __future__ import annotations

import csv
import re
import sys
import time
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from muru.io.manifest import Manifest  # noqa: E402

INDEX = "https://datasetcache.gnps2.org/datasette/database/filename.csv?_size=max&dataset__exact=MSV000091754"
DL = "https://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?forceDownload=true&file=f.MSV000091754/{path}"
OUT = ROOT / "data" / "massive" / "mzml"


def fetch_index(cache: Path) -> list[dict]:
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(INDEX, cache)
    return list(csv.DictReader(cache.open()))


def main() -> None:
    cfg = yaml.safe_load((ROOT / "configs" / "dataset.yaml").read_text())["massive"]
    mixes = {str(m) for m in cfg["replicate_mixes"]}
    modes = set(cfg["replicate_modes"])
    pat = re.compile(cfg["filename_pattern"])

    rows = fetch_index(ROOT / "data" / "massive" / "file_index.csv")
    targets = []
    for r in rows:
        name = r["filepath"].split("/")[-1]
        m = pat.match(name)
        if m and m.group("mix") in mixes and m.group("mode") in modes:
            targets.append((r["filepath"], name, int(r["size"])))
    targets.sort()

    total = sum(s for _, _, s in targets)
    print(f"{len(targets)} files, {total/1e9:.2f} GB")
    OUT.mkdir(parents=True, exist_ok=True)

    for i, (path, name, size) in enumerate(targets, 1):
        dest = OUT / name
        if dest.exists() and dest.stat().st_size == size:
            print(f"[{i}/{len(targets)}] skip (present) {name}")
            continue
        print(f"[{i}/{len(targets)}] {name} ({size/1e6:.0f} MB)", flush=True)
        tmp = dest.with_suffix(".part")
        # MassIVE rate-limits (HTTP 429). Back off and retry rather than
        # hammering the host or silently dropping a file from the subset.
        for attempt in range(1, 7):
            try:
                urllib.request.urlretrieve(DL.format(path=path), tmp)
                break
            except urllib.error.HTTPError as exc:
                if exc.code != 429 or attempt == 6:
                    raise
                wait = 30 * attempt
                print(f"    HTTP 429; retry {attempt}/5 in {wait}s", flush=True)
                time.sleep(wait)
        got = tmp.stat().st_size
        if got != size:
            print(f"    WARNING size {got} != indexed {size}")
        tmp.rename(dest)
        time.sleep(15)  # be a good citizen; the host throttled us once already

    files = sorted(OUT.glob("*.mzML"))
    man = Manifest.build(
        source=f"MassIVE {cfg['accession']}",
        pin={"accession": cfg["accession"], "campaign": cfg["campaign"],
             "mixes": sorted(mixes), "modes": sorted(modes),
             "index_source": INDEX},
        root=OUT, paths=files,
    )
    man.write(ROOT / "artifacts" / "MANIFEST_mzml.json")
    print(f"\n{len(files)} files, {man.total_bytes/1e9:.2f} GB, "
          f"digest={man.corpus_digest()[:16]}...")


if __name__ == "__main__":
    main()
