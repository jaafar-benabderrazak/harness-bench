from harness_eng.grader import grade


def test_exact_match_all_correct():
    r = grade({"a": "x", "b": "y"}, {"a": "x", "b": "y"})
    assert r.success is True
    assert r.field_accuracy == 1.0
    assert r.per_field == {"a": True, "b": True}


def test_normalization_whitespace_and_case():
    r = grade({"title": "  Hello  WORLD  "}, {"title": "hello world"})
    assert r.success is True


def test_partial_match():
    r = grade({"a": "x", "b": "wrong"}, {"a": "x", "b": "y"})
    assert r.success is False
    assert r.field_accuracy == 0.5
    assert r.per_field == {"a": True, "b": False}


def test_missing_field_counts_as_wrong():
    r = grade({"a": "x"}, {"a": "x", "b": "y"})
    assert r.success is False
    assert r.per_field["b"] is False


def test_none_prediction():
    r = grade(None, {"a": "x"})
    assert r.success is False
    assert r.field_accuracy == 0.0
