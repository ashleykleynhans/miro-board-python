#!/usr/bin/env python3
"""Miro MCP Server - Manage Miro boards from an MCP client.

Thin entry point: the real implementation lives in the :mod:`miro_mcp`
package. Kept as a module so the documented ``python server.py`` invocation
keeps working (the installed ``miro mcp-server`` command, via
:mod:`miro_cli`, calls :mod:`miro_mcp` directly rather than through this
file).
"""

from miro_mcp import main  # noqa: F401  (re-exported for the python server.py invocation)

if __name__ == "__main__":  # pragma: no cover
    main()
