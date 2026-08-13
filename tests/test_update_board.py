"""Tests for the update_board CLI."""

from __future__ import annotations

import json

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
        ["--board-id", "b", "--token", "t", "set-color", "1", "--color", "green"],
        [FakeResponse(200, {"id": "1"})],
    )
    assert code == 0
    assert session.calls[0]["json"] == {"style": {"fillColor": "green"}}


def test_resize(monkeypatch):
    code, session = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "resize", "1", "--width", "100", "--height", "200"],
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
    assert session.calls[0]["json"] == {"position": {"x": 5, "y": 6, "origin": "center"}}


def test_tag(monkeypatch):
    code, session = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "tag", "1", "9"],
        [FakeResponse(200, {"id": "1"})],
    )
    assert code == 0
    assert session.calls[0]["json"] == {"tagIds": ["9"]}


def test_delete(monkeypatch):
    code, session = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "delete", "1"],
        [FakeResponse(204)],
    )
    assert code == 0
    assert session.calls[0]["method"] == "DELETE"


def test_batch_update(tmp_path, monkeypatch, capsys):
    batch = tmp_path / "changes.json"
    batch.write_text(json.dumps([
        {"op": "set-text", "item_id": "1", "content": "x"},
        {"op": "set-color", "item_id": "1", "color": "green"},
        {"op": "resize", "item_id": "1", "width": 100, "height": 200},
        {"op": "move", "item_id": "1", "x": 1, "y": 2},
        {"op": "tag", "item_id": "1", "tag_id": "9"},
        {"op": "update", "item_id": "1", "data": {"content": "z"}, "style": {"fillColor": "red"}, "geometry": {"width": 50}, "tag_ids": ["9"]},
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
