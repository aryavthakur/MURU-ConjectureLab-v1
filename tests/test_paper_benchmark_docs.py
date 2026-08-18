from pathlib import Path


AMENDMENT = Path("MURU_PAPER_BENCHMARK_AMENDMENT_A1_ADEQUACY.md")


def test_metrics_document_states_corrected_gates_and_denominators():
    text = Path("MURU_PAPER_BENCHMARK_METRICS.md").read_text()
    assert "164" in text and "144" in text and "36" in text
    assert "lower 95% Wilson bound >= 0.70" in text
    assert "upper 95% Wilson bound <= 0.15" in text
    assert "F19C" in text and "not applicable" in text


def test_metrics_document_binds_the_adequacy_endpoint_scoring_rule():
    text = Path("MURU_PAPER_BENCHMARK_METRICS.md").read_text()
    assert "Amendment A1" in text
    assert "M0_NOT_REJECTED" in text
    assert "M1 sensitivity" in text and "M2 sensitivity" in text and "M3 sensitivity" in text


def test_amendment_a1_records_its_provenance_and_contamination_status():
    text = AMENDMENT.read_text()
    assert "d94d2c9" in text
    assert "BENCHMARK CONTENT FREEZE V1" in text
    assert "EFFECTIVE BENCHMARK CONTENT FREEZE" in text
    assert "pre-execution" in text
    assert "No Development scientific outcome and no Held-out" in text
    assert "Historical benchmark changes.** None beyond this prospective rule completion" in text


def test_amendment_a1_binds_the_five_missing_decisions():
    text = AMENDMENT.read_text()
    assert "leave-one-energy-out" in text
    assert "MAE_k,i <= 0.90 * MAE_0,i" in text
    assert "at least **24 of 30**" in text and "at least **20**" in text
    assert "Binomial(30, 0.5)] = 0.049369" in text
    assert "at least **5 observed distinct" in text
    assert "BOUNDARY_LIMITED" in text


def test_amendment_a1_preserves_the_frozen_g1_thresholds():
    text = AMENDMENT.read_text()
    assert "Spearman(log g_hat, log g) >= 0.80" in text
    assert "`<= 0.80` of the per-energy baseline MAE" in text
    assert "Wilson lower-bound threshold `>= 0.70`" in text


def test_freeze_record_names_both_content_freeze_versions():
    text = Path("MURU_PAPER_BENCHMARK_FREEZE.md").read_text()
    assert "ORIGINAL BENCHMARK CONTENT FREEZE V1" in text and "d94d2c9" in text
    assert "EFFECTIVE BENCHMARK CONTENT FREEZE" in text
    assert "benchmark-content-freeze-a1" in text
    assert "PENDING_LOCK" in text
