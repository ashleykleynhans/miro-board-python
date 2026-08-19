"""Unified `miro` CLI: dispatches to the read/write/update/mcp-server actions.

    miro read [args]         : see read_board.py
    miro write [args]        : see write_board.py
    miro update [args]       : see update_board.py
    miro mcp-server          : run the MCP server (see miro_mcp package)
"""

from __future__ import annotations

import sys
from typing import List, Optional, TextIO

import read_board
import write_board
import update_board
import miro_mcp

_ACTIONS = {
    # Looked up through the module at call time (not bound at import time) so
    # that tests can monkeypatch e.g. `miro_cli.read_board.main`.
    "read": lambda args: read_board.main(args),
    "write": lambda args: write_board.main(args),
    "update": lambda args: update_board.main(args),
}


def _print_usage(stream: TextIO) -> None:
    """Print the top-level usage line to the given stream."""
    print("usage: miro <read|write|update|mcp-server> [args...]", file=stream)


def main(argv: Optional[List[str]] = None) -> int:
    """Dispatch to the read, write, update, or mcp-server action."""
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        _print_usage(sys.stderr)
        return 1

    action, rest = argv[0], argv[1:]

    if action in ("-h", "--help"):
        _print_usage(sys.stdout)
        return 0

    if action == "mcp-server":
        miro_mcp.main()
        return 0

    handler = _ACTIONS.get(action)
    if handler is None:
        known = ", ".join([*_ACTIONS, "mcp-server"])
        print(f"error: unknown action {action!r} (expected one of: {known})", file=sys.stderr)
        return 2

    return handler(rest)


if __name__ == "__main__":
    sys.exit(main())
