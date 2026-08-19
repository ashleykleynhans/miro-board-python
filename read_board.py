"""Read data from a Miro board: list items or export them to JSON.

Usage:
    python read_board.py --board-id <id>                    # summarize board
    python read_board.py --board-id <id> --json items.json # export all items
    python read_board.py --board-id <id> --item-type card   # filter by type
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.markup import escape
from rich.table import Table

from miro_client import MiroClient, MiroError


def summarize(
    board: Dict[str, Any], items: List[Dict[str, Any]], console: Console
) -> None:
    """Print a human-readable summary of the board and its items."""
    console.print(
        f"[bold]Board:[/bold] {escape(str(board.get('name')))} "
        f"[dim](id={escape(str(board['id']))})[/dim]"
    )
    console.print(f"Items: {len(items)}")

    table = Table(title="Items", header_style="bold")
    table.add_column("TYPE")
    table.add_column("ID")
    table.add_column("CONTENT")
    for item in items:
        item_id = item["id"]
        item_type = item.get("type", "?")
        data = item.get("data", {}) or {}
        content = data.get("content") or data.get("title") or ""
        content = " ".join(str(content).split())[:60]
        table.add_row(item_type, escape(str(item_id)), escape(content))
    console.print(table)


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(description="Read items from a Miro board.")
    parser.add_argument("--board-id", default=os.environ.get("MIRO_BOARD_ID"))
    parser.add_argument("--token", default=os.environ.get("MIRO_ACCESS_TOKEN"))
    parser.add_argument(
        "--item-type",
        help="Only show items of this type, e.g. sticky_note, card, shape, text",
    )
    parser.add_argument(
        "--json",
        metavar="FILE",
        help="Write the full item list to FILE as JSON instead of summarizing",
    )
    parser.add_argument(
        "--limit", type=int, default=50, help="Items fetched per API page (max 50)"
    )
    args = parser.parse_args(argv)

    if not args.token:
        parser.error("missing access token (use --token or MIRO_ACCESS_TOKEN)")
    if not args.board_id:
        parser.error("missing board id (use --board-id or MIRO_BOARD_ID)")

    console = Console()
    error_console = Console(stderr=True)
    try:
        client = MiroClient(args.token)
        board = client.get_board(args.board_id)
        items = client.list_items(args.board_id, limit=args.limit)
        if args.item_type:
            items = [i for i in items if i.get("type") == args.item_type]
    except MiroError as exc:
        error_console.print(f"[red]error:[/red] {escape(str(exc))}")
        return 1

    if args.json:
        with open(args.json, "w") as handle:
            json.dump({"board": board, "items": items}, handle, indent=2)
        console.print(f"Wrote {len(items)} items to {escape(str(args.json))}")
    else:
        summarize(board, items, console)
    return 0


if __name__ == "__main__":
    sys.exit(main())
