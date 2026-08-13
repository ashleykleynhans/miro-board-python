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
from typing import Any, Dict, List

from miro_client import MiroClient, MiroError


def summarize(board: Dict[str, Any], items: List[Dict[str, Any]]) -> None:
    """Print a human-readable summary of the board and its items."""
    print(f"Board: {board.get('name')!r} (id={board['id']})")
    print(f"Board size: {board.get('size')}")
    print(f"Items: {len(items)}")
    print()
    print(f"{'TYPE':<14} {'ID':<24} CONTENT")
    print("-" * 80)
    for item in items:
        item_id = item["id"]
        item_type = item.get("type", "?")
        data = item.get("data", {}) or {}
        content = data.get("content") or data.get("title") or ""
        content = " ".join(str(content).split())[:60]
        print(f"{item_type:<14} {item_id:<24} {content}")


def main(argv: List[str]) -> int:
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

    try:
        client = MiroClient(args.token)
        board = client.get_board(args.board_id)
        items = client.list_items(args.board_id, limit=args.limit)
        if args.item_type:
            items = [i for i in items if i.get("type") == args.item_type]
    except MiroError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        with open(args.json, "w") as handle:
            json.dump({"board": board, "items": items}, handle, indent=2)
        print(f"Wrote {len(items)} items to {args.json}")
    else:
        summarize(board, items)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
