"""Tests for the unified miro CLI dispatcher."""

from __future__ import annotations

import sys

import pytest

import miro_cli


def test_no_args_prints_usage_to_stderr_and_returns_1(capsys):
    """Calling main() with no arguments prints usage to stderr and returns 1."""
    code = miro_cli.main([])
    captured = capsys.readouterr()
    assert code == 1
    assert captured.err.startswith("usage: miro")
    assert captured.out == ""


def test_help_flag_prints_usage_to_stdout_and_returns_0(capsys):
    """The -h/--help flag prints usage to stdout and returns 0."""
    code = miro_cli.main(["--help"])
    captured = capsys.readouterr()
    assert code == 0
    assert captured.out.startswith("usage: miro")
    assert captured.err == ""


def test_short_help_flag_prints_usage_to_stdout_and_returns_0(capsys):
    """The -h flag behaves the same as --help."""
    code = miro_cli.main(["-h"])
    captured = capsys.readouterr()
    assert code == 0
    assert captured.out.startswith("usage: miro")


def test_unknown_action_prints_error_and_returns_2(capsys):
    """An unrecognised action prints an error naming it to stderr and returns 2."""
    code = miro_cli.main(["bogus"])
    captured = capsys.readouterr()
    assert code == 2
    assert "bogus" in captured.err
    assert captured.out == ""


def test_read_dispatches_to_read_board_main(monkeypatch):
    """The "read" action calls read_board.main with the remaining args."""
    recorded = {}

    def fake_main(args):
        recorded["args"] = args
        return 0

    monkeypatch.setattr(miro_cli.read_board, "main", fake_main)
    code = miro_cli.main(["read", "--board-id", "b"])
    assert code == 0
    assert recorded["args"] == ["--board-id", "b"]


def test_read_propagates_return_value(monkeypatch):
    """The "read" action propagates read_board.main's return value."""
    monkeypatch.setattr(miro_cli.read_board, "main", lambda args: 7)
    code = miro_cli.main(["read"])
    assert code == 7


def test_write_dispatches_to_write_board_main(monkeypatch):
    """The "write" action calls write_board.main with the remaining args."""
    recorded = {}

    def fake_main(args):
        recorded["args"] = args
        return 0

    monkeypatch.setattr(miro_cli.write_board, "main", fake_main)
    code = miro_cli.main(["write", "--board-id", "b", "sticky", "hello"])
    assert code == 0
    assert recorded["args"] == ["--board-id", "b", "sticky", "hello"]


def test_write_propagates_return_value(monkeypatch):
    """The "write" action propagates write_board.main's return value."""
    monkeypatch.setattr(miro_cli.write_board, "main", lambda args: 3)
    code = miro_cli.main(["write"])
    assert code == 3


def test_update_dispatches_to_update_board_main(monkeypatch):
    """The "update" action calls update_board.main with the remaining args."""
    recorded = {}

    def fake_main(args):
        recorded["args"] = args
        return 0

    monkeypatch.setattr(miro_cli.update_board, "main", fake_main)
    code = miro_cli.main(["update", "--board-id", "b", "set-text"])
    assert code == 0
    assert recorded["args"] == ["--board-id", "b", "set-text"]


def test_update_propagates_return_value(monkeypatch):
    """The "update" action propagates update_board.main's return value."""
    monkeypatch.setattr(miro_cli.update_board, "main", lambda args: 5)
    code = miro_cli.main(["update"])
    assert code == 5


def test_mcp_server_dispatches_to_miro_mcp_main_and_returns_0(monkeypatch):
    """The "mcp-server" action calls miro_mcp.main() and returns 0, without running the real server."""
    recorded = {"called": False}

    def fake_main():
        recorded["called"] = True

    monkeypatch.setattr(miro_cli.miro_mcp, "main", fake_main)
    code = miro_cli.main(["mcp-server"])
    assert code == 0
    assert recorded["called"] is True


def test_main_uses_sys_argv_when_argv_omitted(monkeypatch):
    """main() falls back to sys.argv when called with no arguments, as a console-script entry point would."""
    monkeypatch.setattr(sys, "argv", ["miro", "read", "--help"])
    with pytest.raises(SystemExit):
        miro_cli.main()
