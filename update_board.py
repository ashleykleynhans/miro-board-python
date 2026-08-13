"""Update or delete items on a Miro board.

Usage:
    python update_board.py --board-id <id> set-text <item-id> "New content"
    python update_board.py --board-id <id> set-color <item-id> --color light_blue
    python update_board.py --board-id <id> resize <item-id> --width 300 --height 200
    python update_board.py --board-id <id> move <item-id> --x 500 --y 300
    python update_board.py --board-id <id> tag <item-id> <tag-id>
    python update_board.py --board-id <id> delete <item-id>
    python update_board.py --board-id <id> update --file changes.json
    python update_board.py --board-id <id> update --file changes.json --dry-run

JSON file format for batch updates (a list of operations):
    [
      {"op": "set-text", "item_id": "3456789012345", "content": "Updated"},
      {"op": "set-color", "item_id": "3456789012345", "color": "light_blue"},
      {"op": "resize", "item_id": "3456789012345", "width": 300, "height": 200},
      {"op": "move", "item_id": "3456789012345", "x": 100, "y": 200},
      {"op": "tag", "item_id": "3456789012345", "tag_id": "7654321098765"},
      {"op": "delete", "item_id": "3456789012345"},
      {"op": "update", "item_id": "3456789012345",
       "data": {"content": "x"}, "style": {"fillColor": "green"}}
    ]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

from rich.console import Console
from rich.markup import escape

from miro_client import ITEM_ENDPOINTS, MiroClient, MiroError


def apply_op(
    client: MiroClient,
    board_id: str,
    op: Dict[str, Any],
    dry_run: bool,
    console: Console,
) -> None:
    """Apply a single operation from the batch file to the board."""
    operation = op["op"]
    item_id = op["item_id"]
    if dry_run:
        console.print(f"dry-run: would run {operation!r} on {escape(str(item_id))}")
        return

    if operation == "set-text":
        client.set_sticky_note_text(board_id, item_id, op["content"])
    elif operation == "set-color":
        client.set_item_color(
            board_id, item_id, op["color"], item_type=op.get("item_type")
        )
    elif operation == "resize":
        client.resize_item(
            board_id,
            item_id,
            width=op.get("width"),
            height=op.get("height"),
            item_type=op.get("item_type"),
        )
    elif operation == "move":
        client.move_item(board_id, item_id, x=op["x"], y=op["y"])
    elif operation == "tag":
        client.assign_tag(board_id, item_id, op["tag_id"])
    elif operation == "delete":
        client.delete_item(board_id, item_id)
    elif operation == "update":
        client.update_item(
            board_id,
            item_id,
            item_type=op.get("item_type"),
            data=op.get("data"),
            style=op.get("style"),
            geometry=op.get("geometry"),
        )
    else:
        raise MiroError(f"unsupported operation in file: {operation!r}")
    console.print(f"[green]{operation}[/green] {escape(str(item_id))} -> ok")


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Update or delete Miro board items.")
    parser.add_argument("--board-id", default=os.environ.get("MIRO_BOARD_ID"))
    parser.add_argument("--token", default=os.environ.get("MIRO_ACCESS_TOKEN"))
    sub = parser.add_subparsers(dest="command")

    set_text = sub.add_parser("set-text", help="replace a sticky note's content")
    set_text.add_argument("item_id")
    set_text.add_argument("content")

    set_color = sub.add_parser("set-color", help="set an item's fill color")
    set_color.add_argument("item_id")
    set_color.add_argument("--color", required=True)
    set_color.add_argument(
        "--type", dest="item_type", choices=sorted(ITEM_ENDPOINTS),
        help="item type (omitted when not known: looked up automatically)",
    )

    resize = sub.add_parser("resize", help="resize an item")
    resize.add_argument("item_id")
    resize.add_argument("--width", type=float)
    resize.add_argument("--height", type=float)
    resize.add_argument(
        "--type", dest="item_type", choices=sorted(ITEM_ENDPOINTS),
        help="item type (omitted when not known: looked up automatically)",
    )

    move = sub.add_parser("move", help="move an item to new coordinates")
    move.add_argument("item_id")
    move.add_argument("--x", type=float, required=True)
    move.add_argument("--y", type=float, required=True)

    tag = sub.add_parser("tag", help="assign a tag to an item")
    tag.add_argument("item_id")
    tag.add_argument("tag_id")

    delete = sub.add_parser("delete", help="delete an item")
    delete.add_argument("item_id")

    update = sub.add_parser("update", help="apply operations from a JSON file")
    update.add_argument("--file", required=True)
    update.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if not args.token:
        parser.error("missing access token (use --token or MIRO_ACCESS_TOKEN)")
    if not args.board_id:
        parser.error("missing board id (use --board-id or MIRO_BOARD_ID)")
    if not args.command:
        parser.error("missing subcommand (set-text, set-color, resize, move, tag, delete, or update)")

    client = MiroClient(args.token)
    console = Console()
    error_console = Console(stderr=True)
    try:
        if args.command == "set-text":
            client.set_sticky_note_text(args.board_id, args.item_id, args.content)
            console.print(f"[green]set-text[/green] {escape(str(args.item_id))} -> ok")
        elif args.command == "set-color":
            client.set_item_color(args.board_id, args.item_id, args.color, item_type=args.item_type)
            console.print(f"[green]set-color[/green] {escape(str(args.item_id))} -> ok")
        elif args.command == "resize":
            client.resize_item(args.board_id, args.item_id, width=args.width, height=args.height, item_type=args.item_type)
            console.print(f"[green]resize[/green] {escape(str(args.item_id))} -> ok")
        elif args.command == "move":
            client.move_item(args.board_id, args.item_id, x=args.x, y=args.y)
            console.print(f"[green]move[/green] {escape(str(args.item_id))} -> ok")
        elif args.command == "tag":
            client.assign_tag(args.board_id, args.item_id, args.tag_id)
            console.print(f"[green]tag[/green] {escape(str(args.item_id))} -> ok")
        elif args.command == "delete":
            client.delete_item(args.board_id, args.item_id)
            console.print(f"[green]delete[/green] {escape(str(args.item_id))} -> ok")
        else:
            with open(args.file) as handle:
                ops = json.load(handle)
            if not isinstance(ops, list):
                parser.error("--file must contain a JSON list of operations")
            for op in ops:
                apply_op(client, args.board_id, op, args.dry_run, console)
    except MiroError as exc:
        error_console.print(f"[red]error:[/red] {escape(str(exc))}")
        return 1

    console.print("[green]Done.[/green]")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
