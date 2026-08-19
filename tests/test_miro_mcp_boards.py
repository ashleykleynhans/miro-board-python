"""Tests for the board read tools."""

import pytest

from miro_mcp.tools import boards
from tests.helpers import FakeResponse, install_session


def test_list_boards(monkeypatch, miro_mcp_env):
    install_session(
        monkeypatch,
        [FakeResponse(200, {"data": [{"id": "b1", "name": "Board"}], "cursor": None})],
    )
    assert boards.list_boards() == [{"id": "b1", "name": "Board"}]


def test_get_board(monkeypatch, miro_mcp_env):
    install_session(monkeypatch, [FakeResponse(200, {"id": "board-123", "name": "B"})])
    assert boards.get_board()["name"] == "B"


def test_get_board_missing_id_raises(monkeypatch):
    install_session(monkeypatch)
    with pytest.raises(ValueError, match="missing board id"):
        boards.get_board(None)
