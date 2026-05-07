from __future__ import annotations

import uuid as uuid_lib
from http.cookies import SimpleCookie

import httpx


class TimeTreeAuthError(RuntimeError):
    """Raised when TimeTree email/password authentication fails."""


def sign_in_with_email(
    *,
    email: str,
    password: str,
    uuid: str | None = None,
    base_url: str = "https://timetreeapp.com",
    http_client: httpx.Client | None = None,
) -> str:
    client = http_client or httpx.Client(timeout=30)
    device_uuid = uuid or uuid_lib.uuid4().hex
    response = client.put(
        f"{base_url.rstrip('/')}/api/v1/auth/email/signin",
        json={"uid": email, "password": password, "uuid": device_uuid},
        headers={
            "X-Timetreea": "web/2.1.0/en",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise TimeTreeAuthError(
            f"TimeTree email/password sign-in failed with HTTP {exc.response.status_code}"
        ) from exc

    session_cookie = _extract_session_cookie(response)
    if not session_cookie:
        raise TimeTreeAuthError("TimeTree email/password sign-in did not return a session cookie")
    return session_cookie


def _extract_session_cookie(response: httpx.Response) -> str | None:
    for header in response.headers.get_list("set-cookie"):
        cookie = SimpleCookie()
        cookie.load(header)
        if "_session_id" in cookie:
            return cookie["_session_id"].value
    return None
