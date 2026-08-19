"""Tests for the item tools."""

import pytest

from miro_mcp.tools import items
from tests.helpers import FakeResponse, install_session


def test_list_items(monkeypatch, miro_mcp_env):
    payload = {
        "data": [
            {"id": "i1", "type": "sticky_note", "data": {"content": "a"}},
            {"id": "i2", "type": "card", "data": {"title": "b"}},
        ],
        "cursor": None,
    }
    install_session(monkeypatch, [FakeResponse(200, payload)])
    assert [i["id"] for i in items.list_items()] == ["i1", "i2"]


def test_list_items_filtered(monkeypatch, miro_mcp_env):
    payload = {
        "data": [
            {"id": "i1", "type": "sticky_note", "data": {"content": "a"}},
            {"id": "i2", "type": "card", "data": {"title": "b"}},
        ],
        "cursor": None,
    }
    install_session(monkeypatch, [FakeResponse(200, payload)])
    result = items.list_items("b", item_type="card")
    assert [i["id"] for i in result] == ["i2"]


def test_list_items_missing_board_id(monkeypatch):
    install_session(monkeypatch)
    with pytest.raises(ValueError, match="missing board id"):
        items.list_items(None)


def test_get_item(monkeypatch, miro_mcp_env):
    install_session(monkeypatch, [FakeResponse(200, {"id": "i1", "type": "card"})])
    assert items.get_item("i1")["id"] == "i1"


def test_create_item(monkeypatch, miro_mcp_env):
    session = install_session(monkeypatch, [FakeResponse(200, {"id": "n1", "type": "sticky_note"})])
    result = items.create_item("sticky_note", data={"content": "hi"}, board_id="board-123")
    assert result["id"] == "n1"
    assert session.calls[0]["method"] == "POST"
    assert session.calls[0]["url"] == "/boards/board-123/sticky_notes"
    assert session.calls[0]["json"] == {"data": {"content": "hi"}}


def test_update_item(monkeypatch, miro_mcp_env):
    session = install_session(monkeypatch, [FakeResponse(200, {"id": "i1"})])
    items.update_item("i1", item_type="card", data={"title": "new"})
    assert session.calls[0]["method"] == "PATCH"
    assert session.calls[0]["url"] == "/boards/board-123/cards/i1"


def test_delete_item(monkeypatch, miro_mcp_env):
    install_session(monkeypatch, [FakeResponse(204)])
    assert items.delete_item("i1") == {"deleted_item_id": "i1"}


def test_set_text(monkeypatch, miro_mcp_env):
    session = install_session(monkeypatch, [FakeResponse(200, {"id": "i1"})])
    items.set_text("i1", "updated")
    assert session.calls[0]["method"] == "PATCH"
    assert session.calls[0]["url"] == "/boards/board-123/sticky_notes/i1"


def test_set_color(monkeypatch, miro_mcp_env):
    session = install_session(monkeypatch, [FakeResponse(200, {"id": "i1"})])
    items.set_color("i1", "light_blue", item_type="sticky_note")
    assert session.calls[0]["json"] == {"style": {"fillColor": "light_blue"}}


def test_resize_item(monkeypatch, miro_mcp_env):
    session = install_session(monkeypatch, [FakeResponse(200, {"id": "i1"})])
    items.resize_item("i1", width=300, height=200, item_type="shape")
    assert session.calls[0]["json"] == {"geometry": {"width": 300, "height": 200}}


def test_move_item(monkeypatch, miro_mcp_env):
    session = install_session(monkeypatch, [FakeResponse(200, {"id": "i1"})])
    items.move_item("i1", x=10, y=20)
    assert session.calls[0]["json"] == {"position": {"x": 10, "y": 20}}


def test_add_to_frame(monkeypatch, miro_mcp_env):
    session = install_session(monkeypatch, [FakeResponse(200, {"id": "i1"})])
    items.add_to_frame("f1", "i1")
    assert session.calls[0]["json"] == {"parent": {"id": "f1"}}
