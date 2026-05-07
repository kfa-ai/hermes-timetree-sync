from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any

from hermes_timetree_sync.config import load_settings
from hermes_timetree_sync.timetree_auth import sign_in_with_email
from hermes_timetree_sync.timetree_client import TimeTreeClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hermes TimeTree sync bridge")
    parser.add_argument(
        "command",
        choices=["doctor", "sign-in", "list-calendars"],
        help="Command to run.",
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
            "TIMETREE_SESSION_COOKIE is required. Either run `uv run hermes-timetree-sync "
            "sign-in` with TIMETREE_EMAIL/TIMETREE_PASSWORD configured, or provide a "
            "browser session cookie from an already signed-in TimeTree web session.",
            file=sys.stderr,
        )
        return 2

    client = TimeTreeClient(session_cookie=settings.timetree_session_cookie)
    print_json(client.list_calendars())
    return 0


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
    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
