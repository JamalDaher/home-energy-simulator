"""Regression coverage for comparison cache after deployments."""

from home_energy_simulator.comparison_cache import (
    REQUIRED_COMPARISON_COLUMNS,
    is_current_comparison_table,
)


class FakeTable:
    def __init__(self, columns, rows=3):
        self.columns = columns
        self.rows = rows

    def __len__(self):
        return self.rows


def test_current_comparison_schema_is_accepted():
    assert is_current_comparison_table(FakeTable(list(REQUIRED_COMPARISON_COLUMNS)))


def test_previous_schema_is_rejected():
    previous = REQUIRED_COMPARISON_COLUMNS - {"10-year ownership ($)"}
    assert not is_current_comparison_table(FakeTable(previous))


def test_missing_visualization_column_is_rejected():
    previous = REQUIRED_COMPARISON_COLUMNS - {"First unmet hour"}
    assert not is_current_comparison_table(FakeTable(previous))


def test_empty_table_is_rejected():
    assert not is_current_comparison_table(FakeTable(REQUIRED_COMPARISON_COLUMNS, rows=0))


def test_missing_or_malformed_cache_is_rejected():
    assert not is_current_comparison_table(None)
    assert not is_current_comparison_table({})
