"""Integration test verifying all 8 Streamlit dashboard sections render without exception."""

from __future__ import annotations

from streamlit.testing.v1 import AppTest


def test_all_eight_dashboard_sections_render():
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert not at.exception
    for idx in range(1, 8):
        at.sidebar.radio[0].set_value(at.sidebar.radio[0].options[idx]).run()
        assert not at.exception
