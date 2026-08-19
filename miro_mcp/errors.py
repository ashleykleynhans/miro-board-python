"""Custom exceptions for the Miro MCP server."""


class MiroMCError(RuntimeError):
    """Raised when the MCP server is misconfigured (e.g. missing token)."""
