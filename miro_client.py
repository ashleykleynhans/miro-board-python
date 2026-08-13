"""Core client for the Miro REST API v2.

Thin, token-based wrapper around https://api.miro.com/v2 with helpers for
reading, creating, updating, and deleting board items.

Requires an access token, obtained from a Miro developer app or board share
menu, passed either directly or via the MIRO_ACCESS_TOKEN environment variable.
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
    "square",
    "circle",
    "triangle",
    "hexagon",
    "octagon",
    "parallelogram",
    "star",
    "arrow_right",
    "pentagon",
    "diamond",
    "rhombus",
    "trapezoid",
    "triangle_up",
    "triangle_down",
    "ellipse",
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
            raise MiroError(
                f"{method} {path} -> HTTP {response.status_code}: {detail}"
            )
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
        """Create an item of the given type (sticky_note, card, shape, ...)."""
        body: Dict[str, Any] = {"type": item_type}
        for key, value in {
            "data": data,
            "style": style,
            "position": position,
            "geometry": geometry,
            "parent": {"id": parent_id} if parent_id else None,
        }.items():
            if value is not None:
                body[key] = value
        return self._request("POST", f"/boards/{board_id}/items", json=body)

    def update_item(
        self,
        board_id: str,
        item_id: str,
        *,
        data: Optional[Dict[str, Any]] = None,
        style: Optional[Dict[str, Any]] = None,
        position: Optional[Dict[str, Any]] = None,
        geometry: Optional[Dict[str, Any]] = None,
        tag_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Partially update an item. Only supplied fields are changed."""
        body = {
            key: value
            for key, value in {
                "data": data,
                "style": style,
                "position": position,
                "geometry": geometry,
                "tagIds": tag_ids,
            }.items()
            if value is not None
        }
        return self._request(
            "PATCH", f"/boards/{board_id}/items/{item_id}", json=body
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
    ) -> Dict[str, Any]:
        """Create a sticky note at the given coordinates."""
        return self.create_item(
            board_id,
            "sticky_note",
            data={"content": content},
            style={"fillColor": color},
            position={"x": x, "y": y, "origin": "center"},
            geometry={"width": 180},
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
    ) -> Dict[str, Any]:
        """Create a card with an optional title, description, and assignee."""
        data: Dict[str, Any] = {
            "title": title,
            "description": description,
            "assignee": {"id": assignee_id} if assignee_id else None,
        }
        return self.create_item(
            board_id,
            "card",
            data=data,
            position={"x": x, "y": y, "origin": "center"},
            geometry={"width": 320},
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
            data={"content": content, "shapeType": shape_type},
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
    ) -> Dict[str, Any]:
        """Create a frame to group items visually."""
        return self.create_item(
            board_id,
            "frame",
            data={"title": title},
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
            data={"url": url},
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
        preview_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a document (link preview) item."""
        data = {"title": title, "url": url}
        if preview_url:
            data["previewUrl"] = preview_url
        return self.create_item(
            board_id,
            "document",
            data=data,
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
        text_color: str = "#ffffff",
    ) -> Dict[str, Any]:
        """Create a tag with the given title and colors."""
        return self._request(
            "POST",
            f"/boards/{board_id}/tags",
            json={
                "tag": {
                    "title": title,
                    "fillColor": fill_color,
                    "textColor": text_color,
                }
            },
        )

    def assign_tag(self, board_id: str, item_id: str, tag_id: str) -> Dict[str, Any]:
        """Assign a tag to an item (replaces existing tags on the item)."""
        return self.update_item(board_id, item_id, tag_ids=[tag_id])

    def move_item(
        self,
        board_id: str,
        item_id: str,
        *,
        x: float,
        y: float,
        origin: str = "center",
    ) -> Dict[str, Any]:
        """Move an item to new coordinates."""
        return self.update_item(
            board_id, item_id, position={"x": x, "y": y, "origin": origin}
        )

    def set_sticky_note_text(
        self, board_id: str, item_id: str, content: str
    ) -> Dict[str, Any]:
        """Replace the content of a sticky note."""
        return self.update_item(board_id, item_id, data={"content": content})

    def resize_item(
        self,
        board_id: str,
        item_id: str,
        *,
        width: Optional[float] = None,
        height: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Resize an item. Omitted dimensions keep their current value."""
        geometry: Optional[Dict[str, Any]] = {}
        if width:
            geometry["width"] = width
        if height:
            geometry["height"] = height
        return self.update_item(board_id, item_id, geometry=geometry or None)

    def set_item_color(
        self, board_id: str, item_id: str, color: str
    ) -> Dict[str, Any]:
        """Set the fill color of a sticky note or shape."""
        return self.update_item(board_id, item_id, style={"fillColor": color})

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
        data = {}
        if content is not None:
            data["content"] = content
        if shape_type is not None:
            data["shapeType"] = shape_type
        style = {}
        if fill_color is not None:
            style["fillColor"] = fill_color
        if border_color is not None:
            style["borderColor"] = border_color
        return self.update_item(
            board_id,
            item_id,
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
