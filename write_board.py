"""Write items to a Miro board: sticky notes, cards, text, shapes, frames,
images, documents, embeds, connectors, and tags.

Usage:
    python write_board.py --board-id <id> sticky "Hello world" --x 100 --y 200
    python write_board.py --board-id <id> card --title "Task" --description "Do it"
    python write_board.py --board-id <id> shape "Decision" --shape-type rhombus
    python write_board.py --board-id <id> frame --title "Section" --width 1000
    python write_board.py --board-id <id> image --url https://example.com/pic.png
    python write_board.py --board-id <id> connector --start-item-id <id> --end-item-id <id>
    python write_board.py --board-id <id> tag --title "urgent"
    python write_board.py --board-id <id> --file items.json
    python write_board.py --board-id <id> --file items.json --dry-run

JSON file format (a list of items):
    [
      {"type": "sticky_note", "content": "Hello", "color": "light_yellow",
       "x": 0, "y": 0},
      {"type": "card", "title": "Task 1", "description": "Do the thing",
       "x": 300, "y": 0},
      {"type": "shape", "content": "Decision", "shape_type": "rhombus",
       "fill_color": "#ffffff", "border_color": "#1a1a1a", "x": 600, "y": 0},
      {"type": "frame", "title": "Section", "width": 1000, "height": 700},
      {"type": "image", "url": "https://example.com/pic.png",
       "width": 400, "height": 300},
      {"type": "document", "title": "Spec", "url": "https://example.com/doc"},
      {"type": "embed", "url": "https://example.com"},
      {"type": "connector", "start_item_id": "123", "end_item_id": "456",
       "caption": "links to"}
    ]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.markup import escape

from miro_client import BULK_MAX_ITEMS, MiroClient, MiroError, SHAPE_TYPES

STICKY_COLORS = {
    "red", "orange", "yellow", "green", "cyan", "light_green", "blue",
    "dark_blue", "magenta", "violet", "light_yellow", "light_pink", "gray",
    "light_blue", "dark_gray",
}

# Item types the bulk endpoint accepts. Connectors and tags are created
# through their own endpoints and fall back to individual calls.
BULK_TYPES = {
    "sticky_note", "card", "text", "shape", "frame", "image", "document",
    "embed",
}


def create_from_dict(client: MiroClient, board_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    """Create a single item from a spec dict (see the module docstring)."""
    item_type = spec["type"]
    kwargs: Dict[str, Any] = {
        "x": spec.get("x", 0.0),
        "y": spec.get("y", 0.0),
    }
    if item_type == "sticky_note":
        kwargs["color"] = spec.get("color", "light_yellow")
        return client.create_sticky_note(board_id, spec["content"], **kwargs)
    if item_type == "card":
        kwargs.update(
            {
                "description": spec.get("description", ""),
                "assignee_id": spec.get("assignee_id"),
            }
        )
        return client.create_card(board_id, spec["title"], **kwargs)
    if item_type == "text":
        return client.create_text(board_id, spec["content"], **kwargs)
    if item_type == "shape":
        return client.create_shape(
            board_id,
            spec.get("content", ""),
            shape_type=spec.get("shape_type", "rectangle"),
            fill_color=spec.get("fill_color", "#ffffff"),
            border_color=spec.get("border_color", "#1a1a1a"),
            **kwargs,
        )
    if item_type == "frame":
        return client.create_frame(
            board_id,
            spec.get("title", ""),
            width=spec.get("width", 800),
            height=spec.get("height", 600),
            **kwargs,
        )
    if item_type == "image":
        return client.create_image(
            board_id,
            spec["url"],
            width=spec.get("width"),
            height=spec.get("height"),
            **kwargs,
        )
    if item_type == "document":
        return client.create_document(
            board_id,
            spec["title"],
            spec["url"],
            **kwargs,
        )
    if item_type == "embed":
        return client.create_embed(
            board_id,
            spec["url"],
            width=spec.get("width", 480),
            height=spec.get("height", 320),
            **kwargs,
        )
    if item_type == "connector":
        return client.create_connector(
            board_id,
            spec["start_item_id"],
            spec["end_item_id"],
            caption=spec.get("caption"),
        )
    if item_type == "tag":
        return client.create_tag(
            board_id,
            spec["title"],
            fill_color=spec.get("fill_color", "red"),
        )
    raise MiroError(f"unsupported item type in file: {item_type!r}")


def spec_to_bulk_item(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a spec dict to the ItemCreate shape used by the bulk endpoint.

    Mirrors the defaults applied by create_from_dict so a file produces the
    same items whether created individually or in bulk.
    """
    item_type = spec["type"]
    item: Dict[str, Any] = {
        "type": item_type,
        "position": {"x": spec.get("x", 0.0), "y": spec.get("y", 0.0), "origin": "center"},
    }
    if item_type == "sticky_note":
        item["data"] = {"content": spec["content"]}
        item["style"] = {"fillColor": spec.get("color", "light_yellow")}
        item["geometry"] = {"width": spec.get("width", 180)}
    elif item_type == "card":
        data: Dict[str, Any] = {
            "title": spec["title"],
            "description": spec.get("description", ""),
        }
        if spec.get("assignee_id"):
            data["assigneeId"] = spec["assignee_id"]
        item["data"] = data
        geometry: Dict[str, Any] = {"width": spec.get("width", 320)}
        if spec.get("height") is not None:
            geometry["height"] = spec["height"]
        item["geometry"] = geometry
    elif item_type == "text":
        item["data"] = {"content": spec["content"]}
        item["geometry"] = {"width": spec.get("width", 240)}
    elif item_type == "shape":
        item["data"] = {
            "content": spec.get("content", ""),
            "shape": spec.get("shape_type", "rectangle"),
        }
        item["style"] = {
            "fillColor": spec.get("fill_color", "#ffffff"),
            "borderColor": spec.get("border_color", "#1a1a1a"),
        }
        item["geometry"] = {
            "width": spec.get("width", 160),
            "height": spec.get("height", 80),
        }
    elif item_type == "frame":
        item["data"] = {"title": spec.get("title", "")}
        item["geometry"] = {"width": spec.get("width", 800), "height": spec.get("height", 600)}
        if spec.get("fill_color"):
            item["style"] = {"fillColor": spec["fill_color"]}
    elif item_type == "image":
        item["data"] = {"imageUrl": spec["url"]}
        width = spec.get("width")
        height = spec.get("height")
        if width or height:
            item["geometry"] = {
                "width": width if width else height,
                "height": height if height else width,
            }
    elif item_type == "document":
        item["data"] = {"title": spec["title"], "documentUrl": spec["url"]}
    elif item_type == "embed":
        item["data"] = {"url": spec["url"], "mode": spec.get("mode", "inline")}
        item["geometry"] = {"width": spec.get("width", 480), "height": spec.get("height", 320)}
    else:
        raise MiroError(f"unsupported item type in file: {item_type!r}")
    if spec.get("parent_id"):
        item["parent"] = {"id": spec["parent_id"]}
    return item


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(description="Create items on a Miro board.")
    parser.add_argument("--board-id", default=os.environ.get("MIRO_BOARD_ID"))
    parser.add_argument("--token", default=os.environ.get("MIRO_ACCESS_TOKEN"))
    sub = parser.add_subparsers(dest="command")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dry-run", action="store_true", help="validate without creating")
    common.add_argument("--file", metavar="JSON", help="create many items from a JSON file")

    sticky = sub.add_parser("sticky", help="create a sticky note", parents=[common])
    sticky.add_argument("content")
    sticky.add_argument("--x", type=float, default=0.0)
    sticky.add_argument("--y", type=float, default=0.0)
    sticky.add_argument("--color", default="light_yellow", choices=sorted(STICKY_COLORS))

    card = sub.add_parser("card", help="create a card", parents=[common])
    card.add_argument("--title", required=True)
    card.add_argument("--description", default="")
    card.add_argument("--assignee-id", dest="assignee_id")
    card.add_argument("--x", type=float, default=0.0)
    card.add_argument("--y", type=float, default=0.0)

    text = sub.add_parser("text", help="create a text item", parents=[common])
    text.add_argument("content")
    text.add_argument("--x", type=float, default=0.0)
    text.add_argument("--y", type=float, default=0.0)

    shape = sub.add_parser("shape", help="create a shape", parents=[common])
    shape.add_argument("content", nargs="?", default="")
    shape.add_argument("--shape-type", default="rectangle", choices=sorted(SHAPE_TYPES))
    shape.add_argument("--fill-color", default="#ffffff")
    shape.add_argument("--border-color", default="#1a1a1a")
    shape.add_argument("--x", type=float, default=0.0)
    shape.add_argument("--y", type=float, default=0.0)

    frame = sub.add_parser("frame", help="create a frame", parents=[common])
    frame.add_argument("--title", default="")
    frame.add_argument("--x", type=float, default=0.0)
    frame.add_argument("--y", type=float, default=0.0)
    frame.add_argument("--width", type=float, default=800)
    frame.add_argument("--height", type=float, default=600)

    image = sub.add_parser("image", help="create an image from a URL", parents=[common])
    image.add_argument("--url", required=True)
    image.add_argument("--x", type=float, default=0.0)
    image.add_argument("--y", type=float, default=0.0)
    image.add_argument("--width", type=float)
    image.add_argument("--height", type=float)

    document = sub.add_parser("document", help="create a document link", parents=[common])
    document.add_argument("--title", required=True)
    document.add_argument("--url", required=True)
    document.add_argument("--x", type=float, default=0.0)
    document.add_argument("--y", type=float, default=0.0)

    embed = sub.add_parser("embed", help="create an embedded webpage", parents=[common])
    embed.add_argument("--url", required=True)
    embed.add_argument("--x", type=float, default=0.0)
    embed.add_argument("--y", type=float, default=0.0)
    embed.add_argument("--width", type=float, default=480)
    embed.add_argument("--height", type=float, default=320)

    connector = sub.add_parser("connector", help="connect two items", parents=[common])
    connector.add_argument("--start-item-id", required=True)
    connector.add_argument("--end-item-id", required=True)
    connector.add_argument("--caption")
    connector.add_argument("--color", default="#1a1a1a")

    tag = sub.add_parser("tag", help="create a tag", parents=[common])
    tag.add_argument("--title", required=True)
    tag.add_argument("--fill-color", default="red")

    parser.add_argument("--file", metavar="JSON", help="create many items from a JSON file")
    parser.add_argument("--dry-run", action="store_true", help="validate without creating")
    args = parser.parse_args(argv)

    if not args.token:
        parser.error("missing access token (use --token or MIRO_ACCESS_TOKEN)")
    if not args.board_id:
        parser.error("missing board id (use --board-id or MIRO_BOARD_ID)")
    if not args.command and not args.file:
        parser.error("nothing to create: pass a subcommand or --file")

    if args.file:
        with open(args.file) as handle:
            specs = json.load(handle)
        if not isinstance(specs, list):
            parser.error("--file must contain a JSON list of items")
    else:
        specs = [spec_from_args(args)]

    client = MiroClient(args.token)
    console = Console()
    error_console = Console(stderr=True)
    created: List[Dict[str, Any]] = []
    bulk_specs: List[Dict[str, Any]] = []
    other_specs: List[Dict[str, Any]] = specs
    if args.file and not args.dry_run:
        bulk_specs = [s for s in specs if s["type"] in BULK_TYPES]
        other_specs = [s for s in specs if s["type"] not in BULK_TYPES]

    for i, spec in enumerate(other_specs):
        try:
            if args.dry_run:
                console.print(f"dry-run: would create {escape(spec['type'])}")
                created.append({"id": f"(dry-run {i})", "type": spec["type"]})
            else:
                item = create_from_dict(client, args.board_id, spec)
                created.append(item)
                console.print(
                    f"[green]created[/green] {escape(str(item.get('type')))} "
                    f"{escape(str(item['id']))}"
                )
        except MiroError as exc:
            error_console.print(
                f"[red]error on item {i} ({escape(str(spec.get('type', '?')))}):[/red] "
                f"{escape(str(exc))}"
            )
            return 1

    for start in range(0, len(bulk_specs), BULK_MAX_ITEMS):
        chunk = bulk_specs[start : start + BULK_MAX_ITEMS]
        try:
            items = client.create_items(
                args.board_id, [spec_to_bulk_item(spec) for spec in chunk]
            )
            for item in items:
                created.append(item)
                console.print(
                    f"[green]created[/green] {escape(str(item.get('type')))} "
                    f"{escape(str(item['id']))}"
                )
        except MiroError as exc:
            error_console.print(
                f"[red]error on items {start}-{start + len(chunk) - 1}:[/red] "
                f"{escape(str(exc))}"
            )
            return 1

    console.print(f"[green]Done.[/green] Created {len(created)} item(s).")
    return 0


def spec_from_args(args: argparse.Namespace) -> Dict[str, Any]:
    """Build a single item spec dict from parsed CLI arguments."""
    if args.command == "sticky":
        return {"type": "sticky_note", "content": args.content, "x": args.x, "y": args.y, "color": args.color}
    if args.command == "card":
        return {"type": "card", "title": args.title, "description": args.description, "assignee_id": args.assignee_id, "x": args.x, "y": args.y}
    if args.command == "text":
        return {"type": "text", "content": args.content, "x": args.x, "y": args.y}
    if args.command == "shape":
        return {"type": "shape", "content": args.content, "shape_type": args.shape_type, "fill_color": args.fill_color, "border_color": args.border_color, "x": args.x, "y": args.y}
    if args.command == "frame":
        return {"type": "frame", "title": args.title, "x": args.x, "y": args.y, "width": args.width, "height": args.height}
    if args.command == "image":
        return {"type": "image", "url": args.url, "x": args.x, "y": args.y, "width": args.width, "height": args.height}
    if args.command == "document":
        return {"type": "document", "title": args.title, "url": args.url, "x": args.x, "y": args.y}
    if args.command == "embed":
        return {"type": "embed", "url": args.url, "x": args.x, "y": args.y, "width": args.width, "height": args.height}
    if args.command == "connector":
        return {"type": "connector", "start_item_id": args.start_item_id, "end_item_id": args.end_item_id, "caption": args.caption, "color": args.color}
    if args.command == "tag":
        return {"type": "tag", "title": args.title, "fill_color": args.fill_color}
    raise MiroError(f"unsupported subcommand: {args.command!r}")


if __name__ == "__main__":
    sys.exit(main())
