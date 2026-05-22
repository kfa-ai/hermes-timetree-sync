from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo
from typing import Any

from hermes_timetree_sync.config import load_settings
from hermes_timetree_sync.timetree_auth import sign_in_with_email
from hermes_timetree_sync.timetree_client import TimeTreeClient
from hermes_timetree_sync.timetree_labels import apply_label_policy


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

    timed = subparsers.add_parser(
        "create-timed",
        help="Create one timed TimeTree event through authenticated Safari page context.",
    )
    timed.add_argument("--title", required=True, help="Event title.")
    timed.add_argument("--start", required=True, help="Start as ISO local datetime, e.g. 2026-05-24T12:00.")
    timed.add_argument("--end", required=True, help="End as ISO local datetime, e.g. 2026-05-24T18:00.")
    timed.add_argument("--timezone", default="Australia/Melbourne", help="IANA timezone for naive datetimes.")
    timed.add_argument("--category", default=None, help="Optional TimeTree label policy category, e.g. lynsey.")
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


def _parse_timed_datetime(value: str, timezone: str) -> datetime:
    tz = ZoneInfo(timezone)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=tz)
    return parsed.astimezone(tz)


def build_timed_event_payload(
    *,
    title: str,
    start: str,
    end: str,
    timezone: str = "Australia/Melbourne",
    attendee_id: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    start_dt = _parse_timed_datetime(start, timezone)
    end_dt = _parse_timed_datetime(end, timezone)
    if end_dt <= start_dt:
        raise ValueError("end must be after start")
    payload: dict[str, Any] = {
        "title": title,
        "all_day": False,
        "start_at": int(start_dt.timestamp() * 1000),
        "start_timezone": timezone,
        "end_at": int(end_dt.timestamp() * 1000),
        "end_timezone": timezone,
        "category": 1,
        "type": 0,
        "attendees": [attendee_id] if attendee_id else [],
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
    return apply_label_policy(payload, category=category)


def create_timed_with_safari(
    *,
    title: str,
    start: str,
    end: str,
    timezone: str = "Australia/Melbourne",
    category: str | None = None,
) -> int:
    config = _require_write_config()
    if config is None:
        return 2
    _, calendar_id = config
    try:
        body_template = build_timed_event_payload(
            title=title,
            start=start,
            end=end,
            timezone=timezone,
            category=category,
        )
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        result = _run_safari_timed_create(calendar_id=calendar_id, body_template=body_template)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print_json(result)
    return 0


def _run_safari_timed_create(*, calendar_id: str, body_template: dict[str, Any]) -> dict[str, Any]:
    subprocess.run(
        ["osascript", "-e", f'tell application "Safari" to open location "https://timetreeapp.com/calendars/{calendar_id}"'],
        text=True,
        capture_output=True,
        timeout=15,
        check=True,
    )
    start_at = body_template["start_at"]
    end_at = body_template["end_at"]
    title = body_template["title"]
    js = f"""
(async () => {{
  const result = {{ ok: false, status: null, event: null, verified: false, errors: [] }};
  try {{
    const calendarId = {json.dumps(str(calendar_id))};
    const body = {json.dumps(body_template)};
    const expectedTitle = {json.dumps(title)};
    const expectedStartAt = {int(start_at)};
    const expectedEndAt = {int(end_at)};
    const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';
    const headers = {{'Content-Type':'application/json','Accept':'application/json','X-TimeTreeA':'web/2.1.0/en'}};
    if (csrf) headers['X-CSRF-Token'] = csrf;
    const userResp = await fetch('/api/v1/user', {{credentials:'include', headers}});
    const userPayload = await userResp.json();
    if (!userResp.ok) throw new Error(`user lookup failed: ${{userResp.status}}`);
    const userId = (userPayload.user || userPayload).id;
    body.attendees = [userId];
    const resp = await fetch(`/api/v1/calendar/${{calendarId}}/event`, {{method:'POST', credentials:'include', headers, body: JSON.stringify(body)}});
    result.status = resp.status;
    const payload = await resp.json().catch(() => ({{}}));
    if (!resp.ok) throw new Error(`create failed: ${{resp.status}} ${{JSON.stringify(payload).slice(0, 200)}}`);
    const created = payload.event || payload;
    result.event = {{id: created.id, title: created.title, start_at: created.start_at, end_at: created.end_at, label_id: created.label_id, all_day: created.all_day}};
    const syncResp = await fetch(`/api/v1/calendar/${{calendarId}}/events/sync`, {{credentials:'include', headers}});
    const syncPayload = await syncResp.json();
    if (!syncResp.ok) throw new Error(`verify sync failed: ${{syncResp.status}}`);
    const events = syncPayload.events || [];
    result.verified = events.some(e => e.id === created.id && e.title === expectedTitle && e.start_at === expectedStartAt && e.end_at === expectedEndAt && e.all_day === false);
    result.ok = true;
  }} catch (e) {{
    result.errors.push(String(e && e.message ? e.message : e));
  }}
  window.__hermesTimedCreateResult = result;
}})();
"""
    script = "\n".join([
        "delay 5",
        'tell application "Safari"',
        f"  do JavaScript {json.dumps(js)} in current tab of front window",
        "end tell",
        "delay 4",
        'tell application "Safari"',
        '  set r to do JavaScript "JSON.stringify(window.__hermesTimedCreateResult)" in current tab of front window',
        "end tell",
        "return r",
    ])
    try:
        completed = subprocess.run(["osascript"], input=script, text=True, capture_output=True, timeout=35, check=True)
        payload = json.loads(completed.stdout)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Safari timed event create failed: {exc}") from exc
    if not payload.get("ok"):
        raise RuntimeError(f"Safari timed event create returned errors: {payload.get('errors') or payload}")
    if not payload.get("verified"):
        raise RuntimeError(f"Timed event was created but sync verification failed: {payload.get('event')}")
    return {"event": payload.get("event"), "source": "safari", "verified": True}


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
    if args.command == "create-timed":
        return create_timed_with_safari(
            title=args.title,
            start=args.start,
            end=args.end,
            timezone=args.timezone,
            category=args.category,
        )
    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
