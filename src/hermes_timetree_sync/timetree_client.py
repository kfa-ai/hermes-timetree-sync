from __future__ import annotations

from typing import Any

import httpx

from hermes_timetree_sync.timetree_labels import LabelPolicy, apply_label_policy


class TimeTreeClientError(RuntimeError):
    """Raised when TimeTree returns an unexpected response."""


class TimeTreeClient:
    def __init__(
        self,
        *,
        session_cookie: str,
        base_url: str = "https://timetreeapp.com",
        http_client: httpx.Client | None = None,
        label_policy: LabelPolicy | None = None,
    ) -> None:
        if not session_cookie:
            raise ValueError("session_cookie is required")
        self._session_cookie = session_cookie
        self._base_url = base_url.rstrip("/")
        self._client = http_client or httpx.Client(timeout=30)
        self._label_policy = label_policy

    def list_calendars(self) -> list[dict[str, Any]]:
        payload = self._get("/api/v1/calendars", params={"since": 0})
        calendars = payload.get("calendars", [])
        if not isinstance(calendars, list):
            raise TimeTreeClientError("unexpected calendars payload")
        return calendars

    def list_labels(self, calendar_id: str) -> list[dict[str, Any]]:
        payload = self._get(f"/api/v1/calendar/{calendar_id}/labels")
        # Current TimeTree web payload uses `calendar_labels`; older community
        # clients have sometimes referred to this collection generically as
        # `labels`, so accept both while preferring the live web key.
        labels = payload.get("calendar_labels", payload.get("labels", []))
        if not isinstance(labels, list):
            raise TimeTreeClientError("unexpected labels payload")
        return labels

    def get_current_user(self) -> dict[str, Any]:
        payload = self._get("/api/v1/user")
        user = payload.get("user", payload)
        if not isinstance(user, dict):
            raise TimeTreeClientError("unexpected user payload")
        return user

    def sync_events(self, calendar_id: str, *, since: int | None = None) -> dict[str, Any]:
        params = {"since": since} if since is not None else None
        return self._get(f"/api/v1/calendar/{calendar_id}/events/sync", params=params)

    def create_event(
        self,
        calendar_id: str,
        payload: dict[str, Any],
        *,
        category: str | None = None,
        apply_colour_policy: bool = True,
    ) -> dict[str, Any]:
        body = (
            apply_label_policy(payload, category=category, policy=self._label_policy)
            if apply_colour_policy
            else payload
        )
        return self._request("POST", f"/api/v1/calendar/{calendar_id}/event", json=body)

    def update_event(
        self,
        calendar_id: str,
        event_id: str,
        payload: dict[str, Any],
        *,
        category: str | None = None,
        apply_colour_policy: bool = True,
    ) -> dict[str, Any]:
        body = (
            apply_label_policy(payload, category=category, policy=self._label_policy)
            if apply_colour_policy
            else payload
        )
        return self._request("PUT", f"/api/v1/calendar/{calendar_id}/event/{event_id}", json=body)

    def delete_event(self, calendar_id: str, event_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"/api/v1/calendar/{calendar_id}/event/{event_id}")

    def _get(self, path: str, *, params: dict[str, object] | None = None) -> dict[str, Any]:
        return self._request("GET", path, params=params)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, object] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._client.request(
            method,
            f"{self._base_url}{path}",
            params=params,
            headers={
                "X-Timetreea": "web/2.1.0/en",
                "Cookie": f"_session_id={self._session_cookie}",
                "Accept": "application/json",
            },
            json=json,
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
