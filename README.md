# Miro Board POC

Proof of concept for reading, writing, and updating a Miro board through the
[Miro REST API v2](https://developers.miro.com/reference/api-reference) using
an access token.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# put your token and board id in .env, then:
set -a && source .env && set +a
```

Get a token from the **Miro REST API** section of a board's share menu, or from
a [Miro developer app](https://developers.miro.com). The token needs `boards:read`
and `boards:write` scopes.

Board id is the numeric part of the board URL, e.g. for
`https://miro.com/app/board/uxXXXXXXXXXXXXX/` the id is `uxXXXXXXXXXXXXX`.

## Read

```bash
python read_board.py --board-id uxXXXXXXXXXXXXX
python read_board.py --board-id uxXXXXXXXXXXXXX --json items.json
python read_board.py --board-id uxXXXXXXXXXXXXX --item-type card
```

## Write

```bash
python write_board.py --board-id uxXXXXXXXXXXXXX sticky "Hello world" --x 100 --y 200
python write_board.py --board-id uxXXXXXXXXXXXXX card --title "Task" --description "Do it"
python write_board.py --board-id uxXXXXXXXXXXXXX text "Notes" --x 600
python write_board.py --board-id uxXXXXXXXXXXXXX shape "Decision" --shape-type diamond
python write_board.py --board-id uxXXXXXXXXXXXXX frame --title "Section" --width 1000
python write_board.py --board-id uxXXXXXXXXXXXXX image --url https://example.com/pic.png
python write_board.py --board-id uxXXXXXXXXXXXXX document --title "Spec" --url https://example.com/doc
python write_board.py --board-id uxXXXXXXXXXXXXX embed --url https://example.com
python write_board.py --board-id uxXXXXXXXXXXXXX connector --start-item-id <id> --end-item-id <id> --caption "links to"
python write_board.py --board-id uxXXXXXXXXXXXXX tag --title urgent --fill-color red
python write_board.py --board-id uxXXXXXXXXXXXXX --file items.json --dry-run
```

Batch file (`items.json`):

```json
[
  {"type": "sticky_note", "content": "Idea", "color": "light_yellow", "x": 0, "y": 0},
  {"type": "card", "title": "Task 1", "description": "Details", "x": 300, "y": 0},
  {"type": "text", "content": "Section header", "x": 600, "y": 0},
  {"type": "shape", "content": "Decision", "shape_type": "diamond", "x": 900, "y": 0},
  {"type": "frame", "title": "Section", "width": 1000, "height": 700},
  {"type": "image", "url": "https://example.com/pic.png", "width": 400, "height": 300},
  {"type": "connector", "start_item_id": "123", "end_item_id": "456", "caption": "links to"}
]
```

Supported types in batch files: `sticky_note`, `card`, `text`, `shape`, `frame`,
`image`, `document`, `embed`, `connector`, `tag`.

## Update / delete

```bash
python update_board.py --board-id uxXXXXXXXXXXXXX set-text <item-id> "New text"
python update_board.py --board-id uxXXXXXXXXXXXXX set-color <item-id> --color light_blue
python update_board.py --board-id uxXXXXXXXXXXXXX resize <item-id> --width 300 --height 200
python update_board.py --board-id uxXXXXXXXXXXXXX move <item-id> --x 500 --y 300
python update_board.py --board-id uxXXXXXXXXXXXXX tag <item-id> <tag-id>
python update_board.py --board-id uxXXXXXXXXXXXXX delete <item-id>
python update_board.py --board-id uxXXXXXXXXXXXXX update --file changes.json --dry-run
```

Batch file (`changes.json`):

```json
[
  {"op": "set-text", "item_id": "3456789012345", "content": "Updated"},
  {"op": "set-color", "item_id": "3456789012345", "color": "light_blue"},
  {"op": "resize", "item_id": "3456789012345", "width": 300, "height": 200},
  {"op": "move", "item_id": "3456789012345", "x": 100, "y": 200},
  {"op": "tag", "item_id": "3456789012345", "tag_id": "7654321098765"},
  {"op": "delete", "item_id": "3456789012345"},
  {"op": "update", "item_id": "3456789012345",
   "data": {"content": "x"}, "style": {"fillColor": "green"}}
]
```

Item ids come from `read_board.py --json items.json`.

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

Coverage runs by default and must be 100%, otherwise the test run fails.
Tests use a fake HTTP layer, so no Miro token or network is required.

## Library

`miro_client.py` also works as a library:

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
