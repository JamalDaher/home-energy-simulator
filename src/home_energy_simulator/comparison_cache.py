"""Validation for comparison results retained across app deployments."""

REQUIRED_COMPARISON_COLUMNS = frozenset({
    "Configuration", "Demand served (%)", "First unmet hour",
    "Generator hours", "Final battery charge (%)", "Fuel cost ($)",
    "Equipment + installation ($)", "Modeled outage cost ($)",
    "Annual operating cost ($)", "5-year ownership ($)",
    "10-year ownership ($)", "20-year ownership ($)",
})


def is_current_comparison_table(table):
    """Return False for missing, obsolete or malformed cached results."""
    if table is None or not hasattr(table, "columns"):
        return False
    try:
        return REQUIRED_COMPARISON_COLUMNS.issubset(set(table.columns)) and len(table) > 0
    except (TypeError, ValueError):
        return False
