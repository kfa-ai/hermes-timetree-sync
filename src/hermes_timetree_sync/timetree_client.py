from __future__ import annotations

from typing import Any

import httpx


class TimeTreeClientError(RuntimeError):
    """Raised when TimeTree returns an unexpected response."""


class TimeTreeClient:
    def __init__(
        self,
        *,
        session_cookie: str,
        base_url: str = "https://timetreeapp.com",
        http_client: httpx.Client | None = None,
    ) -> None:
        if not session_cookie:
            raise ValueError("session_cookie is required")
        self._session_cookie = session_cookie
        self._base_url = base_url.rstrip("/")
        self._client = http_client or httpx.Client(timeout=30)

    def list_calendars(self) -> list[dict[str, Any]]:
        payload = self._get("/api/v1/calendars", params={"since": 0})
        calendars = payload.get("calendars", [])
        if not isinstance(calendars, list):
            raise TimeTreeClientError("unexpected calendars payload")
        return calendars

    def list_labels(self, calendar_id: str) -> list[dict[str, Any]]:
        payload = self._get(f"/api/v1/calendar/{calendar_id}/labels")
        labels = payload.get("labels", [])
        if not isinstance(labels, list):
            raise TimeTreeClientError("unexpected labels payload")
        return labels

    def sync_events(self, calendar_id: str, *, since: int | None = None) -> dict[str, Any]:
        params = {"since": since} if since is not None else None
        return self._get(f"/api/v1/calendar/{calendar_id}/events/sync", params=params)

    def _get(self, path: str, *, params: dict[str, object] | None = None) -> dict[str, Any]:
        response = self._client.get(
            f"{self._base_url}{path}",
            params=params,
            headers={
                "X-Timetreea": "web/2.1.0/en",
                "Cookie": f"_session_id={self._session_cookie}",
                "Accept": "application/json",
            },
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise TimeTreeClientError(
                f"TimeTree request failed with HTTP {exc.response.status_code}"
            ) from exc

        payload = response.json()
        if not isinstance(payload, dict):
            raise TimeTreeClientError("unexpected non-object JSON response")
        return payload
