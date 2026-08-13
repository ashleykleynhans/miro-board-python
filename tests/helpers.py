"""Shared fake HTTP layer so tests run without hitting the Miro API."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import miro_client
from miro_client import API_BASE


class FakeResponse:
    """Minimal stand-in for requests.Response."""

    def __init__(
        self,
        status_code: int = 200,
        payload: Optional[Any] = None,
        text: str = "",
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text or ("" if payload is None else json.dumps(payload))

    def json(self) -> Any:
        return self._payload

    @property
    def content(self) -> bytes:
        if self._payload is None:
            return b""
        return json.dumps(self._payload).encode()


class FakeSession:
    """In-memory requests.Session replacement that records outgoing calls."""

    def __init__(self, responses: Optional[List[FakeResponse]] = None) -> None:
        self.headers: Dict[str, str] = {}
        self.calls: List[Dict[str, Any]] = []
        self.responses: List[FakeResponse] = list(responses or [])

    def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> FakeResponse:
        path = url[len(API_BASE):] if url.startswith(API_BASE) else url
        self.calls.append({"method": method, "url": path, "params": params, "json": json})
        if self.responses:
            return self.responses.pop(0)
        return FakeResponse(200, {"id": "fallback"})


def install_session(
    monkeypatch, responses: Optional[List[FakeResponse]] = None
) -> FakeSession:
    """Patch requests.Session with a fake session and return it."""
    session = FakeSession(responses)
    monkeypatch.setattr(miro_client.requests, "Session", lambda: session)
    return session
