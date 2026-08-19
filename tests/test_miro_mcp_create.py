"""Tests for the create tools."""

from miro_mcp.tools import create
from tests.helpers import FakeResponse, install_session


def test_create_sticky_note(monkeypatch, miro_mcp_env):
    session = install_session(monkeypatch, [FakeResponse(200, {"id": "n1"})])
    create.create_sticky_note("Hello", x=1, y=2)
    call = session.calls[0]
    assert call["url"] == "/boards/board-123/sticky_notes"
    assert call["json"]["data"] == {"content": "Hello"}
    assert call["json"]["position"] == {"x": 1, "y": 2, "origin": "center"}


def test_create_card(monkeypatch, miro_mcp_env):
    session = install_session(monkeypatch, [FakeResponse(200, {"id": "c1"})])
    create.create_card("Task", description="Do it")
    call = session.calls[0]
    assert call["url"] == "/boards/board-123/cards"
    assert call["json"]["data"] == {
        "title": "Task",
        "description": "Do it",
        "assigneeId": None,
    }


def test_create_text(monkeypatch, miro_mcp_env):
    session = install_session(monkeypatch, [FakeResponse(200, {"id": "t1"})])
    create.create_text("Notes")
    assert session.calls[0]["url"] == "/boards/board-123/texts"
    assert session.calls[0]["json"]["data"] == {"content": "Notes"}


def test_create_shape(monkeypatch, miro_mcp_env):
    session = install_session(monkeypatch, [FakeResponse(200, {"id": "s1"})])
    create.create_shape("Decision", shape_type="rhombus")
    call = session.calls[0]
    assert call["url"] == "/boards/board-123/shapes"
    assert call["json"]["data"] == {"content": "Decision", "shape": "rhombus"}


def test_create_frame(monkeypatch, miro_mcp_env):
    session = install_session(monkeypatch, [FakeResponse(200, {"id": "f1"})])
    create.create_frame("Section", width=1000)
    call = session.calls[0]
    assert call["url"] == "/boards/board-123/frames"
    assert call["json"]["geometry"] == {"width": 1000, "height": 600}


def test_create_image(monkeypatch, miro_mcp_env):
    session = install_session(monkeypatch, [FakeResponse(200, {"id": "im1"})])
    create.create_image("https://example.com/pic.png", width=400, height=300)
    call = session.calls[0]
    assert call["url"] == "/boards/board-123/images"
    assert call["json"]["data"] == {"imageUrl": "https://example.com/pic.png"}


def test_create_document(monkeypatch, miro_mcp_env):
    session = install_session(monkeypatch, [FakeResponse(200, {"id": "d1"})])
    create.create_document("Spec", "https://example.com/doc")
    assert session.calls[0]["url"] == "/boards/board-123/documents"


def test_create_embed(monkeypatch, miro_mcp_env):
    session = install_session(monkeypatch, [FakeResponse(200, {"id": "e1"})])
    create.create_embed("https://example.com", width=600)
    call = session.calls[0]
    assert call["url"] == "/boards/board-123/embeds"
    assert call["json"]["geometry"] == {"width": 600, "height": 320}


def test_create_connector(monkeypatch, miro_mcp_env):
    session = install_session(monkeypatch, [FakeResponse(200, {"id": "co1"})])
    create.create_connector("a", "b", caption="links to")
    call = session.calls[0]
    assert call["url"] == "/boards/board-123/connectors"
    assert call["json"]["startItem"] == {"id": "a"}
    assert call["json"]["endItem"] == {"id": "b"}
    assert call["json"]["captions"] == [{"text": "links to"}]
