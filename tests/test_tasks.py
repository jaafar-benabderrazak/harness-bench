from harness_eng.config import FIXTURES_DIR
from harness_eng.tasks.loader import load_tasks


def test_tasks_load():
    tasks = load_tasks()
    assert len(tasks) == 5
    for t in tasks:
        assert t.id
        assert t.fields
        assert t.expected
        assert set(t.fields) == set(t.expected.keys())
        assert (FIXTURES_DIR / t.html_path).exists(), f"missing fixture for {t.id}"


def test_expected_field_counts():
    tasks = load_tasks()
    for t in tasks:
        assert len(t.fields) >= 3, f"task {t.id} has too few fields to be interesting"
