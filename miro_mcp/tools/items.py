"""Item tools: list, create, update, move, resize, and delete board items."""

from mcp.server.fastmcp import FastMCP

from ..client import get_client, require_board_id


def list_items(board_id: str | None = None, item_type: str | None = None) -> list[dict]:
    """List all items on a board, optionally filtered by type.

    Args:
        board_id: The board id (falls back to MIRO_BOARD_ID).
        item_type: Only return items of this type (sticky_note, card, text,
            shape, frame, image, document, embed, ...).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    items = client.list_items(board_id)
    if item_type:
        items = [item for item in items if item.get("type") == item_type]
    return items


def get_item(item_id: str, board_id: str | None = None) -> dict:
    """Get a single item by its id.

    Args:
        item_id: The item id.
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    return get_client().get_item(require_board_id(board_id), item_id)


def create_item(
    item_type: str,
    data: dict | None = None,
    style: dict | None = None,
    position: dict | None = None,
    geometry: dict | None = None,
    parent_id: str | None = None,
    board_id: str | None = None,
) -> dict:
    """Create an item of any supported type via its per-type endpoint.

    Args:
        item_type: The item type (sticky_note, card, text, shape, frame,
            image, document, embed, app_card).
        data: Type-specific payload, e.g. {"content": "..."} for sticky notes.
        style: Style overrides, e.g. {"fillColor": "light_yellow"}.
        position: Position, e.g. {"x": 0, "y": 0, "origin": "center"}.
        geometry: Size, e.g. {"width": 180}.
        parent_id: Optional parent frame id.
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    return client.create_item(
        board_id,
        item_type,
        data=data,
        style=style,
        position=position,
        geometry=geometry,
        parent_id=parent_id,
    )


def update_item(
    item_id: str,
    data: dict | None = None,
    style: dict | None = None,
    position: dict | None = None,
    geometry: dict | None = None,
    item_type: str | None = None,
    parent_id: str | None = None,
    board_id: str | None = None,
) -> dict:
    """Partially update an item.

    Args:
        item_id: The item id.
        data: Type-specific payload, e.g. {"content": "..."}.
        style: Style overrides, e.g. {"fillColor": "green"}.
        position: Position, e.g. {"x": 100, "y": 200}.
        geometry: Size, e.g. {"width": 300, "height": 200}.
        item_type: The item type. Omit to look it up automatically.
        parent_id: Optional parent frame id.
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    return client.update_item(
        board_id,
        item_id,
        data=data,
        style=style,
        position=position,
        geometry=geometry,
        item_type=item_type,
        parent_id=parent_id,
    )


def delete_item(item_id: str, board_id: str | None = None) -> dict:
    """Delete an item from a board.

    Args:
        item_id: The item id.
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    client.delete_item(board_id, item_id)
    return {"deleted_item_id": item_id}


def set_text(item_id: str, content: str, board_id: str | None = None) -> dict:
    """Replace the content of a sticky note.

    Args:
        item_id: The sticky note id.
        content: The new content.
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    return client.set_sticky_note_text(board_id, item_id, content)


def set_color(
    item_id: str,
    color: str,
    item_type: str | None = None,
    board_id: str | None = None,
) -> dict:
    """Set the fill color of a sticky note or shape.

    Args:
        item_id: The item id.
        color: The fill color (e.g. light_yellow, light_blue, #ff0000).
        item_type: The item type. Omit to look it up automatically.
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    return client.set_item_color(board_id, item_id, color, item_type=item_type)


def resize_item(
    item_id: str,
    width: float | None = None,
    height: float | None = None,
    item_type: str | None = None,
    board_id: str | None = None,
) -> dict:
    """Resize an item. Omitted dimensions keep their current value.

    Args:
        item_id: The item id.
        width: New width.
        height: New height.
        item_type: The item type. Omit to look it up automatically.
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    return client.resize_item(
        board_id, item_id, width=width, height=height, item_type=item_type
    )


def move_item(
    item_id: str, x: float, y: float, board_id: str | None = None
) -> dict:
    """Move an item to new coordinates.

    Args:
        item_id: The item id.
        x: The new x coordinate.
        y: The new y coordinate.
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    return client.move_item(board_id, item_id, x=x, y=y)


def add_to_frame(
    frame_id: str, item_id: str, board_id: str | None = None
) -> dict:
    """Move an existing item inside a frame.

    Args:
        frame_id: The frame item id.
        item_id: The item to move into the frame.
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    return client.add_to_frame(board_id, frame_id, item_id)


def register(mcp: FastMCP) -> None:
    for fn in (
        list_items,
        get_item,
        create_item,
        update_item,
        delete_item,
        set_text,
        set_color,
        resize_item,
        move_item,
        add_to_frame,
    ):
        mcp.tool()(fn)
