from muru.paper_benchmark.freeze import prepare_content_freeze
from muru.paper_benchmark.governance import ImplementationLock


def test_content_freeze_preparation_waits_for_locked_implementation(tmp_path):
    prepared = prepare_content_freeze(tmp_path, ImplementationLock.pending(), {"complete": False})

    assert prepared.status == "WAITING_FOR_LOCKED_IMPLEMENTATION"
    assert prepared.final_executable_freeze is False
