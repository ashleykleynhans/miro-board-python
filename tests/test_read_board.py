"""Tests for the read_board CLI."""

from __future__ import annotations

import json

import pytest

import read_board
from helpers import FakeResponse, install_session


def run_main(monkeypatch, argv, responses=None):
    session = install_session(monkeypatch, responses)
    return read_board.main(argv), session


def test_summarizes_board(monkeypatch, capsys):
    responses = [
        FakeResponse(200, {"id": "b", "name": "My Board", "size": {"width": 1000, "height": 800}}),
        FakeResponse(200, {
            "data": [
                {"id": "1", "type": "sticky_note", "data": {"content": "Hello world"}},
                {"id": "2", "type": "card", "data": {"title": "Task"}},
                {"id": "3", "type": "shape"},
            ]
        }),
    ]
    code, _ = run_main(monkeypatch, ["--board-id", "b", "--token", "t"], responses)
    out = capsys.readouterr().out
    assert code == 0
    assert "My Board" in out
    assert "Hello world" in out
    assert "Task" in out


def test_json_export(tmp_path, monkeypatch):
    out_file = tmp_path / "items.json"
    responses = [
        FakeResponse(200, {"id": "b", "name": "B"}),
        FakeResponse(200, {"data": [{"id": "1", "type": "sticky_note", "data": {"content": "x"}}]}),
    ]
    code, _ = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "--json", str(out_file)],
        responses,
    )
    assert code == 0
    payload = json.loads(out_file.read_text())
    assert len(payload["items"]) == 1


def test_item_type_filter(tmp_path, monkeypatch):
    out_file = tmp_path / "f.json"
    responses = [
        FakeResponse(200, {"id": "b"}),
        FakeResponse(200, {
            "data": [
                {"id": "1", "type": "sticky_note"},
                {"id": "2", "type": "card"},
            ]
        }),
    ]
    code, _ = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "--item-type", "card", "--json", str(out_file)],
        responses,
    )
    assert code == 0
    payload = json.loads(out_file.read_text())
    assert [item["type"] for item in payload["items"]] == ["card"]


def test_requires_token(monkeypatch):
    install_session(monkeypatch)
    with pytest.raises(SystemExit):
        read_board.main(["--board-id", "b"])


def test_requires_board(monkeypatch):
    install_session(monkeypatch)
    with pytest.raises(SystemExit):
        read_board.main(["--token", "t"])


def test_api_error_returns_1(monkeypatch, capsys):
    code, _ = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t"],
        [FakeResponse(404, text="not found")],
    )
    assert code == 1
    assert "HTTP 404" in capsys.readouterr().err
