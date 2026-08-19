"""Tests for the update_board CLI."""

from __future__ import annotations

import json
import sys

import pytest

import update_board
from helpers import FakeResponse, install_session


def run_main(monkeypatch, argv, responses=None):
    session = install_session(monkeypatch, responses)
    return update_board.main(argv), session


def test_set_text(monkeypatch):
    code, session = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "set-text", "1", "hello"],
        [FakeResponse(200, {"id": "1"})],
    )
    assert code == 0
    assert session.calls[0]["json"] == {"data": {"content": "hello"}}


def test_set_color(monkeypatch):
    code, session = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "set-color", "1", "--color", "green", "--type", "sticky_note"],
        [FakeResponse(200, {"id": "1"})],
    )
    assert code == 0
    assert session.calls[0]["json"] == {"style": {"fillColor": "green"}}


def test_resize(monkeypatch):
    code, session = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "resize", "1", "--width", "100", "--height", "200", "--type", "shape"],
        [FakeResponse(200, {"id": "1"})],
    )
    assert code == 0
    assert session.calls[0]["json"] == {"geometry": {"width": 100, "height": 200}}


def test_move(monkeypatch):
    code, session = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "move", "1", "--x", "5", "--y", "6"],
        [FakeResponse(200, {"id": "1"})],
    )
    assert code == 0
    assert session.calls[0]["json"] == {"position": {"x": 5, "y": 6}}


def test_tag(monkeypatch):
    code, session = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "tag", "1", "9"],
        [FakeResponse(200, {"id": "1"})],
    )
    assert code == 0
    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["params"] == {"tag_id": "9"}


def test_delete(monkeypatch):
    code, session = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "delete", "1"],
        [FakeResponse(204)],
    )
    assert code == 0
    assert session.calls[0]["method"] == "DELETE"


def test_clear_board_deletes_non_frames_before_frames(monkeypatch, capsys):
    """clear-board deletes every item, frames last so none is deleted while still parenting items."""
    items = [
        {"id": "frame-1", "type": "frame"},
        {"id": "card-1", "type": "card"},
        {"id": "sticky-1", "type": "sticky_note"},
    ]
    code, session = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "clear-board", "--yes"],
        [FakeResponse(200, {"data": items}), FakeResponse(204), FakeResponse(204), FakeResponse(204)],
    )
    assert code == 0
    delete_calls = [c for c in session.calls if c["method"] == "DELETE"]
    assert [c["url"] for c in delete_calls] == [
        "/boards/b/items/card-1",
        "/boards/b/items/sticky-1",
        "/boards/b/items/frame-1",
    ]
    assert "Done." in capsys.readouterr().out


def test_clear_board_empty_board_deletes_nothing(monkeypatch, capsys):
    """clear-board on an already-empty board makes no delete calls."""
    code, session = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "clear-board", "--yes"],
        [FakeResponse(200, {"data": []})],
    )
    assert code == 0
    assert session.calls == [session.calls[0]]  # only the list_items call
    assert "already empty" in capsys.readouterr().out


def test_clear_board_dry_run_deletes_nothing(monkeypatch, capsys):
    """clear-board --dry-run lists items without deleting or prompting."""
    items = [{"id": "card-1", "type": "card"}]
    code, session = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "clear-board", "--dry-run"],
        [FakeResponse(200, {"data": items})],
    )
    assert code == 0
    assert len(session.calls) == 1  # only the list_items call, no deletes
    assert "would delete card card-1" in capsys.readouterr().out


def test_clear_board_prompts_without_yes(monkeypatch, capsys):
    """clear-board without --yes asks for typed confirmation before deleting."""
    items = [{"id": "card-1", "type": "card"}]
    monkeypatch.setattr("builtins.input", lambda _: "clear")
    code, session = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "clear-board"],
        [FakeResponse(200, {"data": items}), FakeResponse(204)],
    )
    assert code == 0
    assert len([c for c in session.calls if c["method"] == "DELETE"]) == 1


def test_clear_board_aborts_on_wrong_confirmation(monkeypatch, capsys):
    """clear-board aborts and deletes nothing if the typed confirmation doesn't match."""
    items = [{"id": "card-1", "type": "card"}]
    monkeypatch.setattr("builtins.input", lambda _: "nope")
    code, session = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "clear-board"],
        [FakeResponse(200, {"data": items})],
    )
    assert code == 1
    assert not any(c["method"] == "DELETE" for c in session.calls)
    assert "Aborted" in capsys.readouterr().err


def test_batch_update(tmp_path, monkeypatch, capsys):
    batch = tmp_path / "changes.json"
    batch.write_text(json.dumps([
        {"op": "set-text", "item_id": "1", "content": "x"},
        {"op": "set-color", "item_id": "1", "color": "green", "item_type": "sticky_note"},
        {"op": "resize", "item_id": "1", "width": 100, "height": 200, "item_type": "shape"},
        {"op": "move", "item_id": "1", "x": 1, "y": 2},
        {"op": "tag", "item_id": "1", "tag_id": "9"},
        {"op": "update", "item_id": "1", "item_type": "shape", "data": {"content": "z"}, "style": {"fillColor": "red"}, "geometry": {"width": 50}},
        {"op": "delete", "item_id": "1"},
    ]))
    responses = [FakeResponse(200, {"id": "1"})] * 6 + [FakeResponse(204)]
    code, session = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "update", "--file", str(batch)],
        responses,
    )
    assert code == 0
    assert len(session.calls) == 7
    assert "Done." in capsys.readouterr().out


def test_batch_dry_run(tmp_path, monkeypatch, capsys):
    batch = tmp_path / "changes.json"
    batch.write_text('[{"op": "delete", "item_id": "1"}]')
    code, session = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "update", "--file", str(batch), "--dry-run"],
    )
    assert code == 0
    assert session.calls == []
    assert "would run 'delete' on 1" in capsys.readouterr().out


def test_batch_unsupported_op(tmp_path, monkeypatch, capsys):
    batch = tmp_path / "changes.json"
    batch.write_text('[{"op": "bogus", "item_id": "1"}]')
    code, _ = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "update", "--file", str(batch)],
    )
    assert code == 1
    assert "unsupported operation" in capsys.readouterr().err


def test_batch_must_be_list(tmp_path, monkeypatch):
    batch = tmp_path / "changes.json"
    batch.write_text("{}")
    with pytest.raises(SystemExit):
        run_main(monkeypatch, ["--board-id", "b", "--token", "t", "update", "--file", str(batch)])


def test_requires_token(monkeypatch):
    install_session(monkeypatch)
    with pytest.raises(SystemExit):
        update_board.main(["--board-id", "b"])


def test_requires_board(monkeypatch):
    install_session(monkeypatch)
    with pytest.raises(SystemExit):
        update_board.main(["--token", "t"])


def test_requires_subcommand(monkeypatch):
    install_session(monkeypatch)
    with pytest.raises(SystemExit):
        update_board.main(["--board-id", "b", "--token", "t"])


def test_api_error_returns_1(monkeypatch, capsys):
    code, _ = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "set-text", "1", "x"],
        [FakeResponse(400, text="boom")],
    )
    assert code == 1
    assert "HTTP 400" in capsys.readouterr().err


def test_main_uses_sys_argv_when_argv_omitted(monkeypatch):
    """main() falls back to sys.argv when called with no arguments, as a console-script entry point would."""
    monkeypatch.setattr(sys, "argv", ["update_board", "--help"])
    with pytest.raises(SystemExit):
        update_board.main()
