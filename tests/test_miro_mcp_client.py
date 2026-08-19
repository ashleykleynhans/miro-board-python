"""Tests for the miro_mcp shared client."""

import pytest

import miro_mcp.client as client
from miro_client import MiroClient
from miro_mcp.errors import MiroMCError


def test_miro_mc_error_is_runtime_error():
    assert issubclass(MiroMCError, RuntimeError)


def test_get_client_creates_and_caches():
    try:
        c1 = client.get_client()
        assert isinstance(c1, MiroClient)
        assert client.get_client() is c1
    finally:
        client.reset_client()


def test_reset_client_forces_new_instance():
    try:
        c1 = client.get_client()
        client.reset_client()
        c2 = client.get_client()
        assert c1 is not c2
    finally:
        client.reset_client()


def test_require_board_id_uses_argument():
    assert client.require_board_id("arg-board") == "arg-board"


def test_require_board_id_uses_env(monkeypatch):
    monkeypatch.setenv("MIRO_BOARD_ID", "env-board")
    assert client.require_board_id(None) == "env-board"


def test_require_board_id_missing_raises():
    with pytest.raises(ValueError, match="missing board id"):
        client.require_board_id(None)
