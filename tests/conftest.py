"""Shared pytest fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def clear_miro_env(monkeypatch):
    """Prevent ambient MIRO_* variables from leaking into tests."""
    monkeypatch.delenv("MIRO_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("MIRO_BOARD_ID", raising=False)


@pytest.fixture()
def miro_mcp_env(monkeypatch):
    """Set a token/board and reset the cached MCP client around a test."""
    monkeypatch.setenv("MIRO_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("MIRO_BOARD_ID", "board-123")
    import miro_mcp.client as client

    client.reset_client()
    yield "board-123"
    client.reset_client()
