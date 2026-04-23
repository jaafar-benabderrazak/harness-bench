from harness_eng.cost_estimator import estimate_matrix, format_estimate


def test_estimate_shape_paid_model():
    """For a paid model, total > 0 and safety multiplier applies."""
    est = estimate_matrix(n_tasks=5, n_seeds=1, model="claude-sonnet-4-6")
    assert est["n_tasks"] == 5
    assert est["n_seeds"] == 1
    assert len(est["rows"]) == 5
    assert est["total_usd"] > 0
    assert est["total_usd_with_safety"] == est["total_usd"] * est["safety"]


def test_estimate_shape_ollama_is_free():
    """Ollama-hosted models are priced $0 — total should be exactly $0."""
    est = estimate_matrix(n_tasks=5, n_seeds=1, model="mistral:7b")
    assert est["total_usd"] == 0.0
    assert all(row["cost_usd"] == 0.0 for row in est["rows"])


def test_format_is_printable():
    est = estimate_matrix(n_tasks=5, n_seeds=1, model="claude-sonnet-4-6")
    text = format_estimate(est)
    assert "Projected total" in text
    assert "harness" in text
