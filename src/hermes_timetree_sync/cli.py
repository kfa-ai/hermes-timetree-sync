from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any

from hermes_timetree_sync.config import load_settings
from hermes_timetree_sync.timetree_client import TimeTreeClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hermes TimeTree sync bridge")
    parser.add_argument(
        "command",
        choices=["doctor", "list-calendars"],
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
            "TIMETREE_SESSION_COOKIE is required. For Apple-linked TimeTree accounts, "
            "sign in with Apple in a browser and provide the browser session cookie; "
            "email/password auth is not needed for this command.",
            file=sys.stderr,
        )
        return 2

    client = TimeTreeClient(session_cookie=settings.timetree_session_cookie)
    print_json(client.list_calendars())
    return 0


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "doctor":
        return doctor()
    if args.command == "list-calendars":
        return list_calendars()
    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
