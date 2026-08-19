"""Shared client access for the Miro MCP server.

The tools wrap the synchronous :class:`miro_client.MiroClient` from the parent
project. A single client is created lazily from ``MIRO_ACCESS_TOKEN`` so every
tool call reuses one HTTP session and one token lookup, and a board id can be
supplied per call or taken from ``MIRO_BOARD_ID``.
"""

import logging
import os

from dotenv import load_dotenv

from miro_client import MiroClient

# Load MIRO_ACCESS_TOKEN (and any other vars) from a .env file BEFORE reading
# the token below. Without this, a token placed in .env is never seen when the
# spawning process (e.g. an MCP client) doesn't already export it.
load_dotenv()

ACCESS_TOKEN = os.getenv("MIRO_ACCESS_TOKEN", "")

logger = logging.getLogger("miro_mcp")

_client: MiroClient | None = None


def _env_token() -> str:
    """Return the current value of MIRO_ACCESS_TOKEN (empty when unset)."""
    return os.getenv("MIRO_ACCESS_TOKEN", "")


def _env_board_id() -> str:
    """Return the current value of MIRO_BOARD_ID (empty when unset)."""
    return os.getenv("MIRO_BOARD_ID", "")


def get_client() -> MiroClient:
    """Return the process-wide, lazily-created Miro client."""
    global _client
    if _client is None:
        _client = MiroClient(_env_token())
    return _client


def reset_client() -> None:
    """Drop the cached client so a new one is built next time. For tests."""
    global _client
    _client = None


def require_board_id(board_id: str | None) -> str:
    """Resolve the board id from the argument or the MIRO_BOARD_ID env var."""
    resolved = board_id or _env_board_id()
    if not resolved:
        raise ValueError(
            "missing board id: pass board_id or set MIRO_BOARD_ID in the environment"
        )
    return resolved
