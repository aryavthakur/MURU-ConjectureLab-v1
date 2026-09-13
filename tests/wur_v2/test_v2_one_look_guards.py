"""Historical one-look records cannot be overwritten, and v2 exposure is asserted."""
import pytest

from muru.wur_stage2 import holdcheck, population as POP, stage3
from muru.wur_v2 import exposure


def test_stage3_sealed_tables_refuses_second_call(tmp_path):
    with pytest.raises(POP.PopulationError, match="already accessed"):
        stage3.sealed_tables(tmp_path)


def test_holdcheck_refuses_second_run(tmp_path):
    with pytest.raises(POP.PopulationError, match="already scored"):
        holdcheck.run(tmp_path)


def test_wur_exposure_records_present():
    rec = exposure.assert_wur_exposed()
    assert rec["hold_status"] == "EXPOSED"
    assert rec["stage3_first_access"]["git_tree_dirty"] is False


def test_exposure_guard_fails_without_records(monkeypatch, tmp_path):
    monkeypatch.setattr(exposure, "STAGE3_FIRST_ACCESS", tmp_path / "absent.json")
    with pytest.raises(exposure.ExposureError):
        exposure.assert_wur_exposed()


def test_confirmation_keys_loaded():
    assert len(exposure.lcsb_confirmation_keys()) == 110
