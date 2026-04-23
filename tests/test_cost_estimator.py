from harness_eng.cost_estimator import estimate_matrix, format_estimate


def test_estimate_shape():
    est = estimate_matrix(n_tasks=5, n_seeds=1)
    assert est["n_tasks"] == 5
    assert est["n_seeds"] == 1
    assert len(est["rows"]) == 5
    assert est["total_usd"] > 0
    assert est["total_usd_with_safety"] == est["total_usd"] * est["safety"]


def test_format_is_printable():
    est = estimate_matrix(n_tasks=5, n_seeds=1)
    text = format_estimate(est)
    assert "Projected total" in text
    assert "harness" in text
