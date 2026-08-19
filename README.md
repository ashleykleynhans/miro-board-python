# miro-board-python

![PyPI](https://img.shields.io/pypi/v/miro-board)
![Python Versions](https://img.shields.io/pypi/pyversions/miro-board)
![License](https://img.shields.io/pypi/l/miro-board)
![CI](https://github.com/ashleykleynhans/miro-board-python/actions/workflows/ci.yml/badge.svg?branch=main)

Python CLI and library for reading, writing, and updating a Miro board through
the [Miro REST API v2](https://developers.miro.com/reference/api-reference)
using an access token. Also ships an [MCP](https://modelcontextprotocol.io)
server so MCP clients (e.g. Claude Code) can work with a board directly.

## Installation

```bash
pip install miro-board
```

This installs the library (`miro_client`) and a `miro` command with four
actions: `read`, `write`, `update`, and `mcp-server`.

## Setup

Get a token from the **Miro REST API** section of a board's share menu, or
from a [Miro developer app](https://developers.miro.com). The token needs
`boards:read` and `boards:write` scopes.

Note: the "Miro REST API" token from a board's Share menu is **read-only**. It
works for `miro read`, but `miro write` and `miro update` will fail with HTTP
405. For write access, create a developer app and use an OAuth 2.0 access
token with the `boards:read` and `boards:write` scopes.

Board id is the numeric part of the board URL, e.g. for
`https://miro.com/app/board/uxXXXXXXXXXXXXX/` the id is `uxXXXXXXXXXXXXX`.

Export the token and board id as environment variables so you don't have to
pass them on every command:

```bash
export MIRO_ACCESS_TOKEN=your_token
export MIRO_BOARD_ID=uxXXXXXXXXXXXXX
```

Both can also be passed explicitly with `--token` and `--board-id` on any
command.

## Read

```bash
miro read --board-id uxXXXXXXXXXXXXX
miro read --board-id uxXXXXXXXXXXXXX --json items.json
miro read --board-id uxXXXXXXXXXXXXX --item-type card
```

## Write

```bash
miro write --board-id uxXXXXXXXXXXXXX sticky "Hello world" --x 100 --y 200
miro write --board-id uxXXXXXXXXXXXXX card --title "Task" --description "Do it"
miro write --board-id uxXXXXXXXXXXXXX text "Notes" --x 600
miro write --board-id uxXXXXXXXXXXXXX shape "Decision" --shape-type rhombus
miro write --board-id uxXXXXXXXXXXXXX frame --title "Section" --width 1000
miro write --board-id uxXXXXXXXXXXXXX image --url https://example.com/pic.png
miro write --board-id uxXXXXXXXXXXXXX document --title "Spec" --url https://example.com/doc
miro write --board-id uxXXXXXXXXXXXXX embed --url https://example.com
miro write --board-id uxXXXXXXXXXXXXX connector --start-item-id <id> --end-item-id <id> --caption "links to"
miro write --board-id uxXXXXXXXXXXXXX tag --title urgent --fill-color red
miro write --board-id uxXXXXXXXXXXXXX --file items.json --dry-run
```

Batch file (`items.json`):

```json
[
  {"type": "sticky_note", "content": "Idea", "color": "light_yellow", "x": 0, "y": 0},
  {"type": "card", "title": "Task 1", "description": "Details", "x": 300, "y": 0},
  {"type": "text", "content": "Section header", "x": 600, "y": 0},
  {"type": "shape", "content": "Decision", "shape_type": "rhombus", "x": 900, "y": 0},
  {"type": "frame", "title": "Section", "width": 1000, "height": 700},
  {"type": "image", "url": "https://example.com/pic.png", "width": 400, "height": 300},
  {"type": "connector", "start_item_id": "123", "end_item_id": "456", "caption": "links to"}
]
```

Supported types in batch files: `sticky_note`, `card`, `text`, `shape`, `frame`,
`image`, `document`, `embed`, `connector`, `tag`.

## Update / delete

```bash
miro update --board-id uxXXXXXXXXXXXXX set-text <item-id> "New text"
miro update --board-id uxXXXXXXXXXXXXX set-color <item-id> --color light_blue
miro update --board-id uxXXXXXXXXXXXXX resize <item-id> --width 300 --height 200
miro update --board-id uxXXXXXXXXXXXXX move <item-id> --x 500 --y 300
miro update --board-id uxXXXXXXXXXXXXX tag <item-id> <tag-id>
miro update --board-id uxXXXXXXXXXXXXX delete <item-id>
miro update --board-id uxXXXXXXXXXXXXX update --file changes.json --dry-run
```

Batch file (`changes.json`):

```json
[
  {"op": "set-text", "item_id": "3456789012345", "content": "Updated"},
  {"op": "set-color", "item_id": "3456789012345", "color": "light_blue", "item_type": "sticky_note"},
  {"op": "resize", "item_id": "3456789012345", "width": 300, "height": 200, "item_type": "shape"},
  {"op": "move", "item_id": "3456789012345", "x": 100, "y": 200},
  {"op": "tag", "item_id": "3456789012345", "tag_id": "7654321098765"},
  {"op": "delete", "item_id": "3456789012345"},
  {"op": "update", "item_id": "3456789012345", "item_type": "shape",
   "data": {"content": "x"}, "style": {"fillColor": "green"}}
]
```

Item ids come from `miro read --board-id uxXXXXXXXXXXXXX --json items.json`.
Updates that change an item's content, style, or size need an `item_type`
(sticky_note, card, text, shape, frame, image, document, embed); when omitted
the type is looked up automatically.

## MCP server

The same library powers an MCP server so MCP clients (e.g. Claude Code) can
read and write Miro boards directly.

```bash
miro mcp-server
```

Configure the client in your MCP client config. For Claude Code, add to
`.claude/settings.json` (or your opencode config):

```json
{
  "mcpServers": {
    "miro": {
      "command": "miro",
      "args": ["mcp-server"],
      "env": {
        "MIRO_ACCESS_TOKEN": "your_token",
        "MIRO_BOARD_ID": "uxXXXXXXXXXXXXX"
      }
    }
  }
}
```

The transport defaults to `stdio`; set `MIRO_MCP_TRANSPORT` to `sse` or
`streamable-http` to change it. Board ids fall back to `MIRO_BOARD_ID` when not
passed per call. The server exposes 24 tools: boards, items (create/update/
move/resize/delete), sticky notes, cards, text, shapes, frames, images,
documents, embeds, connectors, and tags.

## Library

`miro_client` also works as a library:

```python
from miro_client import MiroClient

client = MiroClient.from_env()
board = client.get_board("uxXXXXXXXXXXXXX")
sticky = client.create_sticky_note(board["id"], "Hello", x=0, y=0)
client.set_sticky_note_text(board["id"], sticky["id"], "Updated")
```

Supported item helpers: sticky notes, cards, text, shapes, frames, images,
documents, embeds, connectors, and tags. Arbitrary item types can be created
through `client.create_item(...)`.

## Development

To work on the package itself, clone the repository and set up a virtual
environment from source:

```bash
git clone https://github.com/ashleykleynhans/miro-board-python.git
cd miro-board-python
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# Windows (PowerShell): .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# put your token and board id in .env, then:
set -a && source .env && set +a
```

From a local clone, the individual scripts also still work directly, without
going through the `miro` command, e.g. `python read_board.py --board-id ...`,
`python write_board.py --board-id ... sticky "..."`,
`python update_board.py --board-id ... set-text ...`, and `python server.py`
for the MCP server.

## Testing

With the venv active, install the dev dependencies and run the tests:

```bash
pip install -r requirements-dev.txt
pytest
```

Coverage runs by default and must be 100%, otherwise the test run fails.
Tests use a fake HTTP layer, so no Miro token or network is required.

Tests also run automatically on every push to GitHub via a CI workflow; pushes
that only touch irrelevant files (such as `*.md`) are skipped.
