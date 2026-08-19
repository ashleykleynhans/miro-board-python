"""Board read tools: list and inspect Miro boards."""

from mcp.server.fastmcp import FastMCP

from ..client import get_client, require_board_id


def list_boards() -> list[dict]:
    """List the boards the current user owns (or has access to).

    Returns:
        A list of board metadata dicts (id, name, description, owner, ...).
    """
    return get_client().list_boards()


def get_board(board_id: str | None = None) -> dict:
    """Get metadata for a single board.

    Args:
        board_id: The board id (falls back to MIRO_BOARD_ID).
    """
    return get_client().get_board(require_board_id(board_id))


def register(mcp: FastMCP) -> None:
    for fn in (list_boards, get_board):
        mcp.tool()(fn)
