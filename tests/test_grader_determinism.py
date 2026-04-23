"""Golden-trace determinism: grading the same input 100x yields byte-identical output.

Pins the hardened _norm pipeline (NFC -> strip -> casefold -> ASCII-ws-collapse)
against German-ß, NFC-vs-NFD composed graphemes, and whitespace edges.
"""
from __future__ import annotations

import json

from harness_eng.grader import grade


GOLDEN_CASES = [
    ({"name": "Hello World"}, {"name": "hello world"}, True),
    ({"name": "  HELLO\tWORLD\n"}, {"name": "hello world"}, True),
    # casefold normalizes ß -> ss; .lower() would keep ß and mismatch
    ({"greeting": "straße"}, {"greeting": "strasse"}, True),
    # NFC collapses NFD composition
    ({"word": "café"}, {"word": "café"}, True),
    ({"a": "foo"}, {"a": "bar"}, False),
]


def test_golden_cases():
    for predicted, expected, expect_success in GOLDEN_CASES:
        r = grade(predicted, expected)
        assert r.success is expect_success, (
            f"case failed: predicted={predicted!r} expected={expected!r} "
            f"got success={r.success!r} want {expect_success!r}"
        )


def test_100x_determinism():
    """Same input graded 100 times — all result dicts byte-identical when serialized."""
    predicted = {"name": "  Hello  WORLD  ", "price": "19.99"}
    expected = {"name": "hello world", "price": "19.99"}
    results = [grade(predicted, expected) for _ in range(100)]
    serialized = {
        json.dumps(
            {
                "per_field": r.per_field,
                "field_accuracy": r.field_accuracy,
                "success": r.success,
            },
            sort_keys=True,
        )
        for r in results
    }
    assert len(serialized) == 1, f"grader non-deterministic: {len(serialized)} distinct outputs"
