"""Hash verification for the frozen WUR Zenodo release.

Source: Zenodo record 20552933, WUR Mass Spectral Library v1.0, 2026-06-05.
DOI: 10.5281/zenodo.20552933. Licence: CC-BY 4.0.
Whole-archive: 203,752,342 bytes,
sha256 96fe2b1a6c5bcb441ee980b602e58f1b296af09b4eb9b99d56b92d44c03333d2.

Per-file hashes below were computed once, at retrieval, against the frozen
release. A hash mismatch here means the local copy is not that release.
"""
import hashlib
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_FILES = {
    "ETE organic environmental pollutants mass spectral library_NEG_v1.db":
        "13cf566e7c30d9618cb167cb7ff4831cc39e9bb91329fcb14ad15881154b2d90",
    "ETE organic environmental pollutants mass spectral library_NEG_v1.msp":
        "ae4cf59f1e8ff8d60565868b16114684969319274764d5ca4452be4096db388a",
    "ETE organic environmental pollutants mass spectral library_POS_v1.db":
        "79efdfe960abb817d0ca305f99fac1f68d82891cc041a554177fcc88cea5fb68",
    "ETE organic environmental pollutants mass spectral library_POS_v1.msp":
        "f6eff56da0dee73fdb7e33b13eb2a74decdc2b80fd44e334ee1d5816e847f299",
    "FCH food small molecules mass spectral library_NEG_v1.db":
        "f803be723608928f3e63f66f71960b7af2cb26d49013be7294064b8b888ee093",
    "FCH food small molecules mass spectral library_NEG_v1.msp":
        "88a6762a5f2bf41b0bc12fb3d85ec11ec75e4e4307eea3c852f8da8b72b50e50",
    "FCH food small molecules mass spectral library_POS_v1.db":
        "dbc7ffdeeb61bb9018cc6155b62bd67624420d1c01b5d1446f6f3a283700b337",
    "FCH food small molecules mass spectral library_POS_v1.msp":
        "47e6eb23dbb1174f5272c6e08d7cb979887d06ccf9707c1eaaea440624c5d052",
    # NOTE: this filename carries the release's own stray space before
    # "_NEG" -- preserved verbatim, not a typo introduced here.
    "WFSR Polar substances mass spectral library _NEG_v1.db":
        "c54473705c2d04f78cfea22ed40b0c5009efb4c135c1f08af457c7ecec07ab6d",
    "WFSR Polar substances mass spectral library_NEG_v1.msp":
        "4bb4a44ff3547f5018d4e68ce8f992ccddff675260494b687cb0fdc577a60704",
    "WFSR Polar substances mass spectral library_POS_v1.db":
        "2ca9722cab4c68dd886f770f824c83caeaf84018bdaf1189fcca35955e7ca67a",
    "WFSR Polar substances mass spectral library_POS_v1.msp":
        "f68eabc09361ac0e60e9e410d01216c783f3f2d023b99b2d2b40fa831e4f7146",
    "WFSR food safety mass spectral library_NEG_v1.db":
        "f366abc53ae95710e46a19641386f0c79502a5169b781de6dde0fa5b79a4e3c8",
    "WFSR food safety mass spectral library_NEG_v1.msp":
        "a0b76f95d124a115c7329e1726054e8231d49818ab75990653357fc95c332d15",
    "WFSR food safety mass spectral library_POS_v1.db":
        "8417e5c95554b0ec026446bbd7135b4d0ff707c5ff25b8a1e6ec89895b93b759",
    "WFSR food safety mass spectral library_POS_v1.msp":
        "927ed3e358874916031504a180034ed689b17b1d3f7eb97e10d770c60d0c602d",
    "WUR mass spectral library_NEG_v1.db":
        "998eb80129db97dc94abf8feccbc7ab9c40c86cf0650e0fc99b3981816b03dd9",
    "WUR mass spectral library_NEG_v1.msp":
        "77341c91f1d541be11996f3e18fa328978aaa31d661d58c701215732cef7f009",
    "WUR mass spectral library_POS_v1.db":
        "dde1e0cc5fc16fb3f575821ad26d9478fbf1d415273135a3593556bc2cae910e",
    "WUR mass spectral library_POS_v1.msp":
        "cca14c5afce38c2fa0727cdaed774f89393b748ce0f30cd164e735586e33b068",
}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(data_dir: Path) -> dict:
    """Verify every file in EXPECTED_FILES is present under `data_dir` with
    the pinned hash. Never raises -- callers check `missing` and
    `hash_mismatches` and decide whether to fail."""
    files, mismatches, missing = [], [], []
    for name, expected_hash in sorted(EXPECTED_FILES.items()):
        path = data_dir / name
        if not path.exists():
            missing.append(name)
            continue
        actual_hash = sha256_of(path)
        if actual_hash != expected_hash:
            mismatches.append(name)
        files.append({
            "path": name,
            "sha256": actual_hash,
            "size_bytes": path.stat().st_size,
            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        })
    return {
        "source": "Zenodo record 20552933, WUR Mass Spectral Library v1.0",
        "doi": "10.5281/zenodo.20552933",
        "licence": "CC-BY 4.0",
        "root": "data/external/wur",
        "files": files,
        "n_files": len(files),
        "n_expected": len(EXPECTED_FILES),
        "missing": missing,
        "hash_mismatches": mismatches,
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
