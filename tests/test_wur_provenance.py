import hashlib
from pathlib import Path

from muru.io.wur_provenance import canonical_key_hash, environment_provenance

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_key_hash_is_sha256_of_sorted_keys_joined_by_newline():
    keys = ["BBB", "AAA", "CCC"]
    expected = hashlib.sha256("AAA\nBBB\nCCC".encode("utf-8")).hexdigest()
    assert canonical_key_hash(keys) == expected


def test_canonical_key_hash_ignores_input_order():
    assert canonical_key_hash(["B", "A"]) == canonical_key_hash(["A", "B"])


def test_canonical_key_hash_of_an_empty_list_is_the_empty_string_hash():
    assert canonical_key_hash([]) == hashlib.sha256(b"").hexdigest()


def test_canonical_key_hash_distinguishes_different_key_sets():
    assert canonical_key_hash(["A", "B"]) != canonical_key_hash(["A", "C"])


def test_environment_provenance_records_every_required_library():
    env = environment_provenance(ROOT)
    assert set(env) >= {
        "python", "rdkit", "pandas", "numpy", "scipy", "pyarrow",
        "git_commit_sha", "wur_retrieval_manifest_sha256",
    }
    for field in ("python", "rdkit", "pandas", "numpy", "scipy", "pyarrow"):
        assert isinstance(env[field], str) and env[field]


def test_environment_provenance_hashes_the_real_retrieval_manifest():
    env = environment_provenance(ROOT)
    raw = (ROOT / "artifacts" / "wur_retrieval_manifest.json").read_bytes()
    assert env["wur_retrieval_manifest_sha256"] == hashlib.sha256(raw).hexdigest()


def test_environment_provenance_is_json_serializable():
    import json
    json.dumps(environment_provenance(ROOT))
