"""Create tools for the common Miro item types."""

from mcp.server.fastmcp import FastMCP

from ..client import get_client, require_board_id


def create_sticky_note(
    content: str,
    x: float = 0.0,
    y: float = 0.0,
    color: str = "light_yellow",
    board_id: str | None = None,
) -> dict:
    """Create a sticky note at the given coordinates.

    Args:
        content: The sticky note text.
        x: The x coordinate.
        y: The y coordinate.
        color: The fill color (e.g. light_yellow, light_blue, red).
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    return client.create_sticky_note(board_id, content, x=x, y=y, color=color)


def create_card(
    title: str,
    description: str = "",
    assignee_id: str | None = None,
    x: float = 0.0,
    y: float = 0.0,
    board_id: str | None = None,
) -> dict:
    """Create a card with an optional title, description, and assignee.

    Args:
        title: The card title.
        description: The card description.
        assignee_id: The user id to assign the card to.
        x: The x coordinate.
        y: The y coordinate.
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    return client.create_card(
        board_id, title, description=description, assignee_id=assignee_id, x=x, y=y
    )


def create_text(
    content: str,
    x: float = 0.0,
    y: float = 0.0,
    width: float = 240,
    board_id: str | None = None,
) -> dict:
    """Create a text item at the given coordinates.

    Args:
        content: The text content.
        x: The x coordinate.
        y: The y coordinate.
        width: The width of the text item.
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    return client.create_text(board_id, content, x=x, y=y, width=width)


def create_shape(
    content: str = "",
    shape_type: str = "rectangle",
    x: float = 0.0,
    y: float = 0.0,
    fill_color: str = "#ffffff",
    border_color: str = "#1a1a1a",
    board_id: str | None = None,
) -> dict:
    """Create a shape (rectangle, circle, triangle, rhombus, ...).

    Args:
        content: The text inside the shape.
        shape_type: The shape type (e.g. rectangle, round_rectangle, circle,
            triangle, rhombus, parallelogram, trapezoid, pentagon, hexagon,
            octagon, star, cloud, cross, arrows, ...).
        x: The x coordinate.
        y: The y coordinate.
        fill_color: The fill color as a hex value.
        border_color: The border color as a hex value.
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    return client.create_shape(
        board_id,
        content,
        shape_type=shape_type,
        x=x,
        y=y,
        fill_color=fill_color,
        border_color=border_color,
    )


def create_frame(
    title: str = "",
    x: float = 0.0,
    y: float = 0.0,
    width: float = 800,
    height: float = 600,
    board_id: str | None = None,
) -> dict:
    """Create a frame to group items visually.

    Args:
        title: The frame title.
        x: The x coordinate.
        y: The y coordinate.
        width: The frame width.
        height: The frame height.
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    return client.create_frame(board_id, title, x=x, y=y, width=width, height=height)


def create_image(
    url: str,
    x: float = 0.0,
    y: float = 0.0,
    width: float | None = None,
    height: float | None = None,
    board_id: str | None = None,
) -> dict:
    """Create an image item from a public URL.

    Args:
        url: The public image URL.
        x: The x coordinate.
        y: The y coordinate.
        width: The width (falls back to the image's natural size).
        height: The height (falls back to the image's natural size).
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    return client.create_image(board_id, url, x=x, y=y, width=width, height=height)


def create_document(
    title: str,
    url: str,
    x: float = 0.0,
    y: float = 0.0,
    board_id: str | None = None,
) -> dict:
    """Create a document (link preview) item.

    Args:
        title: The document title.
        url: The document URL.
        x: The x coordinate.
        y: The y coordinate.
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    return client.create_document(board_id, title, url, x=x, y=y)


def create_embed(
    url: str,
    x: float = 0.0,
    y: float = 0.0,
    width: float = 480,
    height: float = 320,
    mode: str = "inline",
    board_id: str | None = None,
) -> dict:
    """Create an embedded webpage item.

    Args:
        url: The webpage URL to embed.
        x: The x coordinate.
        y: The y coordinate.
        width: The embed width.
        height: The embed height.
        mode: The embed mode (inline or compact).
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    return client.create_embed(
        board_id, url, x=x, y=y, width=width, height=height, mode=mode
    )


def create_connector(
    start_item_id: str,
    end_item_id: str,
    caption: str | None = None,
    color: str = "#1a1a1a",
    board_id: str | None = None,
) -> dict:
    """Connect two items with a connector line.

    Args:
        start_item_id: The id of the starting item.
        end_item_id: The id of the ending item.
        caption: Optional caption text on the line.
        color: The connector color as a hex value.
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    client = get_client()
    board_id = require_board_id(board_id)
    return client.create_connector(
        board_id, start_item_id, end_item_id, caption=caption, color=color
    )


def register(mcp: FastMCP) -> None:
    for fn in (
        create_sticky_note,
        create_card,
        create_text,
        create_shape,
        create_frame,
        create_image,
        create_document,
        create_embed,
        create_connector,
    ):
        mcp.tool()(fn)
