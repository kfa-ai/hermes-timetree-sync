from __future__ import annotations

import argparse
import json

from hermes_timetree_sync.config import load_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hermes TimeTree sync bridge")
    parser.add_argument(
        "command",
        choices=["doctor"],
        help="Command to run. More commands will be added after the read-only client is implemented.",
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
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "doctor":
        return doctor()
    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
