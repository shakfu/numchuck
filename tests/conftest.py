"""Pytest configuration and fixtures."""

import sys

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "realtime: marks tests requiring real audio hardware (skipped on CI)"
    )
    config.addinivalue_line(
        "markers", "asyncio: marks tests as async"
    )
    config.addinivalue_line(
        "markers", "tui: marks tests requiring a terminal/console (skipped on CI)"
    )


def pytest_collection_modifyitems(config, items):
    """Skip TUI tests on Windows due to prompt_toolkit console issues."""
    if sys.platform == "win32":
        skip_tui = pytest.mark.skip(reason="TUI tests not supported on Windows")
        for item in items:
            if "tui" in item.keywords:
                item.add_marker(skip_tui)


@pytest.fixture
def free_port() -> int:
    """A loopback TCP port that was free when the test started."""
    import socket

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture
def unraisable(monkeypatch):
    """Exceptions reported to sys.unraisablehook during the test."""
    seen = []
    monkeypatch.setattr(sys, "unraisablehook", seen.append)
    return seen
