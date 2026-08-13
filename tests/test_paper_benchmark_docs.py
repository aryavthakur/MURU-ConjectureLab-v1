from pathlib import Path


def test_metrics_document_states_corrected_gates_and_denominators():
    text = Path("MURU_PAPER_BENCHMARK_METRICS.md").read_text()
    assert "164" in text and "144" in text and "36" in text
    assert "lower 95% Wilson bound >= 0.70" in text
    assert "upper 95% Wilson bound <= 0.15" in text
    assert "F19C" in text and "not applicable" in text
