"""Tests for miro_client.MiroClient."""

from __future__ import annotations

import pytest

from helpers import FakeResponse, install_session
from miro_client import MiroClient, MiroError


def client_for(monkeypatch, responses=None):
    session = install_session(monkeypatch, responses)
    return MiroClient("test-token"), session


def test_get_board(monkeypatch):
    client, session = client_for(monkeypatch, [FakeResponse(200, {"id": "b", "name": "B"})])
    assert client.get_board("b") == {"id": "b", "name": "B"}
    assert session.calls[0]["url"] == "/boards/b"


def test_get_item(monkeypatch):
    client, _ = client_for(monkeypatch, [FakeResponse(200, {"id": "1"})])
    assert client.get_item("b", "1") == {"id": "1"}


def test_list_items(monkeypatch):
    client, session = client_for(monkeypatch, [FakeResponse(200, {"data": [{"id": "1"}]})])
    assert client.list_items("b") == [{"id": "1"}]
    assert session.calls[0]["params"] == {"limit": 50}


def test_paginates_with_cursor(monkeypatch):
    responses = [
        FakeResponse(200, {"data": [{"id": "1"}], "cursor": "next"}),
        FakeResponse(200, {"data": [{"id": "2"}]}),
    ]
    client, session = client_for(monkeypatch, responses)
    assert client.list_boards() == [{"id": "1"}, {"id": "2"}]
    assert session.calls[1]["params"]["cursor"] == "next"


def test_create_item_builds_body(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_item("b", "sticky_note", data={"content": "hi"}, position={"x": 1, "y": 2})
    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == "/boards/b/items"
    assert call["json"]["type"] == "sticky_note"
    assert call["json"]["data"] == {"content": "hi"}


def test_create_item_with_parent(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_item("b", "frame", parent_id="f1")
    assert session.calls[0]["json"]["parent"] == {"id": "f1"}


def test_update_item(monkeypatch):
    client, session = client_for(monkeypatch)
    client.update_item("b", "1", data={"content": "x"}, style={"fillColor": "red"})
    call = session.calls[0]
    assert call["method"] == "PATCH"
    assert call["url"] == "/boards/b/items/1"
    assert call["json"] == {"data": {"content": "x"}, "style": {"fillColor": "red"}}


def test_delete_returns_none(monkeypatch):
    client, session = client_for(monkeypatch, [FakeResponse(204)])
    assert client.delete_item("b", "1") is None
    assert session.calls[0]["method"] == "DELETE"


def test_retries_on_rate_limit(monkeypatch):
    slept: list = []
    monkeypatch.setattr("miro_client.time.sleep", lambda seconds: slept.append(seconds))
    responses = [
        FakeResponse(429, text="rate limited"),
        FakeResponse(200, {"ok": True}),
    ]
    client, _ = client_for(monkeypatch, responses)
    assert client.get_board("b") == {"ok": True}
    assert len(slept) == 1


def test_raises_miro_error_on_bad_status(monkeypatch):
    client, _ = client_for(monkeypatch, [FakeResponse(400, text="bad request")])
    with pytest.raises(MiroError) as exc:
        client.get_board("b")
    assert "HTTP 400" in str(exc.value)


def test_create_sticky_note(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_sticky_note("b", "Hello", x=10, y=20, color="light_blue")
    body = session.calls[0]["json"]
    assert body["type"] == "sticky_note"
    assert body["data"] == {"content": "Hello"}
    assert body["style"] == {"fillColor": "light_blue"}
    assert body["position"] == {"x": 10, "y": 20, "origin": "center"}
    assert body["geometry"] == {"width": 180}


def test_create_card_with_assignee(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_card("b", "T", description="D", assignee_id="9", x=1, y=2)
    assert session.calls[0]["json"]["data"] == {
        "title": "T",
        "description": "D",
        "assignee": {"id": "9"},
    }


def test_create_card_without_assignee(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_card("b", "T")
    assert session.calls[0]["json"]["data"] == {
        "title": "T",
        "description": "",
        "assignee": None,
    }


def test_create_text(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_text("b", "Notes", x=5, y=6, width=300)
    body = session.calls[0]["json"]
    assert body["type"] == "text"
    assert body["data"] == {"content": "Notes"}
    assert body["geometry"] == {"width": 300}


def test_create_shape(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_shape("b", "Decision", shape_type="diamond", fill_color="#f00", border_color="#00f")
    body = session.calls[0]["json"]
    assert body["type"] == "shape"
    assert body["data"] == {"content": "Decision", "shapeType": "diamond"}
    assert body["style"] == {"fillColor": "#f00", "borderColor": "#00f"}


def test_create_shape_defaults(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_shape("b")
    body = session.calls[0]["json"]
    assert body["data"] == {"content": "", "shapeType": "rectangle"}
    assert body["style"] == {"fillColor": "#ffffff", "borderColor": "#1a1a1a"}


def test_create_frame(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_frame("b", title="Sec", x=1, y=2, width=1000, height=700)
    body = session.calls[0]["json"]
    assert body["type"] == "frame"
    assert body["data"] == {"title": "Sec"}
    assert body["geometry"] == {"width": 1000, "height": 700}


def test_add_to_frame(monkeypatch):
    client, session = client_for(monkeypatch)
    client.add_to_frame("b", "f1", "1")
    call = session.calls[0]
    assert call["method"] == "PATCH"
    assert call["url"] == "/boards/b/items/1"
    assert call["json"] == {"parent": {"id": "f1"}}


def test_create_image_width_only(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_image("b", "https://x/p.png", width=400)
    assert session.calls[0]["json"]["geometry"] == {"width": 400, "height": 400}


def test_create_image_height_only(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_image("b", "https://x/p.png", height=300)
    assert session.calls[0]["json"]["geometry"] == {"width": 300, "height": 300}


def test_create_image_no_geometry(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_image("b", "https://x/p.png")
    assert "geometry" not in session.calls[0]["json"]


def test_create_document(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_document("b", "Spec", "https://x", preview_url="https://y")
    assert session.calls[0]["json"]["data"] == {
        "title": "Spec",
        "url": "https://x",
        "previewUrl": "https://y",
    }


def test_create_document_without_preview(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_document("b", "Spec", "https://x")
    assert session.calls[0]["json"]["data"] == {"title": "Spec", "url": "https://x"}


def test_create_embed(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_embed("b", "https://x")
    body = session.calls[0]["json"]
    assert body["type"] == "embed"
    assert body["data"] == {"url": "https://x", "mode": "inline"}
    assert body["geometry"] == {"width": 480, "height": 320}


def test_create_connector(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_connector("b", "1", "2", caption="links to")
    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == "/boards/b/connectors"
    assert call["json"]["startItem"] == {"id": "1"}
    assert call["json"]["endItem"] == {"id": "2"}
    assert call["json"]["captions"] == [{"text": "links to"}]


def test_create_connector_without_caption(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_connector("b", "1", "2")
    assert "captions" not in session.calls[0]["json"]


def test_list_tags(monkeypatch):
    client, _ = client_for(monkeypatch, [FakeResponse(200, {"data": [{"id": "t1"}]})])
    assert client.list_tags("b") == [{"id": "t1"}]


def test_create_tag(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_tag("b", "urgent", fill_color="red", text_color="#ffffff")
    call = session.calls[0]
    assert call["url"] == "/boards/b/tags"
    assert call["json"] == {"tag": {"title": "urgent", "fillColor": "red", "textColor": "#ffffff"}}


def test_assign_tag(monkeypatch):
    client, session = client_for(monkeypatch)
    client.assign_tag("b", "1", "t1")
    assert session.calls[0]["json"] == {"tagIds": ["t1"]}


def test_move_item(monkeypatch):
    client, session = client_for(monkeypatch)
    client.move_item("b", "1", x=10, y=20)
    assert session.calls[0]["json"] == {"position": {"x": 10, "y": 20, "origin": "center"}}


def test_set_sticky_note_text(monkeypatch):
    client, session = client_for(monkeypatch)
    client.set_sticky_note_text("b", "1", "new")
    assert session.calls[0]["json"] == {"data": {"content": "new"}}


def test_resize_width_only(monkeypatch):
    client, session = client_for(monkeypatch)
    client.resize_item("b", "1", width=100)
    assert session.calls[0]["json"] == {"geometry": {"width": 100}}


def test_resize_height_only(monkeypatch):
    client, session = client_for(monkeypatch)
    client.resize_item("b", "1", height=200)
    assert session.calls[0]["json"] == {"geometry": {"height": 200}}


def test_resize_both(monkeypatch):
    client, session = client_for(monkeypatch)
    client.resize_item("b", "1", width=100, height=200)
    assert session.calls[0]["json"] == {"geometry": {"width": 100, "height": 200}}


def test_resize_none(monkeypatch):
    client, session = client_for(monkeypatch)
    client.resize_item("b", "1")
    assert session.calls[0]["json"] == {}


def test_set_item_color(monkeypatch):
    client, session = client_for(monkeypatch)
    client.set_item_color("b", "1", "green")
    assert session.calls[0]["json"] == {"style": {"fillColor": "green"}}


def test_update_shape_all_fields(monkeypatch):
    client, session = client_for(monkeypatch)
    client.update_shape("b", "1", content="x", shape_type="circle", fill_color="#fff", border_color="#000")
    assert session.calls[0]["json"] == {
        "data": {"content": "x", "shapeType": "circle"},
        "style": {"fillColor": "#fff", "borderColor": "#000"},
    }


def test_update_shape_no_changes(monkeypatch):
    client, session = client_for(monkeypatch)
    client.update_shape("b", "1")
    assert session.calls[0]["json"] == {}


def test_from_env(monkeypatch):
    monkeypatch.setenv("MIRO_ACCESS_TOKEN", "token")
    client = MiroClient.from_env()
    assert client is not None


def test_from_env_missing_token(monkeypatch):
    monkeypatch.delenv("MIRO_ACCESS_TOKEN", raising=False)
    with pytest.raises(MiroError):
        MiroClient.from_env()
