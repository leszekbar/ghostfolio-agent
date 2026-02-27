"""Minimal test to verify app package is importable."""

import app


def test_app_imports():
    """App package can be imported."""
    assert app is not None
