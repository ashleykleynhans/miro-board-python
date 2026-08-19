"""Miro MCP server package.

Exposes :func:`create_mcp` (build a configured ``FastMCP`` with all tools) and
:func:`main` (validate config + run the server). Tool functions live in
:mod:`miro_mcp.tools` and are plain functions that wrap the synchronous
:class:`miro_client.MiroClient` from this repository - :func:`tools.register_all`
wires them onto a ``FastMCP`` instance.
"""

import logging
import os
import sys

from mcp.server.fastmcp import FastMCP

from . import tools
from .client import ACCESS_TOKEN
from .errors import MiroMCError

__all__ = ["create_mcp", "main", "MiroMCError"]

_ALLOWED_TRANSPORTS = {"stdio", "sse", "streamable-http"}


def create_mcp() -> FastMCP:
    """Build a FastMCP server with all Miro tools registered."""
    mcp = FastMCP("miro")
    tools.register_all(mcp)
    return mcp


def _configure_logging() -> None:
    """Configure stderr logging for the package from MIRO_MCP_LOG_LEVEL."""
    level_name = os.getenv("MIRO_MCP_LOG_LEVEL", "WARNING").upper()
    level = getattr(logging, level_name, logging.WARNING)
    logger = logging.getLogger("miro_mcp")
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        logger.addHandler(handler)


def main() -> None:
    """Entry point: validate config and run the MCP server."""
    _configure_logging()
    if not ACCESS_TOKEN:
        raise MiroMCError(
            "MIRO_ACCESS_TOKEN is not set. Copy .env.example to .env and add your token."
        )
    transport = os.getenv("MIRO_MCP_TRANSPORT", "stdio")
    if transport not in _ALLOWED_TRANSPORTS:
        raise MiroMCError(
            f"Unsupported MIRO_MCP_TRANSPORT={transport!r}. "
            f"Choose one of: {', '.join(sorted(_ALLOWED_TRANSPORTS))}."
        )
    mcp = create_mcp()
    mcp.run(transport=transport)
