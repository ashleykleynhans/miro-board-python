"""Core client for the Miro REST API v2.

Thin, token-based wrapper around https://api.miro.com/v2 with helpers for
reading, creating, updating, and deleting board items.

Requires an access token, obtained from a Miro developer app or board share
menu, passed either directly or via the MIRO_ACCESS_TOKEN environment variable.

The v2 API uses per-item-type endpoints: sticky notes, cards, shapes, frames,
images, documents, embeds, and app cards are created and updated through their
own paths (e.g. POST /boards/{board_id}/sticky_notes) rather than a polymorphic
/items endpoint.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Iterator, List, Optional

import requests

API_BASE = "https://api.miro.com/v2"

SHAPE_TYPES = {
    "rectangle",
    "round_rectangle",
    "circle",
    "triangle",
    "rhombus",
    "parallelogram",
    "trapezoid",
    "pentagon",
    "hexagon",
    "octagon",
    "wedge_round_rectangle_callout",
    "star",
    "flow_chart_predefined_process",
    "cloud",
    "cross",
    "can",
    "right_arrow",
    "left_arrow",
    "left_right_arrow",
    "left_brace",
    "right_brace",
}

ITEM_ENDPOINTS = {
    "sticky_note": "sticky_notes",
    "card": "cards",
    "text": "texts",
    "shape": "shapes",
    "frame": "frames",
    "image": "images",
    "document": "documents",
    "embed": "embeds",
    "app_card": "app_cards",
}


class MiroError(Exception):
    """Raised when the Miro API returns an error response."""


class MiroClient:
    """Stateless client for the Miro REST API v2."""

    def __init__(self, access_token: str) -> None:
        """Initialize the client with the given OAuth access token."""
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }
        )

    # ------------------------------------------------------------------ raw
    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        retries: int = 3,
    ) -> Any:
        """Send a request to the Miro API and return the decoded JSON body."""
        url = f"{API_BASE}{path}"
        for attempt in range(retries):
            response = self._session.request(method, url, params=params, json=json)
            if response.status_code in (429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(1 + attempt)
                continue
            break
        if not 200 <= response.status_code < 300:
            detail = response.text[:500]
            if response.status_code == 405:
                detail += (
                    " (hint: this endpoint does not support that method; "
                    "current Miro APIs use per-item-type endpoints such as "
                    "POST /boards/{board_id}/sticky_notes)"
                )
            raise MiroError(f"{method} {path} -> HTTP {response.status_code}: {detail}")
        if not response.content:
            return None
        return response.json()

    def _paginate(self, path: str, params: Optional[Dict[str, Any]] = None) -> Iterator[Dict[str, Any]]:
        """Yield every item across all pages of a cursor-paginated endpoint."""
        cursor: Optional[str] = None
        while True:
            page_params = dict(params or {})
            if cursor:
                page_params["cursor"] = cursor
            payload = self._request("GET", path, params=page_params)
            for item in payload.get("data", []):
                yield item
            cursor = payload.get("cursor")
            if not cursor:
                break

    def _item_path(self, board_id: str, item_type: str) -> str:
        """Return the per-type item collection path for an item type."""
        endpoint = ITEM_ENDPOINTS.get(item_type)
        if endpoint is None:
            raise MiroError(f"unsupported item type: {item_type!r}")
        return f"/boards/{board_id}/{endpoint}"

    def _resolve_item_type(self, board_id: str, item_id: str) -> str:
        """Look up an item's type so it can be updated via its type endpoint."""
        item = self.get_item(board_id, item_id)
        item_type = item.get("type")
        if item_type not in ITEM_ENDPOINTS:
            raise MiroError(f"cannot update unsupported item type: {item_type!r}")
        return item_type

    # ------------------------------------------------------------- boards
    def get_board(self, board_id: str) -> Dict[str, Any]:
        """Return metadata for a single board."""
        return self._request("GET", f"/boards/{board_id}")

    def list_boards(self) -> List[Dict[str, Any]]:
        """Return the boards owned by the current user (paginated internally)."""
        return list(self._paginate("/boards", {"limit": 50}))

    # --------------------------------------------------------------- items
    def list_items(
        self, board_id: str, *, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Return all items on a board (paginated internally)."""
        return list(self._paginate(f"/boards/{board_id}/items", {"limit": limit}))

    def get_item(self, board_id: str, item_id: str) -> Dict[str, Any]:
        """Return a single item by its id."""
        return self._request("GET", f"/boards/{board_id}/items/{item_id}")

    def create_item(
        self,
        board_id: str,
        item_type: str,
        *,
        data: Optional[Dict[str, Any]] = None,
        style: Optional[Dict[str, Any]] = None,
        position: Optional[Dict[str, Any]] = None,
        geometry: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an item of the given type via its per-type endpoint."""
        body: Dict[str, Any] = {}
        for key, value in {
            "data": data,
            "style": style,
            "position": position,
            "geometry": geometry,
            "parent": {"id": parent_id} if parent_id else None,
        }.items():
            if value is not None:
                body[key] = value
        return self._request("POST", self._item_path(board_id, item_type), json=body)

    def update_item(
        self,
        board_id: str,
        item_id: str,
        *,
        data: Optional[Dict[str, Any]] = None,
        style: Optional[Dict[str, Any]] = None,
        position: Optional[Dict[str, Any]] = None,
        geometry: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None,
        item_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Partially update an item through its per-type endpoint.

        Only supplied fields are changed. If item_type is omitted it is
        resolved from the item itself.
        """
        if item_type is None:
            item_type = self._resolve_item_type(board_id, item_id)
        body: Dict[str, Any] = {}
        for key, value in {
            "data": data,
            "style": style,
            "position": position,
            "geometry": geometry,
            "parent": {"id": parent_id} if parent_id else None,
        }.items():
            if value is not None:
                body[key] = value
        return self._request(
            "PATCH", f"{self._item_path(board_id, item_type)}/{item_id}", json=body
        )

    def delete_item(self, board_id: str, item_id: str) -> None:
        """Delete an item from a board."""
        self._request("DELETE", f"/boards/{board_id}/items/{item_id}")

    # ---------------------------------------------------------- conveniences
    def create_sticky_note(
        self,
        board_id: str,
        content: str,
        *,
        x: float = 0.0,
        y: float = 0.0,
        color: str = "light_yellow",
        width: float = 180,
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a sticky note at the given coordinates.

        Sticky notes have a fixed aspect ratio in Miro: only `width` can be
        given (Miro rejects a request that also specifies `height` with
        "Only height or width should be passed for widgets with fixed
        aspect ratio"). Miro derives the actual height from `width`.
        """
        return self.create_item(
            board_id,
            "sticky_note",
            data={"content": content},
            style={"fillColor": color},
            position={"x": x, "y": y, "origin": "center"},
            geometry={"width": width},
            parent_id=parent_id,
        )

    def create_card(
        self,
        board_id: str,
        title: str,
        *,
        description: str = "",
        assignee_id: Optional[str] = None,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 320,
        height: Optional[float] = None,
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a card with an optional title, description, and assignee.

        Miro collapses a card to its own default height (not the caller's
        intended layout height) unless `height` is given explicitly.
        """
        data: Dict[str, Any] = {
            "title": title,
            "description": description,
            "assigneeId": assignee_id,
        }
        geometry: Dict[str, Any] = {"width": width}
        if height is not None:
            geometry["height"] = height
        return self.create_item(
            board_id,
            "card",
            data=data,
            position={"x": x, "y": y, "origin": "center"},
            geometry=geometry,
            parent_id=parent_id,
        )

    def create_text(
        self,
        board_id: str,
        content: str,
        *,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 240,
    ) -> Dict[str, Any]:
        """Create a text item at the given coordinates."""
        return self.create_item(
            board_id,
            "text",
            data={"content": content},
            position={"x": x, "y": y, "origin": "center"},
            geometry={"width": width},
        )

    def create_shape(
        self,
        board_id: str,
        content: str = "",
        *,
        shape_type: str = "rectangle",
        x: float = 0.0,
        y: float = 0.0,
        fill_color: str = "#ffffff",
        border_color: str = "#1a1a1a",
    ) -> Dict[str, Any]:
        """Create a shape (rectangle, circle, triangle, ...)."""
        return self.create_item(
            board_id,
            "shape",
            data={"content": content, "shape": shape_type},
            style={"fillColor": fill_color, "borderColor": border_color},
            position={"x": x, "y": y, "origin": "center"},
            geometry={"width": 160, "height": 80},
        )

    def create_frame(
        self,
        board_id: str,
        title: str = "",
        *,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 800,
        height: float = 600,
        fill_color: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a frame to group items visually, optionally with a fill color."""
        return self.create_item(
            board_id,
            "frame",
            data={"title": title},
            style={"fillColor": fill_color} if fill_color else None,
            position={"x": x, "y": y, "origin": "center"},
            geometry={"width": width, "height": height},
        )

    def add_to_frame(
        self, board_id: str, frame_id: str, item_id: str
    ) -> Dict[str, Any]:
        """Move an existing item inside a frame."""
        return self._request(
            "PATCH",
            f"/boards/{board_id}/items/{item_id}",
            json={"parent": {"id": frame_id}},
        )

    def create_image(
        self,
        board_id: str,
        url: str,
        *,
        x: float = 0.0,
        y: float = 0.0,
        width: Optional[float] = None,
        height: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Create an image item from a public URL."""
        geometry: Optional[Dict[str, Any]] = None
        if width or height:
            geometry = {
                "width": width if width else height,
                "height": height if height else width,
            }
        return self.create_item(
            board_id,
            "image",
            data={"imageUrl": url},
            position={"x": x, "y": y, "origin": "center"},
            geometry=geometry,
        )

    def create_document(
        self,
        board_id: str,
        title: str,
        url: str,
        *,
        x: float = 0.0,
        y: float = 0.0,
    ) -> Dict[str, Any]:
        """Create a document (link preview) item."""
        return self.create_item(
            board_id,
            "document",
            data={"title": title, "documentUrl": url},
            position={"x": x, "y": y, "origin": "center"},
        )

    def create_embed(
        self,
        board_id: str,
        url: str,
        *,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 480,
        height: float = 320,
        mode: str = "inline",
    ) -> Dict[str, Any]:
        """Create an embedded webpage item."""
        return self.create_item(
            board_id,
            "embed",
            data={"url": url, "mode": mode},
            position={"x": x, "y": y, "origin": "center"},
            geometry={"width": width, "height": height},
        )

    # --------------------------------------------------------- connectors
    def create_connector(
        self,
        board_id: str,
        start_item_id: str,
        end_item_id: str,
        *,
        caption: Optional[str] = None,
        color: str = "#1a1a1a",
    ) -> Dict[str, Any]:
        """Connect two items with a connector line."""
        body: Dict[str, Any] = {
            "startItem": {"id": start_item_id},
            "endItem": {"id": end_item_id},
            "style": {"color": color},
        }
        if caption:
            body["captions"] = [{"text": caption}]
        return self._request("POST", f"/boards/{board_id}/connectors", json=body)

    # --------------------------------------------------------------- tags
    def list_tags(self, board_id: str) -> List[Dict[str, Any]]:
        """Return all tags on a board."""
        return list(self._paginate(f"/boards/{board_id}/tags"))

    def create_tag(
        self,
        board_id: str,
        title: str,
        *,
        fill_color: str = "red",
    ) -> Dict[str, Any]:
        """Create a tag with the given title and fill color."""
        return self._request(
            "POST",
            f"/boards/{board_id}/tags",
            json={"title": title, "fillColor": fill_color},
        )

    def assign_tag(self, board_id: str, item_id: str, tag_id: str) -> Dict[str, Any]:
        """Assign a tag to an item."""
        return self._request(
            "POST", f"/boards/{board_id}/items/{item_id}", params={"tag_id": tag_id}
        )

    # -------------------------------------------------------------- update
    def move_item(
        self,
        board_id: str,
        item_id: str,
        *,
        x: float,
        y: float,
    ) -> Dict[str, Any]:
        """Move an item to new coordinates."""
        return self._request(
            "PATCH",
            f"/boards/{board_id}/items/{item_id}",
            json={"position": {"x": x, "y": y}},
        )

    def set_sticky_note_text(
        self, board_id: str, item_id: str, content: str
    ) -> Dict[str, Any]:
        """Replace the content of a sticky note."""
        return self.update_item(
            board_id, item_id, item_type="sticky_note", data={"content": content}
        )

    def resize_item(
        self,
        board_id: str,
        item_id: str,
        *,
        width: Optional[float] = None,
        height: Optional[float] = None,
        item_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Resize an item. Omitted dimensions keep their current value."""
        geometry: Dict[str, Any] = {}
        if width:
            geometry["width"] = width
        if height:
            geometry["height"] = height
        return self.update_item(
            board_id, item_id, item_type=item_type, geometry=geometry or None
        )

    def set_item_color(
        self,
        board_id: str,
        item_id: str,
        color: str,
        *,
        item_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Set the fill color of a sticky note or shape."""
        return self.update_item(
            board_id, item_id, item_type=item_type, style={"fillColor": color}
        )

    def update_shape(
        self,
        board_id: str,
        item_id: str,
        *,
        content: Optional[str] = None,
        shape_type: Optional[str] = None,
        fill_color: Optional[str] = None,
        border_color: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update the content or style of a shape."""
        data: Dict[str, Any] = {}
        if content is not None:
            data["content"] = content
        if shape_type is not None:
            data["shape"] = shape_type
        style: Dict[str, Any] = {}
        if fill_color is not None:
            style["fillColor"] = fill_color
        if border_color is not None:
            style["borderColor"] = border_color
        return self.update_item(
            board_id,
            item_id,
            item_type="shape",
            data=data or None,
            style=style or None,
        )

    @staticmethod
    def from_env() -> "MiroClient":
        """Build a client from the MIRO_ACCESS_TOKEN environment variable."""
        token = os.environ.get("MIRO_ACCESS_TOKEN")
        if not token:
            raise MiroError(
                "MIRO_ACCESS_TOKEN is not set. Create a Miro developer app "
                "and export the token, e.g. 'export MIRO_ACCESS_TOKEN=...'"
            )
        return MiroClient(token)
