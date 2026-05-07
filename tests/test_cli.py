from __future__ import annotations

import json

from hermes_timetree_sync import cli
from hermes_timetree_sync.cli import build_parser


def test_parser_accepts_doctor_command() -> None:
    args = build_parser().parse_args(["doctor"])
    assert args.command == "doctor"


def test_parser_accepts_list_calendars_command() -> None:
    args = build_parser().parse_args(["list-calendars"])
    assert args.command == "list-calendars"


def test_list_calendars_prints_calendar_json(monkeypatch, capsys) -> None:
    monkeypatch.setenv("TIMETREE_SESSION_COOKIE", "secret-cookie")

    class FakeClient:
        def __init__(self, *, session_cookie: str) -> None:
            assert session_cookie == "secret-cookie"

        def list_calendars(self) -> list[dict[str, str]]:
            return [{"id": "cal_1", "name": "Family"}]

    monkeypatch.setattr(cli, "TimeTreeClient", FakeClient)

    exit_code = cli.main(["list-calendars"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == [{"id": "cal_1", "name": "Family"}]


def test_list_calendars_without_cookie_explains_apple_login_path(monkeypatch, capsys) -> None:
    monkeypatch.delenv("TIMETREE_SESSION_COOKIE", raising=False)

    exit_code = cli.main(["list-calendars"])

    assert exit_code == 2
    err = capsys.readouterr().err
    assert "TIMETREE_SESSION_COOKIE" in err
    assert "Apple" in err
    assert "browser session cookie" in err
