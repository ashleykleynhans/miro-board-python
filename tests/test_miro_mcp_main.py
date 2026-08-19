"""Tests for the miro_mcp server entry point."""

import logging

import pytest

import miro_mcp
from miro_mcp import main
from miro_mcp.errors import MiroMCError


class _FakeMCP:
    def __init__(self):
        self.transport = None

    def run(self, transport=None, mount_path=None):
        self.transport = transport


def _set_token(monkeypatch, value):
    monkeypatch.setattr("miro_mcp.ACCESS_TOKEN", value)


def test_server_entry_reexports_main():
    import server

    assert callable(server.main)


def test_main_runs_stdio(monkeypatch):
    _set_token(monkeypatch, "tok")
    monkeypatch.delenv("MIRO_MCP_TRANSPORT", raising=False)
    fake = _FakeMCP()
    monkeypatch.setattr("miro_mcp.create_mcp", lambda: fake)
    main()
    assert fake.transport == "stdio"


def test_main_runs_sse(monkeypatch):
    _set_token(monkeypatch, "tok")
    monkeypatch.setenv("MIRO_MCP_TRANSPORT", "sse")
    fake = _FakeMCP()
    monkeypatch.setattr("miro_mcp.create_mcp", lambda: fake)
    main()
    assert fake.transport == "sse"


def test_main_runs_streamable_http(monkeypatch):
    _set_token(monkeypatch, "tok")
    monkeypatch.setenv("MIRO_MCP_TRANSPORT", "streamable-http")
    fake = _FakeMCP()
    monkeypatch.setattr("miro_mcp.create_mcp", lambda: fake)
    main()
    assert fake.transport == "streamable-http"


def test_main_missing_token_raises(monkeypatch):
    _set_token(monkeypatch, "")
    with pytest.raises(MiroMCError):
        main()


def test_main_invalid_transport_raises(monkeypatch):
    _set_token(monkeypatch, "tok")
    monkeypatch.setenv("MIRO_MCP_TRANSPORT", "bogus")
    with pytest.raises(MiroMCError):
        main()


def test_main_configures_logging_once(monkeypatch):
    _set_token(monkeypatch, "tok")
    monkeypatch.delenv("MIRO_MCP_TRANSPORT", raising=False)
    fake = _FakeMCP()
    monkeypatch.setattr("miro_mcp.create_mcp", lambda: fake)
    logger = logging.getLogger("miro_mcp")
    logger.handlers.clear()
    main()
    assert logger.handlers
    main()
    assert len(logger.handlers) == 1
    logger.handlers.clear()


def test_configure_logging_invalid_level(monkeypatch):
    monkeypatch.setenv("MIRO_MCP_LOG_LEVEL", "Bogus")
    logger = logging.getLogger("miro_mcp")
    logger.handlers.clear()
    miro_mcp._configure_logging()
    assert logger.level == logging.WARNING
    logger.handlers.clear()
