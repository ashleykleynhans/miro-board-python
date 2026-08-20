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


def test_create_item_uses_per_type_endpoint(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_item("b", "sticky_note", data={"content": "hi"}, position={"x": 1, "y": 2})
    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == "/boards/b/sticky_notes"
    assert call["json"] == {"data": {"content": "hi"}, "position": {"x": 1, "y": 2}}


def test_create_item_with_parent(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_item("b", "frame", parent_id="f1")
    call = session.calls[0]
    assert call["url"] == "/boards/b/frames"
    assert call["json"] == {"parent": {"id": "f1"}}


def test_create_item_unsupported_type(monkeypatch):
    client, _ = client_for(monkeypatch)
    with pytest.raises(MiroError):
        client.create_item("b", "bogus")


def test_update_item(monkeypatch):
    client, session = client_for(monkeypatch)
    client.update_item(
        "b", "1", item_type="sticky_note", data={"content": "x"}, style={"fillColor": "red"}
    )
    call = session.calls[0]
    assert call["method"] == "PATCH"
    assert call["url"] == "/boards/b/sticky_notes/1"
    assert call["json"] == {"data": {"content": "x"}, "style": {"fillColor": "red"}}


def test_update_item_resolves_type(monkeypatch):
    responses = [
        FakeResponse(200, {"id": "1", "type": "shape"}),
        FakeResponse(200, {"id": "1"}),
    ]
    client, session = client_for(monkeypatch, responses)
    client.update_item("b", "1", data={"content": "x"})
    assert session.calls[0]["url"] == "/boards/b/items/1"
    assert session.calls[1]["url"] == "/boards/b/shapes/1"


def test_update_item_unsupported_resolved_type(monkeypatch):
    client, _ = client_for(
        monkeypatch, [FakeResponse(200, {"id": "1", "type": "mindmap_node"})]
    )
    with pytest.raises(MiroError):
        client.update_item("b", "1", data={"content": "x"})


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


def test_405_mentions_per_type_endpoints(monkeypatch):
    client, _ = client_for(monkeypatch, [FakeResponse(405, text="methodNotSupported")])
    with pytest.raises(MiroError) as exc:
        client.get_board("b")
    assert "per-item-type" in str(exc.value)


def test_create_sticky_note(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_sticky_note("b", "Hello", x=10, y=20, color="light_blue")
    body = session.calls[0]["json"]
    assert session.calls[0]["url"] == "/boards/b/sticky_notes"
    assert body["data"] == {"content": "Hello"}
    assert body["style"] == {"fillColor": "light_blue"}
    assert body["position"] == {"x": 10, "y": 20, "origin": "center"}
    assert body["geometry"] == {"width": 180}


def test_create_sticky_note_with_explicit_width(monkeypatch):
    """create_sticky_note sends only width -- Miro rejects a sticky note request that also
    specifies height, since sticky notes have a fixed aspect ratio."""
    client, session = client_for(monkeypatch)
    client.create_sticky_note("b", "Hello", width=200)
    assert session.calls[0]["json"]["geometry"] == {"width": 200}


def test_create_card_with_assignee(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_card("b", "T", description="D", assignee_id="9", x=1, y=2)
    call = session.calls[0]
    assert call["url"] == "/boards/b/cards"
    assert call["json"]["data"] == {
        "title": "T",
        "description": "D",
        "assigneeId": "9",
    }


def test_create_card_without_assignee(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_card("b", "T")
    assert session.calls[0]["json"]["data"] == {
        "title": "T",
        "description": "",
        "assigneeId": None,
    }


def test_create_card_with_parent_id(monkeypatch):
    """create_card nests the new card under the given parent_id."""
    client, session = client_for(monkeypatch)
    client.create_card("b", "Title", parent_id="frame-1")
    call = session.calls[0]
    assert call["json"]["parent"] == {"id": "frame-1"}


def test_create_card_without_height_omits_geometry_height(monkeypatch):
    """create_card leaves height unset by default, matching prior behaviour."""
    client, session = client_for(monkeypatch)
    client.create_card("b", "T")
    assert session.calls[0]["json"]["geometry"] == {"width": 320}


def test_create_card_with_height_overrides_miros_default_collapse(monkeypatch):
    """create_card sends an explicit height so Miro doesn't collapse the card to its own
    default (Miro otherwise renders cards ~60px tall regardless of caller-intended layout)."""
    client, session = client_for(monkeypatch)
    client.create_card("b", "T", width=320, height=220)
    assert session.calls[0]["json"]["geometry"] == {"width": 320, "height": 220}


def test_create_sticky_note_with_parent_id(monkeypatch):
    """create_sticky_note nests the new sticky note under the given parent_id."""
    client, session = client_for(monkeypatch)
    client.create_sticky_note("b", "Content", parent_id="frame-1")
    call = session.calls[0]
    assert call["json"]["parent"] == {"id": "frame-1"}


def test_create_text(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_text("b", "Notes", x=5, y=6, width=300)
    body = session.calls[0]["json"]
    assert session.calls[0]["url"] == "/boards/b/texts"
    assert body["data"] == {"content": "Notes"}
    assert body["geometry"] == {"width": 300}


def test_create_shape(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_shape("b", "Decision", shape_type="rhombus", fill_color="#f00", border_color="#00f")
    body = session.calls[0]["json"]
    assert session.calls[0]["url"] == "/boards/b/shapes"
    assert body["data"] == {"content": "Decision", "shape": "rhombus"}
    assert body["style"] == {"fillColor": "#f00", "borderColor": "#00f"}


def test_create_shape_defaults(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_shape("b")
    body = session.calls[0]["json"]
    assert body["data"] == {"content": "", "shape": "rectangle"}
    assert body["style"] == {"fillColor": "#ffffff", "borderColor": "#1a1a1a"}
    assert body["geometry"] == {"width": 160, "height": 80}


def test_create_shape_with_explicit_width_height_and_parent(monkeypatch):
    """create_shape accepts independent width/height (no fixed aspect ratio, unlike a sticky
    note) and can be nested under a parent frame."""
    client, session = client_for(monkeypatch)
    client.create_shape("b", "Notes", width=320, height=180, parent_id="frame-1")
    body = session.calls[0]["json"]
    assert body["geometry"] == {"width": 320, "height": 180}
    assert body["parent"] == {"id": "frame-1"}


def test_create_frame(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_frame("b", title="Sec", x=1, y=2, width=1000, height=700)
    body = session.calls[0]["json"]
    assert session.calls[0]["url"] == "/boards/b/frames"
    assert body["data"] == {"title": "Sec"}
    assert body["geometry"] == {"width": 1000, "height": 700}


def test_create_frame_with_fill_color(monkeypatch):
    """create_frame sends the given fill_color as the item's style."""
    client, session = client_for(monkeypatch)
    client.create_frame("b", "Section", fill_color="#1a73e8")
    call = session.calls[0]
    assert call["url"] == "/boards/b/frames"
    assert call["json"]["style"] == {"fillColor": "#1a73e8"}


def test_create_frame_without_fill_color_omits_style(monkeypatch):
    """create_frame omits the style field entirely when no fill_color is given."""
    client, session = client_for(monkeypatch)
    client.create_frame("b", "Section")
    call = session.calls[0]
    assert "style" not in call["json"]


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
    body = session.calls[0]["json"]
    assert session.calls[0]["url"] == "/boards/b/images"
    assert body["data"] == {"imageUrl": "https://x/p.png"}
    assert body["geometry"] == {"width": 400, "height": 400}


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
    client.create_document("b", "Spec", "https://x")
    call = session.calls[0]
    assert call["url"] == "/boards/b/documents"
    assert call["json"]["data"] == {"title": "Spec", "documentUrl": "https://x"}


def test_create_embed(monkeypatch):
    client, session = client_for(monkeypatch)
    client.create_embed("b", "https://x")
    body = session.calls[0]["json"]
    assert session.calls[0]["url"] == "/boards/b/embeds"
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
    client.create_tag("b", "urgent", fill_color="red")
    call = session.calls[0]
    assert call["url"] == "/boards/b/tags"
    assert call["json"] == {"title": "urgent", "fillColor": "red"}


def test_assign_tag(monkeypatch):
    client, session = client_for(monkeypatch)
    client.assign_tag("b", "1", "t1")
    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == "/boards/b/items/1"
    assert call["params"] == {"tag_id": "t1"}


def test_move_item(monkeypatch):
    client, session = client_for(monkeypatch)
    client.move_item("b", "1", x=10, y=20)
    call = session.calls[0]
    assert call["url"] == "/boards/b/items/1"
    assert call["json"] == {"position": {"x": 10, "y": 20}}


def test_set_sticky_note_text(monkeypatch):
    client, session = client_for(monkeypatch)
    client.set_sticky_note_text("b", "1", "new")
    call = session.calls[0]
    assert call["url"] == "/boards/b/sticky_notes/1"
    assert call["json"] == {"data": {"content": "new"}}


def test_resize_width_only(monkeypatch):
    client, session = client_for(monkeypatch)
    client.resize_item("b", "1", width=100, item_type="shape")
    assert session.calls[0]["url"] == "/boards/b/shapes/1"
    assert session.calls[0]["json"] == {"geometry": {"width": 100}}


def test_resize_height_only(monkeypatch):
    client, session = client_for(monkeypatch)
    client.resize_item("b", "1", height=200, item_type="shape")
    assert session.calls[0]["json"] == {"geometry": {"height": 200}}


def test_resize_both(monkeypatch):
    client, session = client_for(monkeypatch)
    client.resize_item("b", "1", width=100, height=200, item_type="shape")
    assert session.calls[0]["json"] == {"geometry": {"width": 100, "height": 200}}


def test_resize_none(monkeypatch):
    client, session = client_for(monkeypatch)
    client.resize_item("b", "1", item_type="shape")
    assert session.calls[0]["json"] == {}


def test_set_item_color(monkeypatch):
    client, session = client_for(monkeypatch)
    client.set_item_color("b", "1", "green", item_type="sticky_note")
    call = session.calls[0]
    assert call["url"] == "/boards/b/sticky_notes/1"
    assert call["json"] == {"style": {"fillColor": "green"}}


def test_update_shape_all_fields(monkeypatch):
    client, session = client_for(monkeypatch)
    client.update_shape("b", "1", content="x", shape_type="circle", fill_color="#fff", border_color="#000")
    call = session.calls[0]
    assert call["url"] == "/boards/b/shapes/1"
    assert call["json"] == {
        "data": {"content": "x", "shape": "circle"},
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
