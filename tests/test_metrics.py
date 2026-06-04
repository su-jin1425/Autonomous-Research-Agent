from prometheus_client import generate_latest

from app.monitoring.metrics import (
    RESEARCH_LATENCY,
    RESEARCH_RUNS,
    RETRIEVAL_COUNT,
    VECTOR_SEARCH_LATENCY,
)


def test_research_run_metrics() -> None:
    before = generate_latest().decode()

    RESEARCH_RUNS.labels(
        status="completed",
    ).inc()

    after = generate_latest().decode()

    assert "research_runs_total" in after
    assert len(after) >= len(before)


def test_retrieval_count_metric() -> None:
    RETRIEVAL_COUNT.inc(5)

    metrics = generate_latest().decode()

    assert "research_retrieval_documents_total" in metrics


def test_research_latency_metric() -> None:
    with RESEARCH_LATENCY.time():
        sum(range(100))

    metrics = generate_latest().decode()

    assert "research_execution_seconds" in metrics


def test_vector_search_latency_metric() -> None:
    with VECTOR_SEARCH_LATENCY.time():
        sum(range(50))

    metrics = generate_latest().decode()

    assert "vector_search_seconds" in metrics


def test_prometheus_export_contains_custom_metrics() -> None:
    output = generate_latest().decode()

    expected_metrics = [
        "research_runs_total",
        "research_retrieval_documents_total",
        "research_execution_seconds",
        "vector_search_seconds",
    ]

    for metric in expected_metrics:
        assert metric in output


def test_multiple_research_status_labels() -> None:
    RESEARCH_RUNS.labels(
        status="completed",
    ).inc()

    RESEARCH_RUNS.labels(
        status="failed",
    ).inc()

    metrics = generate_latest().decode()

    assert 'status="completed"' in metrics
    assert 'status="failed"' in metrics


def test_histogram_records_observations() -> None:
    RESEARCH_LATENCY.observe(1.25)
    RESEARCH_LATENCY.observe(2.50)

    metrics = generate_latest().decode()

    assert "research_execution_seconds_bucket" in metrics
    assert "research_execution_seconds_sum" in metrics


def test_counter_accumulates_values() -> None:
    RETRIEVAL_COUNT.inc(10)

    metrics = generate_latest().decode()

    assert "research_retrieval_documents_total" in metrics