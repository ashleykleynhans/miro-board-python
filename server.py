#!/usr/bin/env python3
"""Miro MCP Server - Manage Miro boards from an MCP client.

Thin entry point: the real implementation lives in the :mod:`miro_mcp`
package. Kept as a module so the ``miro-mcp-server`` console script and the
documented ``python server.py`` invocation both keep working.
"""

from miro_mcp import main  # noqa: F401  (re-exported for entry point)

if __name__ == "__main__":  # pragma: no cover
    main()
