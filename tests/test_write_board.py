"""Tests for the write_board CLI."""

from __future__ import annotations

import argparse
import json

import pytest

import write_board
from helpers import FakeResponse, install_session
from miro_client import MiroError


def run_main(monkeypatch, argv, responses=None):
    session = install_session(monkeypatch, responses)
    return write_board.main(argv), session


def test_sticky_dry_run(monkeypatch, capsys):
    code, _ = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "sticky", "hi", "--x", "1", "--y", "2", "--color", "red", "--dry-run"],
    )
    assert code == 0
    assert "would create sticky_note" in capsys.readouterr().out


def test_sticky_create(monkeypatch, capsys):
    code, _ = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "sticky", "hi", "--x", "1", "--y", "2"],
        [FakeResponse(200, {"id": "1", "type": "sticky_note"})],
    )
    assert code == 0
    assert "created sticky_note 1" in capsys.readouterr().out


@pytest.mark.parametrize("argv", [
    ["card", "--title", "T", "--description", "D", "--assignee-id", "9", "--x", "1", "--y", "2"],
    ["text", "hello", "--x", "1", "--y", "2"],
    ["shape", "D", "--shape-type", "rhombus", "--fill-color", "#fff", "--border-color", "#000", "--x", "1", "--y", "2"],
    ["frame", "--title", "F", "--x", "1", "--y", "2", "--width", "1000", "--height", "700"],
    ["image", "--url", "https://x", "--x", "1", "--y", "2", "--width", "400", "--height", "300"],
    ["document", "--title", "S", "--url", "https://x", "--x", "1", "--y", "2"],
    ["embed", "--url", "https://x", "--x", "1", "--y", "2", "--width", "500", "--height", "400"],
    ["connector", "--start-item-id", "1", "--end-item-id", "2", "--caption", "link", "--color", "#000"],
    ["tag", "--title", "urgent", "--fill-color", "red"],
])
def test_subcommands_dry_run(monkeypatch, capsys, argv):
    code, _ = run_main(monkeypatch, ["--board-id", "b", "--token", "t", *argv, "--dry-run"])
    assert code == 0
    assert "would create" in capsys.readouterr().out


def test_batch_dry_run(tmp_path, monkeypatch, capsys):
    batch = tmp_path / "items.json"
    batch.write_text(json.dumps([
        {"type": "sticky_note", "content": "a"},
        {"type": "card", "title": "b"},
        {"type": "shape", "content": "c"},
        {"type": "frame", "title": "d"},
        {"type": "image", "url": "https://x"},
        {"type": "document", "title": "e", "url": "https://x"},
        {"type": "embed", "url": "https://x"},
        {"type": "connector", "start_item_id": "1", "end_item_id": "2"},
        {"type": "tag", "title": "f"},
    ]))
    code, _ = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "--file", str(batch), "--dry-run"],
    )
    assert code == 0
    assert "Created 9 item(s)" in capsys.readouterr().out


def test_batch_create(tmp_path, monkeypatch, capsys):
    batch = tmp_path / "items.json"
    batch.write_text(json.dumps([
        {"type": "sticky_note", "content": "a"},
        {"type": "card", "title": "b"},
        {"type": "text", "content": "c"},
        {"type": "shape", "content": "d"},
        {"type": "frame", "title": "e"},
        {"type": "image", "url": "https://x", "width": 400},
        {"type": "document", "title": "f", "url": "https://x"},
        {"type": "embed", "url": "https://x"},
        {"type": "connector", "start_item_id": "1", "end_item_id": "2", "caption": "link"},
        {"type": "tag", "title": "g"},
    ]))
    responses = [FakeResponse(200, {"id": str(i), "type": "x"}) for i in range(10)]
    code, session = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "--file", str(batch)],
        responses,
    )
    assert code == 0
    assert len(session.calls) == 10
    assert "Created 10 item(s)" in capsys.readouterr().out


def test_batch_unsupported_type(tmp_path, monkeypatch, capsys):
    batch = tmp_path / "items.json"
    batch.write_text('[{"type": "bogus"}]')
    code, _ = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "--file", str(batch)],
    )
    assert code == 1
    assert "unsupported item type" in capsys.readouterr().err


def test_batch_must_be_list(tmp_path, monkeypatch):
    batch = tmp_path / "items.json"
    batch.write_text("{}")
    with pytest.raises(SystemExit):
        run_main(monkeypatch, ["--board-id", "b", "--token", "t", "--file", str(batch)])


def test_requires_token(monkeypatch):
    install_session(monkeypatch)
    with pytest.raises(SystemExit):
        write_board.main(["--board-id", "b"])


def test_requires_board(monkeypatch):
    install_session(monkeypatch)
    with pytest.raises(SystemExit):
        write_board.main(["--token", "t"])


def test_nothing_to_create(monkeypatch):
    install_session(monkeypatch)
    with pytest.raises(SystemExit):
        write_board.main(["--board-id", "b", "--token", "t"])


def test_create_error_returns_1(monkeypatch, capsys):
    code, _ = run_main(
        monkeypatch,
        ["--board-id", "b", "--token", "t", "sticky", "hi"],
        [FakeResponse(400, text="boom")],
    )
    assert code == 1
    assert "error on item 0" in capsys.readouterr().err


def test_spec_from_args_unsupported():
    with pytest.raises(MiroError):
        write_board.spec_from_args(argparse.Namespace(command="bogus"))
