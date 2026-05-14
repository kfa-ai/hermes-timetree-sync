from __future__ import annotations

import json

import httpx

from hermes_timetree_sync.timetree_auth import TimeTreeAuthError, sign_in_with_email


def test_sign_in_with_email_posts_expected_payload_and_returns_session_cookie() -> None:
    seen_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_request
        seen_request = request
        return httpx.Response(
            200,
            json={"ok": True},
            headers={"set-cookie": "_session_id=session-123; Path=/; HttpOnly"},
            request=request,
        )

    session_cookie = sign_in_with_email(
        email="person@example.com",
        password="pw-123",
        uuid="fixeduuid",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert session_cookie == "session-123"
    assert seen_request is not None
    assert str(seen_request.url) == "https://timetreeapp.com/api/v1/auth/email/signin"
    assert seen_request.method == "PUT"
    assert seen_request.headers["x-timetreea"] == "web/2.1.0/en"
    assert seen_request.headers["content-type"] == "application/json"
    assert json.loads(seen_request.content) == {
        "uid": "person@example.com",
        "password": "pw-123",
        "uuid": "fixeduuid",
    }


def test_sign_in_with_email_wraps_auth_failure_without_leaking_password() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "bad credentials"}, request=request)

    try:
        sign_in_with_email(
            email="person@example.com",
            password="super-secret-password",
            uuid="fixeduuid",
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        )
    except TimeTreeAuthError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected TimeTreeAuthError")

    assert "401" in message
    assert "super-secret-password" not in message


def test_sign_in_with_email_errors_when_response_has_no_session_cookie() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True}, request=request)

    try:
        sign_in_with_email(
            email="person@example.com",
            password="pw-123",
            uuid="fixeduuid",
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        )
    except TimeTreeAuthError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected TimeTreeAuthError")

    assert "session cookie" in message
