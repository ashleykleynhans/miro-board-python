"""Shared pytest fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def clear_miro_env(monkeypatch):
    """Prevent ambient MIRO_* variables from leaking into tests."""
    monkeypatch.delenv("MIRO_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("MIRO_BOARD_ID", raising=False)
