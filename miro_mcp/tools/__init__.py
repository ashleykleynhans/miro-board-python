"""Tool registration.

Each submodule exposes plain functions (directly callable and unit testable)
plus a ``register(mcp)`` that wires them onto a ``FastMCP`` instance.
"""

from mcp.server.fastmcp import FastMCP

from . import boards, create, items, tags

__all__ = ["register_all"]


def register_all(mcp: FastMCP) -> None:
    """Register every tool submodule's functions onto ``mcp``."""
    for module in (boards, items, create, tags):
        module.register(mcp)
