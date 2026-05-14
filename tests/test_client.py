from __future__ import annotations

import json

import httpx

from hermes_timetree_sync.timetree_client import TimeTreeClient, TimeTreeClientError
from hermes_timetree_sync.timetree_labels import LabelPolicy


def json_response(payload: object) -> httpx.Response:
    return httpx.Response(200, json=payload)


def test_list_calendars_uses_session_cookie_and_web_user_agent() -> None:
    seen_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_request
        seen_request = request
        return json_response({"calendars": [{"id": "cal_1", "name": "Family"}]})

    transport = httpx.MockTransport(handler)
    client = TimeTreeClient(session_cookie="secret-cookie", http_client=httpx.Client(transport=transport))

    calendars = client.list_calendars()

    assert calendars == [{"id": "cal_1", "name": "Family"}]
    assert seen_request is not None
    assert str(seen_request.url) == "https://timetreeapp.com/api/v1/calendars?since=0"
    assert seen_request.headers["x-timetreea"] == "web/2.1.0/en"
    assert seen_request.headers["cookie"] == "_session_id=secret-cookie"


def test_sync_events_fetches_calendar_sync_endpoint() -> None:
    seen_url = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_url
        seen_url = str(request.url)
        return json_response({"events": [{"id": "evt_1", "title": "School pickup"}], "since": 123})

    transport = httpx.MockTransport(handler)
    client = TimeTreeClient(session_cookie="secret-cookie", http_client=httpx.Client(transport=transport))

    result = client.sync_events("cal_1")

    assert seen_url == "https://timetreeapp.com/api/v1/calendar/cal_1/events/sync"
    assert result == {"events": [{"id": "evt_1", "title": "School pickup"}], "since": 123}


def test_sync_events_can_resume_from_since_cursor() -> None:
    seen_url = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_url
        seen_url = str(request.url)
        return json_response({"events": []})

    transport = httpx.MockTransport(handler)
    client = TimeTreeClient(session_cookie="secret-cookie", http_client=httpx.Client(transport=transport))

    client.sync_events("cal_1", since=123)

    assert seen_url == "https://timetreeapp.com/api/v1/calendar/cal_1/events/sync?since=123"


def test_list_labels_fetches_calendar_labels() -> None:
    seen_url = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_url
        seen_url = str(request.url)
        return json_response({"calendar_labels": [{"id": "lbl_1", "name": "Kids"}]})

    transport = httpx.MockTransport(handler)
    client = TimeTreeClient(session_cookie="secret-cookie", http_client=httpx.Client(transport=transport))

    labels = client.list_labels("cal_1")

    assert seen_url == "https://timetreeapp.com/api/v1/calendar/cal_1/labels"
    assert labels == [{"id": "lbl_1", "name": "Kids"}]


def test_list_labels_accepts_legacy_labels_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response({"labels": [{"id": "lbl_1", "name": "Kids"}]})

    transport = httpx.MockTransport(handler)
    client = TimeTreeClient(session_cookie="secret-cookie", http_client=httpx.Client(transport=transport))

    labels = client.list_labels("cal_1")

    assert labels == [{"id": "lbl_1", "name": "Kids"}]


def test_http_errors_are_wrapped_without_leaking_cookie() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"}, request=request)

    transport = httpx.MockTransport(handler)
    client = TimeTreeClient(session_cookie="secret-cookie", http_client=httpx.Client(transport=transport))

    try:
        client.list_calendars()
    except TimeTreeClientError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected TimeTreeClientError")

    assert "401" in message
    assert "secret-cookie" not in message


def test_create_event_applies_colour_policy_label() -> None:
    seen_json: dict[str, object] | None = None
    label_policy = LabelPolicy.from_mapping(
        {"rules": [{"category": "example-medical", "label_id": 3, "terms": ["ultrasound"]}]}
    )

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_json
        seen_json = dict(json.loads(request.content))
        return json_response({"event": {"id": "evt_1", **seen_json}})

    transport = httpx.MockTransport(handler)
    client = TimeTreeClient(
        session_cookie="secret-cookie",
        http_client=httpx.Client(transport=transport),
        label_policy=label_policy,
    )

    result = client.create_event("cal_1", {"title": "Ultrasound BoxHill"})

    assert seen_json == {"title": "Ultrasound BoxHill", "label_id": 3}
    assert result["event"]["label_id"] == 3


def test_update_event_can_apply_explicit_colour_policy_category() -> None:
    seen_request: httpx.Request | None = None
    label_policy = LabelPolicy.from_mapping(
        {"rules": [{"category": "example-personal", "label_id": 5, "terms": ["day off"]}]}
    )

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_request
        seen_request = request
        return json_response({"event": {"id": "evt_1", **json.loads(request.content)}})

    transport = httpx.MockTransport(handler)
    client = TimeTreeClient(
        session_cookie="secret-cookie",
        http_client=httpx.Client(transport=transport),
        label_policy=label_policy,
    )

    client.update_event("cal_1", "evt_1", {"title": "Day off"}, category="example-personal")

    assert seen_request is not None
    assert str(seen_request.url) == "https://timetreeapp.com/api/v1/calendar/cal_1/event/evt_1"
    assert json.loads(seen_request.content)["label_id"] == 5


def test_delete_event_uses_verified_endpoint() -> None:
    seen_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_request
        seen_request = request
        return json_response({})

    transport = httpx.MockTransport(handler)
    client = TimeTreeClient(session_cookie="secret-cookie", http_client=httpx.Client(transport=transport))

    assert client.delete_event("cal_1", "evt_1") == {}
    assert seen_request is not None
    assert seen_request.method == "DELETE"
    assert str(seen_request.url) == "https://timetreeapp.com/api/v1/calendar/cal_1/event/evt_1"
