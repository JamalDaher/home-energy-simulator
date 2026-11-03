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
