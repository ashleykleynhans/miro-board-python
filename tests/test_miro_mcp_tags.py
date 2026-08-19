"""Tests for the tag tools."""

from miro_mcp.tools import tags
from tests.helpers import FakeResponse, install_session


def test_list_tags(monkeypatch, miro_mcp_env):
    install_session(
        monkeypatch,
        [FakeResponse(200, {"data": [{"id": "t1", "title": "urgent"}], "cursor": None})],
    )
    assert tags.list_tags() == [{"id": "t1", "title": "urgent"}]


def test_create_tag(monkeypatch, miro_mcp_env):
    session = install_session(monkeypatch, [FakeResponse(200, {"id": "t1"})])
    tags.create_tag("urgent", fill_color="red")
    assert session.calls[0]["url"] == "/boards/board-123/tags"
    assert session.calls[0]["json"] == {"title": "urgent", "fillColor": "red"}


def test_assign_tag(monkeypatch, miro_mcp_env):
    session = install_session(monkeypatch, [FakeResponse(200, {"id": "i1"})])
    tags.assign_tag("i1", "t1")
    assert session.calls[0]["method"] == "POST"
    assert session.calls[0]["url"] == "/boards/board-123/items/i1"
    assert session.calls[0]["params"] == {"tag_id": "t1"}
