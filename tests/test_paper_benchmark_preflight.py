from muru.paper_benchmark.artifacts import build_partition
from muru.paper_benchmark.governance import ImplementationLock
from muru.paper_benchmark.preflight import run_preflight


def test_preflight_records_development_only_and_pending_engine(tmp_path):
    build_partition("development", tmp_path)
    report = run_preflight(tmp_path, ImplementationLock.pending())

    assert report.partition == "development"
    assert report.case_count == 80
    assert report.engine_status == "not_run_pending_lock"
    assert report.complete is False
    assert report.held_out_accessed is False
