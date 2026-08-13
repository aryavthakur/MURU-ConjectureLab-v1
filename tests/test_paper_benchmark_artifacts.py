import json

from muru.paper_benchmark.artifacts import build_partition, verify_hash_inventory


def test_development_build_writes_reconstructible_hashes(tmp_path):
    receipt = build_partition("development", tmp_path)

    assert receipt.case_count == 80
    assert verify_hash_inventory(tmp_path) == receipt.hashes
    partition_manifest = json.loads((tmp_path / "paper_benchmark_partition_manifest.json").read_text())
    assert partition_manifest["partitions"]["development"]["case_count"] == 80


def test_development_build_writes_no_held_out_case_file(tmp_path):
    build_partition("development", tmp_path)

    assert not (tmp_path / "inputs" / "held_out.jsonl").exists()
    assert not (tmp_path / "truth" / "held_out.jsonl").exists()
