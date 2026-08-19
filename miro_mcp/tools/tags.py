"""Tag tools: list, create, and assign tags on a board."""

from mcp.server.fastmcp import FastMCP

from ..client import get_client, require_board_id


def list_tags(board_id: str | None = None) -> list[dict]:
    """List all tags on a board.

    Args:
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    return client.list_tags(board_id)


def create_tag(
    title: str,
    fill_color: str = "red",
    board_id: str | None = None,
) -> dict:
    """Create a tag with the given title and fill color.

    Args:
        title: The tag title.
        fill_color: The tag fill color (e.g. red, green, blue).
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    return client.create_tag(board_id, title, fill_color=fill_color)


def assign_tag(
    item_id: str, tag_id: str, board_id: str | None = None
) -> dict:
    """Assign a tag to an item.

    Args:
        item_id: The item id.
        tag_id: The tag id.
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    return client.assign_tag(board_id, item_id, tag_id)


def register(mcp: FastMCP) -> None:
    for fn in (list_tags, create_tag, assign_tag):
        mcp.tool()(fn)
