from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, date, datetime, time
from typing import Any

from hermes_timetree_sync.config import load_settings
from hermes_timetree_sync.timetree_auth import sign_in_with_email
from hermes_timetree_sync.timetree_client import TimeTreeClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hermes TimeTree sync bridge")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="Show local configuration status.")
    subparsers.add_parser("sign-in", help="Experimental email/password sign-in.")
    subparsers.add_parser("list-calendars", help="List TimeTree calendars.")

    create = subparsers.add_parser(
        "create-all-day",
        help="Create an all-day TimeTree event using non-interactive credentials.",
    )
    create.add_argument("--title", required=True, help="Event title, e.g. Day off.")
    create.add_argument("--date", required=True, help="Event date as YYYY-MM-DD.")

    batch = subparsers.add_parser(
        "create-all-day-batch",
        help="Create multiple all-day TimeTree events with one user lookup.",
    )
    batch.add_argument(
        "--event",
        action="append",
        required=True,
        help="Event as YYYY-MM-DD|Title. Repeat for multiple events.",
    )
    return parser


def doctor() -> int:
    settings = load_settings()
    status = {
        "timetree_session_cookie_configured": bool(settings.timetree_session_cookie),
        "timetree_email_configured": bool(settings.timetree_email),
        "timetree_password_configured": bool(settings.timetree_password),
        "timetree_calendar_id_configured": bool(settings.timetree_calendar_id),
    }
    print_json(status)
    return 0


def list_calendars() -> int:
    settings = load_settings()
    if not settings.timetree_session_cookie:
        print(
            "TIMETREE_SESSION_COOKIE is required. Configure a stored TimeTree web session "
            "for non-interactive Hermes use, or run the experimental `sign-in` command "
            "with TIMETREE_EMAIL/TIMETREE_PASSWORD configured.",
            file=sys.stderr,
        )
        return 2

    client = TimeTreeClient(session_cookie=settings.timetree_session_cookie)
    print_json(client.list_calendars())
    return 0


def _require_write_config() -> tuple[str, str] | None:
    settings = load_settings()
    missing = []
    if not settings.timetree_session_cookie:
        missing.append("TIMETREE_SESSION_COOKIE")
    if not settings.timetree_calendar_id:
        missing.append("TIMETREE_CALENDAR_ID")
    if missing:
        print(
            f"{', '.join(missing)} required for non-interactive TimeTree writes.",
            file=sys.stderr,
        )
        return None
    assert settings.timetree_session_cookie is not None
    assert settings.timetree_calendar_id is not None
    return settings.timetree_session_cookie, settings.timetree_calendar_id


def _current_user_id(client: TimeTreeClient) -> str | None:
    current_user = client.get_current_user()
    user_id = current_user.get("id")
    if isinstance(user_id, int):
        return str(user_id)
    if isinstance(user_id, str) and user_id:
        return user_id
    return None


def create_all_day(*, title: str, event_date: str) -> int:
    config = _require_write_config()
    if config is None:
        return 2
    session_cookie, calendar_id = config

    client = TimeTreeClient(session_cookie=session_cookie)
    user_id = _current_user_id(client)
    if not user_id:
        print("Could not determine current TimeTree user id.", file=sys.stderr)
        return 1

    payload = build_all_day_event_payload(title=title, event_date=event_date, attendee_id=user_id)
    print_json(client.create_event(calendar_id, payload))
    return 0


def parse_batch_event(raw_event: str) -> tuple[str, str]:
    event_date, separator, title = raw_event.partition("|")
    if not separator or not event_date.strip() or not title.strip():
        raise ValueError("batch events must use YYYY-MM-DD|Title")
    date.fromisoformat(event_date.strip())
    return event_date.strip(), title.strip()


def create_all_day_batch(raw_events: Sequence[str]) -> int:
    config = _require_write_config()
    if config is None:
        return 2
    session_cookie, calendar_id = config

    try:
        events = [parse_batch_event(raw_event) for raw_event in raw_events]
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    client = TimeTreeClient(session_cookie=session_cookie)
    user_id = _current_user_id(client)
    if not user_id:
        print("Could not determine current TimeTree user id.", file=sys.stderr)
        return 1

    created: list[dict[str, Any]] = []
    for event_date, title in events:
        payload = build_all_day_event_payload(title=title, event_date=event_date, attendee_id=user_id)
        response = client.create_event(calendar_id, payload)
        event = response.get("event") if isinstance(response, dict) else None
        created.append(event if isinstance(event, dict) else response)
    print_json({"events": created})
    return 0


def build_all_day_event_payload(*, title: str, event_date: str, attendee_id: str) -> dict[str, Any]:
    parsed_date = date.fromisoformat(event_date)
    timestamp_ms = int(datetime.combine(parsed_date, time.min, tzinfo=UTC).timestamp() * 1000)
    return {
        "title": title,
        "all_day": True,
        "start_at": timestamp_ms,
        "start_timezone": "UTC",
        "end_at": timestamp_ms,
        "end_timezone": "UTC",
        "category": 1,
        "type": 0,
        "attendees": [attendee_id],
        "alerts": [],
        "recurrences": [],
        "location": "",
        "location_lat": None,
        "location_lon": None,
        "url": None,
        "note": None,
        "attachment": {"virtual_user_attendees": []},
        "files": [],
    }


def sign_in() -> int:
    settings = load_settings()
    if not settings.timetree_email or not settings.timetree_password:
        print(
            "TIMETREE_EMAIL and TIMETREE_PASSWORD are required for email/password sign-in.",
            file=sys.stderr,
        )
        return 2

    session_cookie = sign_in_with_email(
        email=settings.timetree_email,
        password=settings.timetree_password,
    )
    print(f"TIMETREE_SESSION_COOKIE={session_cookie}")
    return 0


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "doctor":
        return doctor()
    if args.command == "sign-in":
        return sign_in()
    if args.command == "list-calendars":
        return list_calendars()
    if args.command == "create-all-day":
        return create_all_day(title=args.title, event_date=args.date)
    if args.command == "create-all-day-batch":
        return create_all_day_batch(args.event)
    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
