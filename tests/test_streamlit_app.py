"""Smoke-test the Streamlit page beyond the server health endpoint.

Streamlit's AppTest executes the script and reports widget/runtime exceptions
without requiring a browser or an external deployed application.
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_initial_render_without_exceptions():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=45)
    app.run()
    assert not app.exception, "\n".join(str(error.message) for error in app.exception)


def test_generator_only_mode_rerenders_without_exceptions():
    """Regression: switching to generator-only must not crash zero-battery paths."""
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=45).run()
    assert not app.exception, "\n".join(str(error.message) for error in app.exception)
    controls = [item for item in app.checkbox if item.label == "Generator-only mode"]
    assert len(controls) == 1, "Generator-only mode control was not found"
    app = controls[0].set_value(True).run()
    assert not app.exception, "\n".join(str(error.message) for error in app.exception)
